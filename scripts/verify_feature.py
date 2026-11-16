from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class FeatureStep:
    """Single command step in a feature runtime verification flow."""

    args: tuple[str, ...]


@dataclass(frozen=True)
class FeatureAssertions:
    """Deterministic runtime assertions declared for a feature."""

    expected_exit_code: int
    stdout_contains: tuple[str, ...]
    expected_paths: tuple[str, ...]


@dataclass(frozen=True)
class FeatureSpec:
    """Complete feature verification specification loaded from feature-map.yaml."""

    name: str
    description: str
    endpoint: str
    steps: tuple[FeatureStep, ...]
    assertions: FeatureAssertions


@dataclass(frozen=True)
class StepExecutionTrace:
    """Captured runtime output of a single executed command step."""

    command: list[str]
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class FeatureVerificationProof:
    """Structured runtime execution proof stored under .artifacts/<feature>/."""

    feature: str
    description: str
    endpoint: str
    timestamp_utc: str
    passed: bool
    failures: tuple[str, ...]
    steps: tuple[StepExecutionTrace, ...]


def _as_str_list(raw_value: object, context: str) -> tuple[str, ...]:
    if not isinstance(raw_value, list) or not all(isinstance(item, str) for item in raw_value):
        raise ValueError(f"AGENTE: '{context}' em feature-map.yaml deve ser uma lista de strings.")
    return tuple(raw_value)


def _resolve_step(raw_step: object, feature_name: str) -> FeatureStep:
    if not isinstance(raw_step, dict):
        raise ValueError(f"AGENTE: step inválido na feature '{feature_name}' em feature-map.yaml.")

    if sys.platform == "win32" and "windows_args" in raw_step:
        raw_args = raw_step["windows_args"]
    elif sys.platform != "win32" and "posix_args" in raw_step:
        raw_args = raw_step["posix_args"]
    elif "args" in raw_step:
        raw_args = raw_step["args"]
    else:
        raise ValueError(
            f"AGENTE: step sem 'args' compatível com a plataforma atual na feature '{feature_name}'."
        )

    return FeatureStep(args=_as_str_list(raw_args, f"{feature_name}.payload.steps"))


def load_feature_map(map_path: Path) -> dict[str, FeatureSpec]:
    """Load and validate feature definitions from feature-map.yaml."""
    raw_content = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    if not isinstance(raw_content, dict) or not isinstance(raw_content.get("features"), dict):
        raise ValueError("AGENTE: feature-map.yaml deve conter um mapeamento raiz 'features'.")

    specs: dict[str, FeatureSpec] = {}
    for feature_name, raw_spec in raw_content["features"].items():
        if not isinstance(feature_name, str) or not isinstance(raw_spec, dict):
            raise ValueError("AGENTE: Cada entrada em 'features' deve mapear um nome string para um objeto.")

        description = raw_spec.get("description")
        endpoint = raw_spec.get("endpoint")
        payload = raw_spec.get("payload")
        assertions = raw_spec.get("assertions")
        if (
            not isinstance(description, str)
            or not isinstance(endpoint, str)
            or not isinstance(payload, dict)
            or not isinstance(assertions, dict)
        ):
            raise ValueError(f"AGENTE: Especificação incompleta para a feature '{feature_name}'.")

        raw_steps = payload.get("steps")
        if not isinstance(raw_steps, list) or not raw_steps:
            raise ValueError(f"AGENTE: Feature '{feature_name}' deve definir ao menos um item em 'payload.steps'.")

        steps = tuple(_resolve_step(step, feature_name) for step in raw_steps)
        exit_code = assertions.get("exit_code", 0)
        if not isinstance(exit_code, int):
            raise ValueError(f"AGENTE: 'assertions.exit_code' deve ser inteiro na feature '{feature_name}'.")

        stdout_contains = _as_str_list(
            assertions.get("stdout_contains", []), f"{feature_name}.assertions.stdout_contains"
        )
        expected_paths = _as_str_list(
            assertions.get("expected_paths", []), f"{feature_name}.assertions.expected_paths"
        )
        specs[feature_name] = FeatureSpec(
            name=feature_name,
            description=description,
            endpoint=endpoint,
            steps=steps,
            assertions=FeatureAssertions(
                expected_exit_code=exit_code,
                stdout_contains=stdout_contains,
                expected_paths=expected_paths,
            ),
        )

    return specs


