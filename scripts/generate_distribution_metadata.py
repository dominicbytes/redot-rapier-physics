#!/usr/bin/env python3
"""Generate deterministic exact-profile license notices and an SPDX SBOM."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "compat" / "rapier-cargo-config.toml"
LOCK = ROOT / "Cargo.lock"
PORTING = ROOT / "porting.json"
REDOT_LOCK = ROOT / "redot.lock.json"
ADDON = ROOT / "bin2d" / "addons" / "godot-rapier2d"
LICENSE_OVERRIDES = ROOT / "compat" / "license-overrides"
NOTICE = ADDON / "THIRDPARTY-REDOT.txt"
MPL_LICENSE = ADDON / "LICENSE-MPL-2.0.txt"
LICENSE_REPORT = ROOT / "docs" / "gamedev" / "evidence" / "rapier2d-exact-feature-licenses.json"
SPDX_REPORT = ROOT / "docs" / "gamedev" / "evidence" / "rapier2d-sbom.spdx.json"
CREATED = "2026-08-12T00:00:00Z"
PACKAGE_RE = re.compile(r"^(?P<name>[A-Za-z0-9_.+-]+) v(?P<version>\S+)")
LICENSE_NAMES = re.compile(r"^(?:licen[cs]e|copying|unlicense|notice)(?:[._-].*)?$", re.I)
LICENSE_NORMALIZATION = {
    "Apache-2.0 / MIT": "Apache-2.0 OR MIT",
    "MIT/Apache-2.0": "MIT OR Apache-2.0",
}
TARGETS = {
    "windows-x86_64": "x86_64-pc-windows-msvc",
    "linux-x86_64": "x86_64-unknown-linux-gnu",
}


class MetadataError(RuntimeError):
    """Raised when exact-profile distribution metadata cannot be proven."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes())


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def command(cargo: Path, subcommand: str, target: str, features: list[str], offline: bool) -> list[str]:
    args = [
        str(cargo),
        subcommand,
        "--config",
        str(CONFIG),
        "--locked",
        "--no-default-features",
        "--features",
        ",".join(features),
        "--target" if subcommand == "tree" else "--filter-platform",
        target,
    ]
    if offline:
        args.append("--offline")
    return args


