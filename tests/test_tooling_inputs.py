from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


PORTING = module("redot_porting")
METADATA = module("generate_distribution_metadata")


class ToolingInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.api = self.root / "extension_api.json"
        self.header = self.root / "gdextension_interface.h"
        self.api.write_bytes(b"api\n")
        self.header.write_bytes(b"header\n")
        self.lock = {"api": {
            "snapshot": "missing-api.json", "interface_header": "missing-header.h",
            "sha256": hashlib.sha256(self.api.read_bytes()).hexdigest(),
            "interface_sha256": hashlib.sha256(self.header.read_bytes()).hexdigest(),
        }}
        self.environment = mock.patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_explicit_inputs_override_environment_and_infer_header(self):
        os.environ["GDRUST_GODOT_API_JSON"] = "missing-env.json"
        self.assertEqual(PORTING.api_inputs(self.root, self.lock, self.api), (self.api, self.header))
        self.assertEqual(METADATA.api_input(self.lock, self.api), self.api)

    def test_environment_inputs_and_separate_header(self):
        other = self.header.rename(self.root / "separate.h")
        os.environ["GDRUST_GODOT_API_JSON"] = str(self.api)
        os.environ["REDOT_INTERFACE_HEADER"] = str(other)
        self.assertEqual(PORTING.api_inputs(self.root, self.lock), (self.api, other))
        self.assertEqual(METADATA.api_input(self.lock, None), self.api)
        self.assertEqual(PORTING.api_inputs(self.root, self.lock, self.api, other), (self.api, other))

    def test_missing_inputs_name_required_options(self):
        with self.assertRaisesRegex(PORTING.ContractError, "API JSON is missing; supply --api"):
            PORTING.api_inputs(self.root, self.lock)
        with self.assertRaisesRegex(METADATA.MetadataError, "API JSON is missing; supply --api"):
            with mock.patch.object(METADATA, "ROOT", self.root):
                METADATA.api_input(self.lock, None)
        self.header.unlink()
        with self.assertRaisesRegex(PORTING.ContractError, "interface header is missing; supply --interface-header"):
            PORTING.api_inputs(self.root, self.lock, self.api)

    def test_both_pinned_input_hashes_are_enforced(self):
        self.api.write_bytes(b"wrong")
        with self.assertRaisesRegex(PORTING.ContractError, "API JSON pinned hash mismatch"):
            PORTING.api_inputs(self.root, self.lock, self.api)
        with self.assertRaisesRegex(METADATA.MetadataError, "API JSON pinned hash mismatch"):
            METADATA.api_input(self.lock, self.api)
        self.api.write_bytes(b"api\n")
        self.header.write_bytes(b"wrong")
        with self.assertRaisesRegex(PORTING.ContractError, "interface header pinned hash mismatch"):
            PORTING.api_inputs(self.root, self.lock, self.api)

    def test_validation_uses_vendored_provenance_without_siblings(self):
        with mock.patch.object(PORTING, "_write_report") as report:
            self.assertEqual(PORTING.main(["validate"]), 0)
        result = report.call_args.args[1]
        self.assertFalse(result["local_api_verified"])
        self.assertEqual(result["infrastructure"]["source_files_verified"], 0)

    def test_cli_inputs_are_forwarded(self):
        for command in (["validate"], ["cargo-build", "--consumer", "consumer", "--dimension", "2d",
                          "--cargo", "cargo", "--target-dir", "target", "--artifact-kind", "editor"]):
            args = PORTING.build_parser().parse_args(command + ["--api", "api.json", "--interface-header", "interface.h",
                                                                "--infrastructure-source", "infrastructure"])
            self.assertEqual(args.api, Path("api.json"))
            self.assertEqual(args.interface_header, Path("interface.h"))
            self.assertEqual(args.infrastructure_source, Path("infrastructure"))

    def test_optional_infrastructure_source_is_verified(self):
        source = self.root / "infrastructure"
        source.mkdir()
        for explicit in (True, False):
            with self.subTest(explicit=explicit), mock.patch.object(PORTING, "verify_snapshot", wraps=PORTING.verify_snapshot) as verify:
                if not explicit:
                    os.environ["REDOT_INFRASTRUCTURE_SOURCE"] = str(source)
                with self.assertRaisesRegex(PORTING.ContractError, "infrastructure file is missing"):
                    PORTING.validate_contract(ROOT, False, infrastructure_source=source if explicit else None)
                self.assertEqual(verify.call_args.args[1], source)
        os.environ.pop("REDOT_INFRASTRUCTURE_SOURCE", None)
        with self.assertRaisesRegex(PORTING.ContractError, "infrastructure source is missing; supply --infrastructure-source"):
            PORTING.validate_contract(ROOT, False, infrastructure_source=self.root / "missing")

    def test_supplied_infrastructure_source_hash_drift_is_rejected(self):
        snapshot = json.loads((ROOT / "redot.lock.json").read_text())["infrastructure"]["snapshot_manifest"]
        snapshot = json.loads((ROOT / snapshot).read_text())
        first = snapshot["files"][0]
        path = self.root / first["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x" * first["bytes"])
        with self.assertRaisesRegex(PORTING.ContractError, "hash drift"):
            PORTING.verify_snapshot(snapshot, self.root)

    def test_cargo_build_preserves_shim_and_explicit_api(self):
        cargo = mock.Mock(spec=Path)
        shim = self.root / "shim" / "cargo"
        cargo.absolute.return_value = shim
        rustc = shim.parent / ("rustc.exe" if os.name == "nt" else "rustc")
        rustc.parent.mkdir()
        rustc.touch()
        with (mock.patch.object(PORTING, "validate_contract", return_value={}) as validate,
              mock.patch.object(PORTING, "api_inputs", return_value=(self.api, self.header)),
              mock.patch.object(PORTING, "_run") as run):
            PORTING.cargo_build(ROOT, self.root, "2d", cargo, self.root / "target", "editor", False,
                                api=self.api, interface_header=self.header, infrastructure_source=self.root)
        cargo.absolute.assert_called_once_with()
        cargo.resolve.assert_not_called()
        self.assertEqual(run.call_args.args[0][0], str(shim))
        self.assertEqual(run.call_args.args[0][2], str((ROOT / "compat/rapier-cargo-config.toml").resolve()))
        self.assertEqual(run.call_args.kwargs["env"]["GDRUST_GODOT_API_JSON"], str(self.api))
        self.assertEqual(run.call_args.kwargs["env"]["RUSTC"], str(rustc))
        self.assertEqual(validate.call_args.kwargs["infrastructure_source"], self.root)

    def test_metadata_outputs_and_lock_hash_ignore_crlf(self):
        porting = json.loads((ROOT / "porting.json").read_text())
        lock = json.loads((ROOT / "redot.lock.json").read_text())
        cargo_lock = self.root / "Cargo.lock"
        license_file = self.root / "LICENSE"
        license_file.write_bytes(b"Mozilla Public License Version 2.0\n")
        packages = {
            ("godot-rapier", porting["product"]["release_version"]): {"name": "godot-rapier", "version": porting["product"]["release_version"], "license": "MPL-2.0"},
            ("godot", lock["bindings"]["gdext_crate_version"]): {"name": "godot", "version": lock["bindings"]["gdext_crate_version"], "license": "MPL-2.0", "source": "git+https://example.invalid/bindings#pinned"},
        }
        memberships = {"windows-x86_64/editor": set(packages)}
        with (mock.patch.object(METADATA, "LOCK", cargo_lock),
              mock.patch.object(METADATA, "cargo_graph", return_value=(memberships, memberships, packages)),
              mock.patch.object(METADATA, "lock_records", return_value={}),
              mock.patch.object(METADATA, "license_candidates", return_value=[license_file])):
            cargo_lock.write_bytes(b"lock\ncontent\n")
            lf = METADATA.build_outputs(Path("cargo"), self.api, True)
            cargo_lock.write_bytes(b"lock\r\ncontent\r\n")
            crlf = METADATA.build_outputs(Path("cargo"), self.api, True)
            self.assertEqual(lf, crlf)
            for index, content in enumerate(lf.values()):
                path = self.root / (str(index) + ".txt")
                path.write_bytes(content.replace(b"\n", b"\r\n"))
                METADATA.apply_outputs({path: content}, check=True)
            self.assertNotEqual(METADATA.sha256_file(self.api), METADATA.sha256(b"api\r\n"))


if __name__ == "__main__":
    unittest.main()
