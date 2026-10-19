#!/usr/bin/env python3
"""Acquire checksum-pinned runtime and binding-input engines from the lock."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import urllib.request

from redot_porting import ContractError, safe_extract_zip, sha256_file, validate_documents

ROOT = Path(__file__).resolve().parents[1]


def download(asset: dict, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    archive = directory / asset["filename"]
    with urllib.request.urlopen(asset["url"], timeout=60) as response, archive.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    if sha256_file(archive) != asset["sha256"]:
        raise ContractError("engine archive checksum mismatch")
    return archive


def verify_version(engine: Path, identity: dict) -> None:
    observed = subprocess.run([str(engine), "--version"], check=True, capture_output=True,
                              text=True, encoding="utf-8", timeout=30).stdout.strip()
    if observed != identity["version_output"]:
        raise ContractError("downloaded engine version_output mismatch")


def acquire(identity: dict, assets: dict, platform: str, directory: Path) -> Path:
    asset = assets[platform]
    archive = download(asset, directory)
    extracted = directory / "editor"
    safe_extract_zip(archive, extracted)
    executables = list(extracted.rglob(asset["executable"]))
    if len(executables) != 1 or not executables[0].is_file():
        raise ContractError("expected exactly one locked engine executable")
    engine = executables[0].resolve()
    if platform == "linux-x86_64":
        engine.chmod(engine.stat().st_mode | 0o111)
    verify_version(engine, identity)
    return engine


def dump_api(engine: Path, snapshot: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for flag, name, key in (("--dump-extension-api", "extension_api.json", "sha256"),
                             ("--dump-gdextension-interface", "gdextension_interface.h", "interface_sha256")):
        output = directory / name
        output.unlink(missing_ok=True)
        subprocess.run([str(engine), "--headless", "--audio-driver", "Dummy", flag,
                        "--quit-after", "2"], cwd=directory, check=True, timeout=120)
        if not output.is_file() or sha256_file(output) != snapshot[key]:
            raise ContractError("dumped API/interface checksum mismatch")


def prepare(lock: dict, platform: str, output: Path, binding: bool, templates: bool) -> dict[str, str]:
    runtime = acquire(lock["redot"], lock["redot"]["assets"], platform, output)
    values = {"REDOT_BIN": str(runtime), "REDOT_ID": lock["redot"]["version_output"]}
    if binding:
        dump_api(runtime, lock["api"], output / "engine-api")
        abi = lock["binding_abi"]
        generator = acquire(abi, abi["source"]["assets"], platform, output / "binding-source")
        dump_api(generator, abi, output / "binding-api")
        values[abi["environment_variable"]] = str((output / "binding-api/extension_api.json").resolve())
        values["REDOT_INTERFACE_HEADER"] = str((output / "binding-api/gdextension_interface.h").resolve())
    if templates:
        archive = download(lock["redot"]["assets"]["export-templates"], output)
        safe_extract_zip(archive, output / "export-templates")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=("windows-x86_64", "linux-x86_64"), required=True)
    parser.add_argument("--output", type=Path, default=Path("build/redot"))
    parser.add_argument("--with-binding-abi", action="store_true")
    parser.add_argument("--with-templates", action="store_true")
    args = parser.parse_args()
    lock = json.loads((ROOT / "redot.lock.json").read_text(encoding="utf-8"))
    validate_documents(json.loads((ROOT / "porting.json").read_text(encoding="utf-8")), lock)
    values = prepare(lock, args.platform, args.output.resolve(), args.with_binding_abi, args.with_templates)
    if os.environ.get("GITHUB_ENV"):
        with Path(os.environ["GITHUB_ENV"]).open("a", encoding="utf-8") as output:
            for key, value in values.items():
                output.write(f"{key}={value}\n")
    print(f"Verified runtime: {values['REDOT_ID']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
