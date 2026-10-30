import tempfile
import unittest
from pathlib import Path

from ve import subs


def words(text, step=0.3, gap_after=None):
    out, t = [], 0.0
    for i, tok in enumerate(text.split()):
        out.append({"text": tok, "start": round(t, 3), "end": round(t + step - 0.02, 3)})
        t += step + (1.0 if gap_after == i else 0)
    return out


class Pages(unittest.TestCase):
    def test_breaks_on_period_and_length(self):
        ps = subs.pages(words("Bitcoin tăng mạnh. Hôm nay thị trường khá sôi động với rất nhiều tin tức mới"))
        self.assertEqual(ps[0]["text"], "Bitcoin tăng mạnh.")
        self.assertTrue(all(len(p["text"]) <= 30 for p in ps))

    def test_breaks_on_pause(self):
        ps = subs.pages(words("một hai ba bốn năm", gap_after=1))
        self.assertEqual(ps[0]["text"], "một hai")

    def test_no_overlap_and_lingers(self):
        ps = subs.pages(words("a b c. d e f."))
        for a, b in zip(ps, ps[1:]):
            self.assertLessEqual(a["end"], b["start"] + 1e-9)

    def test_timestamp(self):
        self.assertEqual(subs.ts(3725.5, ","), "01:02:05,500")
        self.assertEqual(subs.ts(0.0754, "."), "00:00:00.075")


class Files(unittest.TestCase):
    def test_write_and_parse_back(self):
        data = {"duration": 2.3, "words": words("xin chào các bạn. hôm nay giá tăng"), "captions": {}}
        with tempfile.TemporaryDirectory() as d:
            srt, vtt, n = subs.write(data, Path(d) / "x")
            self.assertTrue(vtt.read_text(encoding="utf-8").startswith("WEBVTT"))
            back = subs.parse_srt(srt.read_text(encoding="utf-8"))
            self.assertEqual(len(back), n)
            self.assertLessEqual(back[-1]["end"], 2.3 + 1e-6)  # không vượt độ dài video
            self.assertEqual(" ".join(w["w"].strip() for s in back for w in s["words"]), "xin chào các bạn. hôm nay giá tăng")


if __name__ == "__main__":
    unittest.main()
