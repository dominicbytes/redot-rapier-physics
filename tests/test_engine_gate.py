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
                with mock.patch.object(GATE.subprocess, "run", return_value=subprocess.CompletedProcess([], code, text)):
                    with self.assertRaises(RuntimeError):
                        GATE.run_gate("engine", [], Path(temp) / "engine.log", "SUCCESS")

    def test_colored_runtime_diagnostics_are_not_hidden(self):
        with self.assertRaises(RuntimeError):
            GATE.require_clean_output("\x1b[31mWARNING: unexpected warning\x1b[0m")

    def test_stale_pass_result_cannot_satisfy_a_new_run(self):
        with tempfile.TemporaryDirectory() as temp:
            result = Path(temp) / "result.json"
            result.write_text('{"status":"PASS"}', encoding="utf-8")
            with mock.patch.object(GATE.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "SUCCESS")):
                with self.assertRaises((RuntimeError, OSError)):
                    GATE.run_gate("engine", [], Path(temp) / "engine.log", "SUCCESS", result, "Rapier2D")

    def test_errors_in_engine_log_cannot_hide_behind_clean_console(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "engine.log"
            def execute(*args, **kwargs):
                log.write_text("Parse Error: failed", encoding="utf-8")
                return subprocess.CompletedProcess([], 0, "SUCCESS")
            with mock.patch.object(GATE.subprocess, "run", side_effect=execute):
                with self.assertRaises(RuntimeError):
                    GATE.run_gate("engine", [], log, "SUCCESS")

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


class ImportExceptionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        self.config = json.loads((ROOT / "compat/redot-26.3-import-allowlist.json").read_text())
        cache = self.project / ".godot"
        cache.mkdir()
        (cache / "extension_list.cfg").write_text("res://addons/godot-rapier2d/godot-rapier2d.gdextension\n")
        self.classes = cache / "global_script_class_cache.cfg"
        self.classes.write_text("list=[" + ", ".join(
            '{"class": &"' + name + '", "path": "' + path + '"}'
            for name, path in self.config["required_classes"].items()) + "]")
        self.text = "[ DONE ] loading_editor_layout\n" + "\n".join(self.config["diagnostics"])

    def check(self, text=None, code=0):
        filtered = GATE.completed_import_output(self.text if text is None else text, code, self.config, self.project)
        GATE.require_clean_output(filtered)

    def test_only_exact_shutdown_leaks_are_tolerated(self):
        self.check()
        for diagnostic in ("SCRIPT ERROR: failed", "ERROR: unrelated engine failure",
                           "WARNING: Scan thread aborted...", "WARNING: 3 RIDs of type \"Canvas\" were leaked.",
                           "Failed to load GDExtension"):
            with self.subTest(diagnostic=diagnostic), self.assertRaises(RuntimeError):
                self.check(self.text + "\n" + diagnostic)

    def test_access_violation_requires_exact_crash_diagnostic(self):
        crash = self.text + "\n" + "\n".join(self.config["crash_diagnostics"])
        for code in (3221225477, -1073741819):
            self.check(crash, code)
        for code in (1, 7, 3221225501, -11):
            with self.subTest(code=code), self.assertRaises(RuntimeError):
                self.check(crash, code)
        with self.assertRaises(RuntimeError):
            self.check(code=3221225477)
        with self.assertRaises(RuntimeError):
            self.check(crash, code=0)

    def test_runtime_never_accepts_known_diagnostics(self):
        with self.assertRaises(RuntimeError):
            GATE.require_clean_output(self.text)
        allowlist = ROOT / "compat/redot-26.3-import-allowlist.json"
        for arguments in (["--path", str(self.project)],
                          ["--import", "--path", str(self.project), "--scene", "res://test.tscn"],
                          ["--import", "--path", str(self.project), "--export-release", "preset"],
                          ["--import", "--path", str(self.project), "--", "runtime-argument"]):
            with self.subTest(arguments=arguments), self.assertRaises(RuntimeError):
                GATE.prepare_import_exception("engine", arguments, allowlist)

    def test_incomplete_or_missing_cache_fails(self):
        with self.assertRaises(RuntimeError):
            self.check("import started\n" + "\n".join(self.config["diagnostics"]))
        self.classes.write_text('list=[]')
        with self.assertRaises(RuntimeError):
            self.check()
        self.classes.unlink()
        with self.assertRaises(OSError):
            self.check()

    def test_exact_engine_required_and_old_caches_removed(self):
        allowlist = ROOT / "compat/redot-26.3-import-allowlist.json"
        arguments = ["--import", "--path", str(self.project)]
        for version in ("26.2.stable.official.4f5b14aba", "26.3.stable.official.changed"):
            with mock.patch.object(GATE.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, version)):
                with self.assertRaises(RuntimeError):
                    GATE.prepare_import_exception("engine", arguments, allowlist)
        with mock.patch.object(GATE.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, self.config["engine_version_output"])):
            GATE.prepare_import_exception("engine", arguments, allowlist)
        self.assertFalse(self.classes.exists())
        self.assertFalse((self.project / ".godot/extension_list.cfg").exists())


if __name__ == "__main__":
    unittest.main()
