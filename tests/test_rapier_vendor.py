from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_rapier_vendor as VENDOR


class RapierVendorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in (VENDOR.VENDOR_PATH, "compat/patches"):
            shutil.copytree(ROOT / relative, self.root / relative)
        for relative in ("Cargo.lock", "compat/rapier-cargo-config.toml", VENDOR.PROVENANCE):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, path)

    def test_complete_source_inventory_passes(self):
        self.assertEqual(VENDOR.verify(self.root)["files_verified"], 187)

    def test_patched_text_hash_is_stable_across_checkout_line_endings(self):
        path = self.root / VENDOR.VENDOR_PATH / VENDOR.PATCHED_FILE
        content = path.read_bytes().replace(b"\r\n", b"\n")
        for content in (content, content.replace(b"\n", b"\r\n")):
            path.write_bytes(content)
            self.assertEqual(VENDOR.verify(self.root)["files_verified"], 187)

    def test_unrecorded_source_change_is_rejected(self):
        path = self.root / VENDOR.VENDOR_PATH / "src/lib.rs"
        path.write_bytes(path.read_bytes() + b"\n// drift\n")
        with self.assertRaisesRegex(ValueError, "source hash drift: src/lib.rs"):
            VENDOR.verify(self.root)

    def test_extra_file_and_missing_license_are_rejected(self):
        path = self.root / VENDOR.VENDOR_PATH / "target-output"
        path.touch()
        with self.assertRaisesRegex(ValueError, "source file inventory changed"):
            VENDOR.verify(self.root)
        path.unlink()
        (self.root / VENDOR.VENDOR_PATH / "LICENSE").unlink()
        with self.assertRaisesRegex(ValueError, "source file inventory changed"):
            VENDOR.verify(self.root)

    def test_only_the_recorded_config_path_is_allowed(self):
        path = self.root / "compat/rapier-cargo-config.toml"
        path.write_text(path.read_text().replace(VENDOR.VENDOR_PATH, "../other"))
        with self.assertRaisesRegex(ValueError, "vendor config path changed"):
            VENDOR.verify(self.root)

    def test_registry_rapier_and_other_local_sources_are_rejected(self):
        path = self.root / "Cargo.lock"
        original = path.read_text()
        path.write_text(original.replace('name = "rapier2d"', 'name = "other-local"'))
        with self.assertRaisesRegex(ValueError, "unapproved local lockfile source"):
            VENDOR.verify(self.root)
        path.write_text(original.replace('name = "rapier2d"', 'source = "registry+https://example.invalid/index"\nname = "rapier2d"'))
        with self.assertRaisesRegex(ValueError, "unapproved local lockfile source"):
            VENDOR.verify(self.root)

    def test_patch_and_archive_identity_are_checked(self):
        path = self.root / "compat/patches/rapier-deferred-bvh-join.patch"
        original = path.read_bytes()
        path.write_bytes(original + b"\n")
        with self.assertRaisesRegex(ValueError, "patch hash drift"):
            VENDOR.verify(self.root)
        path.write_bytes(original)
        path = self.root / VENDOR.PROVENANCE
        record = json.loads(path.read_text())
        record["archive_sha256"] = "0" * 64
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, "archive checksum changed"):
            VENDOR.verify(self.root)


if __name__ == "__main__":
    unittest.main()
