#!/usr/bin/env bash
set -euo pipefail
bash "$(dirname "$0")/build-redot-2d.sh" editor
bash "$(dirname "$0")/build-redot-2d.sh" debug
