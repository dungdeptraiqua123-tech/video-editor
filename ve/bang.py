"""Bảng quy chiếu thời gian: lịch xuất hiện các phần tử và từng chữ kèm thời điểm trong video.

Đây là bảng để soát đồ hoạ có bật đúng lúc lời được nói không. Cột Video là thời điểm trong file MP4 xuất ra,
cột Gốc là giây trong file nguồn (cùng hệ với loi-thoai.txt và số giây ghi trong project.json).
"""
from __future__ import annotations

from pathlib import Path

REASON = {"filler": "cắt: từ đệm", "stumble": "cắt: nói vấp", "drop": "cắt: đoạn bỏ", "outside_keep": "cắt: ngoài đoạn giữ"}


def clock(t: float) -> str:
    m, s = divmod(max(0.0, float(t)), 60)
    return f"{int(m):02d}:{s:05.2f}"


def _esc(s) -> str:
    return str(s or "").replace("|", "\\|").replace("\n", " ")


def write(path: Path, name: str, words: list, tl=None, events: list | None = None) -> Path:
    """words: các từ sau khi sửa, thời gian gốc (Word). tl: Timeline sau khi cắt (None nếu chưa dựng)."""
    out = [f"# Bảng quy chiếu thời gian: {name}", ""]
    if tl is None:
        out += ["Chưa dựng nên mới có thời gian theo file gốc. Chạy `video-editor build` để có cột **Video** (thời điểm trong video đã cắt) và lịch xuất hiện các phần tử.", ""]
    else:
        out += [f"Video đã dựng dài **{clock(tl.duration)}** ({tl.duration:.2f}s, file gốc {tl.src_duration:.2f}s).",
                "Cột **Video** là thời điểm trong file MP4 xuất ra. Cột **Gốc** là giây trong file nguồn, cùng hệ với `loi-thoai.txt` và số giây trong `project.json`.", ""]
    if events:
        out += ["## Lịch xuất hiện các phần tử", "", "Phần tử bật trước lời 0,08 giây để mắt kịp bắt.", "", "| Video | Phần tử | Neo theo lời |", "|---|---|---|"]
        out += [f"| {clock(e['t'])} | {_esc(e['what'])} | {_esc(e.get('say'))} |" for e in events]
        out.append("")
    removed = []  # (đầu, cuối, loại) theo thời gian gốc; cụm nói vấp có thể gồm nhiều từ
    if tl is not None:
        for kind, ws in tl.removed.items():
            if isinstance(ws, list):
                removed += [(float(w["start"]) - 0.005, float(w["end"]) + 0.005, kind) for w in ws]
    out += ["## Từng chữ", "", "| # | Chữ | Video | Gốc | Ghi chú |", "|---|---|---|---|---|"]
    for i, w in enumerate(words, 1):
        notes = ["nghe chưa chắc"] if w.p < 0.5 else []
        if tl is None:
            video = "—"
        else:
            mid = (w.start + w.end) / 2
            kind = next((k for a, b, k in removed if a <= mid <= b), None)
            if kind:
                video, notes = "—", notes + [REASON.get(kind, "cắt")]
            elif any(a <= mid <= b for a, b in tl.segments):
                video = clock(tl.map(w.start))
            else:
                video, notes = "—", notes + ["cắt: khoảng lặng"]
        out.append(f"| {i} | {_esc(w.text)} | {video} | {w.start:.2f}–{w.end:.2f} | {', '.join(notes)} |")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path
