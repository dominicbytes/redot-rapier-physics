from __future__ import annotations

from pathlib import Path
import queue
import subprocess
import sys
import threading
import unittest


@unittest.skipUnless(sys.platform == "win32" and sys.maxsize > 2**32, "x64 Windows stacks")
class WindowsStackTests(unittest.TestCase):
    def test_stack_capture_finds_child_and_resumes_every_thread(self):
        path = Path(__file__).resolve().parents[1] / "scripts/windows_stacks.py"
        child = "print('READY', flush=True); input(); print('DONE', flush=True)"
        parent = ("import subprocess,sys; "
                  f"p=subprocess.Popen([sys.executable,'-c',{child!r}], stdin=sys.stdin); p.wait()")
        process = subprocess.Popen([sys.executable, "-c", parent], stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, stdin=subprocess.PIPE, text=True)
        try:
            ready = queue.Queue()
            threading.Thread(target=lambda: ready.put(process.stdout.readline()), daemon=True).start()
            self.assertEqual(ready.get(timeout=10).strip(), "READY")
            captured = subprocess.run([sys.executable, str(path), str(process.pid)],
                                      capture_output=True, text=True, timeout=20, check=False)
            self.assertEqual(captured.returncode, 0)
            text = captured.stdout
            self.assertIn(f"Process {process.pid}", text)
            self.assertGreaterEqual(text.count("Process "), 2)
            self.assertIn("Threads:", text)
            self.assertIn("ntdll.dll+", text.lower())
            self.assertIn("python", text.lower())
            self.assertNotIn("failed", text)
            console, _ = process.communicate(input="continue\n", timeout=10)
            self.assertIn("DONE", console)
            self.assertEqual(process.returncode, 0)
        finally:
            if process.poll() is None:
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               capture_output=True, timeout=10, check=False)
                process.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
