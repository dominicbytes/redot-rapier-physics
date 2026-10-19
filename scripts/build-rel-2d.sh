#!/usr/bin/env bash
set -euo pipefail
# Optional secondary staging directory: RAPIER_COPY_TO.
bash "$(dirname "$0")/build-redot-2d.sh" release
