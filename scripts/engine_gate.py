#!/usr/bin/env python3
"""Run bounded engine checks and require complete, error-free evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
from publication_paths import scrub_text


ERRORS = re.compile(
    r"SCRIPT ERROR|Parse Error|Assertion failed|^ERROR:|"
    r"GDExtension.*(?:error|fail)|Failed to (?:load|initialize).*|"
    r"panicked at|thread .+ panicked|fatal runtime error",
    re.IGNORECASE | re.MULTILINE,
)


def require_clean_output(text: str) -> None:
    if ERRORS.search(text):
        raise RuntimeError("engine diagnostics contain an error")


def validate_result(path: Path, backend: str) -> None:
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("status") != "PASS" or result.get("selected_backend") != backend:
        raise RuntimeError("runtime result did not pass with the expected backend")
    for field in ("rapier_server_registered", "fluid_registered", "state_manager_registered"):
        if result.get(field) is not True:
            raise RuntimeError("runtime result is missing a required extension class")


def run_gate(engine: str, arguments: list[str], log: Path, sentinel: str | None = None,
             result: Path | None = None, backend: str | None = None,
             timeout: int = 180) -> None:
    log = log.resolve()
    log.parent.mkdir(parents=True, exist_ok=True)
    log.unlink(missing_ok=True)
    if result:
        result = result.resolve()
        result.unlink(missing_ok=True)
    arguments = list(arguments)
    separator = arguments.index("--") if "--" in arguments else len(arguments)
    arguments[separator:separator] = ["--log-file", str(log)]
    completed = subprocess.run(
        [engine, *arguments],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False,
    )
    console = completed.stdout
    log_text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    # Keep console diagnostics as well as the engine logger's output.
    log.write_text(scrub_text(console + "\n" + log_text), encoding="utf-8")
    if completed.returncode:
        raise RuntimeError(f"engine exited {completed.returncode}")
    require_clean_output(console + "\n" + log_text)
    if sentinel and sentinel not in console + log_text:
        raise RuntimeError("runtime success sentinel is missing")
    if result:
        if backend:
            validate_result(result, backend)
        elif not result.is_file():
            raise RuntimeError("runtime did not write fresh evidence")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--sentinel")
    parser.add_argument("--result", type=Path)
    parser.add_argument("--backend")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
    if args.result:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        if args.backend:
            arguments += ["--", f"--rapier-result={args.result.resolve()}"]
    try:
        run_gate(args.engine, arguments, args.log, args.sentinel, args.result,
                 args.backend, args.timeout)
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired):
        print("Engine gate failed; inspect captured diagnostics")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
