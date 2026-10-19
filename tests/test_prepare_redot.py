from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_redot as PREPARE
from redot_porting import ContractError


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads((ROOT / "redot.lock.json").read_text())
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)

    def test_download_checks_archive_bytes(self):
        asset = {"filename": "editor.zip", "url": "https://example.invalid/editor.zip",
                 "sha256": hashlib.sha256(b"archive").hexdigest()}
        with mock.patch.object(PREPARE.urllib.request, "urlopen", return_value=io.BytesIO(b"archive")):
            self.assertEqual(PREPARE.download(asset, self.output).read_bytes(), b"archive")
        with mock.patch.object(PREPARE.urllib.request, "urlopen", return_value=io.BytesIO(b"corrupt")):
            with self.assertRaisesRegex(ContractError, "checksum mismatch"):
                PREPARE.download(asset, self.output)

    def test_version_output_checked_against_selected_identity(self):
        for identity in (self.lock["redot"], self.lock["binding_abi"]):
            for observed in (identity["version_output"], "different"):
                with mock.patch.object(PREPARE.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, observed)):
                    if observed == "different":
                        with self.assertRaisesRegex(ContractError, "version_output mismatch"):
                            PREPARE.verify_version(Path("engine"), identity)
                    else:
                        PREPARE.verify_version(Path("engine"), identity)

    def test_api_and_interface_dumps_are_fresh_bounded_and_hash_checked(self):
        snapshot = {"sha256": hashlib.sha256(b"api").hexdigest(),
                    "interface_sha256": hashlib.sha256(b"header").hexdigest()}
        def dump(command, **kwargs):
            name = "extension_api.json" if "--dump-extension-api" in command else "gdextension_interface.h"
            self.assertIn("--audio-driver", command)
            self.assertIn("--quit-after", command)
            self.assertEqual(kwargs["timeout"], 120)
            (kwargs["cwd"] / name).write_bytes(b"api" if name.endswith("json") else b"header")
        with mock.patch.object(PREPARE.subprocess, "run", side_effect=dump):
            PREPARE.dump_api(Path("engine"), snapshot, self.output)
            with self.assertRaisesRegex(ContractError, "checksum mismatch"):
                PREPARE.dump_api(Path("engine"), dict(snapshot, sha256="0" * 64), self.output)
        with mock.patch.object(PREPARE.subprocess, "run"):
            with self.assertRaisesRegex(ContractError, "checksum mismatch"):
                PREPARE.dump_api(Path("engine"), snapshot, self.output)

    def test_generation_engine_never_becomes_runtime_engine(self):
        runtime = self.output / "runtime"
        generator = self.output / "generator"
        with mock.patch.object(PREPARE, "acquire", side_effect=[runtime, generator]) as acquire, \
                mock.patch.object(PREPARE, "dump_api") as dump:
            values = PREPARE.prepare(self.lock, "windows-x86_64", self.output, True, False)
        self.assertEqual(values["REDOT_BIN"], str(runtime))
        self.assertEqual(acquire.call_args_list[0].args[0]["version"], "26.3")
        self.assertEqual(acquire.call_args_list[1].args[0]["version"], "26.2")
        self.assertEqual(dump.call_args_list[0].args[1], self.lock["api"])
        self.assertEqual(dump.call_args_list[1].args[1], self.lock["binding_abi"])
        self.assertEqual(Path(values["GDRUST_GODOT_API_JSON"]).parent.name, "binding-api")

    def test_workflow_uses_lock_for_assets_and_identified_artifacts(self):
        workflow = (ROOT / ".github/workflows/redot-contract.yml").read_text()
        self.assertIn("- redot-26.3", workflow)
        self.assertNotIn("26.2", workflow)
        self.assertNotIn("releases/download/", workflow)
        self.assertEqual(workflow.count("--with-binding-abi"), 2)
        self.assertIn("build/from-linux/build/redot/binding-api/extension_api.json", workflow)
        for line in workflow.splitlines():
            if "--import " in line and "engine_gate.py" in line:
                self.assertIn("--import-allowlist", line)
            if "--scene " in line:
                self.assertNotIn("--import-allowlist", line)
            if line.strip().startswith("name: rapier2d-") or line.strip().startswith("name: redot-rapier2d-"):
                self.assertIn("needs.identity.outputs.engine", line)


if __name__ == "__main__":
    unittest.main()
