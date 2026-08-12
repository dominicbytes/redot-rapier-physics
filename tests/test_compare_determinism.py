from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "compare_determinism", ROOT / "scripts/compare_determinism.py"
)
assert SPEC and SPEC.loader
COMPARE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMPARE)


def replay(os_name: str) -> dict:
    frame = [["0000000000000000"] * 9]
    return {
        "protocol": COMPARE.PROTOCOL,
        "profile": {
            "simulation_frames": 300,
            "physics_ticks_per_second": 60,
            "body_count": 1,
            "seed": 0,
            "precision": "single",
            "solver_parallel": False,
            "redot_separate_thread": False,
        },
        "observed": {"os": os_name, "arch": "x86_64"},
        "frames": [copy.deepcopy(frame) for _ in range(300)],
    }


class DeterminismComparisonTests(unittest.TestCase):
    def test_platform_metadata_is_not_part_of_the_canonical_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            paths = []
            for name in ("Windows", "Linux"):
                path = temp / f"{name}.json"
                path.write_text(json.dumps(replay(name)), encoding="utf-8")
                paths.append(path)
            result = COMPARE.compare_replays(paths)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["run_count"], 2)
            self.assertEqual(result["platforms"], ["Linux-x86_64", "Windows-x86_64"])

    def test_first_divergent_state_fails_the_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            first = replay("Windows")
            second = replay("Linux")
            second["frames"][119][0][4] = "0000000000000001"
            paths = []
            for name, value in (("first", first), ("second", second)):
                path = temp / f"{name}.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                paths.append(path)
            with self.assertRaisesRegex(COMPARE.ReplayError, "divergence"):
                COMPARE.compare_replays(paths)

    def test_parallel_profile_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            path = Path(temp_name) / "parallel.json"
            value = replay("Windows")
            value["profile"]["solver_parallel"] = True
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(COMPARE.ReplayError, "solver_parallel"):
                COMPARE.inspect_replay(path)


if __name__ == "__main__":
    unittest.main()
