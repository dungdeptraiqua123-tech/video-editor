"""Kiểm thử phần 0.3: icon theo lời, giá thật, dò nhịp, đồ hoạ mới, chữ đập, phụ đề song ngữ, làm sạch giọng."""
import math
import tempfile
import unittest
from pathlib import Path

from ve import gia, icons, nhip
from ve.content import resolve_content
from ve.env import ENGINE, VEError
from ve.media import clean_filter
from ve.subs import write_second


def words(text, start=0.0, step=0.4):
    out, t = [], start
    for tok in text.split():
        out.append({"text": tok, "start": round(t, 2), "end": round(t + step - 0.05, 2)})
        t += step
    return out


class Icons(unittest.TestCase):
    def test_brand_and_concept_match(self):
        w = words("hôm nay Claude và ChatGPT nói về ngân hàng trung ương với Bitcoin Cash")
        hits = icons.find(w, icons.lexicon({}))
        labels = [h["entry"].get("label") for h in hits]
        self.assertIn("Claude", labels)
        self.assertTrue(any(h["entry"]["icon"].startswith("lu:") for h in hits))
        # cụm dài thắng cụm ngắn
        cash = [h for h in hits if " ".join(x["text"] for x in w[h["i"]:h["i"] + h["n"]]) == "Bitcoin Cash"]
        self.assertEqual(len(cash), 1)

    def test_exact_case(self):
        lex = icons.lexicon({})
        self.assertFalse([h for h in icons.find(words("ai cũng biết"), lex) if h["entry"].get("icon") == "lu:bot"])
        self.assertTrue([h for h in icons.find(words("công nghệ AI mới"), lex) if h["entry"].get("icon") == "lu:bot"])

    def test_plan_spacing_and_off(self):
        w = words("Claude " * 40, step=0.5)
        dur = w[-1]["end"] + 3
        pops, inline, _ = icons.plan(w, {}, [], dur, 1.0, 2.0)
        ts = [p["t"] for p in pops]
        self.assertTrue(all(b - a >= 11.9 for a, b in zip(ts, ts[1:])))
        self.assertTrue(all(b - a >= 3.9 for a, b in zip(sorted(w[i]["start"] for i in inline), sorted(w[i]["start"] for i in inline)[1:])))
        pops, inline, _ = icons.plan(w, {"icons": {"off": ["claude"]}}, [], dur, 1.0, 2.0)
        self.assertEqual((pops, inline), ([], {}))
        self.assertEqual(icons.plan(w, {"icons": False}, [], dur, 1.0, 2.0)[:2], ([], {}))

    def test_skip_during_graphic(self):
        w = words("chào bạn " * 5 + "Claude rất hay")
        t = next(x["start"] for x in w if x["text"] == "Claude")
        pops, _, _ = icons.plan(w, {}, [{"start": t - 1, "end": t + 1}], 30, 0.5, 1.0)
        self.assertEqual(pops, [])

    @unittest.skipUnless((ENGINE / "node_modules" / "simple-icons").exists(), "bộ dựng chưa cài simple-icons")
    def test_svg_data(self):
        d = icons.svg_data("si:claude", {"label": "Claude"})
        self.assertEqual(d["kind"], "brand")
        self.assertTrue(d["color"].startswith("#"))
        self.assertIsNotNone(icons.svg_data("lu:landmark", {}))


