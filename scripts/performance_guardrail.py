#!/usr/bin/env python3
"""Run and compare the frozen Redot Rapier2D performance workloads."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "rapier2d-performance"
SCENARIOS = ROOT / "tests" / "performance_scenarios.json"
DEFAULT_GUARDRAIL = ROOT / "tests" / "performance_guardrail.json"
ADDON = ROOT / "bin2d" / "addons" / "godot-rapier2d"
SENTINEL = "REDOT RAPIER2D PERFORMANCE SAMPLE: SUCCESS"
MEASUREMENT = "wall-clock interval between consecutive physics-frame signals"


class PerformanceError(RuntimeError):
    """Raised when a workload or guardrail is invalid."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_manifest_sha256() -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in FIXTURE.rglob("*") if item.is_file()):
        relative = path.relative_to(FIXTURE).as_posix()
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise PerformanceError("cannot aggregate an empty sample")
    ordered = sorted(values)
    index = max(0, math.ceil(fraction * len(ordered)) - 1)
    return ordered[index]


def summarize(samples: list[dict[str, Any]]) -> dict[str, Any]:
    physics = [float(value) for sample in samples for value in sample["physics_ms"]]
    memory = [int(value) for sample in samples for value in sample["static_memory_bytes"]]
    return {
        "run_count": len(samples),
        "sample_count": len(physics),
        "physics_ms": {
            "median": statistics.median(physics),
            "p95": percentile(physics, 0.95),
            "maximum": max(physics),
        },
        "static_memory_bytes": {
            "median": int(statistics.median(memory)),
            "maximum": max(memory),
        },
        "per_run_p95_ms": [percentile([float(v) for v in sample["physics_ms"]], 0.95) for sample in samples],
    }


def patch_descriptor_for_release(project: Path) -> dict[str, str]:
    descriptor = project / "addons" / "godot-rapier2d" / "godot-rapier2d.gdextension"
    text = descriptor.read_text(encoding="utf-8")
    replacements = {
        'windows.editor.x86_64 = "bin/libgodot_rapier.windows.editor.x86_64-pc-windows-msvc.dll"':
            'windows.editor.x86_64 = "bin/libgodot_rapier.windows.release.x86_64-pc-windows-msvc.dll"',
        'linux.editor.x86_64 = "bin/libgodot_rapier.linux.editor.x86_64-unknown-linux-gnu.so"':
            'linux.editor.x86_64 = "bin/libgodot_rapier.linux.release.x86_64-unknown-linux-gnu.so"',
    }
    for old, new in replacements.items():
        if text.count(old) != 1:
            raise PerformanceError(f"descriptor release-profile mapping not found: {old}")
        text = text.replace(old, new)
    descriptor.write_text(text, encoding="utf-8", newline="\n")
    binaries = descriptor.parent / "bin"
    return {
        "windows-x86_64": sha256_file(binaries / "libgodot_rapier.windows.release.x86_64-pc-windows-msvc.dll"),
        "linux-x86_64": sha256_file(binaries / "libgodot_rapier.linux.release.x86_64-unknown-linux-gnu.so"),
    }


def engine_version(redot: Path) -> str:
    result = subprocess.run(
        [str(redot), "--version"], check=False, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
        timeout=30,
    )
    if result.returncode:
        raise PerformanceError("Redot --version failed")
    return result.stdout.strip()


def process_affinity() -> list[int] | None:
    if hasattr(os, "sched_getaffinity"):
        return sorted(os.sched_getaffinity(0))
    if os.name == "nt":
        process_mask = ctypes.c_size_t()
        system_mask = ctypes.c_size_t()
        kernel32 = ctypes.windll.kernel32
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        kernel32.GetProcessAffinityMask.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.POINTER(ctypes.c_size_t),
        )
        kernel32.GetProcessAffinityMask.restype = ctypes.c_int
        if kernel32.GetProcessAffinityMask(
            kernel32.GetCurrentProcess(),
            ctypes.byref(process_mask),
            ctypes.byref(system_mask),
        ):
            return [
                index
                for index in range(ctypes.sizeof(ctypes.c_size_t) * 8)
                if process_mask.value & (1 << index)
            ]
    return None


def execution_environment(redot: Path, native_hashes: dict[str, str]) -> dict[str, Any]:
    process_cpu_count = (
        os.process_cpu_count() if hasattr(os, "process_cpu_count") else os.cpu_count()
    )
    return {
        "redot_version": engine_version(redot),
        "host_os": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpu_count": os.cpu_count(),
        "process_cpu_count": process_cpu_count,
        "cpu_affinity": process_affinity(),
        "native_release_sha256": native_hashes,
    }


