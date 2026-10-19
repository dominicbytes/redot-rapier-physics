from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_2d_parity", ROOT / "scripts/verify_2d_parity.py"
)
assert SPEC and SPEC.loader
PARITY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PARITY)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


class SourceDeltaRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.name", "Parity Test")
        git(self.repo, "config", "user.email", "parity@example.invalid")
        git(self.repo, "config", "core.autocrlf", "false")
        (self.repo / "src").mkdir()
        (self.repo / "src/a.rs").write_text("fn a() {}\n", encoding="utf-8")
        (self.repo / "src/b.rs").write_text("fn b() {}\n", encoding="utf-8")
        git(self.repo, "add", "src")
        git(self.repo, "commit", "-q", "-m", "upstream")
        self.commit = git(self.repo, "rev-parse", "HEAD")
        (self.repo / "compat/source-deltas").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def record(self, name: str, body: str) -> None:
        (self.repo / "compat/source-deltas" / f"{name}.toml").write_text(body, encoding="utf-8")

    def valid_record(self, name: str = "fix-a", files: str = '["src/a.rs"]') -> None:
        self.record(
            name,
            f'id = "{name}"\n'
            'summary = "Fix a"\n'
            'origin = "inherited-upstream"\n'
            'upstream = "not yet reported"\n'
            f"files = {files}\n",
        )

    def compare(self):
        return PARITY._compare_runtime_source(self.repo, self.commit)

    def test_unchanged_source_passes_without_records(self) -> None:
        count, _, deltas = self.compare()
        self.assertEqual(count, 2)
        self.assertEqual(deltas, [])

    def test_unrecorded_change_is_rejected(self) -> None:
        (self.repo / "src/a.rs").write_text("fn a() { fixed(); }\n", encoding="utf-8")
        with self.assertRaisesRegex(PARITY.ParityError, "unauthorized runtime source delta: src/a.rs"):
            self.compare()

    def test_recorded_change_passes_and_is_reported(self) -> None:
        (self.repo / "src/a.rs").write_text("fn a() { fixed(); }\n", encoding="utf-8")
        self.valid_record()
        _, _, deltas = self.compare()
        self.assertEqual(
            deltas,
            [
                {
                    "id": "fix-a",
                    "origin": "inherited-upstream",
                    "upstream": "not yet reported",
                    "files": ["src/a.rs"],
                }
            ],
        )

    def test_record_does_not_authorize_other_files(self) -> None:
        (self.repo / "src/a.rs").write_text("fn a() { fixed(); }\n", encoding="utf-8")
        (self.repo / "src/b.rs").write_text("fn b() { changed(); }\n", encoding="utf-8")
        self.valid_record()
        with self.assertRaisesRegex(PARITY.ParityError, "unauthorized runtime source delta: src/b.rs"):
            self.compare()

    def test_crlf_checkout_of_recorded_file_is_not_a_delta(self) -> None:
        (self.repo / "src/a.rs").write_bytes(b"fn a() {}\r\n")
        self.valid_record()
        with self.assertRaisesRegex(PARITY.ParityError, "unchanged files"):
            self.compare()

    def test_stale_record_is_rejected(self) -> None:
        self.valid_record()
        with self.assertRaisesRegex(PARITY.ParityError, r"unchanged files: \['src/a.rs'\]"):
            self.compare()

    def test_record_naming_unknown_file_is_rejected(self) -> None:
        self.valid_record(files='["src/missing.rs"]')
        with self.assertRaisesRegex(PARITY.ParityError, "outside the upstream runtime source"):
            self.compare()

    def test_record_shape_is_validated(self) -> None:
        cases = {
            "missing field": 'id = "bad"\nsummary = "x"\norigin = "redot-port"\nfiles = ["src/a.rs"]\n',
            "id mismatch": 'id = "other"\nsummary = "x"\norigin = "redot-port"\nupstream = "x"\nfiles = ["src/a.rs"]\n',
            "bad origin": 'id = "bad"\nsummary = "x"\norigin = "unknown"\nupstream = "x"\nfiles = ["src/a.rs"]\n',
            "empty summary": 'id = "bad"\nsummary = " "\norigin = "redot-port"\nupstream = "x"\nfiles = ["src/a.rs"]\n',
            "no files": 'id = "bad"\nsummary = "x"\norigin = "redot-port"\nupstream = "x"\nfiles = []\n',
        }
        (self.repo / "src/a.rs").write_text("fn a() { fixed(); }\n", encoding="utf-8")
        for label, body in cases.items():
            with self.subTest(label):
                self.record("bad", body)
                with self.assertRaises(PARITY.ParityError):
                    self.compare()


if __name__ == "__main__":
    unittest.main()
