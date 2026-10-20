from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("engine_gate", ROOT / "scripts/engine_gate.py")
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


class EngineGateTests(unittest.TestCase):
    def test_native_failure_and_missing_sentinel_fail(self):
        for code, text in ((7, "SUCCESS"), (0, "frame bound reached"),
                           (0, "SUCCESS\nSCRIPT ERROR: failed"),
                           (0, "SUCCESS\nthread 'worker' panicked at failure")):
            with self.subTest(code=code, text=text), tempfile.TemporaryDirectory() as temp:
                with mock.patch.object(GATE, "run_engine", return_value=subprocess.CompletedProcess([], code, text)):
                    with self.assertRaises(RuntimeError):
                        GATE.run_gate("engine", [], Path(temp) / "engine.log", "SUCCESS")

    def test_colored_runtime_diagnostics_are_not_hidden(self):
        with self.assertRaises(RuntimeError):
            GATE.require_clean_output("\x1b[31mWARNING: unexpected warning\x1b[0m")

    def test_stale_pass_result_cannot_satisfy_a_new_run(self):
        with tempfile.TemporaryDirectory() as temp:
            result = Path(temp) / "result.json"
            result.write_text('{"status":"PASS"}', encoding="utf-8")
            with mock.patch.object(GATE, "run_engine", return_value=subprocess.CompletedProcess([], 0, "SUCCESS")):
                with self.assertRaises((RuntimeError, OSError)):
                    GATE.run_gate("engine", [], Path(temp) / "engine.log", "SUCCESS", result, "Rapier2D")

    def test_errors_in_engine_log_cannot_hide_behind_clean_console(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "engine.log"
            def execute(*args, **kwargs):
                log.write_text("Parse Error: failed", encoding="utf-8")
                return subprocess.CompletedProcess([], 0, "SUCCESS")
            with mock.patch.object(GATE, "run_engine", side_effect=execute):
                with self.assertRaises(RuntimeError):
                    GATE.run_gate("engine", [], log, "SUCCESS")

    def test_completing_other_scenes_and_heartbeats_do_not_extend_a_stalled_scene(self):
        progress = GATE.RegressionProgress()
        text = "REGRESSION START id=1 frame=3 scene=res://stalled.gd\n"
        progress.update(text, 10)
        text += "REGRESSION START id=2 frame=4 scene=res://fast.gd\n"
        progress.update(text, 11)
        text += "REGRESSION END id=2 frame=9 scene=res://fast.gd\nREGRESSION FRAME frame=60\n"
        progress.update(text, 12)
        self.assertFalse(progress.overdue(14, 5))
        self.assertTrue(progress.overdue(15, 5))
        self.assertIn("res://stalled.gd (started at frame 3)", progress.describe())
        self.assertIn("last physics frame: 60", progress.describe())
        text += "REGRESSION END id=1 frame=61 scene=res://stalled.gd\n"
        progress.update(text, 16)
        self.assertFalse(progress.overdue(20, 5))

    def test_partial_progress_lines_are_read_when_they_finish(self):
        progress = GATE.RegressionProgress()
        progress.update("REGRESSION START id=1 frame=3 scene=res://stal", 10)
        self.assertFalse(progress.active)
        progress.update("REGRESSION START id=1 frame=3 scene=res://stalled.gd\n", 11)
        self.assertIn("res://stalled.gd", progress.describe())

    def test_scene_deadline_terminates_before_suite_deadline(self):
        script = ("import pathlib,sys,time; "
                  "p=pathlib.Path(sys.argv[sys.argv.index('--log-file')+1]); "
                  "p.write_text('REGRESSION START id=1 frame=17 scene=res://stalled.gd\\n'); "
                  "print('partial console',flush=True); time.sleep(30)")
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "engine.log"
            with mock.patch.object(GATE, "capture_timeout_stacks", return_value="native stacks"):
                with self.assertRaises(RuntimeError):
                    GATE.run_gate(sys.executable, ["-c", script], log, timeout=10, scene_timeout=0.1)
            text = log.read_text(encoding="utf-8")
            self.assertIn("Engine timed out (scene deadline)", text)
            self.assertIn("res://stalled.gd (started at frame 17)", text)
            self.assertIn("native stacks", text)

    def test_timeout_preserves_partial_console_and_rejects_early_success(self):
        script = "import time; print('STATUS: SUCCESS', flush=True); print('last physics frame: 17', flush=True); time.sleep(30)"
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "engine.log"
            with mock.patch.object(GATE, "capture_timeout_stacks", return_value="native stacks", create=True):
                with self.assertRaises((RuntimeError, subprocess.TimeoutExpired)):
                    GATE.run_gate(sys.executable, ["-c", script], log, "STATUS: SUCCESS", timeout=1)
            self.assertIn("last physics frame: 17", log.read_text(encoding="utf-8"))
            self.assertIn("timed out", log.read_text(encoding="utf-8"))

    def test_result_requires_backend_and_all_registered_classes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "result.json"
            good = dict(status="PASS", selected_backend="Rapier2D", rapier_server_registered=True,
                        fluid_registered=True, state_manager_registered=True)
            for field in good:
                value = dict(good)
                value.pop(field)
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.subTest(field=field), self.assertRaises(RuntimeError):
                    GATE.validate_result(path, "Rapier2D")
            path.write_text(json.dumps(good), encoding="utf-8")
            GATE.validate_result(path, "Rapier2D")


if __name__ == "__main__":
    unittest.main()
