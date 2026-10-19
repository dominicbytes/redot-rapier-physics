#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${GDRUST_GODOT_API_JSON:?Set GDRUST_GODOT_API_JSON to the pinned Redot API JSON}"
: "${CARGO_TARGET_DIR:?Set CARGO_TARGET_DIR to a build directory outside the checkout}"
kind=${1:?Expected editor, debug, or release}
case "$kind" in
    editor) features=single-dim2,redot-compat,serde-serialize,parallel,register-docs,godot/api-custom-json ;;
    debug|release) features=single-dim2,redot-compat,serde-serialize,parallel,godot/api-custom-json ;;
    *) echo "Unsupported artifact kind: $kind" >&2; exit 2 ;;
esac
case "$(uname -s)" in
    Linux) platform=linux; target=x86_64-unknown-linux-gnu; source=libgodot_rapier.so; suffix=so ;;
    MINGW*|MSYS*|CYGWIN*) platform=windows; target=x86_64-pc-windows-msvc; source=godot_rapier.dll; suffix=dll ;;
    *) echo "Only Windows/Linux x86-64 are supported; macOS/web/mobile builds are upstream-only." >&2; exit 2 ;;
esac
"${PYTHON:-python}" -I scripts/redot_porting.py validate --api "$GDRUST_GODOT_API_JSON"
args=(--config compat/rapier-cargo-config.toml --locked --no-default-features --features "$features" --target "$target")
profile=debug
if [[ "$kind" == release ]]; then
    args+=(--release)
    profile=release
fi
cargo build "${args[@]}"
destination="bin2d/addons/godot-rapier2d/bin/libgodot_rapier.$platform.$kind.$target.$suffix"
mkdir -p "$(dirname "$destination")"
cp "$CARGO_TARGET_DIR/$target/$profile/$source" "$destination"
if [[ -n "${RAPIER_COPY_TO:-}" ]]; then
    mkdir -p "$RAPIER_COPY_TO"
    cp "$destination" "$RAPIER_COPY_TO/"
fi