class Gia(unittest.TestCase):
    def setUp(self):
        day = 86400_000
        self.d = {"coin": "bitcoin", "vs": "usd", "source": "CoinGecko",
                  "prices": [[1_700_000_000_000 + i * day // 4, 60000 + 1000 * math.sin(i / 5) + i * 10] for i in range(4 * 40)]}

    def test_summary_window(self):
        s = gia.summary(self.d, 7)
        self.assertLessEqual(s["low"], s["first"])
        self.assertGreaterEqual(s["high"], s["last"])
        self.assertEqual(len(gia.downsample(gia.window(self.d, 7))), gia.POINTS)

    def test_apply_chart_and_price(self):
        with tempfile.TemporaryDirectory() as td:
            gia.save(Path(td), self.d)
            g = {"type": "chart", "title": "BTC 7 ngày", "data": {"coin": "btc", "ngay": 7}, "tags": [{"i": "cuoi", "text": "auto", "say": "x"}]}
            notes = gia.apply(g, Path(td))
            self.assertEqual(len(g["points"]), gia.POINTS)
            self.assertEqual(g["tags"][0]["i"], gia.POINTS - 1)
            self.assertTrue(g["tags"][0]["text"].startswith("$"))
            self.assertIn("CoinGecko", g["source"])
            self.assertTrue(notes and "bitcoin" in notes[0])
            p = {"type": "price", "label": "BTC", "data": "bitcoin"}
            gia.apply(p, Path(td))
            self.assertAlmostEqual(p["value"], round(self.d["prices"][-1][1], 2))
            with self.assertRaises(VEError):
                gia.apply({"type": "chart", "data": {"coin": "solana"}}, Path(td))

    def test_csv(self):
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "g.csv"
            f.write_text("date,close\n2025-10-01,\"118,000\"\n2025-10-02,120500\n", encoding="utf-8")
            d = gia.from_csv(f, "BTC")
            self.assertEqual(d["coin"], "bitcoin")
            self.assertEqual([p for _, p in d["prices"]], [118000.0, 120500.0])

    def test_money(self):
        self.assertEqual(gia.money(87250), "$87.2K")
        self.assertEqual(gia.money(0.512), "$0.51")


class Nhip(unittest.TestCase):
    def test_tempo_from_clicks(self):
        sr, bpm = nhip.SR, 120
        x = [0.0] * (sr * 12)
        for k in range(24):
            i = int(k * 60 / bpm * sr)
            x[i:i + 300] = [0.8] * 300
        env = nhip.onset_envelope(x)
        got, beats = nhip.tempo_and_beats(env, sr / nhip.HOP)
        self.assertAlmostEqual(got, bpm, delta=4)
        self.assertGreater(len(beats), 18)
        # phách rơi đúng chỗ tiếng gõ (lệch ≤ 1 khung)
        self.assertLess(min(abs(beats[3] - k * 0.5) for k in range(24)), 2 * nhip.HOP / sr)

    def test_decode_real_file(self):
        import shutil
        import subprocess
        if not shutil.which("ffmpeg"):
            self.skipTest("không có ffmpeg")
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "click.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "aevalsrc='if(lt(mod(t,0.5),0.03),sin(2*PI*1000*t),0)':d=10", str(f)], check=True)
            r = nhip.beats(f)
            self.assertAlmostEqual(r["bpm"], 120, delta=4)

    def test_snap(self):
        self.assertEqual(nhip.snap([1.1, 2.9, 5.0], [1.0, 2.0, 3.0]), [1.0, 3.0, 5.0])
        self.assertEqual(nhip.snap([1.5], []), [1.5])


class NewGraphics(unittest.TestCase):
    TEXT = "hôm nay so sánh Bitcoin với vàng năm 2020 rồi 2024 tỉ lệ 60 phần trăm và ba lý do một hai ba cuối cùng cảm ơn mọi người đã xem video rất nhiều nhé"

    def resolve(self, g, **extra):
        w = words(self.TEXT)
        c = {"hook": {"title": "x"}, "hookSec": 1.0, "outroSec": 2.0, "cta": "Theo dõi",
             "beats": [{"start": "so sánh", "end": "ba lý do", "head": "Thử", "g": g}], **extra}
        return resolve_content(c, w, w[-1]["end"] + 4)

    def test_compare_ok(self):
        d, rep = self.resolve({"type": "compare", "title": "BTC vs vàng", "left": {"label": "Bitcoin", "value": "+120%", "say": "Bitcoin"},
                               "right": {"label": "Vàng", "value": "+30%", "say": "vàng"}, "winner": "left"})
        self.assertEqual(rep.errors, [])

    def test_table_cells_mismatch(self):
        _, rep = self.resolve({"type": "table", "title": "Bảng", "cols": ["A", "B"], "rows": [{"cells": ["1"]}]})
        self.assertTrue(rep.errors)

    def test_timeline_too_few(self):
        _, rep = self.resolve({"type": "timeline", "title": "Mốc", "items": [{"when": "2020", "text": "a", "say": "2020"}]})
        self.assertTrue(any("2–5" in w for w in rep.warnings))
        _, rep = self.resolve({"type": "timeline", "title": "Mốc", "items": [{"text": "a", "say": "2020"}, {"when": "2024", "text": "b", "say": "2024"}]})
        self.assertTrue(rep.errors)

    def test_progress_and_punch(self):
        d, rep = self.resolve({"type": "progress", "title": "Tỉ lệ", "items": [{"label": "BTC", "value": 60, "suffix": "%", "say": "60"}]},
                              punches=[{"say": "cuối cùng", "text": "3 LÝ DO"}])
        self.assertEqual(rep.errors, [])
        self.assertEqual(len(d["punches"]), 1)
        _, rep = self.resolve({"type": "quote", "text": "x" * 200})
        self.assertTrue(rep.errors or rep.warnings)


class Misc(unittest.TestCase):
    def test_clean_filter(self):
        self.assertEqual(clean_filter(False), "")
        self.assertIn("afftdn", clean_filter("nhe"))
        self.assertIn("anlmdn", clean_filter("manh"))
        with self.assertRaises(VEError):
            clean_filter("sieu")

    def test_second_srt(self):
        with tempfile.TemporaryDirectory() as td:
            p = write_second({"duration": 5, "second": [{"start": 0.5, "end": 2, "text": "Hello"}, {"start": 6, "end": 7, "text": "x"}]}, Path(td) / "v", "en")
            self.assertEqual(p.name, "v.en.srt")
            self.assertIn("Hello", p.read_text(encoding="utf-8"))
            self.assertNotIn("x\n", p.read_text(encoding="utf-8"))
            self.assertIsNone(write_second({"duration": 5}, Path(td) / "w"))


if __name__ == "__main__":
    unittest.main()
