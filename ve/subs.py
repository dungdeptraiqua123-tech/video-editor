"""Phụ đề SRT và VTT từ dữ liệu render (thời gian đã tính sau khi cắt, khớp video).

Gom cụm giống hệt engine/src/Captions.tsx (buildPages), nên phụ đề rời khớp phụ đề cháy trong video.
"""
import re
from pathlib import Path


def pages(words, max_chars=30, max_words=8):
    out, cur = [], []
    def flush():
        nonlocal cur
        if cur:
            out.append({"start": cur[0]["start"], "end": cur[-1]["end"], "text": " ".join(w["text"] for w in cur)})
        cur = []
    for i, w in enumerate(words):
        prev = words[i - 1] if i else None
        n = len(" ".join(x["text"] for x in cur)) + len(w["text"]) + 1
        if cur and (n > max_chars or len(cur) >= max_words or (prev and w["start"] - prev["end"] > 0.35)):
            flush()
        cur.append(w)
        if re.search(r"[.!?]$", w["text"]) or (w["text"].endswith(",") and len(cur) >= 4):
            flush()
    flush()
    for i, p in enumerate(out):
        nxt = out[i + 1]["start"] if i + 1 < len(out) else p["end"] + 0.6
        p["end"] = min(nxt, p["end"] + 0.6)
    return out


def ts(t, sep):
    ms = round(t * 1000)
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02}{sep}{ms % 1000:03}"


def write(data: dict, stem: Path) -> tuple[Path, Path, int]:
    cap = data.get("captions", {})
    ps = [p for p in pages(data["words"], cap.get("maxChars", 30), cap.get("maxWords", 8)) if p["start"] < data["duration"]]
    for p in ps:
        p["end"] = min(p["end"], data["duration"])
    srt = "\n".join(f"{i}\n{ts(p['start'], ',')} --> {ts(p['end'], ',')}\n{p['text']}\n" for i, p in enumerate(ps, 1))
    vtt = "WEBVTT\n\n" + "\n".join(f"{ts(p['start'], '.')} --> {ts(p['end'], '.')}\n{p['text']}\n" for p in ps)
    a, b = Path(f"{stem}.srt"), Path(f"{stem}.vtt")
    a.write_text(srt, encoding="utf-8")
    b.write_text(vtt, encoding="utf-8")
    return a, b, len(ps)


def parse_srt(text: str) -> list:
    """SRT (vd. xuất từ CapCut) -> transcript dạng Whisper, chia đều thời gian cho từng chữ trong mỗi dòng."""
    segs = []
    for block in re.split(r"\n\s*\n", text.replace("\r", "").strip()):
        lines = [l for l in block.split("\n") if l.strip()]
        tl = next((l for l in lines if "-->" in l), None)
        if not tl:
            continue
        a, b = [_sec(x) for x in tl.split("-->")]
        body = " ".join(lines[lines.index(tl) + 1:])
        body = re.sub(r"<[^>]+>", "", body).split()
        if not body or b <= a:
            continue
        step = (b - a) / len(body)
        segs.append({"start": a, "end": b, "text": " " + " ".join(body),
                     "words": [{"w": " " + w, "s": round(a + k * step, 3), "e": round(a + (k + 1) * step, 3), "p": 1.0} for k, w in enumerate(body)]})
    return segs


def _sec(x: str) -> float:
    h, m, s = x.strip().split()[0].replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)
