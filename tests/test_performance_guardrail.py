from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "performance_guardrail", ROOT / "scripts/performance_guardrail.py"
)
assert SPEC and SPEC.loader
PERFORMANCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PERFORMANCE)


def sample_summary(value: float) -> dict:
    return {
        "summary": {
            "run_count": 3,
            "sample_count": 3,
            "physics_ms": {"median": value, "p95": value, "maximum": value},
            "static_memory_bytes": {"median": 1024, "maximum": 1024},
            "per_run_p95_ms": [value, value, value],
        },
        "samples": [
            {"physics_ms": [value], "static_memory_bytes": [1024, 1024]}
            for _ in range(3)
        ],
    }


class PerformanceGuardrailTests(unittest.TestCase):
    def test_process_affinity_is_sorted_when_available(self) -> None:
        affinity = PERFORMANCE.process_affinity()
        if affinity is not None:
            self.assertEqual(affinity, sorted(set(affinity)))
            self.assertGreater(len(affinity), 0)

    def reports(self) -> tuple[dict, dict, dict]:
        environment = {
            "redot_version": "26.2.stable.official.4f5b14aba",
            "host_os": "test-os",
            "machine": "x86_64",
            "processor": "test-cpu",
            "logical_cpu_count": 8,
            "process_cpu_count": 4,
            "cpu_affinity": [0, 1, 2, 3],
        }
        common = {
            "status": "PASS",
            "scenario_contract_sha256": "scenario",
            "fixture_manifest_sha256": "fixture",
            "runner_sha256": "runner",
            "environment": environment,
        }
        baseline = {
            **common,
            "scenarios": {
                name: sample_summary(1.0)
                for name in ("bodies-small", "bodies-medium", "bodies-high")
            },
        }
        candidate = {
            **copy.deepcopy(common),
            "scenarios": {
                name: sample_summary(1.0)
                for name in (
                    "bodies-small",
                    "bodies-medium",
                    "bodies-high",
                    "fluid-2048",
                )
            },
        }
        body_rule = {
            "median_ratio_max": 2.0,
            "median_additive_ms": 0.0,
            "p95_ratio_max": 2.0,
            "p95_additive_ms": 0.0,
            "memory_ratio_max": 2.0,
            "memory_additive_bytes": 0,
        }
        guardrail = {
            "scenario_contract_sha256": "scenario",
            "fixture_manifest_sha256": "fixture",
            "runner_sha256": "runner",
            "stability": {
                "per_run_p95_range_ms_max": 16.667,
                "per_run_memory_growth_bytes_max": 1024,
            },
            "body_scenarios": {
                name: copy.deepcopy(body_rule)
                for name in ("bodies-small", "bodies-medium", "bodies-high")
            },
            "fluid_scenario": {
                "id": "fluid-2048",
                "p95_ms_max": 100.0,
                "maximum_ms_max": 100.0,
            },
        }
        return baseline, candidate, guardrail

    def write_reports(self, directory: Path) -> tuple[Path, Path, Path, Path]:
        baseline, candidate, guardrail = self.reports()
        paths = tuple(
            directory / name
            for name in ("baseline.json", "candidate.json", "guardrail.json", "result.json")
        )
        for path, report in zip(paths[:3], (baseline, candidate, guardrail)):
            path.write_text(json.dumps(report), encoding="utf-8")
        return paths

    def test_matching_environment_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            baseline, candidate, guardrail, output = self.write_reports(Path(temp_name))
            result = PERFORMANCE.compare(baseline, candidate, guardrail, output)
            self.assertEqual(result["status"], "PASS")

    def test_affinity_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            baseline, candidate, guardrail, output = self.write_reports(Path(temp_name))
            changed = json.loads(candidate.read_text(encoding="utf-8"))
            changed["environment"]["cpu_affinity"] = [0, 1]
            candidate.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(
                PERFORMANCE.PerformanceError, "environments differ: cpu_affinity"
            ):
                PERFORMANCE.compare(baseline, candidate, guardrail, output)


if __name__ == "__main__":
    unittest.main()
