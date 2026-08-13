#!/usr/bin/env python3
"""Validate and exercise the Redot Rapier porting contract.

The upstream checkout remains read-only. Cargo runs in a generated consumer
copy so an externally patched lockfile cannot alter the pinned source tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import zipfile
from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE_PATTERN = re.compile(
    r"^v?(?P<upstream>\d+\.\d+\.\d+)-redot\.(?P<revision>[1-9]\d*)$"
)
EXPECTED_ADDONS = {
    "2d": {
        "display_name": "Redot Rapier Physics 2D",
        "slug": "redot-rapier-physics-2d",
        "internal_path": "addons/godot-rapier2d",
        "source_path": "bin2d/addons/godot-rapier2d",
        "descriptor": "bin2d/addons/godot-rapier2d/godot-rapier2d.gdextension",
        "entry_symbol": "rapier_2d_init",
        "cargo_features": [
            "single-dim2",
            "redot-compat",
            "serde-serialize",
            "parallel",
            "register-docs",
        ],
        "export_excluded_features": ["register-docs"],
    },
    "3d": {
        "display_name": "Redot Rapier Physics 3D",
        "slug": "redot-rapier-physics-3d",
        "internal_path": "addons/godot-rapier3d",
        "source_path": "bin3d/addons/godot-rapier3d",
        "descriptor": "bin3d/addons/godot-rapier3d/godot-rapier3d.gdextension",
        "entry_symbol": "rapier_3d_init",
        "cargo_features": ["single-dim3", "redot-compat"],
    },
}
EXPECTED_PLATFORMS = {
    "windows-x86_64": ("windows", "x86_64", "required", True),
    "linux-x86_64": ("linux", "x86_64", "required", True),
    "macos-universal": ("macos", "universal", "deferred", False),
}
REQUIRED_PACKAGE_FILES = {
    "README.md",
    "LICENSE",
    "LICENSE-MPL-2.0.txt",
    "THIRDPARTY.txt",
    "THIRDPARTY-REDOT.txt",
    "godot-rapier2d.gdextension",
    "plugin.info.cfg",
}
REQUIRED_PACKAGE_BINARIES = {
    "2d": {
        "bin/libgodot_rapier.windows.editor.x86_64-pc-windows-msvc.dll",
        "bin/libgodot_rapier.windows.debug.x86_64-pc-windows-msvc.dll",
        "bin/libgodot_rapier.windows.release.x86_64-pc-windows-msvc.dll",
        "bin/libgodot_rapier.linux.editor.x86_64-unknown-linux-gnu.so",
        "bin/libgodot_rapier.linux.debug.x86_64-unknown-linux-gnu.so",
        "bin/libgodot_rapier.linux.release.x86_64-unknown-linux-gnu.so",
    }
}
EXPECTED_2D_LIBRARIES = {
    "windows.editor.x86_64": "bin/libgodot_rapier.windows.editor.x86_64-pc-windows-msvc.dll",
    "windows.debug.x86_64": "bin/libgodot_rapier.windows.debug.x86_64-pc-windows-msvc.dll",
    "windows.release.x86_64": "bin/libgodot_rapier.windows.release.x86_64-pc-windows-msvc.dll",
    "linux.editor.x86_64": "bin/libgodot_rapier.linux.editor.x86_64-unknown-linux-gnu.so",
    "linux.debug.x86_64": "bin/libgodot_rapier.linux.debug.x86_64-unknown-linux-gnu.so",
    "linux.release.x86_64": "bin/libgodot_rapier.linux.release.x86_64-unknown-linux-gnu.so",
}
IGNORED_PACKAGE_DIRECTORIES = {".git", ".godot", "__pycache__"}


class ContractError(RuntimeError):
    """Raised when a pinned contract or probe boundary is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load {path}: {exc}") from exc
    _require(isinstance(value, dict), f"{path} must contain a JSON object")
    return value


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractError(f"cannot read {path}: {exc}") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_digest(files: list[dict[str, Any]]) -> str:
    payload = "".join(f"{item['sha256']}  {item['path']}\n" for item in files)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def collect_package_payload(root: Path, addon: dict[str, Any]) -> list[dict[str, Any]]:
    dimension = addon.get("dimension")
    _require(dimension == "2d", "only the approved Rapier2D package may be emitted")
    _require(addon.get("product_enabled") is True, "Rapier2D product must be enabled")
    _require(addon.get("package_enabled") is True, "Rapier2D packaging must be enabled")

    source_root = root / addon["source_path"]
    _require(source_root.is_dir(), f"package source is missing: {source_root}")
    expected_binaries = REQUIRED_PACKAGE_BINARIES[dimension]
    payload: list[dict[str, Any]] = []
    observed_relative: set[str] = set()
    for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
        relative = source.relative_to(source_root)
        if any(part in IGNORED_PACKAGE_DIRECTORIES for part in relative.parts):
            continue
        relative_posix = relative.as_posix()
        if relative.parts[0] == "bin" and relative_posix not in expected_binaries:
            continue
        installed = (PurePosixPath(addon["internal_path"]) / relative_posix).as_posix()
        _require("godot-rapier3d" not in installed, "Rapier2D payload contains Rapier3D")
        observed_relative.add(relative_posix)
        payload.append(
            {
                "source": str(source),
                "path": installed,
                "sha256": sha256_file(source),
                "bytes": source.stat().st_size,
                "executable": relative_posix.endswith(".so"),
            }
        )

    missing_files = sorted(REQUIRED_PACKAGE_FILES - observed_relative)
    _require(not missing_files, f"package files are missing: {', '.join(missing_files)}")
    missing_binaries = sorted(expected_binaries - observed_relative)
    _require(
        not missing_binaries,
        f"required package binaries are missing: {', '.join(missing_binaries)}",
    )
    _require(payload, "package payload is empty")
    payload.sort(key=lambda item: item["path"])
    return payload


