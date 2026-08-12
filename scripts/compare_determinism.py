#!/usr/bin/env python3
"""Validate and compare canonical Rapier2D deterministic replay outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PROTOCOL = "redot-rapier2d-determinism-v1"
CHECKPOINTS = (60, 120, 180, 240, 300)


class ReplayError(RuntimeError):
    """Raised when replay evidence is incomplete or divergent."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def inspect_replay(path: Path) -> dict[str, Any]:
    try:
        replay = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReplayError(f"cannot load {path}: {exc}") from exc
    if replay.get("protocol") != PROTOCOL:
        raise ReplayError(f"unexpected protocol in {path}")
    profile = replay.get("profile")
    frames = replay.get("frames")
    observed = replay.get("observed")
    if not isinstance(profile, dict) or not isinstance(frames, list):
        raise ReplayError(f"invalid replay structure in {path}")
    if not isinstance(observed, dict):
        raise ReplayError(f"missing observed identity in {path}")
    if profile.get("simulation_frames") != len(frames):
        raise ReplayError(f"frame count mismatch in {path}")
    if len(frames) < CHECKPOINTS[-1]:
        raise ReplayError(f"replay is too short in {path}")
    if profile.get("solver_parallel") is not False:
        raise ReplayError(f"solver_parallel must be false in {path}")
    if profile.get("redot_separate_thread") is not False:
        raise ReplayError(f"Redot separate-thread physics must be false in {path}")
    if any(not isinstance(frame, list) for frame in frames):
        raise ReplayError(f"invalid frame payload in {path}")

    canonical = {"protocol": PROTOCOL, "profile": profile, "frames": frames}
    return {
        "path": str(path.resolve()),
        "observed": observed,
        "profile": profile,
        "checkpoint_sha256": {
            str(frame): sha256(frames[frame - 1]) for frame in CHECKPOINTS
        },
        "final_state_sha256": sha256(frames[-1]),
        "replay_sha256": sha256(canonical),
        "frame_count": len(frames),
    }


def compare_replays(paths: list[Path]) -> dict[str, Any]:
    if len(paths) < 2:
        raise ReplayError("at least two replay outputs are required")
    runs = [inspect_replay(path) for path in paths]
    reference = runs[0]
    identity_fields = (
        "profile",
        "checkpoint_sha256",
        "final_state_sha256",
        "replay_sha256",
        "frame_count",
    )
    for run in runs[1:]:
        for field in identity_fields:
            if run[field] != reference[field]:
                raise ReplayError(
                    f"determinism divergence in {field}: "
                    f"{reference['path']} != {run['path']}"
                )
    return {
        "status": "PASS",
        "protocol": PROTOCOL,
        "run_count": len(runs),
        "platforms": sorted(
            {
                f"{run['observed'].get('os')}-{run['observed'].get('arch')}"
                for run in runs
            }
        ),
        "profile": reference["profile"],
        "checkpoint_sha256": reference["checkpoint_sha256"],
        "final_state_sha256": reference["final_state_sha256"],
        "replay_sha256": reference["replay_sha256"],
        "runs": runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replays", nargs="+", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = compare_replays([path.resolve() for path in args.replays])
    except ReplayError as exc:
        report = {"status": "FAIL", "error": str(exc)}
        code = 2
    else:
        code = 0
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