def run_backend(redot: Path, backend: str, output: Path) -> dict[str, Any]:
    if backend not in {"default", "rapier"}:
        raise PerformanceError(f"unsupported backend: {backend}")
    config = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    samples_by_scenario: dict[str, list[dict[str, Any]]] = {}
    native_hashes: dict[str, str] | None = None
    with tempfile.TemporaryDirectory(prefix=f"redot-rapier2d-performance-{backend}-") as temporary:
        project = Path(temporary) / "project"
        shutil.copytree(FIXTURE, project)
        shutil.copytree(ADDON, project / "addons" / "godot-rapier2d")
        shutil.copy2(project / f"project.{backend}.godot", project / "project.godot")
        native_hashes = patch_descriptor_for_release(project)
        import_log = output / f"{backend}-import.log"
        imported = subprocess.run(
            [
                str(redot), "--headless", "--path", str(project), "--import",
                "--quit-after", "300", "--log-file", str(import_log.resolve()),
            ],
            cwd=ROOT, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", timeout=120,
        )
        if imported.returncode:
            raise PerformanceError(
                f"{backend} fixture import exited {imported.returncode}\n{imported.stdout[-4000:]}"
            )
        for scenario in config["scenarios"]:
            if backend == "default" and not scenario["baseline"]:
                continue
            scenario_samples = []
            for run_index in range(1, int(config["runs_per_scenario"]) + 1):
                stem = f"{backend}-{scenario['id']}-run-{run_index}"
                result_path = output / f"{stem}.json"
                log_path = output / f"{stem}.log"
                result_path.unlink(missing_ok=True)
                log_path.unlink(missing_ok=True)
                command = [
                    str(redot), "--headless", "--fixed-fps", str(config["fixed_fps"]),
                    "--path", str(project), "--scene", "res://main.tscn",
                    "--quit-after", str(config["warmup_frames"] + config["sample_frames"] + 300),
                    "--log-file", str(log_path.resolve()), "--",
                    f"--scenario={scenario['id']}", f"--kind={scenario['kind']}",
                    f"--count={scenario['count']}", f"--columns={scenario['columns']}",
                    f"--warmup={config['warmup_frames']}", f"--samples={config['sample_frames']}",
                    f"--result={result_path.resolve()}",
                ]
                completed = subprocess.run(
                    command, cwd=ROOT, check=False, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                    errors="replace", timeout=120,
                )
                console = completed.stdout
                if completed.returncode:
                    raise PerformanceError(f"{stem} exited {completed.returncode}\n{console[-4000:]}")
                if not result_path.is_file():
                    raise PerformanceError(f"{stem} did not write a result")
                sample = json.loads(result_path.read_text(encoding="utf-8"))
                log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
                if sample.get("status") != "PASS" or SENTINEL not in (console + log_text):
                    raise PerformanceError(f"{stem} did not pass its correctness gate")
                if sample.get("measurement") != MEASUREMENT:
                    raise PerformanceError(f"{stem} used an unexpected timing measurement")
                if len(sample.get("physics_ms", [])) != config["sample_frames"]:
                    raise PerformanceError(f"{stem} returned an incomplete physics sample")
                scenario_samples.append(sample)
            samples_by_scenario[scenario["id"]] = scenario_samples
    report = {
        "schema_version": 1,
        "status": "PASS",
        "backend": backend,
        "scenario_contract": str(SCENARIOS.relative_to(ROOT)).replace("\\", "/"),
        "scenario_contract_sha256": sha256_file(SCENARIOS),
        "fixture_manifest_sha256": fixture_manifest_sha256(),
        "runner_sha256": sha256_file(Path(__file__)),
        "environment": execution_environment(redot, native_hashes),
        "scenarios": {
            scenario_id: {
                "summary": summarize(samples),
                "samples": samples,
            }
            for scenario_id, samples in samples_by_scenario.items()
        },
    }
    output_path = output / f"performance-{backend}.json"
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output_path)
    return report