def _zip_info(name: str, executable: bool = False) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = ((0o755 if executable else 0o644) & 0xFFFF) << 16
    return info


def write_deterministic_zip(
    payload: list[dict[str, Any]], archive: Path
) -> Path:
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as bundle:
        for item in sorted(payload, key=lambda record: record["path"]):
            source = Path(item["source"])
            _require(source.is_file(), f"package source is missing: {source}")
            _require(
                sha256_file(source) == item["sha256"],
                f"package source changed after collection: {source}",
            )
            bundle.writestr(
                _zip_info(item["path"], bool(item.get("executable"))),
                source.read_bytes(),
            )
    return archive


def verify_package_archive(
    archive: Path, payload: list[dict[str, Any]]
) -> dict[str, Any]:
    _require(archive.is_file(), f"package archive is missing: {archive}")
    expected = {item["path"]: item for item in payload}
    with zipfile.ZipFile(archive) as bundle:
        members = [member for member in bundle.infolist() if not member.is_dir()]
        names = [member.filename for member in members]
        _require(len(names) == len(set(names)), "package archive contains duplicate paths")
        _require(sorted(names) == sorted(expected), "package archive payload mismatch")
        for member in members:
            mode = member.external_attr >> 16
            _require(not stat.S_ISLNK(mode), f"package symlink is forbidden: {member.filename}")
            actual = hashlib.sha256(bundle.read(member)).hexdigest()
            _require(
                actual == expected[member.filename]["sha256"],
                f"package file hash mismatch: {member.filename}",
            )
    return {
        "archive": archive.name,
        "archive_sha256": sha256_file(archive),
        "archive_bytes": archive.stat().st_size,
        "file_count": len(expected),
        "payload_manifest_sha256": manifest_digest(
            [
                {"path": item["path"], "sha256": item["sha256"]}
                for item in sorted(payload, key=lambda record: record["path"])
            ]
        ),
    }


