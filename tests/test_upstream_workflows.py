from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INHERITED = (
    "runner", "release", "android_builds", "ios_builds", "macos_builds",
    "web_builds", "linux_builds", "windows_builds", "godot_builds",
    "determinism_checks", "static_checks", "test_checks", "compatibility_checks",
)
GUARD = "github.repository == 'appsinacup/godot-rapier-physics'"


class UpstreamWorkflowTests(unittest.TestCase):
    def test_runner_has_only_manual_trigger(self):
        runner = (ROOT / ".github/workflows/runner.yml").read_text(encoding="utf-8")
        triggers = runner.split("on:", 1)[1].split("concurrency:", 1)[0]
        self.assertEqual(triggers.strip(), "workflow_dispatch:")

    def test_all_inherited_jobs_require_upstream_repository(self):
        for name in INHERITED:
            with self.subTest(workflow=name):
                workflow = (ROOT / ".github/workflows" / (name + ".yml")).read_text(encoding="utf-8")
                jobs = workflow.split("jobs:", 1)[1]
                bodies = re.findall(r"^  [\w-]+:\n(.*?)(?=^  [\w-]+:\n|\Z)", jobs, re.M | re.S)
                self.assertTrue(bodies)
                for body in bodies:
                    self.assertIn("    if: " + GUARD, body)

    def test_release_caller_also_requires_main(self):
        runner = (ROOT / ".github/workflows/runner.yml").read_text(encoding="utf-8")
        self.assertIn("if: " + GUARD + " && github.ref == 'refs/heads/main'", runner)


if __name__ == "__main__":
    unittest.main()