def compare(baseline_path: Path, candidate_path: Path, guardrail_path: Path, output: Path) -> dict[str, Any]:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    guardrail = json.loads(guardrail_path.read_text(encoding="utf-8"))
    if baseline.get("status") != "PASS" or candidate.get("status") != "PASS":
        raise PerformanceError("baseline and candidate reports must pass before comparison")
    if baseline["scenario_contract_sha256"] != candidate["scenario_contract_sha256"]:
        raise PerformanceError("baseline and candidate scenario contracts differ")
    if guardrail["scenario_contract_sha256"] != candidate["scenario_contract_sha256"]:
        raise PerformanceError("frozen guardrail does not match the scenario contract")
    for field in ("fixture_manifest_sha256", "runner_sha256"):
        if baseline[field] != candidate[field] or guardrail[field] != candidate[field]:
            raise PerformanceError(f"frozen guardrail does not match {field}")
    environment_fields = (
        "redot_version",
        "host_os",
        "machine",
        "processor",
        "logical_cpu_count",
        "process_cpu_count",
        "cpu_affinity",
    )
    for field in environment_fields:
        if baseline["environment"].get(field) != candidate["environment"].get(field):
            raise PerformanceError(f"baseline and candidate environments differ: {field}")
    checks = []
    failures = []
    stability = guardrail["stability"]
    for scenario_id, scenario in candidate["scenarios"].items():
        per_run = [float(value) for value in scenario["summary"]["per_run_p95_ms"]]
        spread = max(per_run) - min(per_run)
        spread_pass = spread <= float(stability["per_run_p95_range_ms_max"])
        spread_check = {
            "scenario": scenario_id,
            "metric": "per_run_p95_range_ms",
            "observed": spread,
            "limit": float(stability["per_run_p95_range_ms_max"]),
            "pass": spread_pass,
        }
        checks.append(spread_check)
        if not spread_pass:
            failures.append(spread_check)
        memory_growth = max(
            int(sample["static_memory_bytes"][-1]) - int(sample["static_memory_bytes"][0])
            for sample in scenario["samples"]
        )
        memory_pass = memory_growth <= int(stability["per_run_memory_growth_bytes_max"])
        memory_check = {
            "scenario": scenario_id,
            "metric": "per_run_static_memory_growth_bytes",
            "observed": memory_growth,
            "limit": int(stability["per_run_memory_growth_bytes_max"]),
            "pass": memory_pass,
        }
        checks.append(memory_check)
        if not memory_pass:
            failures.append(memory_check)
    for scenario_id, rule in guardrail["body_scenarios"].items():
        base = baseline["scenarios"][scenario_id]["summary"]
        cand = candidate["scenarios"][scenario_id]["summary"]
        for metric in ("median", "p95"):
            observed = float(cand["physics_ms"][metric])
            limit = float(base["physics_ms"][metric]) * float(rule[f"{metric}_ratio_max"]) + float(rule[f"{metric}_additive_ms"])
            passed = observed <= limit
            check = {"scenario": scenario_id, "metric": f"physics_ms.{metric}", "observed": observed, "limit": limit, "pass": passed}
            checks.append(check)
            if not passed:
                failures.append(check)
        observed_memory = int(cand["static_memory_bytes"]["maximum"])
        memory_limit = int(float(base["static_memory_bytes"]["maximum"]) * float(rule["memory_ratio_max"]) + int(rule["memory_additive_bytes"]))
        passed_memory = observed_memory <= memory_limit
        memory_check = {"scenario": scenario_id, "metric": "static_memory_bytes.maximum", "observed": observed_memory, "limit": memory_limit, "pass": passed_memory}
        checks.append(memory_check)
        if not passed_memory:
            failures.append(memory_check)
    fluid_rule = guardrail["fluid_scenario"]
    fluid = candidate["scenarios"][fluid_rule["id"]]["summary"]
    for metric in ("p95", "maximum"):
        observed = float(fluid["physics_ms"][metric])
        limit = float(fluid_rule[f"{metric}_ms_max"])
        passed = observed <= limit
        check = {"scenario": fluid_rule["id"], "metric": f"physics_ms.{metric}", "observed": observed, "limit": limit, "pass": passed}
        checks.append(check)
        if not passed:
            failures.append(check)
    report = {
        "schema_version": 1,
        "status": "PASS" if not failures else "FAIL",
        "policy": "regression guardrail; improvement over the default backend is not required",
        "guardrail": str(guardrail_path.resolve()),
        "guardrail_sha256": sha256_file(guardrail_path),
        "baseline": str(baseline_path.resolve()),
        "baseline_sha256": sha256_file(baseline_path),
        "candidate": str(candidate_path.resolve()),
        "candidate_sha256": sha256_file(candidate_path),
        "checks": checks,
        "failures": failures,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--backend", choices=("default", "rapier"), required=True)
    run_parser.add_argument("--redot-bin", type=Path, required=True)
    run_parser.add_argument("--output-dir", type=Path, required=True)
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--baseline", type=Path, required=True)
    compare_parser.add_argument("--candidate", type=Path, required=True)
    compare_parser.add_argument("--guardrail", type=Path, default=DEFAULT_GUARDRAIL)
    compare_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "run":
            if not args.redot_bin.is_file():
                raise PerformanceError(f"Redot executable not found: {args.redot_bin}")
            run_backend(args.redot_bin.resolve(), args.backend, args.output_dir.resolve())
        else:
            result = compare(
                args.baseline.resolve(), args.candidate.resolve(),
                args.guardrail.resolve(), args.output.resolve(),
            )
            if result["status"] != "PASS":
                return 2
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired, PerformanceError) as exc:
        print(f"performance guardrail: FAIL: {exc}", file=sys.stderr)
        return 2
    print("performance guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
