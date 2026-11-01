"""Bám mặt (làm mượt, nhảy đúng chỗ cắt, khi nào bật) và phân tích video mẫu (đổi cảnh, bỏ phiếu nhịp)."""
import unittest

from ve import face as F
from ve import mau as MAU


def samples(fn, dur=12.0, fps=4, h=0.3):
    """Mẫu dò mặt giả: fn(t) trả tâm x (None = không thấy mặt)."""
    out = []
    for i in range(int(dur * fps)):
        t = i / fps
        x = fn(t)
        out.append([t, [] if x is None else [[x - h * 0.28, 0.3, h * 0.56, h]]])
    return out


class WantedTest(unittest.TestCase):
    def test_auto_only_when_source_wider(self):
        self.assertTrue(F.wanted({}, 1920, 1080, 1080, 1920))   # 16:9 → 9:16
        self.assertTrue(F.wanted({}, 1920, 1080, 1080, 1080))   # 16:9 → 1:1
        self.assertFalse(F.wanted({}, 1080, 1920, 1080, 1920))  # cùng khổ
        self.assertFalse(F.wanted({}, 1080, 1920, 1920, 1080))  # quay dọc xuất ngang: giữ trọn khung

    def test_switch(self):
        self.assertFalse(F.wanted({"face": {"track": False}}, 1920, 1080, 1080, 1920))
        self.assertTrue(F.wanted({"face": {"track": True}}, 1080, 1920, 1080, 1920))


class SmoothTest(unittest.TestCase):
    def test_still_face_does_not_jitter(self):
        import random

        rnd = random.Random(1)
        res = F.smooth(samples(lambda t: 0.3 + rnd.uniform(-0.015, 0.015)), [], 4)
        xs = [x for _, x, _ in res["track"]]
        self.assertLess(max(xs) - min(xs), 0.012)
        self.assertEqual(res["coverage"], 1.0)

    def test_follows_motion(self):
        res = F.smooth(samples(lambda t: 0.2 + 0.05 * t), [], 4)
        for t, x, _ in res["track"][4:-4]:
            self.assertLess(abs(x - (0.2 + 0.05 * t)), 0.05, t)

    def test_jumps_at_cut(self):
        res = F.smooth(samples(lambda t: 0.25 if t < 6 else 0.75), [6.0], 4)
        before = [x for t, x, _ in res["track"] if t < 5.98]
        after = [x for t, x, _ in res["track"] if t >= 6.0]
        self.assertTrue(all(abs(x - 0.25) < 0.02 for x in before))
        self.assertTrue(all(abs(x - 0.75) < 0.02 for x in after))
        # có mốc ngay trước chỗ cắt để khung nhảy thẳng, không trôi
        self.assertTrue(any(5.97 <= t < 6.0 for t, _, _ in res["track"]))

    def test_gaps_filled_and_coverage(self):
        res = F.smooth(samples(lambda t: None if 3 <= t < 5 else 0.6), [], 4)
        self.assertAlmostEqual(res["coverage"], 40 / 48, places=3)
        self.assertTrue(all(abs(x - 0.6) < 0.01 for _, x, _ in res["track"]))

    def test_no_face_segment_uses_previous(self):
        res = F.smooth(samples(lambda t: 0.4 if t < 6 else None), [6.0], 4)
        self.assertTrue(all(abs(x - 0.4) < 0.01 for t, x, _ in res["track"] if t >= 6))

    def test_false_positive_ignored(self):
        def s():
            out = samples(lambda t: 0.5)
            for i in range(0, len(out), 5):
                out[i][1].append([0.05, 0.05, 0.03, 0.04])  # khung nhỏ dò nhầm ở góc
            return out
        res = F.smooth(s(), [], 4)
        self.assertTrue(all(abs(x - 0.5) < 0.01 for _, x, _ in res["track"]))

    def test_boundaries(self):
        self.assertEqual(F.boundaries([[0, 6.3], [6.72, 16.78], [18.04, 24]]), [6.3, 16.36])


class MauTest(unittest.TestCase):
    def test_changes_grouped(self):
        pairs = [(i / 12, 0.004) for i in range(240)]
        for t in (4.0, 4.08, 4.17, 10.0, 15.5):
            pairs[int(t * 12)] = (t, 0.3)
        r = MAU.changes_from_scores(pairs)
        self.assertEqual(len(r["changes"]), 3)
        self.assertAlmostEqual(r["threshold"], 0.1)

    def test_motion_not_counted(self):
        # chuyển động đều (điểm cao đều) không bị tính là đổi cảnh
        r = MAU.changes_from_scores([(i / 12, 0.05 + 0.01 * (i % 3)) for i in range(120)])
        self.assertEqual(r["changes"], [])

    def test_suggest_fast(self):
        shots = MAU.shot_stats([1.5 * i for i in range(1, 20)], 30)
        sp = {"wordsPerMin": 250}
        pz = {"reliable": True, "p90": 0.3, "share": 0.06}
        s = MAU.suggest(shots, sp, 30, pz)
        self.assertEqual(s["pace"], "nhanh")
        self.assertEqual(s["graphics"], "nhieu")
        self.assertEqual(s["gap"], 0.35)

    def test_suggest_measured_draft(self):
        # số đo thật của bản nháp BTC 30 giây (dựng với nhịp "vua", đồ hoạ "nhieu")
        shots = MAU.shot_stats([4.08, 16.0, 18.83, 22.5, 29.08, 31.67], 32.68)
        s = MAU.suggest(shots, {"wordsPerMin": 247}, 32.68, {"reliable": True, "p90": 0.42, "share": 0.13})
        self.assertEqual(s["pace"], "vua")
        self.assertEqual(s["graphics"], "nhieu")

    def test_single_shot_talking_head(self):
        shots = MAU.shot_stats([], 60)
        s = MAU.suggest(shots, {"wordsPerMin": 150}, 60, {"reliable": True, "p90": 0.9, "share": 0.25})
        self.assertEqual(s["pace"], "cham")
        self.assertTrue(any("một cảnh liền" in w for w in s["why"]))

    def test_music_bed(self):
        s = MAU.suggest(MAU.shot_stats([], 30), None, 30, {"reliable": False, "p90": 0, "share": 0})
        self.assertIsNone(s["gap"])
        self.assertTrue(any("nhạc nền" in w for w in s["why"]))

    def test_url_rejected(self):
        from pathlib import Path
        from ve.env import VEError

        for url in ("https://youtube.com/watch?v=x", "www.tiktok.com/@a/video/1"):
            with self.assertRaises(VEError) as cm:
                MAU.analyze(url, Path("/tmp/khong-dung"))
            self.assertIn("trên máy", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
