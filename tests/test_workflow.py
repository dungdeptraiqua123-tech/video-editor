import json
import os
import tempfile
import unittest
from pathlib import Path

from ve import bang, notes
from ve.project import Project, cut_settings, rules_text
from ve.storyboard import describe, frame_count, sample_times
from ve.timeline import CutConfig, Word, build_timeline


class Style(unittest.TestCase):
    def test_pace_sets_cut_defaults_and_explicit_values_win(self):
        self.assertEqual(cut_settings({"style": {"pace": "nhanh"}, "cuts": {"gap": None}})["gap"], 0.35)
        self.assertEqual(cut_settings({"style": {"pace": "cham"}, "cuts": {}})["fillers"], "suggest")
        # dự án cũ ghi số cụ thể: giữ nguyên
        self.assertEqual(cut_settings({"style": {"pace": "nhanh"}, "cuts": {"gap": 0.55}})["gap"], 0.55)
        with self.assertRaises(Exception):
            cut_settings({"style": {"pace": "sieu-nhanh"}})

    def test_rules_only_listed_when_present(self):
        self.assertEqual(rules_text({"rules": []}), "")
        self.assertIn("1. Không dùng màu đỏ", rules_text({"rules": ["Không dùng màu đỏ", " "]}))


class Table(unittest.TestCase):
    def test_word_rows_carry_video_time_and_cut_reason(self):
        ws = [Word("xin", 0.0, 0.3), Word("ờ", 0.4, 0.6), Word("chào", 3.0, 3.3, 0.3)]
        tl = build_timeline(ws, 4.0, CutConfig(fillers="auto"))
        p = Path(tempfile.mkdtemp()) / "b.md"
        bang.write(p, "thử", ws, tl, [{"t": 0.5, "what": "beats[0] mở", "say": "\"chào\""}])
        t = p.read_text(encoding="utf-8")
        self.assertIn("| 00:00.50 | beats[0] mở | \"chào\" |", t)
        self.assertIn("| 2 | ờ | — | 0.40–0.60 | cắt: từ đệm |", t)
        row = next(x for x in t.splitlines() if x.startswith("| 3 | chào"))
        self.assertIn(bang.clock(tl.map(3.0)), row)
        self.assertIn("nghe chưa chắc", row)


DATA = {"duration": 100.0, "hookSec": 3.0, "outroSec": 3.5, "mode": "talking", "hook": {"title": "Mở"}, "cta": "Theo dõi",
        "beats": [{"start": 40.0, "end": 41.5, "head": "Giá", "g": {"type": "stat", "d": 0.3}}],
        "topics": [{"start": 10, "end": 30, "title": "Chủ đề A"}],
        "words": [{"text": "giá", "start": 40.2, "end": 40.5}, {"text": "tăng", "start": 40.6, "end": 40.9}]}


class Storyboard(unittest.TestCase):
    def test_count_follows_length(self):
        self.assertEqual(frame_count(25), 6)
        self.assertEqual(frame_count(173), 22)
        self.assertEqual(frame_count(900), 24)

    def test_random_spread_reproducible_and_covers_every_graphic(self):
        a, b = sample_times(DATA, 7), sample_times(DATA, 7)
        self.assertEqual(a, b)
        self.assertNotEqual(a, sample_times(DATA, 8))
        self.assertTrue(any(40.0 <= t <= 41.5 for t in a))  # khung đồ hoạ ngắn vẫn có ảnh
        gaps = [y - x for x, y in zip(a, a[1:])]
        self.assertLess(max(gaps), 2 * 100 / frame_count(100))  # không dồn cục

    def test_titles_describe_scene_and_speech(self):
        self.assertEqual(describe(DATA, 1.0)[0], "Mở đầu: Mở")
        self.assertEqual(describe(DATA, 20.0)[0], "Người nói + thẻ: Chủ đề A")
        scene, said = describe(DATA, 40.8)
        self.assertEqual((scene, said), ("Đồ hoạ: Giá", "“giá tăng”"))
        self.assertEqual(describe(DATA, 98.0)[0], "Kết: Theo dõi")


class Notes(unittest.TestCase):
    def test_add_dedupe_and_read(self):
        p = Path(tempfile.mkdtemp()) / "GHI-NHO.md"
        notes.add("Phụ đề  to hơn", "BTC", "phu-de", p)
        notes.add("Phụ đề to hơn", "BTC", "phu-de", p)
        notes.add("Nhịp nhanh hơn ở đoạn đầu", "", "nhip", p)
        es = notes.entries(p)
        self.assertEqual(len(es), 2)
        self.assertTrue(es[0].endswith("· phu-de · BTC] Phụ đề to hơn"))
        with self.assertRaises(notes.VEError):
            notes.add("x", kind="la", p=p)


class Sfx(unittest.TestCase):
    def test_real_files_by_default_custom_and_off(self):
        from ve.build import sfx_for

        root = Path(tempfile.mkdtemp())
        (root / "project.json").write_text(json.dumps({"sfx": True}), encoding="utf-8")
        s = sfx_for(Project(root), place=False)
        self.assertEqual(s["files"]["whoosh"], "sfx/whoosh.mp3")
        (root / "project.json").write_text(json.dumps({"sfx": {"files": {"click": "", "impact": "am/rieng.wav"}, "volume": 0.5}}), encoding="utf-8")
        s = sfx_for(Project(root), place=False)
        self.assertNotIn("click", s["files"])
        self.assertEqual((s["files"]["impact"], s["volume"]), ("am/rieng.wav", 0.5))
        (root / "project.json").write_text(json.dumps({"sfx": False}), encoding="utf-8")
        self.assertIs(sfx_for(Project(root), place=False), False)


if __name__ == "__main__":
    unittest.main()
