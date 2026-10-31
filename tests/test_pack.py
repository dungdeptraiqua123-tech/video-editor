"""Bản gọn để tải lên: chỉ gồm phần lõi, không kèm thư viện tham khảo và bộ cài skill liên quan."""
import importlib.util
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("dong_goi", ROOT / "tools" / "dong-goi.py")
dong_goi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dong_goi)


class PackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.res = dong_goi.pack(Path(cls.tmp.name) / "ve.zip")
        with zipfile.ZipFile(cls.res["out"]) as z:
            cls.names = z.namelist()
            cls.third = z.read("video-editor/THIRD_PARTY.md").decode("utf-8")
            cls.skill = z.read("video-editor/SKILL.md").decode("utf-8")
            cls.safety = z.read("video-editor/AN-TOAN.md").decode("utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_core_only(self):
        self.assertIn("video-editor/SKILL.md", self.names)
        self.assertIn("video-editor/AN-TOAN.md", self.names)
        self.assertIn("video-editor/ve/cli.py", self.names)
        self.assertIn("video-editor/engine/src/Video.tsx", self.names)
        for bad in ("reference/", "tests/", "tools/", "ve/skills.py", "__pycache__", "node_modules/"):
            self.assertFalse([n for n in self.names if bad in n], bad)

    def test_small(self):
        self.assertLess(self.res["zip_bytes"], 5_000_000)

    def test_frontmatter(self):
        m = re.match(r"---\nname: (\S+)\ndescription: (.+?)\n---\n", self.skill, re.S)
        self.assertTrue(m)
        self.assertEqual(m.group(1), "video-editor")
        self.assertLess(len(m.group(2)), 1024)

    def test_third_party_trimmed(self):
        self.assertNotIn("| `reference/", self.third)
        self.assertIn("Remotion", self.third)

    def test_safety_doc_core_only(self):
        self.assertIn("## Phần lõi", self.safety)
        self.assertIn("## Bản gọn để tải lên", self.safety)
        self.assertNotIn("heygen", self.safety.lower())
        self.assertNotIn("## Chỉ có ở bản đầy đủ", self.safety)

    def test_network_hosts_known(self):
        allowed = {"127.0.0.1", "api.elevenlabs.io", "assets.mixkit.co", "huggingface.co", "registry.npmjs.org", "remotion.dev",
                   "github.com", "dotenvx.com", "opencollective.com", "patreon.com", "tidelift.com"}
        self.assertEqual(set(self.res["hosts"]) - allowed, set())


if __name__ == "__main__":
    unittest.main()
