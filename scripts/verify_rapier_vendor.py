#!/usr/bin/env python3
"""Verify the sole approved local dependency and its complete source inventory."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tomllib

VENDOR_PATH = "compat/vendor/rapier2d-0.35.1"
PROVENANCE = "compat/provenance/rapier2d-vendor.json"
ARCHIVE_SHA256 = "74bfd393193e08a812ba0c83c7c844dff29979fd30f96de2854cdea507350065"
PATCHED_FILE = "src/pipeline/physics_pipeline/mod.rs"


def vendor_package(package: dict, root: Path) -> bool:
    return (package["name"] == "rapier2d" and package["version"] == "0.35.1"
            and package.get("source") is None
            and Path(package["manifest_path"]).resolve() == (root / VENDOR_PATH / "Cargo.toml").resolve())


def verify(root: Path) -> dict:
    def require(condition, message):
        if not condition:
            raise ValueError("Rapier vendor: " + message)

    record = json.loads((root / PROVENANCE).read_text(encoding="utf-8"))
    require((record["schema_version"], record["name"], record["version"], record["path"])
            == (1, "rapier2d", "0.35.1", VENDOR_PATH), "unapproved dependency")
    require(record["archive_sha256"] == ARCHIVE_SHA256, "archive checksum changed")
    require(record["omitted_files"] == [], "published crate files must be retained")
    require(set(record["patched_files"]) == {PATCHED_FILE}, "unapproved source patch")
    require(record["patched_source_line_endings"] == "LF", "patched source must use canonical LF")
    require(set(record["added_files"]) == {"LICENSE"}, "unapproved added files")
    require(len(record["upstream_files"]) == 186, "incomplete published crate inventory")
    expected = dict(record["upstream_files"])
    expected.update(record["patched_files"])
    expected.update(record["added_files"])
    vendor = root / VENDOR_PATH
    observed = {path.relative_to(vendor).as_posix() for path in vendor.rglob("*") if path.is_file()}
    require(observed == set(expected), "source file inventory changed")
    for relative, checksum in expected.items():
        path = vendor / relative
        require(path.resolve().is_relative_to(vendor.resolve()) and not path.is_symlink(), "source escapes vendor directory")
        content = path.read_bytes()
        if relative == PATCHED_FILE:
            content = content.replace(b"\r\n", b"\n")
        require(hashlib.sha256(content).hexdigest() == checksum, "source hash drift: " + relative)
    require(record["patch"] == "compat/patches/rapier-deferred-bvh-join.patch", "unapproved patch path")
    require(hashlib.sha256((root / record["patch"]).read_bytes()).hexdigest() == record["patch_sha256"], "patch hash drift")
    config = tomllib.loads((root / "compat/rapier-cargo-config.toml").read_text(encoding="utf-8"))
    require(set(config["patch"]["crates-io"]) == {"godot", "rapier2d"}, "unapproved dependency override")
    require(config["patch"]["crates-io"]["rapier2d"] == {"path": VENDOR_PATH}, "vendor config path changed")
    packages = tomllib.loads((root / "Cargo.lock").read_text(encoding="utf-8"))["package"]
    local = [package for package in packages if "source" not in package]
    require({package["name"] for package in local} == {"godot-rapier", "rapier2d"}, "unapproved local lockfile source")
    rapier = [package for package in packages if package["name"] == "rapier2d"]
    require(len(rapier) == 1 and rapier[0]["version"] == "0.35.1"
            and "source" not in rapier[0] and "checksum" not in rapier[0], "Rapier lockfile must use the patched source")
    return {"path": VENDOR_PATH, "files_verified": len(expected), "archive_sha256": ARCHIVE_SHA256,
            "patch_sha256": record["patch_sha256"], "patched_files": sorted(record["patched_files"])}


if __name__ == "__main__":
    print(json.dumps(verify(Path(__file__).resolve().parents[1]), indent=2))
