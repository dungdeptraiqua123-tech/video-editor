import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ve import skills as SK


def fake_ref(root: Path) -> Path:
    ref = root / "reference"
    for s, names in {"hyperframes": ["hyperframes", "media-use"], "herk-edit-kit": ["hyperframes", "cut-silences"], "gsap": ["gsap-core"]}.items():
        for n in names:
            d = ref / s / n
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(f"---\nname: {n}\ndescription: {s} {n}\n---\nbody\n", encoding="utf-8")
    return ref


class Install(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.p = mock.patch.object(SK, "REF", fake_ref(self.tmp))
        self.p.start()
        self.dst = self.tmp / "skills"

    def tearDown(self):
        self.p.stop()

    def test_installs_all_and_renames_duplicates(self):
        r = SK.install(self.dst)
        self.assertEqual(sorted(r["installed"]), ["cut-silences", "gsap-core", "herk-hyperframes", "hyperframes", "media-use"])
        # bộ chính thức giữ tên gốc, bản trùng được đổi cả tên thư mục lẫn name trong SKILL.md
        self.assertIn("description: hyperframes hyperframes", (self.dst / "hyperframes" / "SKILL.md").read_text())
        self.assertIn("name: herk-hyperframes\n", (self.dst / "herk-hyperframes" / "SKILL.md").read_text())
        self.assertEqual(json.loads((self.dst / "gsap-core" / SK.MARK).read_text())["set"], "gsap")

    def test_never_overwrites_user_skill_and_reinstall_is_clean(self):
        own = self.dst / "media-use"
        own.mkdir(parents=True)
        (own / "SKILL.md").write_text("của tôi")
        SK.install(self.dst)
        r = SK.install(self.dst)
        self.assertEqual(r["skipped"], ["media-use"])
        self.assertEqual((own / "SKILL.md").read_text(), "của tôi")
        st = SK.status(self.dst)
        self.assertEqual((st["installed"], st["total"], st["conflicts"]), (4, 5, ["media-use"]))

    def test_only_and_remove(self):
        r = SK.install(self.dst, ["gsap"])
        self.assertEqual(r["installed"], ["gsap-core"])
        with self.assertRaises(SK.VEError):
            SK.install(self.dst, ["khong-co"])
        SK.install(self.dst)
        self.assertEqual(SK.remove(self.dst), 5)
        self.assertEqual([d.name for d in self.dst.iterdir()], [])


if __name__ == "__main__":
    unittest.main()
