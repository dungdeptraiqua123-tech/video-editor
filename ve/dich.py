"""Phụ đề song ngữ: work/dich.json chứa từng câu lời thoại (giây theo file gốc) để điền bản dịch.

`video-editor dich <dự án> --ngon-ngu en` tạo file (giữ bản dịch đã điền nếu câu không đổi). Người dựng (hoặc Claude)
điền ô "dich" từng câu, đặt captions.second = "en" trong project.json, build sẽ đặt dòng dịch dưới phụ đề chính
và xuất thêm file .en.srt. Không gọi dịch vụ dịch nào: bản dịch do người dựng viết, nên không lộ nội dung ra ngoài.
"""
from __future__ import annotations

from .env import VEError, info, read_json, write_json


def path(prj):
    return prj.work / "dich.json"


def make(prj, lang: str = "en") -> None:
    tp = prj.work / "transcript.json"
    if not tp.exists():
        raise VEError("Chưa có lời thoại (work/transcript.json).", f"Chạy `video-editor transcribe {prj.root}` trước.")
    old = {}
    p = path(prj)
    if p.exists():
        d = read_json(p)
        old = {s["text"]: s.get("dich", "") for s in d.get("cau", [])}
    drop = set(prj.cfg.get("dropSegments") or [])
    cau = []
    for s in read_json(tp):
        if round(float(s["start"]), 2) in {round(float(x), 2) for x in drop}:
            continue
        t = s["text"].strip()
        if t:
            cau.append({"start": round(float(s["start"]), 2), "end": round(float(s["end"]), 2), "text": t, "dich": old.get(t, "")})
    write_json(p, {"_ghi_chu": f"Điền ô dich cho từng câu (ngôn ngữ {lang}), giữ ngắn để vừa một dòng. Câu để trống sẽ không hiện dòng dịch.", "lang": lang, "cau": cau})
    done = sum(1 for c in cau if c["dich"])
    info(f"✓ {p}: {len(cau)} câu, đã có bản dịch {done}. Điền xong thì đặt \"captions\": {{\"second\": \"{lang}\"}} rồi build.")


def load(prj, tl) -> list[dict]:
    """Các dòng dịch theo thời gian video đã cắt. Rỗng nếu captions.second chưa bật."""
    lang = (prj.cfg.get("captions") or {}).get("second")
    if not lang:
        return []
    p = path(prj)
    if not p.exists():
        raise VEError("captions.second đã bật nhưng chưa có work/dich.json.", f"Chạy `video-editor dich {prj.root} --ngon-ngu {lang}` rồi điền bản dịch.")
    d = read_json(p)
    out = []
    for c in d.get("cau", []):
        if not str(c.get("dich", "")).strip():
            continue
        a, b = tl.map(float(c["start"])), tl.map(float(c["end"]))
        if b - a < 0.3:
            continue  # câu nằm trong đoạn đã cắt
        out.append({"start": round(a, 2), "end": round(b, 2), "text": c["dich"].strip()})
    if not out:
        raise VEError("work/dich.json chưa có câu nào được dịch.", "Điền ô dich cho các câu, hoặc bỏ captions.second.")
    return out