def run(args: list[str], env: dict[str, str]) -> str:
    result = subprocess.run(
        args,
        cwd=ROOT,
        env=env,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise MetadataError(
            f"command failed ({result.returncode}): {' '.join(args)}\n{result.stderr.strip()}"
        )
    return result.stdout


def profiles(porting: dict[str, Any]) -> dict[str, list[str]]:
    addon = next(item for item in porting["addons"] if item["dimension"] == "2d")
    editor = list(addon["cargo_features"]) + list(addon["dependency_features"])
    excluded = set(addon["export_excluded_features"])
    export = [feature for feature in addon["cargo_features"] if feature not in excluded]
    export += list(addon["dependency_features"])
    expected_dependency = ["godot/api-custom-json"]
    if addon["dependency_features"] != expected_dependency:
        raise MetadataError("dependency feature must remain godot/api-custom-json")
    forbidden = {"api-custom", "api-4-4", "api-4-5", "api-4-6", "api-4-7"}
    if forbidden.intersection(editor):
        raise MetadataError("top-level API selector detected in Rapier2D profile")
    return {"editor": editor, "export": export}


def parse_tree(output: str) -> set[tuple[str, str]]:
    packages: set[tuple[str, str]] = set()
    for line in output.splitlines():
        display = line.split("\t", 1)[0].strip()
        match = PACKAGE_RE.match(display)
        if match:
            packages.add((match.group("name"), match.group("version")))
    if not packages:
        raise MetadataError("cargo tree returned no packages")
    return packages


def cargo_graph(
    cargo: Path,
    api: Path,
    profile_features: dict[str, list[str]],
    offline: bool,
) -> tuple[dict[str, set[tuple[str, str]]], dict[tuple[str, str], dict[str, Any]]]:
    env = dict(os.environ)
    env["GDRUST_GODOT_API_JSON"] = str(api.resolve())
    env["RUSTUP_TOOLCHAIN"] = "1.94.0"
    memberships: dict[str, set[tuple[str, str]]] = {}
    metadata_packages: dict[tuple[str, str], dict[str, Any]] = {}
    for platform_name, target in TARGETS.items():
        for profile_name, feature_list in profile_features.items():
            profile_id = f"{platform_name}/{profile_name}"
            tree_args = command(cargo, "tree", target, feature_list, offline)
            tree_args += [
                "--edges",
                "normal,build",
                "--prefix",
                "none",
                "--no-dedupe",
                "--format",
                "{p}\t{l}\t{r}",
            ]
            memberships[profile_id] = parse_tree(run(tree_args, env))

            metadata_args = command(cargo, "metadata", target, feature_list, offline)
            metadata_args += ["--format-version", "1"]
            metadata = json.loads(run(metadata_args, env))
            for package in metadata["packages"]:
                key = (package["name"], package["version"])
                previous = metadata_packages.get(key)
                if previous and previous.get("source") != package.get("source"):
                    raise MetadataError(f"ambiguous package source for {key[0]} {key[1]}")
                metadata_packages[key] = package
    active = set().union(*memberships.values())
    missing = sorted(active - set(metadata_packages))
    if missing:
        raise MetadataError(f"cargo metadata omitted active packages: {missing}")
    return memberships, {key: metadata_packages[key] for key in active}


def lock_records() -> dict[tuple[str, str, str | None], dict[str, Any]]:
    lock = tomllib.loads(LOCK.read_text(encoding="utf-8"))
    return {
        (item["name"], item["version"], item.get("source")): item
        for item in lock["package"]
    }


def license_candidates(package: dict[str, Any]) -> list[Path]:
    overrides = sorted(
        LICENSE_OVERRIDES.glob(f"{package['name']}-{package['version']}-LICENSE*")
    )
    if overrides:
        return overrides
    manifest = Path(package["manifest_path"])
    direct = package.get("license_file")
    if direct:
        candidate = manifest.parent / direct
        if candidate.is_file():
            return [candidate]
    directory = manifest.parent
    for _ in range(7):
        try:
            candidates = sorted(
                path
                for path in directory.iterdir()
                if path.is_file() and LICENSE_NAMES.match(path.name)
            )
        except OSError:
            break
        if candidates:
            return candidates
        if directory.parent == directory:
            break
        directory = directory.parent
    return []


def standard_license_candidate(
    marker: str, packages: dict[tuple[str, str], dict[str, Any]]
) -> Path | None:
    matches = []
    for key in sorted(packages):
        candidate_package = packages[key]
        for path in license_candidates(candidate_package):
            text = path.read_text(encoding="utf-8", errors="replace")
            if marker in text:
                matches.append((sha256(path.read_bytes().replace(b"\r\n", b"\n")), path.name, path))
    return min(matches, key=lambda item: (item[0], item[1]))[2] if matches else None


def source_location(package: dict[str, Any], root_repository: str) -> str:
    source = package.get("source")
    if source:
        return str(source)
    if package["name"] == "godot-rapier":
        return root_repository
    return "NOASSERTION"


def related_license_candidates(
    package: dict[str, Any],
    declared: str,
    packages: dict[tuple[str, str], dict[str, Any]],
) -> list[Path]:
    stem = re.sub(r"(?:[-_](?:derive|macros?|impl))$", "", package["name"])
    repository = package.get("repository")
    related = []
    for key in sorted(packages):
        candidate_package = packages[key]
        if candidate_package is package:
            continue
        candidate_stem = re.sub(r"(?:[-_](?:derive|macros?|impl))$", "", key[0])
        same_project = candidate_stem == stem or (
            repository and candidate_package.get("repository") == repository
        )
        if same_project:
            related.extend(license_candidates(candidate_package))
    related = sorted(set(related))
    if declared in {"MIT", "Apache-2.0", "Zlib", "Unlicense"}:
        token = declared.split("-", 1)[0].upper()
        matching = [path for path in related if token in path.name.upper()]
        if matching:
            return matching
    if not related and declared in {"Apache-2.0", "MPL-2.0", "Unlicense", "Unicode-3.0"}:
        token = declared.split("-", 1)[0].upper()
        for key in sorted(packages):
            candidate_package = packages[key]
            candidate_declared = LICENSE_NORMALIZATION.get(
                candidate_package.get("license"), candidate_package.get("license")
            )
            if candidate_declared != declared:
                continue
            candidates = license_candidates(candidate_package)
            matching = [path for path in candidates if token in path.name.upper()]
            if matching:
                return matching
            if candidates:
                return candidates
    return related


def registry_checksum(
    package: dict[str, Any], records: dict[tuple[str, str, str | None], dict[str, Any]]
) -> str | None:
    source = package.get("source")
    item = records.get((package["name"], package["version"], source))
    return item.get("checksum") if item else None


def spdx_id(package: dict[str, Any]) -> str:
    key = f"{package['name']}@{package['version']}@{package.get('source') or 'workspace'}"
    stem = re.sub(r"[^A-Za-z0-9.-]", "-", f"{package['name']}-{package['version']}")
    return f"SPDXRef-Package-{stem}-{sha256(key.encode())[:8]}"


def purl(package: dict[str, Any]) -> str:
    value = f"pkg:cargo/{quote(package['name'])}@{quote(package['version'])}"
    source = package.get("source")
    if source and source.startswith("git+"):
        value += f"?vcs_url={quote(source, safe='')}"
    return value


def build_outputs(cargo: Path, api: Path, offline: bool) -> dict[Path, bytes]:
    porting = json.loads(PORTING.read_text(encoding="utf-8"))
    redot_lock = json.loads(REDOT_LOCK.read_text(encoding="utf-8"))
    profile_features = profiles(porting)
    memberships, packages_by_key = cargo_graph(cargo, api, profile_features, offline)
    lock = lock_records()
    root_repository = porting["product"]["repository"]

    text_groups: dict[str, dict[str, Any]] = {}
    package_records: list[dict[str, Any]] = []
    mpl_records: list[dict[str, Any]] = []
    package_by_spdx: dict[str, dict[str, Any]] = {}
    root_spdx = ""
    gdext_package = packages_by_key.get(("godot", redot_lock["bindings"]["gdext_crate_version"]))
    mpl_fallback = license_candidates(gdext_package) if gdext_package else []
    if not mpl_fallback:
        raise MetadataError("gdext MPL-2.0 license text not found")
    for key in sorted(packages_by_key):
        package = packages_by_key[key]
        raw_license = package.get("license")
        if not raw_license:
            raise MetadataError(f"missing declared license: {key[0]} {key[1]}")
        declared = LICENSE_NORMALIZATION.get(raw_license, raw_license)
        candidates = license_candidates(package)
        if not candidates and declared == "MPL-2.0":
            candidates = mpl_fallback
        if not candidates:
            candidates = related_license_candidates(package, declared, packages_by_key)
        if not candidates:
            raise MetadataError(f"license text not found: {key[0]} {key[1]}")
        if any(path.parent == LICENSE_OVERRIDES for path in candidates) and "Apache-2.0" in declared:
            if not any(
                "Apache License" in path.read_text(encoding="utf-8", errors="replace")
                for path in candidates
            ):
                apache = standard_license_candidate("Apache License", packages_by_key)
                if apache is None:
                    raise MetadataError("Apache-2.0 license text not found")
                candidates.append(apache)
        license_files = []
        for candidate in candidates:
            content = candidate.read_bytes().replace(b"\r\n", b"\n")
            digest = sha256(content)
            group = text_groups.setdefault(
                digest,
                {"content": content, "filenames": set(), "packages": set()},
            )
            group["filenames"].add(candidate.name)
            group["packages"].add(f"{key[0]} {key[1]}")
            license_files.append({"filename": candidate.name, "sha256": digest})
        member_profiles = sorted(
            profile_id for profile_id, members in memberships.items() if key in members
        )
        source = source_location(package, root_repository)
        checksum = registry_checksum(package, lock)
        record = {
            "name": key[0],
            "version": key[1],
            "license": declared,
            "source": source,
            "repository": package.get("repository"),
            "cargo_checksum_sha256": checksum,
            "profiles": member_profiles,
            "license_files": sorted(license_files, key=lambda item: (item["filename"], item["sha256"])),
        }
        package_records.append(record)
        if "MPL-2.0" in declared:
            mpl_records.append(
                {
                    "name": key[0],
                    "version": key[1],
                    "source_code": source,
                    "repository": package.get("repository"),
                }
            )

        identifier = spdx_id(package)
        if key[0] == "godot-rapier":
            root_spdx = identifier
        spdx_package: dict[str, Any] = {
            "SPDXID": identifier,
            "name": key[0],
            "versionInfo": key[1],
            "downloadLocation": source,
            "filesAnalyzed": False,
            "licenseConcluded": declared,
            "licenseDeclared": declared,
            "copyrightText": "NOASSERTION",
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": purl(package),
                }
            ],
        }
        if checksum:
            spdx_package["checksums"] = [{"algorithm": "SHA256", "checksumValue": checksum}]
        package_by_spdx[identifier] = spdx_package

    if not root_spdx:
        raise MetadataError("workspace package missing from exact Cargo graph")
    if not mpl_records:
        raise MetadataError("MPL-2.0 dependency source-availability set is empty")

    mpl_content = None
    for digest, group in text_groups.items():
        text = group["content"].decode("utf-8", errors="replace")
        if "Mozilla Public License Version 2.0" in text:
            mpl_content = group["content"]
            break
    if mpl_content is None:
        raise MetadataError("complete MPL-2.0 license text not found")

    profile_report = {
        profile_id: {
            "target": TARGETS[profile_id.split("/", 1)[0]],
            "features": profile_features[profile_id.split("/", 1)[1]],
            "package_count": len(members),
            "packages": [f"{name}@{version}" for name, version in sorted(members)],
        }
        for profile_id, members in sorted(memberships.items())
    }
    license_report = {
        "schema_version": 1,
        "status": "PASS",
        "product": {
            "name": "Redot Rapier Physics 2D",
            "version": porting["product"]["release_version"],
            "repository": root_repository,
        },
        "inputs": {
            "cargo_lock_sha256": sha256_file(LOCK),
            "redot_api_sha256": redot_lock["api"]["sha256"],
            "redot_rust_repository": redot_lock["bindings"]["compatibility_repository"],
            "redot_rust_commit": redot_lock["bindings"]["compatibility_commit"],
            "gdext_repository": redot_lock["bindings"]["gdext_repository"],
            "gdext_revision": redot_lock["bindings"]["gdext_revision"],
            "rust_toolchain": redot_lock["rust"]["toolchain"],
        },
        "profiles": profile_report,
        "exact_package_count": len(package_records),
        "license_text_count": len(text_groups),
        "mpl_source_availability": sorted(mpl_records, key=lambda item: (item["name"], item["version"])),
        "packages": package_records,
    }

    notice_lines = [
        "Redot Rapier Physics 2D exact-profile third-party notices",
        "==========================================================",
        "",
        f"Release: {porting['product']['release_version']}",
        f"Cargo.lock SHA-256: {sha256_file(LOCK)}",
        f"Redot API SHA-256: {redot_lock['api']['sha256']}",
        "Build profiles: Windows x86-64 and Linux x86-64; editor and export;",
        "single-dim2 + redot-compat + serde-serialize + parallel, with",
        "register-docs only in editor builds and godot/api-custom-json supplied",
        "as a dependency-qualified feature.",
        "",
        "MPL-2.0 source availability",
        "---------------------------",
        "The distributed native libraries incorporate MPL-2.0-covered crates.",
        "The exact Source Code Form used for each crate is available at the",
        "immutable Cargo source below. The gdext crates are unmodified and are",
        f"pinned to {redot_lock['bindings']['gdext_revision']}.",
        "A complete MPL-2.0 license is included as LICENSE-MPL-2.0.txt.",
        "",
    ]
    for record in sorted(mpl_records, key=lambda item: (item["name"], item["version"])):
        notice_lines.append(
            f"- {record['name']} {record['version']}: {record['source_code']}"
        )
    notice_lines += ["", "Exact resolved package inventory", "-------------------------------", ""]
    for record in package_records:
        notice_lines.append(
            f"- {record['name']} {record['version']} | {record['license']} | {record['source']}"
        )
    notice_lines += ["", "Embedded license texts", "----------------------", ""]
    for digest, group in sorted(text_groups.items()):
        notice_lines += [
            f"===== LICENSE TEXT SHA-256 {digest} =====",
            f"Applies to: {', '.join(sorted(group['packages']))}",
            f"Source filenames: {', '.join(sorted(group['filenames']))}",
            "",
            group["content"].decode("utf-8", errors="replace").rstrip(),
            "",
        ]
    notice_bytes = ("\n".join(notice_lines).rstrip() + "\n").encode("utf-8")

    namespace_key = sha256_file(LOCK)[:16]
    relationships = [
        {
            "spdxElementId": "SPDXRef-DOCUMENT",
            "relationshipType": "DESCRIBES",
            "relatedSpdxElement": root_spdx,
        }
    ]
    relationships += [
        {
            "spdxElementId": root_spdx,
            "relationshipType": "DEPENDS_ON",
            "relatedSpdxElement": identifier,
        }
        for identifier in sorted(package_by_spdx)
        if identifier != root_spdx
    ]
    spdx = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"redot-rapier-physics-2d-{porting['product']['release_version']}",
        "documentNamespace": f"{root_repository}/sbom/{porting['product']['release_version']}/{namespace_key}",
        "creationInfo": {
            "created": CREATED,
            "creators": ["Tool: redot-rapier2d-generate-distribution-metadata/1"],
        },
        "documentDescribes": [root_spdx],
        "packages": [package_by_spdx[key] for key in sorted(package_by_spdx)],
        "relationships": relationships,
    }
    return {
        NOTICE: notice_bytes,
        MPL_LICENSE: mpl_content.rstrip() + b"\n",
        LICENSE_REPORT: json_bytes(license_report),
        SPDX_REPORT: json_bytes(spdx),
    }


def apply_outputs(outputs: dict[Path, bytes], check: bool) -> None:
    mismatches = []
    for path, content in outputs.items():
        if check:
            if not path.is_file() or path.read_bytes() != content:
                mismatches.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    if mismatches:
        raise MetadataError("generated distribution metadata is stale: " + ", ".join(mismatches))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cargo", type=Path)
    parser.add_argument("--api", type=Path)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    redot_lock = json.loads(REDOT_LOCK.read_text(encoding="utf-8"))
    api = args.api or (ROOT / redot_lock["api"]["snapshot"])
    if not api.is_file():
        raise SystemExit(f"Redot API JSON not found: {api}")
    cargo_value = args.cargo or (Path(shutil.which("cargo")) if shutil.which("cargo") else None)
    if cargo_value is None or not cargo_value.is_file():
        raise SystemExit("Cargo executable not found; pass --cargo")
    try:
        outputs = build_outputs(cargo_value.resolve(), api.resolve(), args.offline)
        apply_outputs(outputs, args.check)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, MetadataError) as exc:
        print(f"distribution metadata: FAIL: {exc}", file=sys.stderr)
        return 2
    mode = "verified" if args.check else "generated"
    print(f"distribution metadata: PASS ({mode}; {len(outputs)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
