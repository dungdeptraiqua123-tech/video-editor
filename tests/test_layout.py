"""Soát bố cục tự động (ve/layout.py) từ số đo giả, cảnh báo dùng cảnh motion chưa hợp lý, mã icon, chính tả chữ trên hình."""
import unittest

from ve import layout as LAYOUT
from ve import motion as MOTION
from ve import soat as SOAT

D = {"format": {"fps": 30}, "duration": 34.0, "hookSec": 2.0, "outroSec": 3.0,
     "beats": [{"start": 4.0, "end": 8.0, "g": {"type": "motion", "scene": "so-do", "layer": "full"}},
               {"start": 9.0, "end": 13.0, "g": {"type": "motion", "scene": "chat", "layer": "overlay"}},
               {"start": 17.0, "end": 21.0, "g": {"type": "motion", "scene": "vi-lanh", "layer": "full"}}]}
FACE = {"x": 216, "y": 384, "w": 648, "h": 614}


def item(kind, r, name="", scene="", text="", **kw):
    return {"kind": kind, "name": name, "scene": scene, "layer": "", "r": r, "o": 1, "shown": 1, "anc": [], "text": text, **kw}


def probe(t, items, codes=(), face=None):
    return {"output": f"/x/{t}.jpg", "frame": int(t * 30), "w": 1080, "h": 1920, "face": face, "items": items, "codes": list(codes)}


class Analyze(unittest.TestCase):
    def msgs(self, probes, shots=None):
        return [f"{x['where']}: {x['msg']}" for x in LAYOUT.analyze(D, probes, shots or {})]

    def test_icon_code_and_clipped_text_under_pip(self):
        ms = self.msgs([probe(5, [item("pip", [790, 110, 240, 300], "o-mat"),
                                  item("text", [70, 260, 760, 90], "dong-nghieng", "so-do", "an toàn, không bị mất"),
                                  item("text", [400, 500, 200, 60], "nhan", "so-do", "lu:wallet")], codes=["lu:wallet"])])
        self.assertTrue(any("mã icon `lu:wallet`" in m for m in ms), ms)
        self.assertTrue(any("bị ô mặt người nói che" in m and "dòng nghiêng" in m for m in ms), ms)
        self.assertTrue(all(m.startswith("beats[0] motion so-do") for m in ms), ms)

    def test_cut_text_and_orphan_word(self):
        ms = self.msgs([probe(5, [item("text", [70, 260, 900, 90], "tieu-de", "so-do", "Rút về ví lạnh", shown=0.8),
                                  item("cta", [130, 200, 820, 160], "keu-goi", "", "Theo dõi để xem video tiếp theo", lines=2, lastLine="theo")])])
        self.assertTrue(any("bị cắt mất 20%" in m for m in ms), ms)
        self.assertTrue(any("\"theo\" đứng lẻ" in m for m in ms), ms)

    def test_overlay_window_covers_face_and_topic_overlaps(self):
        ms = self.msgs([probe(10, [item("topic", [50, 90, 560, 260], "the-chu-de", "", "Đặt tiền ở đâu cho an toàn?"),
                                   item("box", [70, 260, 940, 560], "cua-so", "chat", filled=True),
                                   item("text", [120, 300, 600, 60], "bong-bong", "chat", "Có staking được không?")], face=FACE)])
        self.assertTrue(any("cửa sổ che" in m and "mặt người nói" in m for m in ms), ms)
        self.assertTrue(any("thẻ chủ đề" in m and "đè lên nhau" in m for m in ms), ms)
        # chữ nằm trong thẻ của chính cảnh thì không tính là đè
        self.assertFalse(any("bong bóng chat «Có staking được không?» và cửa sổ" in m for m in ms), ms)

    def test_empty_scene_and_window(self):
        shots = {"/x/17.5.jpg": (17.5, "motion-1"), "/x/19.jpg": (19, "motion-2")}
        ms = self.msgs([probe(17.5, [item("box", [70, 500, 940, 560], "cua-so", "vi-lanh", filled=False)]),
                        probe(19, [item("box", [70, 500, 940, 560], "cua-so", "vi-lanh", filled=False),
                                   item("text", [70, 260, 600, 90], "tieu-de", "vi-lanh", "Rút về ví lạnh")])], shots)
        self.assertTrue(any("cảnh mở ra chưa có chữ" in m for m in ms), ms)
        self.assertTrue(any("cửa sổ còn trống" in m for m in ms), ms)

    def test_nested_text_reported_once_with_hidden_items_before(self):
        # phần tử mờ (bị lọc) đứng trước không làm lệch quan hệ cha / con: chỉ báo cửa sổ, không báo từng bong bóng bên trong
        items = [item("text", [0, 0, 10, 10], "chu", "chat", "x", o=0.1),
                 item("box", [70, 900, 940, 560], "cua-so", "chat", filled=True),
                 item("text", [100, 1000, 600, 60], "bong-bong", "chat", "Xin chào", anc=[1]),
                 item("captions", [100, 1300, 880, 160])]
        self.assertEqual([x["msg"] for x in LAYOUT.analyze(D, [probe(10, items)], {})], ["cửa sổ đè lên phụ đề"])

    def test_clean_frame_and_merge_repeats(self):
        clean = [item("text", [70, 260, 600, 90], "tieu-de", "so-do", "Để coin ở đâu?"), item("captions", [100, 1380, 880, 120])]
        self.assertEqual(LAYOUT.analyze(D, [probe(5, clean)], {}), [])
        bad = [item("text", [70, 260, 900, 90], "tieu-de", "so-do", "Rất dài", shown=0.7)]
        out = LAYOUT.analyze(D, [probe(5, bad), probe(6, bad)], {})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["times"], [5.0, 6.0])


