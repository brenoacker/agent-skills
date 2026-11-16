from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

DOMAIN_FORBIDDEN_INTERNAL = (
    "scripts.infrastructure",
    "scripts.validate",
    "scripts.verify_feature",
    "scripts.pedagogical_lint",
    "scripts.check_deps",
    "tests",
)
DOMAIN_FORBIDDEN_SIDE_EFFECTS = ("os", "subprocess", "urllib", "http", "requests", "shutil", "socket")
INFRA_FORBIDDEN_PREFIXES = (
    "scripts.validate",
    "scripts.verify_feature",
    "scripts.pedagogical_lint",
    "scripts.check_deps",
    "tests",
)


@dataclass(frozen=True)
class DependencyViolation:
    """Represents an architectural boundary or dependency cycle violation."""

    source_module: str
    target_module: str
    line: int
    message: str


def _module_name_from_path(root: Path, py_file: Path) -> str:
    rel = py_file.relative_to(root)
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _matches_prefix(target: str, prefix: str) -> bool:
    return target == prefix or target.startswith(f"{prefix}.")


def _extract_imports(py_file: Path, current_module: str) -> list[tuple[str, int]]:
    source = py_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(py_file))
    imports: list[tuple[str, int]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            base_module = node.module or ""
            if node.level > 0:
                pkg_parts = current_module.split(".")
                if py_file.stem != "__init__":
                    pkg_parts = pkg_parts[:-1]
                trim = node.level - 1
                anchor = pkg_parts[:-trim] if trim > 0 else pkg_parts
                resolved_base = ".".join([*anchor, base_module]) if base_module else ".".join(anchor)
            else:
                resolved_base = base_module

            if resolved_base:
                imports.append((resolved_base, node.lineno))
                for alias in node.names:
                    imports.append((f"{resolved_base}.{alias.name}", node.lineno))

    return imports


def _collect_module_files(root: Path) -> dict[str, Path]:
    modules: dict[str, Path] = {}
    for folder_name in ("scripts", "tests"):
        base_dir = root / folder_name
        if not base_dir.is_dir():
            continue
        for py_file in sorted(base_dir.rglob("*.py")):
            if "__pycache__" in py_file.parts:
                continue
            mod_name = _module_name_from_path(root, py_file)
            if mod_name:
                modules[mod_name] = py_file
    return modules


def _detect_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    visited: set[str] = set()
    active_stack: list[str] = []
    active_set: set[str] = set()
    cycles: list[list[str]] = []

    def dfs(node: str) -> None:
        visited.add(node)
        active_stack.append(node)
        active_set.add(node)
        for neighbor in sorted(graph.get(node, set())):
            if neighbor in active_set:
                start_idx = active_stack.index(neighbor)
                cycles.append([*active_stack[start_idx:], neighbor])
            elif neighbor not in visited and neighbor in graph:
                dfs(neighbor)
        active_stack.pop()
        active_set.remove(node)

    for module_name in sorted(graph):
        if module_name not in visited:
            dfs(module_name)

    return cycles


def check_dependencies(root: Path) -> list[DependencyViolation]:
    """Check architectural boundaries and circular dependencies under root."""
    modules = _collect_module_files(root)
    violations: list[DependencyViolation] = []
    internal_graph: dict[str, set[str]] = {name: set() for name in modules if _matches_prefix(name, "scripts")}

    for source_module, py_file in sorted(modules.items()):
        imports = _extract_imports(py_file, source_module)
        for target, line_no in imports:
            if _matches_prefix(source_module, "scripts.domain"):
                if any(_matches_prefix(target, forbidden) for forbidden in DOMAIN_FORBIDDEN_INTERNAL) or any(
                    _matches_prefix(target, forbidden) for forbidden in DOMAIN_FORBIDDEN_SIDE_EFFECTS
                ):
                    violations.append(
                        DependencyViolation(
                            source_module=source_module,
                            target_module=target,
                            line=line_no,
                            message=(
                                "AGENTE: Violação de fronteira arquitetural — a camada 'scripts/domain' deve conter "
                                f"apenas regras puras e não pode importar '{target}' em '{source_module}'. "
                                "Mova efeitos colaterais e I/O para 'scripts/infrastructure/'."
                            ),
                        )
                    )

            elif _matches_prefix(source_module, "scripts.infrastructure"):
                if any(_matches_prefix(target, forbidden) for forbidden in INFRA_FORBIDDEN_PREFIXES):
                    violations.append(
                        DependencyViolation(
                            source_module=source_module,
                            target_module=target,
                            line=line_no,
                            message=(
                                "AGENTE: Violação de fronteira arquitetural — 'scripts/infrastructure' "
                                f"('{source_module}') não pode importar da camada de entrada/CLI ou de 'tests' "
                                f"('{target}')."
                            ),
                        )
                    )

            if _matches_prefix(source_module, "scripts") and _matches_prefix(target, "tests"):
                violations.append(
                    DependencyViolation(
                        source_module=source_module,
                        target_module=target,
                        line=line_no,
                        message=(
                            f"AGENTE: Violação de fronteira arquitetural — código de produção em '{source_module}' "
                            f"não pode importar de 'tests' ('{target}')."
                        ),
                    )
                )

            if source_module in internal_graph and target in internal_graph and target != source_module:
                internal_graph[source_module].add(target)

    for cycle in _detect_cycles(internal_graph):
        cycle_text = " -> ".join(cycle)
        violations.append(
            DependencyViolation(
                source_module=cycle[0],
                target_module=cycle[-1],
                line=1,
                message=(
                    f"AGENTE: Dependência circular detectada entre módulos: {cycle_text}. "
                    "Extraia interfaces ou tipos compartilhados para 'scripts/domain/'."
                ),
            )
        )

    return violations


def main() -> None:
    """CLI entry point for architectural boundary and cycle checks."""
    parser = argparse.ArgumentParser(description="Check architectural dependency boundaries")
    parser.add_argument("--root", default=".", help="Repository root directory")
    args = parser.parse_args()

    violations = check_dependencies(Path(args.root).resolve())
    if violations:
        for violation in violations:
            print(f"{violation.source_module}:{violation.line}: {violation.message}")
        sys.exit(1)

    print("Dependency check PASSED: All architectural boundaries and layer contracts are intact.")
    sys.exit(0)


if __name__ == "__main__":
    main()
