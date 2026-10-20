from __future__ import annotations

import io
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import publication_paths as PATHS


class PublicationPathTests(unittest.TestCase):
    def test_report_paths_are_relative_or_logical(self):
        self.assertEqual(PATHS.report_path(ROOT / "scripts/compare_determinism.py"), "scripts/compare_determinism.py")
        with tempfile.TemporaryDirectory() as temporary:
            private = Path(temporary) / "private-input.json"
            self.assertEqual(PATHS.report_path(private, "replay"), "<replay>")
            report = PATHS.safe_report({"error": str(private), "nested": [str(ROOT / "build/input")]})
            text = json.dumps(report)
            self.assertNotIn(str(ROOT), text)
            self.assertNotIn(str(Path.home()), text)
            self.assertEqual(PATHS.path_hits(text.encode()), 0)

    def test_scanner_checks_ascii_utf16_and_nested_archive_members(self):
        private = chr(82) + ":" + chr(92) + "private" + chr(92) + "source.rs"
        for encoding in ("ascii", "utf-16-le", "utf-16-be"):
            payload = private.encode(encoding)
            self.assertGreater(PATHS.scan_payload(payload), 0)
            self.assertGreater(PATHS.scan_payload(b"!" + payload), 0)
            inner = io.BytesIO()
            with zipfile.ZipFile(inner, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("binary.dll", payload)
            outer = io.BytesIO()
            with zipfile.ZipFile(outer, "w") as archive:
                archive.writestr("nested.zip", inner.getvalue())
            self.assertGreater(PATHS.scan_payload(outer.getvalue()), 0)
        self.assertEqual(PATHS.scan_payload(b"res://main.tscn https://example.test/source /source/main.rs"), 0)

    def test_drive_letter_needs_a_path_segment(self):
        # Byte runs like these occur in release machine code; none of them is a path.
        for noise in (b"\x90D:\\$'\x00", b"\x00a:/\x01\x02", b"xx C:\\ yy"):
            self.assertEqual(PATHS.path_hits(noise), 0)
        for path in (b"D:\\a\\repo", b"C:/build/src", b"E:\\src", b"F:\\My Folder\\x"):
            self.assertGreater(PATHS.path_hits(path), 0)

    def test_unix_and_runner_roots_are_rejected(self):
        for root in ("home", "Users", "__w"):
            self.assertGreater(PATHS.path_hits(("/" + root + "/private/source").encode()), 0)
        with mock.patch.dict(os.environ, {"RUNNER_WORKSPACE": "/private-runner/work"}):
            self.assertGreater(PATHS.path_hits(b"/private-runner/work/source.rs"), 0)

    def test_rustflags_remap_every_root_and_neutralize_pdb(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            env = {"CARGO_HOME": str(temp / "cargo"), "RUSTUP_HOME": str(temp / "rustup"),
                   "CARGO_TARGET_DIR": str(temp / "target")}
            with mock.patch.dict(os.environ, env), mock.patch.object(PATHS.subprocess, "check_output", return_value=str(temp / "toolchain")):
                flags = PATHS.rustflags(True)
            for source in (Path.home(), ROOT, temp / "cargo", temp / "cargo/registry", temp / "cargo/git", temp / "rustup", temp / "toolchain", temp / "target"):
                self.assertTrue(any(flag.startswith("--remap-path-prefix=" + str(source.resolve()) + "=") for flag in flags))
            self.assertIn("link-arg=/PDBALTPATH:%_PDB%", flags)
            vendor = ROOT / "compat/vendor/rapier2d-0.35.1/src/pipeline/physics_pipeline/mod.rs"
            remapped = str(vendor.resolve())
            for flag in flags:
                if flag.startswith("--remap-path-prefix="):
                    source, destination = flag[len("--remap-path-prefix="):].split("=", 1)
                    if str(vendor.resolve()).startswith(source):
                        remapped = str(vendor.resolve()).replace(source, destination, 1)
            self.assertEqual(remapped.replace(chr(92), "/"),
                             "/source/compat/vendor/rapier2d-0.35.1/src/pipeline/physics_pipeline/mod.rs")

    def test_failed_report_does_not_serialize_private_exception_paths(self):
        spec = importlib.util.spec_from_file_location("porting_report", ROOT / "scripts/redot_porting.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "report.json"
            with mock.patch("sys.stdout", new=io.StringIO()):
                module._write_report(output, {"status": "FAIL", "error": str(ROOT / "missing/input")})
            self.assertEqual(PATHS.path_hits(output.read_bytes()), 0)
            with mock.patch.object(module, "ROOT", Path(temporary) / "missing"), mock.patch("sys.stdout", new=io.StringIO()):
                self.assertEqual(module.main(["validate", "--skip-local-files", "--report", str(output)]), 2)
            self.assertEqual(PATHS.path_hits(output.read_bytes()), 0)


if __name__ == "__main__":
    unittest.main()
