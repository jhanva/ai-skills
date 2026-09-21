import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS_SCRIPT = (
    ROOT / "plugins" / "core" / "skills" / "orchestrate" / "scripts" / "harness.py"
)


def load_harness():
    spec = importlib.util.spec_from_file_location("orchestrate_harness", HARNESS_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo cargar harness.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RouterTests(unittest.TestCase):
    def test_read_only_low_risk_task_routes_to_explorer(self) -> None:
        harness = load_harness()
        task = {
            "mode": "read",
            "risk_dimensions": {
                "ambiguity": 0,
                "coupling": 0,
                "blast_radius": 0,
                "verifiability": 0,
                "sensitivity": 0,
                "reversibility": 0,
            },
        }

        self.assertEqual(
            {"role": "explorer", "score": 0, "reason": "low-risk read-only task"},
            harness.route_task(task),
        )

    def test_sensitive_task_always_routes_to_orchestrator(self) -> None:
        harness = load_harness()
        task = {
            "mode": "write",
            "risk_dimensions": {
                "ambiguity": 0,
                "coupling": 0,
                "blast_radius": 0,
                "verifiability": 0,
                "sensitivity": 2,
                "reversibility": 0,
            },
        }

        self.assertEqual(
            {"role": "orchestrator", "score": 2, "reason": "sensitive task override"},
            harness.route_task(task),
        )


class TaskContractTests(unittest.TestCase):
    def test_contract_without_acceptance_is_rejected(self) -> None:
        harness = load_harness()
        task = {
            "task_id": "billing-create-invoice",
            "objective": "Crear factura en borrador.",
            "mode": "write",
            "allowed_paths": ["apps/web/src/modules/billing/**"],
            "forbidden_paths": [],
            "commands": ["pnpm test --filter billing"],
            "risk_dimensions": {name: 0 for name in harness.RISK_DIMENSIONS},
            "max_attempts": 2,
            "expected_result": "result-envelope-v1",
        }

        self.assertEqual(
            ["acceptance must be a non-empty list of strings"],
            harness.validate_task(task),
        )

    def test_contract_rejects_incomplete_or_out_of_range_risk_dimensions(self) -> None:
        harness = load_harness()
        task = {
            "task_id": "billing-create-invoice",
            "objective": "Crear factura en borrador.",
            "mode": "read",
            "allowed_paths": ["apps/web/src/modules/billing/**"],
            "forbidden_paths": [],
            "acceptance": ["tests pass"],
            "commands": [],
            "risk_dimensions": {
                "ambiguity": 3,
                "coupling": 0,
            },
            "max_attempts": 2,
            "expected_result": "result-envelope-v1",
        }

        self.assertEqual(
            [
                "risk_dimensions must contain exactly: ambiguity, blast_radius, coupling, "
                "reversibility, sensitivity, verifiability",
                "risk_dimensions.ambiguity must be 0, 1, or 2",
            ],
            harness.validate_task(task),
        )

    def test_contract_rejects_invalid_identity_scope_and_retry_policy(self) -> None:
        harness = load_harness()
        task = {
            "task_id": "Invalid task id",
            "objective": "",
            "mode": "write",
            "allowed_paths": [],
            "forbidden_paths": "migrations/**",
            "acceptance": ["tests pass"],
            "commands": [],
            "risk_dimensions": {name: 0 for name in harness.RISK_DIMENSIONS},
            "max_attempts": 3,
            "expected_result": "free-form",
        }

        self.assertEqual(
            [
                "task_id must use lowercase letters, digits, and hyphens",
                "objective must be a non-empty string",
                "allowed_paths must be a non-empty list of strings",
                "forbidden_paths must be a list of strings",
                "write tasks must define at least one verification command",
                "max_attempts must be 1 or 2",
                "expected_result must be result-envelope-v1",
            ],
            harness.validate_task(task),
        )

    def test_contract_rejects_unsafe_scope_patterns(self) -> None:
        harness = load_harness()
        task = {
            "task_id": "bounded-change",
            "objective": "Cambiar un modulo acotado.",
            "mode": "write",
            "allowed_paths": ["../outside/**"],
            "forbidden_paths": ["C:/secrets/**"],
            "acceptance": ["tests pass"],
            "commands": ["python -m unittest"],
            "risk_dimensions": {name: 0 for name in harness.RISK_DIMENSIONS},
            "max_attempts": 2,
            "expected_result": "result-envelope-v1",
        }

        self.assertEqual(
            [
                "allowed_paths entries must be repository-relative patterns",
                "forbidden_paths entries must be repository-relative patterns",
            ],
            harness.validate_task(task),
        )


class ResultEnvelopeTests(unittest.TestCase):
    def test_passed_result_rejects_file_outside_contract_scope(self) -> None:
        harness = load_harness()
        task = {
            "task_id": "billing-create-invoice",
            "mode": "write",
            "allowed_paths": ["apps/web/src/modules/billing/**"],
            "forbidden_paths": ["apps/web/src/modules/billing/admin/**"],
        }
        result = {
            "task_id": "billing-create-invoice",
            "status": "passed",
            "summary": "Implementado y verificado.",
            "changed_files": ["packages/db/migrations/001.sql"],
            "checks": [{"command": "pnpm test --filter billing", "result": "passed"}],
            "assumptions": [],
            "risks": [],
            "out_of_scope": [],
        }

        self.assertEqual(
            ["changed file is outside allowed_paths: packages/db/migrations/001.sql"],
            harness.validate_result(task, result),
        )

    def test_passed_result_requires_successful_checks(self) -> None:
        harness = load_harness()
        task = {
            "task_id": "billing-create-invoice",
            "mode": "write",
            "allowed_paths": ["apps/web/src/modules/billing/**"],
            "forbidden_paths": [],
        }
        result = {
            "task_id": "billing-create-invoice",
            "status": "passed",
            "summary": "Implementado con un test fallando.",
            "changed_files": ["apps/web/src/modules/billing/create-invoice.ts"],
            "checks": [{"command": "pnpm test --filter billing", "result": "failed"}],
            "assumptions": [],
            "risks": [],
            "out_of_scope": [],
        }

        self.assertEqual(
            ["passed results require at least one check and every check must pass"],
            harness.validate_result(task, result),
        )

    def test_result_rejects_absolute_or_parent_traversal_paths(self) -> None:
        harness = load_harness()
        task = {
            "task_id": "bounded-change",
            "mode": "write",
            "allowed_paths": ["**"],
            "forbidden_paths": [],
        }
        result = {
            "task_id": "bounded-change",
            "status": "passed",
            "summary": "Cambios reportados.",
            "changed_files": ["../outside.txt", "C:/secrets.txt"],
            "checks": [{"command": "python -m unittest", "result": "passed"}],
            "assumptions": [],
            "risks": [],
            "out_of_scope": [],
        }

        self.assertEqual(
            [
                "changed file must be a repository-relative path: ../outside.txt",
                "changed file must be a repository-relative path: C:/secrets.txt",
            ],
            harness.validate_result(task, result),
        )

class HarnessCliTests(unittest.TestCase):
    def test_route_command_prints_structured_decision(self) -> None:
        task = {
            "task_id": "map-billing-module",
            "objective": "Mapear dependencias de billing.",
            "mode": "read",
            "allowed_paths": ["apps/web/src/modules/billing/**"],
            "forbidden_paths": [],
            "acceptance": ["lista de dependencias con rutas"],
            "commands": [],
            "risk_dimensions": {
                "ambiguity": 0,
                "coupling": 0,
                "blast_radius": 0,
                "verifiability": 0,
                "sensitivity": 0,
                "reversibility": 0,
            },
            "max_attempts": 2,
            "expected_result": "result-envelope-v1",
        }
        with tempfile.TemporaryDirectory() as tmp:
            task_path = Path(tmp) / "task.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(HARNESS_SCRIPT), "route", str(task_path)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("explorer", json.loads(result.stdout)["role"])

if __name__ == "__main__":
    unittest.main()
