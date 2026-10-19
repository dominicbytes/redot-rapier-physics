#!/usr/bin/env python3
"""Remap build paths and reject filesystem identities in publication payloads."""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ABSOLUTE = re.compile(
    r"(?<![a-zA-Z0-9])[a-zA-Z]:[\\/]|/(?:home|Users|__w|tmp)/|"
    r"/(?:mnt|cygdrive)/[a-zA-Z]/|/[a-z]/(?:a|work|Users)/",
    re.IGNORECASE,
)


def report_path(path: Path, role: str = "input") -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return "<" + role + ">"


def private_roots() -> list[str]:
    roots = {str(ROOT), str(Path.home())}
    for key in ("GITHUB_WORKSPACE", "RUNNER_WORKSPACE", "RUNNER_TEMP", "CARGO_HOME", "RUSTUP_HOME", "CARGO_TARGET_DIR", "TEMP", "TMP"):
        if os.environ.get(key):
            roots.add(os.environ[key])
    return sorted({variant for root in roots for variant in (root, root.replace("\\", "/"))}, key=len, reverse=True)


def scrub_text(text: str) -> str:
    for root in private_roots():
        text = re.sub(re.escape(root), "<runtime>", text, flags=re.IGNORECASE)
    # Consume the complete path, including a quoted path containing spaces.
    text = re.sub(r"(?i)(?<![a-z0-9])[a-z]:[\\/][^\r\n\"'<>]*", "<absolute-path>", text)
    text = re.sub(r"/(?:home|Users|__w|tmp)/[^\r\n\"'<>]*", "<absolute-path>", text)
    text = re.sub(r"(?<![\w./:])/(?!/)[^\r\n\"'<>]*", "<absolute-path>", text)
    return text


def safe_report(value):
    if isinstance(value, dict):
        return {scrub_text(str(key)): safe_report(item) for key, item in value.items()}
    if isinstance(value, list):
        return [safe_report(item) for item in value]
    return scrub_text(value) if isinstance(value, str) else value


def rustflags(windows: bool) -> list[str]:
    home = Path.home()
    cargo = Path(os.environ.get("CARGO_HOME", home / ".cargo"))
    rustup = Path(os.environ.get("RUSTUP_HOME", home / ".rustup"))
    sysroot = Path(subprocess.check_output(["rustc", "--print", "sysroot"], text=True).strip())
    mappings = [(home, "/user"), (cargo, "/cargo"), (cargo / "registry", "/cargo/registry"),
                (cargo / "git", "/cargo/git"), (rustup, "/rust"), (sysroot, "/rust/toolchain"),
                (ROOT, "/source")]
    if os.environ.get("CARGO_TARGET_DIR"):
        mappings.append((Path(os.environ["CARGO_TARGET_DIR"]), "/target"))
    flags = []
    # rustc chooses the last matching mapping; keep specific roots last.
    for source, destination in mappings:
        for spelling in sorted({str(source.resolve()), source.resolve().as_posix()}):
            flags.append(f"--remap-path-prefix={spelling}={destination}")
    if windows:
        flags += ["-C", "link-arg=/PDBALTPATH:%_PDB%"]
    return flags


def path_hits(data: bytes) -> int:
    count = 0
    strings = [data.decode("latin1")]
    strings += [data[offset:].decode(encoding, errors="ignore")
                for encoding in ("utf-16-le", "utf-16-be") for offset in (0, 1)]
    for decoded in strings:
        text = "\n".join(re.findall(r"[ -~]{5,}", decoded))
        count += len(ABSOLUTE.findall(text))
        for root in private_roots():
            count += len(re.findall(re.escape(root), text, flags=re.IGNORECASE))
    return count


def scan_payload(data: bytes) -> int:
    count = 0
    if data.startswith(b"PK\x03\x04"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            count += path_hits(archive.comment)
            for entry in archive.infolist():
                count += path_hits(entry.filename.encode("utf-8"))
                count += path_hits(entry.comment) + path_hits(entry.extra)
                if not entry.is_dir():
                    count += scan_payload(archive.read(entry))
        return count
    return path_hits(data)


def files(paths):
    for path in paths:
        if not path.exists():
            raise RuntimeError("publication input is missing")
        yield from sorted(item for item in path.rglob("*") if item.is_file()) if path.is_dir() else [path]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    flags = sub.add_parser("rustflags")
    flags.add_argument("--windows", action="store_true")
    for name in ("scan", "sanitize"):
        command = sub.add_parser(name)
        command.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    if args.command == "rustflags":
        print("\x1f".join(rustflags(args.windows)))
        return 0
    if args.command == "sanitize":
        for path in files(args.paths):
            text = path.read_text(encoding="utf-8", errors="replace")
            if path.suffix == ".json":
                text = json.dumps(safe_report(json.loads(text)), indent=2, sort_keys=True) + "\n"
            else:
                text = scrub_text(text)
            path.write_text(text, encoding="utf-8")
        return 0
    hits = sum(scan_payload(path.read_bytes()) for path in files(args.paths))
    print(f"Publication absolute-path hits: {hits}")
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
