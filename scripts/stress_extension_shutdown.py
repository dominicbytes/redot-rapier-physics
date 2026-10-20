"""Require successful child-process termination after parallel fluid work."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

from engine_gate import run_gate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--project", type=Path, default=Path("bin2d"))
    parser.add_argument("--log-dir", required=True, type=Path)
    parser.add_argument("--runs", type=int, default=50)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    if args.runs < 1 or args.timeout < 1:
        parser.error("runs and timeout must be positive")
    for index in range(args.runs):
        try:
            run_gate(args.engine, [
                "--headless", "--audio-driver", "Dummy", "--fixed-fps", "60",
                "--path", str(args.project), "--script",
                "res://test/unit/test_worker_shutdown.gd", "--quit-after", "120",
            ], args.log_dir / f"shutdown-{index:03}.log",
                sentinel="WORKER SHUTDOWN TEST: SUCCESS", timeout=args.timeout)
        except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired):
            print(f"Worker shutdown failed on run {index + 1}; inspect captured diagnostics")
            return 1
    print(f"WORKER SHUTDOWN STRESS: SUCCESS ({args.runs} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
