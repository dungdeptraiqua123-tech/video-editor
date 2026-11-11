"""Bộ dựng HyperFrames: chọn bộ dựng, lịch âm hiệu ứng / nhạc nền chép đúng theo Video.tsx, dự án index.html sinh ra hợp lệ."""
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ve import hf as HF
from ve.env import SKILL_DIR, VEError


def data(**kw):
    d = {
        "format": {"w": 1080, "h": 1920, "fps": 30},
        "duration": 10.0,
        "mode": "talking",
        "media": {"main": "cut.mp4", "hasVideo": True, "srcW": 1080, "srcH": 1920},
        "sfx": {"files": {r: f"sfx/{r}.mp3" for r in ("whoosh", "impact", "riser", "click", "pop", "tick")}, "volume": 1.0},
        "hookSec": 1.5,
        "outroSec": 2.0,
        "words": [{"text": "a", "start": 1.0, "end": 1.3}, {"text": "b", "start": 1.4, "end": 1.8}, {"text": "c", "start": 5.0, "end": 5.4}],
        "beats": [{"start": 2.0, "end": 5.0, "head": "x", "g": {"type": "levels", "title": "t", "levels": [{"value": "1", "label": "a", "kind": "res", "d": 0.1}, {"value": "2", "label": "b", "kind": "sup", "d": 1.5}]}}],
        "topics": [{"start": 0, "end": 10, "kicker": "k", "title": "t", "items": [{"at": 0.5, "text": "trước hook"}, {"at": 6.0, "text": "giữa"}, {"at": 9.5, "text": "trong outro"}]}],
        "pops": [{"t": 3.0, "id": "si:bitcoin", "word": "Bitcoin"}],
        "punches": [{"t": 6.5, "text": "$87K"}],
    }
    d.update(kw)
    return d


class EngineChoice(unittest.TestCase):
    def test_default_and_overrides(self):
        prj = mock.Mock(cfg={})
        with mock.patch.dict(os.environ, {}, clear=False), mock.patch.object(HF, "load_config", return_value={}):
            os.environ.pop("VE_ENGINE", None)
            self.assertEqual(HF.engine_name(prj), "remotion")
            with mock.patch.dict(os.environ, {"VE_ENGINE": "hf"}):
                self.assertEqual(HF.engine_name(prj), "hyperframes")
                # project.json thắng biến môi trường
                self.assertEqual(HF.engine_name(mock.Mock(cfg={"engine": "remotion"})), "remotion")
        with mock.patch.object(HF, "load_config", return_value={"engine": "hyperframes"}):
            os.environ.pop("VE_ENGINE", None)
            self.assertTrue(HF.is_hf(prj))

    def test_unknown_engine_is_an_error(self):
        with self.assertRaises(VEError):
            HF.engine_name(mock.Mock(cfg={"engine": "after-effects"}))


