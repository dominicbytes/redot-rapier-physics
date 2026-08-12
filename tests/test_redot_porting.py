from __future__ import annotations

import copy
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "redot_porting", ROOT / "scripts/redot_porting.py"
)
assert SPEC and SPEC.loader
PORTING = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PORTING)


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.porting = load("porting.json")
        self.lock = load("redot.lock.json")

    def test_checked_in_contract_passes(self) -> None:
        api_path = (ROOT / self.lock["api"]["snapshot"]).resolve()
        infrastructure_path = (
            ROOT / self.lock["infrastructure"]["source_hint"]
        ).resolve()
        verify_local_files = api_path.is_file() and infrastructure_path.is_dir()
        result = PORTING.validate_contract(
            ROOT, verify_local_files=verify_local_files
        )
        self.assertEqual(result["release_tag"], "v0.35.2-redot.1")
        self.assertEqual(result["required_platforms"], ["linux-x86_64", "windows-x86_64"])
        self.assertEqual(result["deferred_platforms"], ["macos-universal"])
        self.assertEqual(result["local_api_verified"], verify_local_files)
        self.assertTrue(result["source_contract_verified"])
        self.assertEqual(result["addon_files_verified"], ["2d", "3d"])
        self.assertEqual(
            result["infrastructure"]["source_files_verified"],
            31 if verify_local_files else 0,
        )
        self.assertIn(
            'channel = "1.94.0"',
            (ROOT / "rust-toolchain.toml").read_text(encoding="utf-8"),
        )

    def test_second_redot_identity_is_rejected(self) -> None:
        changed = copy.deepcopy(self.porting)
        changed["certified_redot"].append(copy.deepcopy(changed["certified_redot"][0]))
        with self.assertRaisesRegex(PORTING.ContractError, "exactly one Redot identity"):
            PORTING.validate_documents(changed, self.lock)

    def test_export_template_asset_is_locked(self) -> None:
        templates = self.lock["redot"]["assets"]["export-templates"]
        self.assertEqual(
            templates["sha256"],
            "fa8c648bd9a9d911daffbcc4e1786d0248794571a7e4ed954444197c809079ea",
        )
        changed = copy.deepcopy(self.lock)
        del changed["redot"]["assets"]["export-templates"]
        with self.assertRaisesRegex(PORTING.ContractError, "asset lock is incomplete"):
            PORTING.validate_documents(self.porting, changed)

    def test_release_tag_must_match_version(self) -> None:
        changed = copy.deepcopy(self.porting)
        changed["product"]["release_tag"] = "v0.35.2-redot.2"
        with self.assertRaisesRegex(PORTING.ContractError, "tag/version mismatch"):
            PORTING.validate_documents(changed, self.lock)

    def test_top_level_api_feature_is_rejected(self) -> None:
        changed = copy.deepcopy(self.porting)
        changed["addons"][0]["cargo_features"].append("api-4-5")
        with self.assertRaisesRegex(PORTING.ContractError, "cargo_features mismatch"):
            PORTING.validate_documents(changed, self.lock)

    def test_redot_compat_feature_is_required(self) -> None:
        changed = copy.deepcopy(self.porting)
        changed["addons"][0]["cargo_features"].remove("redot-compat")
        with self.assertRaisesRegex(PORTING.ContractError, "cargo_features mismatch"):
            PORTING.validate_documents(changed, self.lock)

    def test_wrong_custom_json_route_is_rejected(self) -> None:
        changed = copy.deepcopy(self.porting)
        changed["addons"][0]["dependency_features"] = ["api-custom"]
        with self.assertRaisesRegex(PORTING.ContractError, "dependency feature"):
            PORTING.validate_documents(changed, self.lock)

    def test_macos_cannot_become_required_silently(self) -> None:
        changed = copy.deepcopy(self.porting)
        macos = next(item for item in changed["platforms"] if item["os"] == "macos")
        macos["status"] = "required"
        macos["required"] = True
        with self.assertRaisesRegex(PORTING.ContractError, "macos-universal"):
            PORTING.validate_documents(changed, self.lock)

    def test_only_rapier2d_packaging_is_enabled(self) -> None:
        rapier2d = next(
            item for item in self.porting["addons"] if item["dimension"] == "2d"
        )
        rapier3d = next(
            item for item in self.porting["addons"] if item["dimension"] == "3d"
        )
        self.assertTrue(rapier2d["package_enabled"])
        self.assertEqual(rapier2d["export_excluded_features"], ["register-docs"])
        self.assertFalse(rapier3d["package_enabled"])

        changed = copy.deepcopy(self.porting)
        next(
            item for item in changed["addons"] if item["dimension"] == "2d"
        )["package_enabled"] = False
        with self.assertRaisesRegex(
            PORTING.ContractError, "Rapier2D packaging must be enabled"
        ):
            PORTING.validate_documents(changed, self.lock)

        changed = copy.deepcopy(self.porting)
        rapier3d = next(item for item in changed["addons"] if item["dimension"] == "3d")
        rapier3d["package_enabled"] = True
        with self.assertRaisesRegex(PORTING.ContractError, "Rapier3D package must stay disabled"):
            PORTING.validate_documents(changed, self.lock)

    def test_rapier2d_package_payload_is_lean_and_cross_platform(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            source = temp / "bin2d" / "addons" / "godot-rapier2d"
            files = {
                "README.md": b"readme\n",
                "LICENSE": b"license\n",
                "LICENSE-MPL-2.0.txt": b"mpl license\n",
                "THIRDPARTY.txt": b"notices\n",
                "THIRDPARTY-REDOT.txt": b"exact feature notices\n",
                "godot-rapier2d.gdextension": b"descriptor\n",
                "plugin.info.cfg": b"metadata\n",
                "custom_nodes/rapier_rigid_body_2d.gd": b"extends RigidBody2D\n",
                "bin/libgodot_rapier.windows.editor.x86_64-pc-windows-msvc.dll": b"windows-editor",
                "bin/libgodot_rapier.windows.debug.x86_64-pc-windows-msvc.dll": b"windows-debug",
                "bin/libgodot_rapier.windows.release.x86_64-pc-windows-msvc.dll": b"windows-release",
                "bin/libgodot_rapier.linux.editor.x86_64-unknown-linux-gnu.so": b"linux-editor",
                "bin/libgodot_rapier.linux.debug.x86_64-unknown-linux-gnu.so": b"linux-debug",
                "bin/libgodot_rapier.linux.release.x86_64-unknown-linux-gnu.so": b"linux-release",
                "bin/libgodot_rapier.macos.framework/Info.plist": b"deferred",
            }
            for relative, content in files.items():
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

            addon = copy.deepcopy(self.porting["addons"][0])
            addon["source_path"] = "bin2d/addons/godot-rapier2d"
            payload = PORTING.collect_package_payload(temp, addon)
            paths = [item["path"] for item in payload]

            self.assertEqual(paths, sorted(paths))
            self.assertIn("addons/godot-rapier2d/README.md", paths)
            self.assertIn("addons/godot-rapier2d/LICENSE", paths)
            self.assertIn("addons/godot-rapier2d/LICENSE-MPL-2.0.txt", paths)
            self.assertIn("addons/godot-rapier2d/THIRDPARTY-REDOT.txt", paths)
            self.assertIn(
                "addons/godot-rapier2d/bin/libgodot_rapier.windows.editor.x86_64-pc-windows-msvc.dll",
                paths,
            )
            self.assertIn(
                "addons/godot-rapier2d/bin/libgodot_rapier.windows.release.x86_64-pc-windows-msvc.dll",
                paths,
            )
            self.assertIn(
                "addons/godot-rapier2d/bin/libgodot_rapier.linux.editor.x86_64-unknown-linux-gnu.so",
                paths,
            )
            self.assertIn(
                "addons/godot-rapier2d/bin/libgodot_rapier.linux.release.x86_64-unknown-linux-gnu.so",
                paths,
            )
            self.assertFalse(any("macos" in path for path in paths))
            self.assertFalse(any("godot-rapier3d" in path for path in paths))

    def test_rapier2d_package_archive_is_deterministic_and_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            source = temp / "bin2d" / "addons" / "godot-rapier2d"
            required = [
                "README.md",
                "LICENSE",
                "LICENSE-MPL-2.0.txt",
                "THIRDPARTY.txt",
                "THIRDPARTY-REDOT.txt",
                "godot-rapier2d.gdextension",
                "plugin.info.cfg",
                "bin/libgodot_rapier.windows.editor.x86_64-pc-windows-msvc.dll",
                "bin/libgodot_rapier.windows.debug.x86_64-pc-windows-msvc.dll",
                "bin/libgodot_rapier.windows.release.x86_64-pc-windows-msvc.dll",
                "bin/libgodot_rapier.linux.editor.x86_64-unknown-linux-gnu.so",
                "bin/libgodot_rapier.linux.debug.x86_64-unknown-linux-gnu.so",
                "bin/libgodot_rapier.linux.release.x86_64-unknown-linux-gnu.so",
            ]
            for relative in required:
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((relative + "\n").encode("utf-8"))

            addon = copy.deepcopy(self.porting["addons"][0])
            addon["source_path"] = "bin2d/addons/godot-rapier2d"
            payload = PORTING.collect_package_payload(temp, addon)
            first = temp / "first.zip"
            second = temp / "second.zip"
            PORTING.write_deterministic_zip(payload, first)
            PORTING.write_deterministic_zip(payload, second)

            self.assertEqual(PORTING.sha256_file(first), PORTING.sha256_file(second))
            verified = PORTING.verify_package_archive(first, payload)
            self.assertEqual(verified["file_count"], len(payload))

            install = temp / "install"
            PORTING.safe_extract_zip(first, install)
            self.assertTrue(
                (install / "addons" / "godot-rapier2d" / "README.md").is_file()
            )

    def test_clean_install_export_templates_are_configured_per_platform(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            project = Path(temp_name)
            source = ROOT / "tests/fixtures/rapier2d-clean-install/export_presets.cfg"
            (project / "export_presets.cfg").write_text(
                source.read_text(encoding="utf-8"), encoding="utf-8"
            )

            result = PORTING.configure_export_templates(
                project,
                Path("C:/templates/windows_debug_x86_64.exe"),
                Path("C:/templates/windows_release_x86_64.exe"),
                Path("/templates/linux_debug.x86_64"),
                Path("/templates/linux_release.x86_64"),
            )
            configured = (project / "export_presets.cfg").read_text(encoding="utf-8")

            self.assertEqual(result["status"], "PASS")
            self.assertIn(
                'custom_template/debug="C:/templates/windows_debug_x86_64.exe"',
                configured,
            )
            self.assertIn(
                'custom_template/release="C:/templates/windows_release_x86_64.exe"',
                configured,
            )
            self.assertIn(
                'custom_template/debug="/templates/linux_debug.x86_64"',
                configured,
            )
            self.assertIn(
                'custom_template/release="/templates/linux_release.x86_64"',
                configured,
            )
            self.assertEqual(configured.count("custom_template/debug="), 2)
            self.assertEqual(configured.count("custom_template/release="), 2)

    def test_infrastructure_manifest_is_self_authenticating(self) -> None:
        snapshot = load("docs/gamedev/evidence/redot-porting-infrastructure.snapshot.json")
        result = PORTING.verify_snapshot(snapshot, None)
        self.assertEqual(result["file_count"], 31)
        self.assertEqual(result["manifest_sha256"], snapshot["manifest_sha256"])

    def test_redot_cpp_adapter_is_rejected(self) -> None:
        changed = copy.deepcopy(self.lock)
        changed["bindings"]["mode"] = "redot_cpp"
        with self.assertRaisesRegex(PORTING.ContractError, "Rust/Cargo mode"):
            PORTING.validate_documents(self.porting, changed)

    def test_workflow_matrix_is_windows_linux_only(self) -> None:
        workflow = (ROOT / ".github/workflows/redot-contract.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("windows-2022", workflow)
        self.assertIn("ubuntu-24.04", workflow)
        self.assertNotIn("macos-latest", workflow)
        self.assertRegex(workflow, re.compile(r"actions/checkout@[0-9a-f]{40}"))
        self.assertRegex(workflow, re.compile(r"actions/upload-artifact@[0-9a-f]{40}"))
        self.assertRegex(workflow, re.compile(r"actions/download-artifact@[0-9a-f]{40}"))
        self.assertGreaterEqual(workflow.count("--fixed-fps 60"), 8)
        self.assertGreaterEqual(workflow.count("--quit-after 600"), 4)
        self.assertEqual(workflow.count("--quit-after 30000"), 2)
        self.assertEqual(
            workflow.count(
                "cargo clippy --config compat/rapier-cargo-config.toml --locked"
            ),
            2,
        )
        self.assertNotIn(
            "cargo --config compat/rapier-cargo-config.toml clippy", workflow
        )
        self.assertIn('RUSTUP_TOOLCHAIN: "1.94.0"', workflow)
        self.assertEqual(workflow.count("strip --strip-debug"), 1)
        self.assertIn("scripts/verify_2d_parity.py", workflow)
        self.assertIn("scripts/generate_distribution_metadata.py", workflow)
        self.assertIn("scripts/compare_determinism.py", workflow)
        self.assertIn("scripts/performance_guardrail.py compare", workflow)
        self.assertIn("materialize-clean-install", workflow)
        self.assertIn("--export-debug", workflow)
        self.assertIn("--export-release", workflow)


if __name__ == "__main__":
    unittest.main()
