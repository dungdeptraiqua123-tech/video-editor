"""Cắt video dài thành short: chấm điểm đoạn, không chồng nhau, bỏ từ nối đầu, tạo dự án con dùng lại lời thoại."""
import json
import tempfile
import unittest
from pathlib import Path

from ve import shorts as SH
from ve.env import VEError
from ve.project import Project, init_project


def seg(start, text, gap_after=0.05, per=0.3):
    """Đoạn Whisper giả: mỗi từ dài `per` giây, liền nhau."""
    ws, t = [], start
    for w in text.split():
        ws.append({"w": " " + w, "s": round(t, 2), "e": round(t + per - 0.02, 2), "p": 0.95})
        t += per
    return {"start": start, "end": round(t, 2), "text": " " + text, "words": ws}, t + gap_after


def transcript(lines, start=0.0):
    out, t = [], start
    for text, gap in lines:
        s, t = seg(t, text, gap)
        out.append(s)
    return out


FILLER = "thị trường hôm qua đi ngang không có gì nhiều để nói thêm cả ngày"


class ScoreTest(unittest.TestCase):
    def test_skip_connector_before_strong_opener(self):
        segs = transcript([(FILLER, 0.05), ("và bạn hãy hết sức lưu ý là tối nay có tin cực kỳ quan trọng", 0.05)])
        units = SH.units_from(segs)
        self.assertEqual(units[1].lead, 1)
        c = SH.score_window(units, 1, 1, 2, 60, 30)
        self.assertTrue(c.hook.startswith("bạn hãy"), c.hook)
        self.assertAlmostEqual(c.start, units[1].words[1].start)
        self.assertGreaterEqual(c.parts["start"], 0.75)

    def test_keep_connector_when_next_is_not_new_idea(self):
        segs = transcript([("và cái giá thì vẫn đứng yên ở đó", 0.05)])
        self.assertEqual(SH.units_from(segs)[0].lead, 0)

    def test_hook_beats_plain_start(self):
        segs = transcript([("bạn hãy lưu ý điều cực kỳ quan trọng này trước khi vào lệnh", 0.6), (FILLER, 0.6)])
        units = SH.units_from(segs)
        strong = SH.score_window(units, 0, 0, 2, 60, 5)
        plain = SH.score_window(units, 1, 1, 2, 60, 5)
        self.assertGreater(strong.parts["hook"], plain.parts["hook"])

    def test_intro_penalty(self):
        segs = transcript([("xin chào các bạn chào mừng các bạn quay trở lại với kênh", 0.6), (FILLER, 0.6)])
        units = SH.units_from(segs)
        c = SH.score_window(units, 0, 1, 2, 60, 8)
        self.assertTrue(any("câu chào mở" in r for r in c.reasons))

    def test_long_segment_split_at_pause(self):
        s, _ = seg(0, "câu thứ nhất nói về giá Bitcoin hôm nay đang tăng nhẹ", per=0.4)
        s2, _ = seg(s["end"] + 0.8, "câu thứ hai nói về dòng tiền ETF đổ vào rất mạnh", per=0.4)
        merged = {"start": 0, "end": s2["end"], "text": s["text"] + s2["text"], "words": s["words"] + s2["words"]}
        units = SH.units_from([merged])
        self.assertEqual(len(units), 2)


class PickTest(unittest.TestCase):
    def test_no_overlap(self):
        lines = [(f"ý số {i} có con số {i * 100} và lưu ý quan trọng cho anh em", 0.5) for i in range(40)]
        units = SH.units_from(transcript(lines))
        chosen = SH.pick(SH.candidates(units, 10, 20), n=6)
        self.assertGreaterEqual(len(chosen), 3)
        for x, y in zip(chosen, chosen[1:]):
            self.assertLessEqual(x.end - y.start, 1.0)
        for c in chosen:
            self.assertTrue(10 <= c.dur <= 20, c.dur)


class MakeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        src = self.root / "dai.mp4"
        src.write_bytes(b"0" * 100)
        self.prj = init_project(self.root / "dai", str(src), None, "9:16", "trung-tinh", None, None, "Video dài", None, pace="nhanh")
        lines = [("xin chào các bạn", 0.6)] + [(f"phần {i} giá đang ở mốc {80 + i} ngàn anh em lưu ý", 0.5) for i in range(30)]
        (self.prj.work / "transcript.json").write_text(json.dumps(transcript(lines)), encoding="utf-8")
        self.prj.cfg["music"] = {"file": "nhac.mp3", "volume": 0.1}
        self.prj.cfg["content"]["hook"]["title"] = "tiêu đề video dài"
        self.prj.save()

    def tearDown(self):
        self.tmp.cleanup()

    def test_suggest_then_make(self):
        res = SH.suggest(self.prj, 3, 10, 20)
        self.assertTrue(res)
        self.assertTrue((self.prj.work / "de-xuat-short.md").exists())
        made = SH.make(self.prj, "1, 30-45")
        self.assertEqual(len(made), 2)
        kid = Project(made[0])
        self.assertEqual(kid.cfg["cuts"]["keep"], [[res[0]["start"], res[0]["end"]]])
        self.assertEqual(kid.cfg["style"]["pace"], "nhanh")
        self.assertEqual(kid.cfg["content"]["hook"]["title"], "")  # nội dung viết lại cho từng short
        self.assertTrue(Path(kid.cfg["input"]).is_absolute())
        self.assertEqual(Path(kid.cfg["music"]["file"]), self.prj.root / "nhac.mp3")
        self.assertIn("transcribe", kid.state())
        segs = json.loads((kid.work / "transcript.json").read_text(encoding="utf-8"))
        self.assertTrue(all(s["end"] > res[0]["start"] - 2 and s["start"] < res[0]["end"] + 2 for s in segs))
        self.assertTrue((kid.work / "loi-thoai.txt").exists())
        self.assertEqual(Project(made[1]).cfg["cuts"]["keep"], [[30.0, 45.0]])
        self.assertTrue(made[1].name.startswith("02-"))

    def test_bad_pick(self):
        SH.suggest(self.prj, 2, 10, 20)
        with self.assertRaises(VEError):
            SH.make(self.prj, "9")
        with self.assertRaises(VEError):
            SH.make(self.prj, "10-11")

    def test_script_project_rejected(self):
        kb = self.root / "kb.txt"
        kb.write_text("kịch bản", encoding="utf-8")
        p = init_project(self.root / "kb", None, str(kb), "9:16", "trung-tinh", None, None, None, None)
        with self.assertRaises(VEError):
            SH.make(p, "1")


if __name__ == "__main__":
    unittest.main()
