from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "distribution_metadata", ROOT / "scripts/generate_distribution_metadata.py"
)
assert SPEC and SPEC.loader
METADATA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(METADATA)


class DistributionMetadataTests(unittest.TestCase):
    def test_license_text_normalization_ignores_platform_whitespace(self) -> None:
        unix = b"line one\nline two\n"
        windows_with_trailing_space = b"line one\r\nline two \t\r\n"
        self.assertEqual(
            METADATA.normalize_license_text(unix),
            METADATA.normalize_license_text(windows_with_trailing_space),
        )

    def test_cargo_shim_symlink_is_not_resolved_to_rustup(self) -> None:
        cargo = mock.Mock(spec=Path)
        absolute = Path("cargo-shim-absolute")
        cargo.absolute.return_value = absolute
        self.assertEqual(METADATA.cargo_executable_path(cargo), absolute)
        cargo.absolute.assert_called_once_with()
        cargo.resolve.assert_not_called()

    def test_exact_feature_profiles_use_dependency_qualified_custom_json(self) -> None:
        porting = json.loads((ROOT / "porting.json").read_text(encoding="utf-8"))
        profiles = METADATA.profiles(porting)
        for features in profiles.values():
            self.assertIn("godot/api-custom-json", features)
            self.assertNotIn("api-custom", features)
            self.assertFalse(any(feature.startswith("api-") for feature in features))
        self.assertIn("register-docs", profiles["editor"])
        self.assertNotIn("register-docs", profiles["export"])

    def test_checked_in_metadata_is_structurally_complete(self) -> None:
        licenses = json.loads(METADATA.LICENSE_REPORT.read_text(encoding="utf-8"))
        spdx = json.loads(METADATA.SPDX_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(licenses["status"], "PASS")
        self.assertEqual(len(licenses["packages"]), 87)
        self.assertEqual(spdx["spdxVersion"], "SPDX-2.3")
        self.assertEqual(len(spdx["packages"]), 87)
        self.assertTrue(METADATA.NOTICE.read_text(encoding="utf-8").startswith(
            "Redot Rapier Physics 2D exact-profile third-party notices"
        ))
        self.assertIn(
            "Mozilla Public License Version 2.0",
            METADATA.MPL_LICENSE.read_text(encoding="utf-8"),
        )

    def test_check_mode_rejects_stale_output(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "build") as temp_name:
            path = Path(temp_name) / "generated.txt"
            path.write_bytes(b"old\n")
            with self.assertRaisesRegex(METADATA.MetadataError, "metadata is stale"):
                METADATA.apply_outputs({path: b"new\n"}, check=True)


if __name__ == "__main__":
    unittest.main()
