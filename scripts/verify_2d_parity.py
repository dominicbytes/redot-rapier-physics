#!/usr/bin/env python3
"""Prove that the Redot 2D port preserves the pinned upstream runtime surface."""

from __future__ import annotations

import argparse
import configparser
import hashlib
import json
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path
from typing import Any


ADDON_SOURCE = Path("bin2d/addons/godot-rapier2d")
ADDON_INSTALL = Path("addons/godot-rapier2d")
DESCRIPTOR = ADDON_SOURCE / "godot-rapier2d.gdextension"
PLUGIN_INFO = ADDON_SOURCE / "plugin.info.cfg"
AUTHORIZED_SOURCE_DELTAS = {
    "src/bodies/rapier_direct_body_state_2d.rs",
    "src/bodies/rapier_direct_body_state_3d.rs",
}
EXPECTED_LIBRARIES = {
    "windows.editor.x86_64": "bin/libgodot_rapier.windows.editor.x86_64-pc-windows-msvc.dll",
    "windows.debug.x86_64": "bin/libgodot_rapier.windows.debug.x86_64-pc-windows-msvc.dll",
    "windows.release.x86_64": "bin/libgodot_rapier.windows.release.x86_64-pc-windows-msvc.dll",
    "linux.editor.x86_64": "bin/libgodot_rapier.linux.editor.x86_64-unknown-linux-gnu.so",
    "linux.debug.x86_64": "bin/libgodot_rapier.linux.debug.x86_64-unknown-linux-gnu.so",
    "linux.release.x86_64": "bin/libgodot_rapier.linux.release.x86_64-unknown-linux-gnu.so",
}
EDITOR_FEATURES = {
    "single-dim2",
    "redot-compat",
    "serde-serialize",
    "parallel",
    "register-docs",
}
EXPORT_FEATURES = EDITOR_FEATURES - {"register-docs"}
DEPENDENCY_FEATURES = {"godot/api-custom-json"}


class ParityError(RuntimeError):
    """Raised when an upstream 2D capability is removed or weakened."""