class SoundPlan(unittest.TestCase):
    def test_sfx_schedule_matches_video_tsx(self):
        ev = HF.sfx_events(data())
        roles = [e[0] for e in ev]
        # whoosh 6 khung trước khung đồ hoạ, 24 khung, 0.17
        w = next(e for e in ev if e[0] == "whoosh")
        self.assertAlmostEqual(w[1], (60 - 6) / 30)
        self.assertAlmostEqual(w[2], 24 / 30)
        self.assertAlmostEqual(w[3], 0.17)
        # pop chỉ cho phần tử bật sau 0,25 s (phần tử bật ngay lúc mở đã có whoosh) + pop của icon theo lời
        pops = sorted(round(e[1], 3) for e in ev if e[0] == "pop")
        self.assertEqual(pops, [3.0, 3.5])
        # tick: chỉ ý trong khoảng giữa hook và outro
        self.assertEqual([round(e[1], 2) for e in ev if e[0] == "tick"], [6.0])
        # impact mở đầu + chữ đập; riser 30 khung trước outro; click 30 khung sau
        self.assertEqual(sorted(round(e[1], 2) for e in ev if e[0] == "impact"), [0.0, 6.5])
        self.assertAlmostEqual(next(e for e in ev if e[0] == "riser")[1], (300 - 60 - 30) / 30)
        self.assertAlmostEqual(next(e for e in ev if e[0] == "click")[1], (300 - 60 + 30) / 30)
        self.assertIn("click", roles)

    def test_sfx_volume_and_off(self):
        ev = HF.sfx_events(data(sfx={"files": {"pop": "sfx/pop.mp3"}, "volume": 0.5}))
        self.assertTrue(ev and all(e[0] == "pop" for e in ev))
        self.assertAlmostEqual(ev[0][3], 0.11)
        self.assertEqual(HF.sfx_events(data(sfx=False)), [])

    def test_no_tick_without_speaker(self):
        self.assertFalse([e for e in HF.sfx_events(data(mode="faceless")) if e[0] == "tick"])

    def test_music_lane_ducks_under_speech_and_fades(self):
        d = data()
        d["media"]["music"] = {"src": "nhac.mp3", "volume": 0.2, "duck": 0.3, "fade": 1.0}
        lane = HF.music_lane(d, 0.0, 10.0)
        at = lambda t: min(lane, key=lambda p: abs(p["t"] - t))["v"]  # noqa: E731
        self.assertEqual(lane[0], {"t": 0.0, "v": 0.0})  # tăng dần từ 0
        self.assertAlmostEqual(at(1.5), 0.3, places=3)  # đang nói: hạ xuống duck
        self.assertAlmostEqual(at(3.0), 1.0, places=3)  # nghỉ nói: lên lại
        self.assertAlmostEqual(at(10.0), 0.0, places=3)  # giảm dần ở cuối
        self.assertTrue(all(0 <= p["v"] <= 1 for p in lane))
        self.assertEqual([p["t"] for p in lane], sorted(p["t"] for p in lane))

    def test_music_lane_respects_point_limit(self):
        d = data(duration=600.0)
        d["words"] = [{"text": "x", "start": i * 1.0, "end": i * 1.0 + 0.3} for i in range(600)]
        d["media"]["music"] = {"src": "nhac.mp3", "volume": 0.2}
        self.assertLessEqual(len(HF.music_lane(d, 0.0, 600.0)), 500)


class ProjectFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ve-hf-"))
        (self.tmp / "media" / "sfx").mkdir(parents=True)
        (self.tmp / "work").mkdir()
        for f in ("cut.mp4", "broll.mp4", "sfx/pop.mp3", "sfx/whoosh.mp3"):
            (self.tmp / "media" / f).write_bytes(b"x")

    def prj(self):
        return mock.Mock(root=self.tmp, media=self.tmp / "media", work=self.tmp / "work", cfg={"name": "Thử <&>"}, slug="thu")

    def test_plan_media_video_clips(self):
        d = data(duration=9.99)
        d["beats"].append({"start": 6.0, "end": 8.0, "head": "", "g": {"type": "motion", "scene": "x", "params": {"items": [{"src": "broll.mp4"}, {"src": "anh.png"}]}}})
        vids, auds = HF.plan_media(self.prj(), d)
        self.assertEqual(vids[0][:4], ("v-main", "cut.mp4", 0.0, 10.0))  # làm tròn đúng số khung như Remotion
        self.assertEqual(vids[0][4], {"data-has-audio": "true"})
        b = [v for v in vids if v[1] == "broll.mp4"]
        self.assertEqual(len(b), 1)
        self.assertAlmostEqual(b[0][2], 6.0)
        self.assertAlmostEqual(b[0][3], 2.0)
        self.assertIn("muted", b[0][4])
        self.assertTrue(all(a[0].startswith("sfx-") for a in auds))

    def test_faceless_main_is_audio_and_background_loops(self):
        d = data(mode="faceless", duration=10.0)
        d["media"] = {"main": "voice.m4a", "hasVideo": False, "background": {"src": "broll.mp4", "duration": 4.0}}
        vids, auds = HF.plan_media(self.prj(), d)
        self.assertEqual([(v[1], v[2], v[3]) for v in vids], [("broll.mp4", 0.0, 4.0), ("broll.mp4", 4.0, 4.0), ("broll.mp4", 8.0, 2.0)])
        self.assertEqual(auds[0][:2], ("a-main", "voice.m4a"))

    def test_index_html(self):
        d = data()
        (self.tmp / "work" / "data.json").write_text(json.dumps(d), encoding="utf-8")
        bundle = self.tmp / "bundle"
        bundle.mkdir()
        for f in ("ve.js", "ve.css", "gsap.min.js"):
            (bundle / f).write_text("//", encoding="utf-8")
        with mock.patch.object(HF, "bundle", return_value=bundle), mock.patch("ve.render._data", return_value=self.tmp / "work" / "data.json"):
            out = HF.project(self.prj())
        html = (out / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-composition-id="main"', html)
        self.assertIn('data-duration="10"', html)
        self.assertIn("&lt;&amp;&gt;", html)  # tên dự án được thoát ký tự
        self.assertIn('window.__timelines["main"] = tl', html)
        # mọi thẻ media có id, class clip, thời gian; <audio> có id để vào bản trộn
        tags = re.findall(r"<(video|audio) ([^>]*)>", html)
        self.assertTrue(tags)
        for kind, attrs in tags:
            self.assertRegex(attrs, r'id="[^"]+"')
            self.assertIn('class="clip"', attrs)
            self.assertRegex(attrs, r'data-start="[\d.]+"')
            if kind == "video":
                self.assertTrue("data-has-audio" in attrs or "muted" in attrs)
        props = json.loads((out / "ve" / "props.json").read_text(encoding="utf-8"))
        self.assertEqual(props["mediaBase"], "assets/")
        self.assertTrue((out / "assets").exists())
        clips = (out / "ve" / "clips.js").read_text(encoding="utf-8")
        self.assertIn("assets/cut.mp4", clips)


class Sources(unittest.TestCase):
    def test_shim_covers_every_remotion_import(self):
        """Mọi tên engine/src lấy từ "remotion" phải có trong lớp thay thế của HyperFrames."""
        names = set()
        for f in (SKILL_DIR / "engine" / "src").rglob("*.ts*"):
            for m in re.finditer(r'import\s*\{([^}]*)\}\s*from\s*"remotion"', f.read_text(encoding="utf-8")):
                names |= {x.strip().split(" as ")[0] for x in m.group(1).split(",") if x.strip()}
        shim = (SKILL_DIR / "engine-hf" / "shim" / "remotion.tsx").read_text(encoding="utf-8")
        exported = set(re.findall(r"export (?:const|type|function) (\w+)", shim))
        self.assertFalse(names - exported, f"thiếu trong shim: {sorted(names - exported)}")

    def test_pinned_versions(self):
        pkg = json.loads((SKILL_DIR / "engine-hf" / "package.json").read_text(encoding="utf-8"))
        for k, v in pkg["dependencies"].items():
            self.assertRegex(v, r"^\d+\.\d+\.\d+$", f"{k} phải ghim đúng phiên bản")
        lock = json.loads((SKILL_DIR / "engine-hf" / "package-lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["packages"]["node_modules/hyperframes"]["version"], pkg["dependencies"]["hyperframes"])
        # dùng chung phiên bản đồ hoạ với bộ dựng Remotion
        rem = json.loads((SKILL_DIR / "engine" / "package.json").read_text(encoding="utf-8"))["dependencies"]
        for k in ("react", "react-dom", "simple-icons", "lucide-static", "@fontsource/be-vietnam-pro"):
            self.assertEqual(pkg["dependencies"][k], rem[k], k)


if __name__ == "__main__":
    unittest.main()
