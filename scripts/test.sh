#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${REDOT_BIN:?Set REDOT_BIN to the pinned Redot editor executable}"
"$REDOT_BIN" --headless --audio-driver Dummy --path ./bin2d --quit-after 30000 start.tscn
