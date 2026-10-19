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
    r"SCRIPT ERROR|Parse Error|Assertion failed|^ERROR:|^WARNING:|CrashHandlerException|"
    r"GDExtension.*(?:error|fail)|Failed to (?:load|initialize).*|"
    r"panicked at|thread .+ panicked|fatal runtime error|^FATAL:|error\(-[0-9]+\)",
    re.IGNORECASE | re.MULTILINE,
)


def require_clean_output(text: str) -> None:
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    if ERRORS.search(text):
        raise RuntimeError("engine diagnostics contain an error")


def prepare_import_exception(engine: str, arguments: list[str], allowlist: Path) -> tuple[dict, Path]:
    config = json.loads(allowlist.read_text(encoding="utf-8"))
    # An explicit import is required; editor, exports, scripts and scenes cannot opt in.
    if ("--import" not in arguments or "--path" not in arguments or "--" in arguments
            or any(arg in ("--scene", "--script", "-s") or arg.startswith("--export")
                   or arg.endswith((".tscn", ".gd")) for arg in arguments)):
        raise RuntimeError("temporary exception is restricted to import steps")
    version = subprocess.run([engine, "--version"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=30, check=False)
    if version.returncode or version.stdout.strip() != config["engine_version_output"]:
        raise RuntimeError("temporary import exception requires the exact locked engine")
    project = Path(arguments[arguments.index("--path") + 1]).resolve()
    for name in ("extension_list.cfg", "global_script_class_cache.cfg"):
        (project / ".godot" / name).unlink(missing_ok=True)
    return config, project


def completed_import_output(text: str, code: int, config: dict, project: Path) -> str:
    if code not in (0, config["allowed_exit_code"], config["allowed_exit_code"] - 2**32):
        raise RuntimeError("import exited with an unrecognized code")
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    if not re.search(r"\[ DONE \]\s+loading_editor_layout", text):
        raise RuntimeError("import did not finish loading the editor")
    cache = project / ".godot"
    extensions = (cache / "extension_list.cfg").read_text(encoding="utf-8")
    if "res://addons/godot-rapier2d/godot-rapier2d.gdextension" not in extensions.splitlines():
        raise RuntimeError("completed import is missing the extension")
    classes = (cache / "global_script_class_cache.cfg").read_text(encoding="utf-8")
    for name, path in config["required_classes"].items():
        if not re.search(r'"class": &"' + re.escape(name) + r'"[^}]*"path": "' + re.escape(path) + '"', classes):
            raise RuntimeError("completed import is missing a required Rapier class")
    allowed = set(config["diagnostics"])
    if code:
        # The crash handler sometimes dies after printing its banner; then the banner must end the output.
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if config["crash_diagnostics"][0] in text:
            allowed.update(config["crash_diagnostics"])
        elif lines[-1:] != [config["crash_banner"]]:
            raise RuntimeError("access violation lacks the known shutdown diagnostic")
        allowed.add(config["crash_banner"])
    elif config["crash_banner"] in text:
        raise RuntimeError("crash output without an access violation")
    filtered = []
    for line in text.splitlines():
        if line.strip() in allowed:
            continue
        if code and re.fullmatch(config["crash_frame_pattern"], line.strip()):
            continue
        filtered.append(line)
    return "\n".join(filtered)


def validate_result(path: Path, backend: str) -> None:
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("status") != "PASS" or result.get("selected_backend") != backend:
        raise RuntimeError("runtime result did not pass with the expected backend")
    for field in ("rapier_server_registered", "fluid_registered", "state_manager_registered"):
        if result.get(field) is not True:
            raise RuntimeError("runtime result is missing a required extension class")


def run_gate(engine: str, arguments: list[str], log: Path, sentinel: str | None = None,
             result: Path | None = None, backend: str | None = None,
             timeout: int = 180, import_allowlist: Path | None = None) -> None:
    log = log.resolve()
    log.parent.mkdir(parents=True, exist_ok=True)
    log.unlink(missing_ok=True)
    if result:
        result = result.resolve()
        result.unlink(missing_ok=True)
    arguments = list(arguments)
    exception = prepare_import_exception(engine, arguments, import_allowlist) if import_allowlist else None
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
    diagnostics = console + "\n" + log_text
    if exception:
        diagnostics = completed_import_output(diagnostics, completed.returncode, *exception)
        print(f"TEMPORARY Redot 26.3 import exception: completed caches verified; exit={completed.returncode}")
    elif completed.returncode:
        raise RuntimeError(f"engine exited {completed.returncode}")
    require_clean_output(diagnostics)
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
    parser.add_argument("--import-allowlist", type=Path)
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
    if args.result:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        if args.backend:
            arguments += ["--", f"--rapier-result={args.result.resolve()}"]
    try:
        run_gate(args.engine, arguments, args.log, args.sentinel, args.result,
                 args.backend, args.timeout, args.import_allowlist)
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired):
        print("Engine gate failed; inspect captured diagnostics")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
