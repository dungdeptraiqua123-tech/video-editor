import unittest

from ve.content import Finder, resolve_content
from ve.timeline import CutConfig, Word, build_timeline


def words(text, start=0.0, step=0.4):
    out, t = [], start
    for tok in text.split():
        out.append({"text": tok, "start": round(t, 2), "end": round(t + step - 0.05, 2)})
        t += step
    return out


TEXT = "xin chào các bạn hôm nay Bitcoin tăng lên 87 ngàn đô và hỗ trợ là 85 ngàn đô sau đó chúng ta xem tiếp phần altcoin nhé cảm ơn mọi người đã theo dõi video này rất nhiều"


class Resolve(unittest.TestCase):
    def setUp(self):
        self.w = words(TEXT)
        self.dur = self.w[-1]["end"] + 4
        self.content = {"hook": {"title": "Bitcoin 87K"}, "hookSec": 1.0, "outroSec": 2.0, "cta": "Theo dõi"}

    def test_phrase_start_and_anchor(self):
        c = dict(self.content, beats=[{"start": "Bitcoin tăng", "end": "85 ngàn đô", "head": "Mốc giá",
                                       "g": {"type": "levels", "title": "Mốc", "levels": [
                                           {"value": "87K", "label": "Cản", "kind": "res", "say": "87 ngàn"},
                                           {"value": "85K", "label": "Hỗ trợ", "kind": "sup", "say": "85 ngàn"}]}}])
        d, rep = resolve_content(c, self.w, self.dur)
        self.assertEqual(rep.errors, [])
        b = d["beats"][0]
        t_btc = next(x["start"] for x in self.w if x["text"] == "Bitcoin")
        self.assertAlmostEqual(b["start"], t_btc - 0.25, places=2)
        # phần tử bật đúng lúc được nói (trừ 0,08s), tính từ lúc khung mở
        t87 = next(x["start"] for x in self.w if x["text"] == "87")
        self.assertAlmostEqual(b["start"] + b["g"]["levels"][0]["d"], t87 - 0.08, places=2)
        self.assertGreater(b["g"]["levels"][1]["d"], b["g"]["levels"][0]["d"])

    def test_number_parts_match(self):
        f = Finder(words("phá được 85.500 rồi vùng 300-400 nghìn"))
        self.assertIsNotNone(f.find("85.500"))
        self.assertIsNotNone(f.find("85"))
        self.assertIsNotNone(f.find("400 nghìn"))
        self.assertIsNone(f.find("500"))  # phần thập phân/nghìn không tính là một vế

        c = dict(self.content, beats=[{"start": "Bitcoin tang", "g": {"type": "title", "kicker": "A", "text": "B"}}])
        _, rep = resolve_content(c, self.w, self.dur)
        self.assertEqual(len(rep.errors), 1)
        self.assertIn("Bitcoin tăng", rep.errors[0])

    def test_anchor_outside_beat_is_error(self):
        c = dict(self.content, beats=[{"start": "xin chào", "dur": 2, "g": {"type": "stat", "icon": "up", "big": "1", "label": "x", "say": "cảm ơn"}}])
        _, rep = resolve_content(c, self.w, self.dur)
        self.assertTrue(any("cảm ơn" in e for e in rep.errors))

    def test_schema_errors(self):
        c = dict(self.content, beats=[
            {"start": 2, "dur": 2, "g": {"type": "pie"}},
            {"start": 5, "dur": 2, "g": {"type": "stat", "icon": "rocket", "big": "1"}},
            {"start": 8, "dur": 2, "g": {"type": "chart", "title": "x", "points": [1], "tags": [{"i": 3, "text": "a"}]}},
        ])
        _, rep = resolve_content(c, self.w, self.dur)
        txt = " | ".join(rep.errors)
        self.assertIn("pie", txt)
        self.assertIn("rocket", txt)
        self.assertIn("label", txt)
        self.assertIn("points", txt)
        self.assertIn("ngoài khoảng", txt)

    def test_numeric_times_follow_cut(self):
        ws = [Word("một", 0.1, 0.5), Word("hai", 0.5, 0.9), Word("ba", 5.1, 5.5), Word("bốn", 5.5, 9.9)]
        tl = build_timeline(ws, 12.0, CutConfig())
        c = dict(self.content, hookSec=0.2, outroSec=0.2, beats=[{"start": 5.1, "end": 5.6, "g": {"type": "title", "kicker": "a", "text": "b"}}])
        d, rep = resolve_content(c, tl.words, tl.duration, tl)
        self.assertAlmostEqual(d["beats"][0]["start"], tl.map(5.1), places=2)
        self.assertLess(d["beats"][0]["start"], 2.0)  # đã dồn theo bản cắt, không còn ở giây 5

    def test_overlap_pushed_and_outro_trimmed(self):
        c = dict(self.content, beats=[
            {"start": 2.0, "end": 6.0, "g": {"type": "title", "kicker": "a", "text": "b"}},
            {"start": 5.0, "end": 9.0, "g": {"type": "title", "kicker": "a", "text": "c"}},
            {"start": self.dur - 3, "end": self.dur, "g": {"type": "title", "kicker": "a", "text": "d"}},
        ])
        d, rep = resolve_content(c, self.w, self.dur)
        self.assertGreaterEqual(d["beats"][1]["start"], d["beats"][0]["end"])
        self.assertLessEqual(d["beats"][2]["end"], self.dur - 2.0 + 1e-6)
        self.assertTrue(any("chồng" in w for w in rep.warnings))

    def test_auto_zooms_avoid_beats(self):
        c = dict(self.content, beats=[{"start": 2.0, "end": 6.0, "g": {"type": "title", "kicker": "a", "text": "b"}}])
        d, _ = resolve_content(c, self.w, self.dur, mode="talking")
        self.assertFalse(any(1.5 <= z <= 6.5 for z in d["zooms"]))


if __name__ == "__main__":
    unittest.main()