def safe_extract_zip(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            relative = PurePosixPath(member.filename)
            _require(
                not relative.is_absolute()
                and relative.parts
                and ".." not in relative.parts,
                f"unsafe archive member: {member.filename}",
            )
            mode = member.external_attr >> 16
            _require(not stat.S_ISLNK(mode), f"archive symlink is forbidden: {member.filename}")
            output = destination.joinpath(*relative.parts)
            _require(
                destination_root == output.resolve()
                or destination_root in output.resolve().parents,
                f"unsafe archive destination: {member.filename}",
            )
            if member.is_dir():
                output.mkdir(parents=True, exist_ok=True)
                continue
            output.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(member) as source, output.open("wb") as target:
                shutil.copyfileobj(source, target)
            if mode & 0o111:
                output.chmod(output.stat().st_mode | 0o111)


def parse_release_tag(value: str) -> tuple[str, int]:
    match = RELEASE_PATTERN.fullmatch(value)
    if not match:
        raise ContractError(
            f"release identity {value!r} must match v<upstream>-redot.<revision>"
        )
    return match.group("upstream"), int(match.group("revision"))


def validate_documents(
    porting: dict[str, Any], lock: dict[str, Any]
) -> dict[str, Any]:
    _require(porting.get("schema_version") == 2, "porting schema must be 2")
    _require(lock.get("schema_version") == 2, "Redot lock schema must be 2")

    product = porting.get("product") or {}
    upstream = porting.get("upstream") or {}
    release_version = product.get("release_version", "")
    release_tag = product.get("release_tag", "")
    parsed_version, revision = parse_release_tag(release_version)
    parsed_tag_version, tag_revision = parse_release_tag(release_tag)
    _require(release_tag == f"v{release_version}", "release tag/version mismatch")
    _require(parsed_version == parsed_tag_version, "release upstream mismatch")
    _require(revision == tag_revision, "release revision mismatch")
    _require(upstream.get("version") == parsed_version, "upstream version mismatch")
    _require(upstream.get("tag") == f"v{parsed_version}", "upstream tag mismatch")
    _require(
        re.fullmatch(r"[0-9a-f]{40}", upstream.get("commit", "")) is not None,
        "upstream commit must be a full lowercase SHA-1",
    )
    _require(
        re.fullmatch(r"[0-9a-f]{40}", upstream.get("tree", "")) is not None,
        "upstream tree must be a full lowercase SHA-1",
    )
    _require(
        re.fullmatch(
            r"[0-9a-f]{64}", upstream.get("tracked_payload_manifest_sha256", "")
        )
        is not None,
        "upstream tracked payload hash must be a full lowercase SHA-256",
    )
    _require(upstream.get("tracked_file_count", 0) > 0, "upstream file count required")

    support = porting.get("certified_redot") or []
    _require(len(support) == 1, "exactly one Redot identity must be certified")
    support_identity = support[0]
    redot = lock.get("redot") or {}
    api = lock.get("api") or {}
    for key in (
        "version",
        "status",
        "tag",
        "commit",
        "compatibility_version",
        "precision",
    ):
        _require(
            support_identity.get(key) == redot.get(key),
            f"certified Redot {key} does not match the lock",
        )
    assets = redot.get("assets") or {}
    _require(
        set(assets) == {"windows-x86_64", "linux-x86_64", "export-templates"},
        "Redot release asset lock is incomplete",
    )
    for asset_id, asset in assets.items():
        _require(
            re.fullmatch(r"[0-9a-f]{64}", asset.get("sha256", "")) is not None,
            f"Redot asset hash is invalid: {asset_id}",
        )
        release_download_prefix = (
            "https://github.com/Redot-Engine/redot-engine/releases/download/"
            f"{redot.get('tag', '')}/"
        )
        _require(
            asset.get("url", "").startswith(release_download_prefix),
            f"Redot asset URL is outside the locked release: {asset_id}",
        )
    _require(
        support_identity.get("api_snapshot") == api.get("snapshot"),
        "API snapshot path mismatch",
    )
    _require(
        support_identity.get("api_sha256") == api.get("sha256"),
        "API snapshot hash mismatch",
    )
    _require(
        support_identity.get("interface_header") == api.get("interface_header"),
        "interface path mismatch",
    )
    _require(
        support_identity.get("interface_sha256") == api.get("interface_sha256"),
        "interface hash mismatch",
    )

    bindings = lock.get("bindings") or {}
    _require(bindings.get("mode") == "redot-rust-cargo", "Rust/Cargo mode required")
    _require(
        bindings.get("dependency_feature") == "godot/api-custom-json",
        "the dependency-qualified custom JSON feature is required",
    )
    _require("redot_cpp" not in json.dumps(lock), "redot-cpp is forbidden")
    _require(
        (lock.get("rust") or {}).get("toolchain") == "1.94.0",
        "Rust 1.94.0 must remain pinned",
    )

    addons = porting.get("addons") or []
    by_dimension = {addon.get("dimension"): addon for addon in addons}
    _require(len(addons) == 2, "exactly two addon records are required")
    _require(set(by_dimension) == set(EXPECTED_ADDONS), "addon dimensions must be 2d/3d")
    for dimension, expected in EXPECTED_ADDONS.items():
        addon = by_dimension[dimension]
        for key, value in expected.items():
            _require(addon.get(key) == value, f"{dimension} addon {key} mismatch")
        _require(
            addon.get("dependency_features") == ["godot/api-custom-json"],
            f"{dimension} must use dependency feature godot/api-custom-json",
        )
        top_level = addon.get("cargo_features") or []
        _require(
            not any(feature.startswith("api-") or feature == "api-custom" for feature in top_level),
            f"{dimension} contains a forbidden top-level API feature",
        )
        _require(addon.get("compatibility_probe") is True, f"{dimension} probe required")
    _require(by_dimension["2d"].get("product_enabled") is True, "Rapier2D must be active")
    _require(
        by_dimension["2d"].get("package_enabled") is True,
        "Rapier2D packaging must be enabled",
    )
    _require(by_dimension["3d"].get("product_enabled") is False, "Rapier3D must stay reserved")
    _require(
        by_dimension["3d"].get("package_enabled") is False,
        "Rapier3D package must stay disabled",
    )

    platforms = porting.get("platforms") or []
    by_id = {platform.get("id"): platform for platform in platforms}
    _require(len(platforms) == 3, "platform contract must name required and deferred desktop targets")
    _require(set(by_id) == set(EXPECTED_PLATFORMS), "platform IDs do not match the approved matrix")
    for platform_id, expected in EXPECTED_PLATFORMS.items():
        platform = by_id[platform_id]
        actual = (
            platform.get("os"),
            platform.get("arch"),
            platform.get("status"),
            platform.get("required"),
        )
        _require(actual == expected, f"platform contract mismatch for {platform_id}")

    return {
        "release_version": release_version,
        "release_tag": release_tag,
        "upstream_commit": upstream["commit"],
        "redot_commit": redot["commit"],
        "addons": sorted(by_dimension),
        "required_platforms": sorted(
            platform_id for platform_id, item in by_id.items() if item["required"]
        ),
        "deferred_platforms": sorted(
            platform_id for platform_id, item in by_id.items() if not item["required"]
        ),
    }


def verify_snapshot(snapshot: dict[str, Any], source: Path | None) -> dict[str, Any]:
    files = snapshot.get("files") or []
    _require(snapshot.get("file_count") == len(files), "snapshot file count mismatch")
    _require(
        manifest_digest(files) == snapshot.get("manifest_sha256"),
        "infrastructure snapshot manifest hash mismatch",
    )
    paths: set[str] = set()
    for item in files:
        relative = Path(item.get("path", ""))
        _require(
            item.get("path") and not relative.is_absolute() and ".." not in relative.parts,
            "snapshot contains an unsafe path",
        )
        _require(item["path"] not in paths, "snapshot contains a duplicate path")
        paths.add(item["path"])
        _require(
            re.fullmatch(r"[0-9a-f]{64}", item.get("sha256", "")) is not None,
            f"invalid snapshot hash for {item.get('path')}",
        )
    verified = 0
    if source is not None:
        _require(source.is_dir(), f"infrastructure source is missing: {source}")
        for item in files:
            path = source / Path(item["path"])
            _require(path.is_file(), f"infrastructure file is missing: {item['path']}")
            _require(path.stat().st_size == item["bytes"], f"size drift: {item['path']}")
            _require(sha256_file(path) == item["sha256"], f"hash drift: {item['path']}")
            verified += 1
    return {
        "manifest_sha256": snapshot["manifest_sha256"],
        "file_count": len(files),
        "source_files_verified": verified,
    }


def validate_contract(root: Path, verify_local_files: bool = True) -> dict[str, Any]:
    porting = _load_json(root / "porting.json")
    lock = _load_json(root / "redot.lock.json")
    summary = validate_documents(porting, lock)

    infrastructure = lock["infrastructure"]
    snapshot_path = root / infrastructure["snapshot_manifest"]
    snapshot = _load_json(snapshot_path)
    _require(
        snapshot.get("manifest_sha256") == infrastructure.get("snapshot_manifest_sha256"),
        "locked infrastructure manifest hash mismatch",
    )
    source = (root / infrastructure["source_hint"]).resolve() if verify_local_files else None
    summary["infrastructure"] = verify_snapshot(snapshot, source)

    cargo_manifest = _read_text(root / "Cargo.toml")
    cargo_version = re.search(
        r'^version\s*=\s*"([^"]+)"\s*$', cargo_manifest, re.MULTILINE
    )
    _require(cargo_version is not None, "Cargo package version is missing")
    _require(
        cargo_version.group(1) == summary["release_version"],
        "Cargo package version does not match the release contract",
    )
    _require(
        re.search(
            r"^redot-compat\s*=\s*\[\s*\]\s*$",
            cargo_manifest,
            re.MULTILINE,
        )
        is not None,
        "redot-compat must remain an empty downstream selector feature",
    )
    rust_toolchain = _read_text(root / "rust-toolchain.toml")
    _require(
        re.search(r'^channel\s*=\s*"1\.94\.0"\s*$', rust_toolchain, re.MULTILINE)
        is not None,
        "rust-toolchain.toml must pin exact Rust 1.94.0",
    )

    cargo_lock = _read_text(root / "Cargo.lock")
    locked_package = re.search(
        r'\[\[package\]\]\s+name\s*=\s*"godot-rapier"\s+'
        r'version\s*=\s*"([^"]+)"',
        cargo_lock,
    )
    _require(locked_package is not None, "Cargo lock is missing godot-rapier")
    _require(
        locked_package.group(1) == summary["release_version"],
        "Cargo lock package version does not match the release contract",
    )

    for dimension in ("2d", "3d"):
        state_source = _read_text(
            root / f"src/bodies/rapier_direct_body_state_{dimension}.rs"
        )
        _require(
            state_source.count('feature = "redot-compat"') == 2,
            f"{dimension} must select exactly two redot-compat cfg branches",
        )

    required_library_keys = (
        "windows.editor.x86_64",
        "windows.debug.x86_64",
        "windows.release.x86_64",
        "linux.editor.x86_64",
        "linux.debug.x86_64",
        "linux.release.x86_64",
    )
    forbidden_library_markers = (
        "macos.",
        "android.",
        "ios.",
        "web.",
        ".x86_32",
        ".arm32",
        ".arm64",
    )
    for addon in porting["addons"]:
        source_path = root / addon["source_path"]
        descriptor_path = root / addon["descriptor"]
        metadata_path = source_path / "plugin.info.cfg"
        _require(source_path.is_dir(), f"missing {addon['source_path']}")
        _require(descriptor_path.is_file(), f"missing {addon['descriptor']}")
        _require(metadata_path.is_file(), f"missing {metadata_path}")

        descriptor = _read_text(descriptor_path)
        _require(
            f'entry_symbol = "{addon["entry_symbol"]}"' in descriptor,
            f"{addon['dimension']} descriptor entry symbol mismatch",
        )
        _require(
            'compatibility_minimum = "4.5"' in descriptor,
            f"{addon['dimension']} descriptor must target API 4.5",
        )
        _require(
            "reloadable = false" in descriptor,
            f"{addon['dimension']} descriptor must disable hot reload",
        )
        for key in required_library_keys:
            _require(
                re.search(rf"^{re.escape(key)}\s*=", descriptor, re.MULTILINE)
                is not None,
                f"{addon['dimension']} descriptor is missing {key}",
            )
        if addon["dimension"] == "2d":
            for key, relative_path in EXPECTED_2D_LIBRARIES.items():
                _require(
                    re.search(
                        rf'^{re.escape(key)}\s*=\s*"{re.escape(relative_path)}"\s*$',
                        descriptor,
                        re.MULTILINE,
                    )
                    is not None,
                    f"2d descriptor path mismatch for {key}",
                )
        _require(
            not any(marker in descriptor for marker in forbidden_library_markers),
            f"{addon['dimension']} descriptor advertises a deferred platform",
        )

        metadata = _read_text(metadata_path)
        _require(
            f'name="{addon["display_name"]}"' in metadata,
            f"{addon['dimension']} public display name mismatch",
        )
        _require(
            f'version="{summary["release_version"]}"' in metadata,
            f"{addon['dimension']} metadata version mismatch",
        )

    summary["source_contract_verified"] = True
    summary["addon_files_verified"] = sorted(
        addon["dimension"] for addon in porting["addons"]
    )

    if verify_local_files:
        api = lock["api"]
        for path_key, hash_key in (
            ("snapshot", "sha256"),
            ("interface_header", "interface_sha256"),
        ):
            path = (root / api[path_key]).resolve()
            _require(path.is_file(), f"locked API artifact is missing: {path}")
            _require(sha256_file(path) == api[hash_key], f"locked API artifact drift: {path}")
        summary["local_api_verified"] = True
    else:
        summary["local_api_verified"] = False
    return summary


def _run(command: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ContractError(f"command failed ({completed.returncode}): {' '.join(command)}\n{detail}")
    return completed.stdout.strip()


def _git(source: Path, *args: str) -> str:
    return _run(
        [
            "git",
            "-c",
            f"safe.directory={source.resolve().as_posix()}",
            "-C",
            str(source.resolve()),
            *args,
        ]
    )


def tracked_paths(source: Path) -> list[str]:
    output = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={source.resolve().as_posix()}",
            "-C",
            str(source.resolve()),
            "ls-files",
            "-z",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if output.returncode != 0:
        raise ContractError(output.stderr.decode("utf-8", errors="replace").strip())
    return [item.decode("utf-8") for item in output.stdout.split(b"\0") if item]


def source_report(source: Path, expected_commit: str | None = None) -> dict[str, Any]:
    _require(source.is_dir(), f"source checkout is missing: {source}")
    head = _git(source, "rev-parse", "HEAD")
    tree = _git(source, "rev-parse", "HEAD^{tree}")
    dirty = _git(source, "status", "--porcelain", "--untracked-files=no")
    if expected_commit:
        _require(head == expected_commit, f"source HEAD {head} != {expected_commit}")
    _require(not dirty, "tracked source checkout is dirty")

    files: list[dict[str, Any]] = []
    total_bytes = 0
    for relative_text in tracked_paths(source):
        path = source / relative_text
        _require(path.is_file(), f"tracked file is missing: {relative_text}")
        size = path.stat().st_size
        total_bytes += size
        files.append(
            {
                "path": Path(relative_text).as_posix(),
                "sha256": sha256_file(path),
                "bytes": size,
            }
        )
    files.sort(key=lambda item: item["path"])
    return {
        "head": head,
        "tree": tree,
        "clean": True,
        "tracked_files": len(files),
        "tracked_bytes": total_bytes,
        "tracked_payload_manifest_sha256": manifest_digest(files),
    }


def assert_locked_source(root: Path, report: dict[str, Any]) -> None:
    upstream = _load_json(root / "porting.json")["upstream"]
    for report_key, lock_key in (
        ("head", "commit"),
        ("tree", "tree"),
        ("tracked_files", "tracked_file_count"),
        ("tracked_payload_manifest_sha256", "tracked_payload_manifest_sha256"),
    ):
        _require(
            report[report_key] == upstream[lock_key],
            f"source {report_key} does not match porting.json",
        )


def prepare_consumer(source: Path, output: Path, expected_commit: str) -> dict[str, Any]:
    before = source_report(source, expected_commit)
    if output.exists():
        _require(output.is_dir(), f"consumer output is not a directory: {output}")
        _require(not any(output.iterdir()), f"consumer output is not empty: {output}")
    else:
        output.mkdir(parents=True)
    for relative_text in tracked_paths(source):
        source_path = source / relative_text
        destination = output / relative_text
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
    copied = source_report(source, expected_commit)
    _require(before == copied, "source changed while preparing the consumer")
    return {
        "source": str(source.resolve()),
        "consumer": str(output.resolve()),
        "source_boundary": copied,
    }


def cargo_build(
    root: Path,
    consumer: Path,
    dimension: str,
    cargo: Path,
    target_dir: Path,
    artifact_kind: str,
    generate_lock: bool,
) -> dict[str, Any]:
    contract = validate_contract(root, verify_local_files=True)
    porting = _load_json(root / "porting.json")
    lock = _load_json(root / "redot.lock.json")
    addon = next(item for item in porting["addons"] if item["dimension"] == dimension)
    _require(
        artifact_kind in {"editor", "debug", "release"},
        f"unknown artifact kind: {artifact_kind}",
    )
    excluded = set(addon.get("export_excluded_features") or [])
    features = [
        feature
        for feature in addon["cargo_features"]
        if artifact_kind == "editor" or feature not in excluded
    ] + addon["dependency_features"]
    config = (root / "compat/rapier-cargo-config.toml").resolve()
    api_json = (root / lock["api"]["snapshot"]).resolve()
    environment = os.environ.copy()
    environment[lock["api"]["environment_variable"]] = str(api_json)
    environment["CARGO_TARGET_DIR"] = str(target_dir.resolve())
    environment["CARGO_HOME"] = str((target_dir.resolve().parent / "cargo-home").resolve())
    rustc = cargo.resolve().parent / ("rustc.exe" if os.name == "nt" else "rustc")
    if rustc.is_file():
        environment["RUSTC"] = str(rustc)
    base = [str(cargo.resolve()), "--config", str(config)]
    if generate_lock:
        _run(base + ["generate-lockfile"], cwd=consumer, env=environment)
    command = base + [
        "build",
        "--locked",
        "--no-default-features",
        "--features",
        ",".join(features),
    ]
    if artifact_kind == "release":
        command.append("--release")
    _run(command, cwd=consumer, env=environment)
    return {
        "status": "PASS",
        "dimension": dimension,
        "artifact_kind": artifact_kind,
        "cargo_profile": "release" if artifact_kind == "release" else "dev",
        "features": features,
        "api_sha256": lock["api"]["sha256"],
        "gdext_revision": lock["bindings"]["gdext_revision"],
        "target_dir": str(target_dir.resolve()),
        "contract": contract,
    }


def package_addon(root: Path, dimension: str, output_dir: Path) -> dict[str, Any]:
    # A standalone checkout carries the self-authenticating infrastructure
    # snapshot, but not the original sibling development directory.
    contract = validate_contract(root, verify_local_files=False)
    porting = _load_json(root / "porting.json")
    addon = next(
        (item for item in porting["addons"] if item["dimension"] == dimension),
        None,
    )
    _require(addon is not None, f"unknown addon dimension: {dimension}")
    payload = collect_package_payload(root, addon)
    version = porting["product"]["release_version"]
    package_name = f"{addon['slug']}-{version}"
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"{package_name}.zip"
    write_deterministic_zip(payload, archive)
    verification = verify_package_archive(archive, payload)

    file_records = [
        {
            "path": item["path"],
            "sha256": item["sha256"],
            "bytes": item["bytes"],
        }
        for item in payload
    ]
    manifest = {
        "schema_version": 1,
        "publication_state": porting["product"]["publication_state"],
        "package": {
            "dimension": addon["dimension"],
            "display_name": addon["display_name"],
            "slug": addon["slug"],
            "version": version,
            "tag": porting["product"]["release_tag"],
            "internal_path": addon["internal_path"],
        },
        "certified_redot": porting["certified_redot"][0],
        "required_platforms": contract["required_platforms"],
        "upstream": porting["upstream"],
        "cargo_features": addon["cargo_features"],
        "build_profiles": {
            "editor": addon["cargo_features"] + addon["dependency_features"],
            "debug": [
                feature
                for feature in addon["cargo_features"]
                if feature not in set(addon.get("export_excluded_features") or [])
            ]
            + addon["dependency_features"],
            "release": [
                feature
                for feature in addon["cargo_features"]
                if feature not in set(addon.get("export_excluded_features") or [])
            ]
            + addon["dependency_features"],
        },
        "dependency_features": addon["dependency_features"],
        "payload_manifest_sha256": verification["payload_manifest_sha256"],
        "files": file_records,
        "archive": {
            "name": archive.name,
            "sha256": verification["archive_sha256"],
            "bytes": verification["archive_bytes"],
        },
    }
    manifest_path = output_dir / f"{package_name}.manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "status": "PASS",
        "archive": str(archive.resolve()),
        "manifest": str(manifest_path.resolve()),
        **verification,
    }


def materialize_clean_install(
    archive: Path,
    fixture: Path,
    output: Path,
    project_config: Path | None = None,
) -> dict[str, Any]:
    _require(archive.is_file(), f"package archive is missing: {archive}")
    _require((fixture / "project.godot").is_file(), f"fixture is not a Redot project: {fixture}")
    if output.exists():
        _require(output.is_dir(), f"clean-install output is not a directory: {output}")
        _require(not any(output.iterdir()), f"clean-install output is not empty: {output}")
    else:
        output.mkdir(parents=True)
    shutil.copytree(fixture, output, dirs_exist_ok=True)
    if project_config is not None:
        _require(project_config.is_file(), f"project config is missing: {project_config}")
        shutil.copy2(project_config, output / "project.godot")
    safe_extract_zip(archive, output)

    addon = output / "addons" / "godot-rapier2d"
    for required in (
        "README.md",
        "LICENSE",
        "LICENSE-MPL-2.0.txt",
        "THIRDPARTY-REDOT.txt",
        "godot-rapier2d.gdextension",
        *sorted(REQUIRED_PACKAGE_BINARIES["2d"]),
    ):
        _require((addon / required).is_file(), f"installed package file is missing: {required}")
    _require(
        not (output / "addons" / "godot-rapier3d").exists(),
        "clean install unexpectedly contains Rapier3D",
    )

    installed = []
    for path in sorted(item for item in addon.rglob("*") if item.is_file()):
        installed.append(
            {
                "path": path.relative_to(output).as_posix(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    return {
        "status": "PASS",
        "project": str(output.resolve()),
        "archive_sha256": sha256_file(archive),
        "installed_file_count": len(installed),
        "installed_payload_manifest_sha256": manifest_digest(installed),
        "files": installed,
    }


def configure_export_templates(
    project: Path,
    windows_debug_template: Path,
    windows_release_template: Path,
    linux_debug_template: Path,
    linux_release_template: Path,
) -> dict[str, Any]:
    presets_path = project / "export_presets.cfg"
    _require(presets_path.is_file(), f"export presets are missing: {presets_path}")
    contents = _read_text(presets_path)

    configured: dict[str, str] = {}
    for preset_name, field, template in (
        ("Windows x86-64", "debug", windows_debug_template),
        ("Windows x86-64", "release", windows_release_template),
        ("Linux x86-64", "debug", linux_debug_template),
        ("Linux x86-64", "release", linux_release_template),
    ):
        preset_index = None
        for match in re.finditer(
            r"(?ms)^\[preset\.(\d+)\]\r?\n(?P<body>.*?)(?=^\[|\Z)",
            contents,
        ):
            if re.search(
                rf'^name\s*=\s*"{re.escape(preset_name)}"\s*$',
                match.group("body"),
                re.MULTILINE,
            ):
                preset_index = match.group(1)
                break
        _require(preset_index is not None, f"export preset is missing: {preset_name}")

        options = re.search(
            rf"(?ms)^\[preset\.{preset_index}\.options\]\r?\n(?P<body>.*?)(?=^\[|\Z)",
            contents,
        )
        _require(options is not None, f"export preset options are missing: {preset_name}")
        template_value = template.as_posix()
        replacement = f"custom_template/{field}={json.dumps(template_value)}"
        body, count = re.subn(
            rf"(?m)^custom_template/{field}=.*$",
            replacement,
            options.group("body"),
        )
        _require(count == 1, f"{field} template field is missing: {preset_name}")
        contents = contents[: options.start("body")] + body + contents[options.end("body") :]
        configured[f"{preset_name} {field}"] = template_value

    presets_path.write_text(contents, encoding="utf-8")
    return {
        "status": "PASS",
        "project": str(project.resolve()),
        "presets": configured,
    }


def _write_report(path: Path | None, report: dict[str, Any]) -> None:
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    print(payload, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate the pinned port contract")
    validate.add_argument("--skip-local-files", action="store_true")
    validate.add_argument("--redot-bin", type=Path)
    validate.add_argument("--report", type=Path)

    source_hash = subparsers.add_parser("source-hash", help="hash every tracked source file")
    source_hash.add_argument("--source", type=Path, required=True)
    source_hash.add_argument("--expected-commit")
    source_hash.add_argument("--report", type=Path)

    prepare = subparsers.add_parser("prepare-consumer", help="copy tracked source externally")
    prepare.add_argument("--source", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--expected-commit", required=True)
    prepare.add_argument("--report", type=Path)

    cargo = subparsers.add_parser("cargo-build", help="build an external consumer")
    cargo.add_argument("--consumer", type=Path, required=True)
    cargo.add_argument("--dimension", choices=sorted(EXPECTED_ADDONS), required=True)
    cargo.add_argument("--cargo", type=Path, required=True)
    cargo.add_argument("--target-dir", type=Path, required=True)
    cargo.add_argument(
        "--artifact-kind",
        choices=("editor", "debug", "release"),
        required=True,
    )
    cargo.add_argument("--generate-lock", action="store_true")
    cargo.add_argument("--report", type=Path)

    package = subparsers.add_parser(
        "package", help="create the deterministic Rapier2D desktop package"
    )
    package.add_argument("--dimension", choices=("2d",), default="2d")
    package.add_argument("--output-dir", type=Path, required=True)
    package.add_argument("--report", type=Path)

    verify_package = subparsers.add_parser(
        "verify-package", help="verify a package against the current source payload"
    )
    verify_package.add_argument("--dimension", choices=("2d",), default="2d")
    verify_package.add_argument("--archive", type=Path, required=True)
    verify_package.add_argument("--report", type=Path)

    install = subparsers.add_parser(
        "materialize-clean-install", help="install a package into a fresh test project"
    )
    install.add_argument("--archive", type=Path, required=True)
    install.add_argument("--fixture", type=Path, required=True)
    install.add_argument("--output", type=Path, required=True)
    install.add_argument("--project-config", type=Path)
    install.add_argument("--report", type=Path)

    configure_exports = subparsers.add_parser(
        "configure-export-templates",
        help="set the clean-install release templates for Windows and Linux",
    )
    configure_exports.add_argument("--project", type=Path, required=True)
    configure_exports.add_argument(
        "--windows-debug-template", type=Path, required=True
    )
    configure_exports.add_argument(
        "--windows-release-template", type=Path, required=True
    )
    configure_exports.add_argument(
        "--linux-debug-template", type=Path, required=True
    )
    configure_exports.add_argument(
        "--linux-release-template", type=Path, required=True
    )
    configure_exports.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            report = validate_contract(ROOT, verify_local_files=not args.skip_local_files)
            if args.redot_bin:
                lock = _load_json(ROOT / "redot.lock.json")
                observed = _run([str(args.redot_bin.resolve()), "--version"])
                _require(observed == lock["redot"]["version_output"], "Redot version mismatch")
                report["redot_version_output"] = observed
        elif args.command == "source-hash":
            report = source_report(args.source.resolve(), args.expected_commit)
            assert_locked_source(ROOT, report)
        elif args.command == "prepare-consumer":
            report = prepare_consumer(
                args.source.resolve(), args.output.resolve(), args.expected_commit
            )
            assert_locked_source(ROOT, report["source_boundary"])
        elif args.command == "cargo-build":
            report = cargo_build(
                ROOT,
                args.consumer.resolve(),
                args.dimension,
                args.cargo,
                args.target_dir.resolve(),
                args.artifact_kind,
                args.generate_lock,
            )
        elif args.command == "package":
            report = package_addon(ROOT, args.dimension, args.output_dir.resolve())
        elif args.command == "verify-package":
            porting = _load_json(ROOT / "porting.json")
            addon = next(
                item for item in porting["addons"] if item["dimension"] == args.dimension
            )
            payload = collect_package_payload(ROOT, addon)
            report = {
                "status": "PASS",
                **verify_package_archive(args.archive.resolve(), payload),
            }
        elif args.command == "materialize-clean-install":
            report = materialize_clean_install(
                args.archive.resolve(),
                args.fixture.resolve(),
                args.output.resolve(),
                args.project_config.resolve() if args.project_config else None,
            )
        elif args.command == "configure-export-templates":
            report = configure_export_templates(
                args.project.resolve(),
                args.windows_debug_template,
                args.windows_release_template,
                args.linux_debug_template,
                args.linux_release_template,
            )
        else:  # pragma: no cover
            raise ContractError(f"unknown command: {args.command}")
        _write_report(args.report, {"status": "PASS", **deepcopy(report)})
        return 0
    except ContractError as exc:
        failure = {"status": "FAIL", "command": args.command, "error": str(exc)}
        report_path = getattr(args, "report", None)
        if report_path is not None:
            _write_report(report_path, failure)
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