class SceneLint(unittest.TestCase):
    words = [{"text": t, "start": i * 0.4} for i, t in enumerate("Trên sàn thì em cái coi đó nó có stacking được hay là tính năng gì".split())]

    def test_chat_without_app_two_node_diagram_icon_code_in_label(self):
        beats = [{"start": 0, "end": 5, "g": {"type": "motion", "scene": "chat", "layer": "overlay", "params": {"ask": "Có stacking được không?"}}},
                 {"start": 5, "end": 9, "g": {"type": "motion", "scene": "so-do", "params": {"nodes": [{"label": "sàn", "icon": "lu:building-2"}, {"label": "lu:wallet"}],
                                                                                              "center": {"icon": "🤖"}}}}]
        out = MOTION.lint(beats, self.words, 30)
        txt = " | ".join(m for _, _, m in out)
        self.assertIn("không nói về app", txt)
        self.assertIn("so-do chỉ có 2 nút", txt)
        self.assertIn("dễ che mặt", txt)
        self.assertIn('mã icon "lu:wallet" nằm ở khoá "label"', txt)
        self.assertIn("emoji", txt)
        self.assertEqual([lv for lv, _, m in out if "lu:wallet" in m], ["err"])
        self.assertEqual(MOTION.icon_codes(beats), {"lu:building-2", "lu:wallet"})

    def test_suggest_new_scenes_for_advice_video(self):
        self.assertIn(("so-sanh", "so-sanh"), MOTION.suggest("đầu tư 2-3 năm thì nên để coi trên sàn hay ví Metamask"))
        self.assertIn(("re-nhanh", "re-nhanh"), MOTION.suggest("Còn không thì em để trên ví cá nhân của em"))
        self.assertIn(("luu-y", "luu-y"), MOTION.suggest("Lưu ý đừng để hết trên sàn"))
        self.assertNotIn("chat", [s for _, s in MOTION.suggest("Trên sàn thì em cái coi đó nó có stacking được")])


class DisplaySpelling(unittest.TestCase):
    def test_only_on_screen_text_is_checked(self):
        sugs = [{"sai": "stacking", "dung": "staking"}, {"sai": "thủ động", "dung": "thụ động"}, {"sai": "coi", "dung": "coin"}]
        content = {"beats": [{"start": "cái coi đó", "g": {"type": "motion", "params": {
            "title": "Có stacking được không?", "items": [{"text": "Tạo dòng tiền thụ động", "say": "thủ động"}], "icon": "lu:coins"}}}]}
        out = SOAT.check_content(content, sugs)
        self.assertEqual(len(out), 1)
        self.assertIn("stacking", out[0])
        self.assertNotIn("lu:coins", " ".join(SOAT.display_texts(content)))


if __name__ == "__main__":
    unittest.main()
