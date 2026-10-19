from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")
if os.name == "nt" and shutil.which("git"):
    git_bash = Path(shutil.which("git")).parents[1] / "bin" / "bash.exe"
    if git_bash.is_file():
        BASH = str(git_bash)


@unittest.skipUnless(BASH, "Bash is required to exercise the shell helpers")
class BuildScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.scripts = self.root / "scripts"
        self.scripts.mkdir()
        for path in (ROOT / "scripts").glob("*.sh"):
            shutil.copyfile(path, self.scripts / path.name)
        tools = self.root / "tools"
        tools.mkdir()
        stubs = {
            "uname": 'printf "%s\\n" "$TEST_PLATFORM"',
            "python": 'printf "%s\\n" "$*" >> validation-args',
            "cargo": '''printf "%s\\n" "$*" >> cargo-args
profile=debug
target=x86_64-unknown-linux-gnu
source=libgodot_rapier.so
for arg in "$@"; do
    case "$arg" in
        --release) profile=release ;;
        x86_64-pc-windows-msvc) target=$arg; source=godot_rapier.dll ;;
    esac
done
mkdir -p "$CARGO_TARGET_DIR/$target/$profile"
printf library > "$CARGO_TARGET_DIR/$target/$profile/$source"''',
            "redot": 'printf "%s\\n" "$*" > redot-args',
        }
        for name, body in stubs.items():
            path = tools / name
            path.write_text("#!/usr/bin/env bash\nset -eu\n" + body + "\n", newline="\n")
            path.chmod(0o755)
        self.env = dict(os.environ, PATH=str(tools) + os.pathsep + os.environ["PATH"],
                        TEST_PLATFORM="Linux", GDRUST_GODOT_API_JSON="api.json",
                        CARGO_TARGET_DIR="target", REDOT_BIN="./tools/redot", PYTHON="python")
        # Git Bash prepends its own tools on startup; keep the stubs first.
        (self.root / "bash-env").write_text('export PATH="$PWD/tools:$PATH"\n', newline="\n")
        self.env["BASH_ENV"] = "bash-env"
        self.env.pop("RAPIER_COPY_TO", None)

    def run_script(self, name):
        return subprocess.run([BASH, str(self.scripts / name)], cwd=self.root, env=self.env,
                              capture_output=True, text=True, timeout=30)

    def test_supported_profiles_stage_descriptor_names_and_optional_copy(self):
        for platform, triple, suffix in (("Linux", "x86_64-unknown-linux-gnu", "so"),
                                         ("MINGW64_NT", "x86_64-pc-windows-msvc", "dll")):
            self.env["TEST_PLATFORM"] = platform
            self.env["RAPIER_COPY_TO"] = "secondary"
            for name in ("build-dev-2d.sh", "build-rel-2d.sh"):
                result = self.run_script(name)
                self.assertEqual(result.returncode, 0, result.stderr)
            os_name = "linux" if platform == "Linux" else "windows"
            for kind in ("editor", "debug", "release"):
                name = f"libgodot_rapier.{os_name}.{kind}.{triple}.{suffix}"
                self.assertTrue((self.root / "bin2d/addons/godot-rapier2d/bin" / name).is_file())
                self.assertTrue((self.root / "secondary" / name).is_file())
        commands = (self.root / "cargo-args").read_text().splitlines()
        self.assertEqual(len(commands), 6)
        for index, command in enumerate(commands):
            self.assertIn("--config compat/rapier-cargo-config.toml --locked --no-default-features", command)
            self.assertIn("single-dim2,redot-compat,serde-serialize,parallel", command)
            self.assertIn("godot/api-custom-json", command)
            self.assertEqual("register-docs" in command, index % 3 == 0)
            self.assertEqual("--release" in command, index % 3 == 2)
        self.assertEqual((self.root / "validation-args").read_text().count("--api api.json"), 6)

    def test_no_secondary_copy_without_explicit_destination(self):
        self.assertEqual(self.run_script("build-rel-2d.sh").returncode, 0)
        self.assertFalse((self.root / "secondary").exists())

    def test_missing_api_and_unsupported_platform_fail_before_cargo(self):
        self.env.pop("GDRUST_GODOT_API_JSON")
        result = self.run_script("build-dev-2d.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("GDRUST_GODOT_API_JSON", result.stderr)
        self.env["GDRUST_GODOT_API_JSON"] = "api.json"
        self.env["TEST_PLATFORM"] = "Darwin"
        result = self.run_script("build-dev-2d.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("upstream-only", result.stderr)
        self.assertFalse((self.root / "cargo-args").exists())

    def test_unsupported_entry_points_explain_port_boundary(self):
        for name in ("build-dev-2d-f64.sh", "build-dev-2d-web.sh", "build-dev-3d.sh", "build-rel-3d.sh"):
            result = self.run_script(name)
            self.assertEqual(result.returncode, 2)
            self.assertIn("upstream-only", result.stderr)

    def test_test_script_honors_redot_bin_and_frame_bound(self):
        result = self.run_script("test.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = (self.root / "redot-args").read_text()
        self.assertIn("--headless --audio-driver Dummy", args)
        self.assertIn("--quit-after 30000", args)
        self.env.pop("REDOT_BIN")
        self.assertNotEqual(self.run_script("test.sh").returncode, 0)


if __name__ == "__main__":
    unittest.main()
