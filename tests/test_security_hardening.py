import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class TestSecurityHardening(unittest.TestCase):
    def test_autostart_uses_subprocess_not_os_system(self):
        content = (REPO_ROOT / "ui" / "main_window.py").read_text(encoding="utf-8")
        self.assertNotIn("os.system(", content)
        self.assertIn("subprocess.run(", content)

    def test_bare_except_reduced_in_main(self):
        content = (REPO_ROOT / "main.py").read_text(encoding="utf-8")
        self.assertNotIn("except:\n", content)
        self.assertIn("except Exception as e:", content)


if __name__ == "__main__":
    unittest.main()