def verify_feature(spec: FeatureSpec, repo_root: Path) -> FeatureVerificationProof:
    """Execute a feature flow in isolation and write structured execution proof."""
    failures: list[str] = []
    traces: list[StepExecutionTrace] = []
    combined_stdout_parts: list[str] = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        for step in spec.steps:
            resolved_cmd = [
                arg.replace("{python}", sys.executable).replace("{temp_dir}", tmp_dir) for arg in step.args
            ]
            completed = subprocess.run(
                resolved_cmd,
                cwd=str(repo_root),
                capture_output=True,
                text=True,
            )
            traces.append(
                StepExecutionTrace(
                    command=resolved_cmd,
                    returncode=completed.returncode,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                )
            )
            combined_stdout_parts.append(completed.stdout)
            if completed.returncode != spec.assertions.expected_exit_code:
                failures.append(
                    f"Step '{' '.join(resolved_cmd)}' returned {completed.returncode}, "
                    f"expected {spec.assertions.expected_exit_code}."
                )

        combined_stdout = "\n".join(combined_stdout_parts)
        for expected_substr in spec.assertions.stdout_contains:
            if expected_substr not in combined_stdout:
                failures.append(f"Expected substring '{expected_substr}' not found in stdout.")

        for rel_path in spec.assertions.expected_paths:
            candidate = Path(tmp_dir) / rel_path
            if not candidate.exists():
                failures.append(f"Expected artifact path '{rel_path}' missing in isolated destination.")

    proof = FeatureVerificationProof(
        feature=spec.name,
        description=spec.description,
        endpoint=spec.endpoint,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        passed=len(failures) == 0,
        failures=tuple(failures),
        steps=tuple(traces),
    )

    artifact_dir = repo_root / ".artifacts" / spec.name
    artifact_dir.mkdir(parents=True, exist_ok=True)
    proof_file = artifact_dir / "execution-proof.json"
    proof_file.write_text(json.dumps(asdict(proof), indent=2, ensure_ascii=False), encoding="utf-8")
    return proof


def main() -> None:
    """CLI entry point for verifying runtime feature specifications."""
    parser = argparse.ArgumentParser(description="Verify runtime features from feature-map.yaml")
    parser.add_argument("feature", nargs="?", help="Feature name from feature-map.yaml")
    parser.add_argument("--all", action="store_true", help="Verify all features defined in feature-map.yaml")
    parser.add_argument("--root", default=str(REPO_ROOT), help="Repository root directory")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    specs = load_feature_map(repo_root / "feature-map.yaml")

    if args.all:
        selected = list(specs.values())
    elif args.feature:
        if args.feature not in specs:
            available = ", ".join(sorted(specs))
            print(f"AGENTE: Feature '{args.feature}' não encontrada em feature-map.yaml. Disponíveis: {available}")
            sys.exit(1)
        selected = [specs[args.feature]]
    else:
        available = ", ".join(sorted(specs))
        print(f"AGENTE: Informe o nome da feature ou use --all. Disponíveis: {available}")
        sys.exit(1)

    all_passed = True
    for spec in selected:
        proof = verify_feature(spec, repo_root)
        status = "PASSED" if proof.passed else "FAILED"
        print(f"[{status}] {spec.name} -> .artifacts/{spec.name}/execution-proof.json")
        if not proof.passed:
            all_passed = False
            for failure in proof.failures:
                print(f"  - {failure}")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
