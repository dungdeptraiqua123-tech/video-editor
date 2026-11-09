"""Cảnh motion: tên cảnh có sẵn khớp engine, kiểm tra cảnh viết riêng, neo thời gian trong params, gói riêng theo dự án."""
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from ve import motion as MOTION
from ve.content import resolve_content

from tests.test_content import TEXT, words

ROOT = Path(__file__).resolve().parents[1]


def prj_at(d: Path):
    return SimpleNamespace(root=d, work=d / "work", media=d / "media")


GOOD = '''import React from "react";
import { AbsoluteFill } from "remotion";
import { Headline, Checklist, SceneProps } from "./kit";

const Canh: React.FC<SceneProps> = ({ p, safe }) => (
  <AbsoluteFill>
    <Headline x={safe.left} y={safe.top} title={p.title} />
    <Checklist x={safe.left} y={600} items={(p.items || []).map((it: any) => ({ text: it.text, at: it.d ?? 0.5 }))} />
  </AbsoluteFill>
);
export default Canh;
'''


class BuiltinNames(unittest.TestCase):
    def test_builtin_matches_engine(self):
        src = (ROOT / "engine/src/motion/scenes.tsx").read_text(encoding="utf-8")
        block = src[src.index("registerScenes({"):]
        names = set(re.findall(r'^\s*"?([a-z0-9-]+)"?:\s*[A-Z]\w*,', block, re.M))
        self.assertEqual(names, MOTION.BUILTIN)


class SceneFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        (self.d / "motion").mkdir()
        self.prj = prj_at(self.d)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, code):
        (self.d / "motion" / name).write_text(code, encoding="utf-8")

    def test_good_scene(self):
        self.write("checklist-rieng.tsx", GOOD)
        self.assertEqual(MOTION.check_scenes(self.prj), [])
        self.assertTrue(MOTION.known(self.prj)("checklist-rieng"))
        self.assertTrue(MOTION.known(self.prj)("chat"))
        self.assertFalse(MOTION.known(self.prj)("khong-co"))

    def test_bad_scenes(self):
        self.write("Sai_Ten.tsx", GOOD)
        self.write("chat.tsx", GOOD)
        self.write("mang.tsx", GOOD.replace('import { AbsoluteFill } from "remotion";', 'import { AbsoluteFill } from "remotion";\nimport axios from "axios";') + "\nfetch('http://x');\n")
        self.write("thieu.tsx", GOOD.replace("export default Canh;", ""))
        errs = "\n".join(MOTION.check_scenes(self.prj))
        self.assertIn("Sai_Ten.tsx: tên file", errs)
        self.assertIn("chat.tsx: trùng tên cảnh có sẵn", errs)
        self.assertIn('không được import "axios"', errs)
        self.assertIn("gọi mạng hoặc eval", errs)
        self.assertIn("thieu.tsx: thiếu `export default`", errs)

    def test_import_other_scene(self):
        self.write("phan-a.tsx", GOOD)
        self.write("phan-b.tsx", GOOD.replace('import { Headline', 'import A from "./phan-a";\nimport { Headline'))
        self.assertEqual(MOTION.check_scenes(self.prj), [])

    def test_stage_registers_scenes(self):
        self.write("canh-mot.tsx", GOOD)
        self.write("canh-hai.tsx", GOOD)
        with tempfile.TemporaryDirectory() as eng, mock.patch.object(MOTION, "ENGINE", Path(eng)):
            d = MOTION.stage(self.prj)
            idx = (d / "index.ts").read_text(encoding="utf-8")
            self.assertIn('registerRoot(RemotionRoot);', idx)
            self.assertIn('"canh-hai": S0', idx)
            self.assertIn('"canh-mot": S1', idx)
            self.assertTrue((d / "canh-mot.tsx").is_file())
            self.assertIn("motion/kit", (d / "kit.ts").read_text(encoding="utf-8"))