def _normalized(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def _git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise ParityError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def _upstream_file(repo: Path, commit: str, path: str) -> bytes:
    return _normalized(_git(repo, "show", f"{commit}:{path}"))


def _tree_paths(repo: Path, commit: str, prefix: str) -> list[str]:
    output = _git(repo, "ls-tree", "-r", "--name-only", commit, "--", prefix)
    return [line for line in output.decode("utf-8").splitlines() if line]


def _compat_expected(upstream: bytes, path: str) -> bytes:
    replacements = {
        b'#[cfg(any(feature = "api-4-4", feature = "api-4-5"))]':
            b'#[cfg(any(feature = "api-4-4", feature = "api-4-5", feature = "redot-compat"))]',
        b'#[cfg(not(any(feature = "api-4-4", feature = "api-4-5")))]':
            b'#[cfg(not(any(feature = "api-4-4", feature = "api-4-5", feature = "redot-compat")))]',
    }
    expected = upstream
    for old, new in replacements.items():
        if expected.count(old) != 1:
            raise ParityError(f"unexpected upstream cfg shape in {path}")
        expected = expected.replace(old, new)
    return expected


def _compare_runtime_source(repo: Path, commit: str) -> tuple[int, str]:
    paths = _tree_paths(repo, commit, "src")
    digest = hashlib.sha256()
    for path in paths:
        current_path = repo / path
        if not current_path.is_file():
            raise ParityError(f"upstream runtime source removed: {path}")
        upstream = _upstream_file(repo, commit, path)
        current = _normalized(current_path.read_bytes())
        expected = (
            _compat_expected(upstream, path)
            if path in AUTHORIZED_SOURCE_DELTAS
            else upstream
        )
        if current != expected:
            raise ParityError(f"unauthorized runtime source delta: {path}")
        digest.update(path.encode("utf-8") + b"\0" + hashlib.sha256(current).digest())
    return len(paths), digest.hexdigest()


def _compare_addon_source(repo: Path, commit: str) -> int:
    excluded = {DESCRIPTOR.as_posix(), PLUGIN_INFO.as_posix()}
    paths = _tree_paths(repo, commit, ADDON_SOURCE.as_posix())
    compared = 0
    for path in paths:
        if path in excluded:
            continue
        current_path = repo / path
        if not current_path.is_file():
            raise ParityError(f"upstream addon asset removed: {path}")
        if _normalized(current_path.read_bytes()) != _upstream_file(repo, commit, path):
            raise ParityError(f"unauthorized addon asset delta: {path}")
        compared += 1
    return compared


def _compare_cargo_contract(repo: Path, commit: str, release_version: str) -> None:
    upstream = tomllib.loads(_upstream_file(repo, commit, "Cargo.toml").decode("utf-8"))
    current = tomllib.loads((repo / "Cargo.toml").read_text(encoding="utf-8"))
    if current["package"]["version"] != release_version:
        raise ParityError("Cargo package version does not match porting.json")
    current["package"]["version"] = upstream["package"]["version"]
    if current["features"].pop("redot-compat", None) != []:
        raise ParityError("redot-compat must remain an empty selector feature")
    if current != upstream:
        raise ParityError("Cargo feature/dependency contract drifted from upstream")


def _read_cfg(path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read(path, encoding="utf-8")
    return parser


def _check_descriptor(repo: Path, release_version: str) -> None:
    descriptor = _read_cfg(repo / DESCRIPTOR)
    configuration = descriptor["configuration"]
    if configuration.get("entry_symbol", "").strip('"') != "rapier_2d_init":
        raise ParityError("2D entry symbol changed")
    if configuration.get("compatibility_minimum", "").strip('"') != "4.5":
        raise ParityError("Redot compatibility minimum changed")
    libraries = {key: value.strip('"') for key, value in descriptor["libraries"].items()}
    if libraries != EXPECTED_LIBRARIES:
        raise ParityError("desktop library matrix is not the exact six-profile contract")
    info = _read_cfg(repo / PLUGIN_INFO)
    if info["plugin"].get("version", "").strip('"') != release_version:
        raise ParityError("plugin.info.cfg version does not match porting.json")


def _check_feature_profile(config: dict[str, Any]) -> None:
    addon = next(item for item in config["addons"] if item["dimension"] == "2d")
    if set(addon["cargo_features"]) != EDITOR_FEATURES:
        raise ParityError("editor feature profile is incomplete")
    if set(addon["export_excluded_features"]) != {"register-docs"}:
        raise ParityError("export profile may exclude only register-docs")
    if set(addon["dependency_features"]) != DEPENDENCY_FEATURES:
        raise ParityError("dependency-qualified custom JSON feature changed")
    if not addon["product_enabled"] or not addon["package_enabled"]:
        raise ParityError("Rapier2D product/package gate is disabled")


def _check_archive(repo: Path, archive: Path) -> dict[str, Any]:
    if not archive.is_file():
        raise ParityError(f"package archive not found: {archive}")
    with zipfile.ZipFile(archive) as package:
        files = {name for name in package.namelist() if not name.endswith("/")}
    prefix = ADDON_INSTALL.as_posix() + "/"
    if any(not name.startswith(prefix) for name in files):
        raise ParityError("package contains files outside addons/godot-rapier2d")
    if any("godot-rapier3d" in name for name in files):
        raise ParityError("Rapier2D package contains Rapier3D payload")

    addon_root = repo / ADDON_SOURCE
    source_payload = {
        (ADDON_INSTALL / path.relative_to(addon_root)).as_posix()
        for path in addon_root.rglob("*")
        if path.is_file() and path.relative_to(addon_root).parts[0] != "bin"
    }
    missing = sorted(source_payload - files)
    if missing:
        raise ParityError(f"package omitted addon runtime assets: {missing}")
    expected_binaries = {prefix + path for path in EXPECTED_LIBRARIES.values()}
    native_files = {
        name
        for name in files
        if name.endswith((".dll", ".so", ".wasm")) or ".framework/" in name
    }
    if native_files != expected_binaries:
        raise ParityError("package native payload is not the exact six-profile contract")
    return {
        "path": str(archive.resolve()),
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "file_count": len(files),
        "native_file_count": len(native_files),
    }


def verify(repo: Path, archive: Path | None) -> dict[str, Any]:
    config = json.loads((repo / "porting.json").read_text(encoding="utf-8"))
    commit = config["upstream"]["commit"]
    release_version = config["product"]["release_version"]
    source_count, source_digest = _compare_runtime_source(repo, commit)
    addon_count = _compare_addon_source(repo, commit)
    _compare_cargo_contract(repo, commit, release_version)
    _check_descriptor(repo, release_version)
    _check_feature_profile(config)
    report: dict[str, Any] = {
        "status": "PASS",
        "upstream_commit": commit,
        "release_version": release_version,
        "runtime_source_files_compared": source_count,
        "runtime_source_manifest_sha256": source_digest,
        "upstream_addon_files_compared": addon_count,
        "authorized_runtime_deltas": sorted(AUTHORIZED_SOURCE_DELTAS),
        "editor_features": sorted(EDITOR_FEATURES),
        "export_features": sorted(EXPORT_FEATURES),
        "dependency_features": sorted(DEPENDENCY_FEATURES),
        "platforms": ["windows-x86_64", "linux-x86_64"],
        "package": _check_archive(repo, archive) if archive else None,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = verify(args.repo.resolve(), args.archive.resolve() if args.archive else None)
    except (OSError, KeyError, ValueError, ParityError, zipfile.BadZipFile) as exc:
        report = {"status": "FAIL", "error": str(exc)}
        code = 2
    else:
        code = 0
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")
    sys.stdout.write(payload)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
