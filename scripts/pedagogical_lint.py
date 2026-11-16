from __future__ import annotations

import argparse
import ast
import io
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

SUPPRESSION_MARKERS = (
    "type: ignore",
    "noqa",
    "@ts-ignore",
    "@ts-expect-error",
    "@ts-nocheck",
    "eslint-disable",
)
DEBT_MARKERS = ("TODO", "FIXME", "HACK", "WORKAROUND")

MSG_SUPPRESSION = "AGENTE: Nunca suprima erros de tipo ou lint. Corrija a tipagem ou a lógica na origem."
MSG_INLINE_COMMENT = (
    "AGENTE: Comentários inline são proibidos pois frequentemente mascaram gambiarras. "
    "Torne o código autoexplicativo através de nomes claros e tipos."
)
MSG_BLOCKING_API = (
    "AGENTE: Não use chamadas bloqueantes ('requests', 'time.sleep'). "
    "Utilize o cliente HTTP assíncrono do projeto e 'await asyncio.sleep()'."
)


@dataclass(frozen=True)
class LintViolation:
    """Represents a single deterministic pedagogical lint violation."""

    file_path: str
    line: int
    code: str
    message: str


def _collect_python_files(targets: list[Path]) -> list[Path]:
    files: list[Path] = []
    for target in targets:
        if target.is_file() and target.suffix == ".py":
            files.append(target)
        elif target.is_dir():
            for candidate in sorted(target.rglob("*.py")):
                if "__pycache__" not in candidate.parts and "tlc-spec-lean" not in candidate.parts:
                    files.append(candidate)
    return files


def lint_source(source: str, file_label: str) -> list[LintViolation]:
    """Inspect Python source text for suppressions, inline comments, and blocking APIs."""
    violations: list[LintViolation] = []

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError as exc:
        violations.append(
            LintViolation(
                file_path=file_label,
                line=1,
                code="SYNTAX",
                message=f"AGENTE: Erro de tokenização Python ({exc}). Corrija a sintaxe antes de prosseguir.",
            )
        )
        return violations

    for token in tokens:
        if token.type != tokenize.COMMENT:
            continue
        comment_text = token.string
        line_no = token.start[0]
        if line_no == 1 and comment_text.startswith("#!"):
            continue
        lowered = comment_text.lower()
        if any(marker in lowered for marker in SUPPRESSION_MARKERS):
            violations.append(
                LintViolation(file_path=file_label, line=line_no, code="SUPPRESSION", message=MSG_SUPPRESSION)
            )
            continue
        if any(marker in comment_text.upper() for marker in DEBT_MARKERS):
            violations.append(
                LintViolation(file_path=file_label, line=line_no, code="COMMENT", message=MSG_INLINE_COMMENT)
            )
            continue
        violations.append(
            LintViolation(file_path=file_label, line=line_no, code="COMMENT", message=MSG_INLINE_COMMENT)
        )

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        violations.append(
            LintViolation(
                file_path=file_label,
                line=exc.lineno or 1,
                code="SYNTAX",
                message=f"AGENTE: Erro de sintaxe Python ({exc.msg}). Corrija a sintaxe antes de prosseguir.",
            )
        )
        return violations

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "requests" or alias.name.startswith("requests."):
                    violations.append(
                        LintViolation(
                            file_path=file_label,
                            line=node.lineno,
                            code="TID251",
                            message=MSG_BLOCKING_API,
                        )
                    )
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            if module_name == "requests" or module_name.startswith("requests."):
                violations.append(
                    LintViolation(
                        file_path=file_label,
                        line=node.lineno,
                        code="TID251",
                        message=MSG_BLOCKING_API,
                    )
                )
            elif module_name == "time" and any(alias.name == "sleep" for alias in node.names):
                violations.append(
                    LintViolation(
                        file_path=file_label,
                        line=node.lineno,
                        code="TID251",
                        message=MSG_BLOCKING_API,
                    )
                )
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "time" and node.attr == "sleep":
                violations.append(
                    LintViolation(
                        file_path=file_label,
                        line=node.lineno,
                        code="TID251",
                        message=MSG_BLOCKING_API,
                    )
                )

    return violations


def lint_paths(paths: list[Path]) -> list[LintViolation]:
    """Run pedagogical lint rules across all Python files under the given paths."""
    violations: list[LintViolation] = []
    for py_file in _collect_python_files(paths):
        source = py_file.read_text(encoding="utf-8")
        violations.extend(lint_source(source, str(py_file)))
    return violations


def main() -> None:
    """CLI entry point for running pedagogical static checks."""
    parser = argparse.ArgumentParser(description="Run pedagogical LLM lint rules")
    parser.add_argument(
        "--path",
        dest="paths",
        action="append",
        help="File or directory to lint (defaults to scripts and tests)",
    )
    args = parser.parse_args()

    target_paths = [Path(p) for p in args.paths] if args.paths else [Path("scripts"), Path("tests")]
    violations = lint_paths(target_paths)

    if violations:
        for violation in violations:
            print(f"{violation.file_path}:{violation.line}: [{violation.code}] {violation.message}")
        sys.exit(1)

    print("Pedagogical lint PASSED: 0 suppressions, 0 inline comments, 0 blocking APIs.")
    sys.exit(0)


if __name__ == "__main__":
    main()