class MotionContent(unittest.TestCase):
    def setUp(self):
        self.w = words(TEXT)
        self.dur = self.w[-1]["end"] + 4
        self.base = {"hook": {"title": "Bitcoin"}, "hookSec": 1.0, "outroSec": 2.0, "cta": "Theo dõi"}

    def test_params_anchor_to_seconds(self):
        c = dict(self.base, beats=[{"start": "Bitcoin tăng", "end": "85 ngàn đô", "head": "",
                                    "g": {"type": "motion", "scene": "checklist", "params": {"title": "Mốc giá", "items": [
                                        {"text": "Cản 87K", "say": "87 ngàn"}, {"text": "Hỗ trợ 85K", "say": "85 ngàn"}]}}}])
        d, rep = resolve_content(c, self.w, self.dur)
        self.assertEqual(rep.errors, [])
        items = d["beats"][0]["g"]["params"]["items"]
        self.assertGreater(items[1]["d"], items[0]["d"])
        self.assertNotIn("say", items[0])

    def test_unknown_scene_and_layer(self):
        c = dict(self.base, beats=[{"start": "Bitcoin tăng", "dur": 3, "g": {"type": "motion", "scene": "khong-co", "layer": "giua"}}])
        _, rep = resolve_content(c, self.w, self.dur)
        errs = "\n".join(rep.errors)
        self.assertIn('không có cảnh motion "khong-co"', errs)
        self.assertIn("motion/khong-co.tsx", errs)
        self.assertIn("layer chỉ là", errs)

    def test_overlay_does_not_cover_speaker(self):
        g = {"type": "motion", "scene": "chu-nghieng", "layer": "overlay", "params": {"big": "newbie"}}
        c = dict(self.base, beats=[{"start": "xin chào", "end": "cảm ơn", "g": g}])
        _, rep = resolve_content(c, self.w, self.dur, mode="talking")
        self.assertFalse([w for w in rep.warnings if "phủ" in w and "thời lượng" in w])
        g2 = dict(g, layer="full")
        _, rep2 = resolve_content(dict(self.base, beats=[{"start": "xin chào", "end": "cảm ơn", "g": g2}]), self.w, self.dur, mode="talking")
        self.assertTrue([w for w in rep2.warnings if "thời lượng" in w])


class Library(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        (self.d / "du-an" / "motion").mkdir(parents=True)
        (self.d / "du-an" / "work").mkdir()
        (self.d / "du-an" / "motion" / "keo-tha.tsx").write_text(GOOD, encoding="utf-8")
        self.prj = prj_at(self.d / "du-an")
        self.prj.cfg = {"content": {"beats": [{"head": "Kéo file video vào chat", "g": {"type": "motion", "scene": "keo-tha"}}]}}
        self.home = mock.patch("ve.env.HOME", self.d / "home")
        self.home.start()

    def tearDown(self):
        self.home.stop()
        self.tmp.cleanup()

    def test_plan_sheet_suggests(self):
        (self.prj.work / "loi-thoai.txt").write_text(
            "[   0.50 –    3.00] Trước đây mình mất 3 tiếng để edit\n[   3.00 –    5.00] Bước đầu tiên là cài Claude Code\n[   5.00 –    6.00] Xin chào cả nhà\n",
            encoding="utf-8")
        txt = MOTION.plan_sheet(self.prj).read_text(encoding="utf-8")
        self.assertIn("| 0.50–3.00 | Trước đây mình mất 3 tiếng để edit | so-lieu, thoi-gian | dem-so, dong-ho |", txt)
        self.assertIn("checklist", txt.splitlines()[[i for i, l in enumerate(txt.splitlines()) if "Bước đầu tiên" in l][0]])
        self.assertIn("| Xin chào cả nhà | — | người nói |", txt)

    def test_autosave_rate_find_use(self):
        self.assertEqual(MOTION.autosave(self.prj, approved=True), ["keo-tha"])
        item = MOTION.lib_items()[0]
        self.assertEqual((item["name"], item["score"], item["y"]), ("keo-tha", 1.0, "Kéo file video vào chat"))
        self.assertEqual(MOTION.find("kéo file vào chat")[0]["name"], "keo-tha")
        MOTION.rate("keo-tha", -2, "chuyển động quá chậm")
        self.assertEqual(MOTION.lib_items()[0]["score"], -1.0)
        self.assertIn("chuyển động quá chậm", MOTION.lib_items()[0]["notes"][-1])
        MOTION.set_off("keo-tha")
        self.assertNotIn("keo-tha", [r["name"] for r in MOTION.find("kéo file vào chat")])
        other = prj_at(self.d / "khac")
        dst = MOTION.use(other, "keo-tha", "keo-tha-2")
        self.assertTrue(dst.is_file())
        self.assertTrue(MOTION.known(other)("keo-tha-2"))


if __name__ == "__main__":
    unittest.main()
