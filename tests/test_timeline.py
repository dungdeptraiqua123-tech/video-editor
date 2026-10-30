import unittest

from ve.timeline import CutConfig, Word, apply_fixes, build_timeline, find_fillers, find_stumbles


def W(spec):
    """'a:0-0.3 b:0.3-0.6' -> [Word]"""
    out = []
    for tok in spec.split():
        t, r = tok.rsplit(":", 1)
        a, b = r.split("-")
        out.append(Word(t, float(a), float(b)))
    return out


class Fixes(unittest.TestCase):
    def test_multiword_and_delete(self):
        ws = apply_fixes(W("lon:0-0.2 sọt:0.2-0.4 bên:0.5-0.6 hiểm:0.6-0.7 ok:1-1.2"), [["lon sọt", "long short"], ["bên hiểm", ""]])
        self.assertEqual([w.text for w in ws], ["long", "short", "ok"])
        self.assertAlmostEqual(ws[1].start, 0.2)

    def test_keeps_trailing_punctuation(self):
        ws = apply_fixes(W("Sol,:0-0.3 tăng:0.3-0.5"), [["Sol", "Solana"]])
        self.assertEqual(ws[0].text, "Solana,")


class Detect(unittest.TestCase):
    def test_fillers(self):
        self.assertEqual(find_fillers(W("ờ:0-0.2 Bitcoin:0.2-0.5 ừm:0.6-0.8"), ["ờ", "ừm"]), [0, 2])

    def test_stumble_found(self):
        ws = W("là:0-0.1 cái:0.1-0.2 là:0.3-0.4 cái:0.4-0.5 giá:0.5-0.7")
        self.assertEqual(find_stumbles(ws), [(0, 1)])

    def test_reduplication_ignored(self):
        self.assertEqual(find_stumbles(W("từ:0-0.2 từ:0.2-0.4 tăng:0.4-0.6")), [])

    def test_punctuation_between_repeats_ignored(self):
        self.assertEqual(find_stumbles(W("đúng.:0-0.2 đúng:0.3-0.5")), [])


class Cut(unittest.TestCase):
    def setUp(self):
        # nói 0–1s, im 1–3s, nói 3–4s
        self.ws = W("một:0.1-0.5 hai:0.5-0.9 ba:3.1-3.5 bốn:3.5-3.9")

    def test_silence_removed_and_map(self):
        tl = build_timeline(self.ws, 5.0, CutConfig())
        self.assertEqual(len(tl.segments), 2)
        self.assertLess(tl.duration, 2.6)
        # thời gian từng từ sau cắt = map(thời gian gốc), tăng dần, nằm trong video
        starts = [w["start"] for w in tl.words]
        self.assertEqual(starts, sorted(starts))
        self.assertAlmostEqual(tl.words[2]["start"], tl.map(3.1), places=3)
        self.assertTrue(all(0 <= w["start"] <= w["end"] <= tl.duration + 1e-6 for w in tl.words))

    def test_unmap_roundtrip(self):
        tl = build_timeline(self.ws, 5.0, CutConfig())
        for t in (0.2, 0.7, 3.2, 3.8):
            self.assertAlmostEqual(tl.unmap(tl.map(t)), t, places=3)

    def test_drop_range(self):
        tl = build_timeline(self.ws, 5.0, CutConfig(drop=[[3.0, 4.0]]))
        self.assertEqual([w["text"] for w in tl.words], ["một", "hai"])
        self.assertLess(tl.duration, 1.5)

    def test_keep_range(self):
        tl = build_timeline(self.ws, 5.0, CutConfig(keep=[[3.0, 4.2]]))
        self.assertEqual([w["text"] for w in tl.words], ["ba", "bốn"])

    def test_filler_auto_removed_without_eating_neighbours(self):
        ws = W("giá:0-0.4 ờ:0.4-0.9 tăng:0.9-1.3")
        tl = build_timeline(ws, 2.0, CutConfig(fillers="auto", filler_words=["ờ"]))
        self.assertEqual([w["text"] for w in tl.words], ["giá", "tăng"])
        self.assertAlmostEqual(tl.words[1]["start"] - tl.words[0]["end"], 0.0, places=2)
        self.assertEqual(len(tl.removed["filler"]), 1)

    def test_suggest_mode_keeps_words(self):
        ws = W("thì:0-0.2 thì:0.2-0.4 tăng:0.4-0.8")
        tl = build_timeline(ws, 1.0, CutConfig(stumbles="suggest"))
        self.assertEqual(len(tl.words), 3)
        self.assertEqual(len(tl.suggestions["stumble"]), 1)

    def test_everything_dropped_raises(self):
        with self.assertRaises(ValueError):
            build_timeline(self.ws, 5.0, CutConfig(drop=[[0, 5]]))

    def test_no_silence_cut(self):
        tl = build_timeline(self.ws, 5.0, CutConfig(silence=False))
        self.assertAlmostEqual(tl.duration, 5.0)


if __name__ == "__main__":
    unittest.main()
