"""Xuất phụ đề SRT và VTT từ src/data.json (thời gian đã tính sau khi cắt, khớp video render).

  python3 export_subs.py src/data.json phu-de     -> phu-de.srt, phu-de.vtt

Gom cụm giống hệt Captions.tsx (buildPages), nên phụ đề rời khớp phụ đề cháy trong video.
"""
import json, re, sys

MAX_CHARS, MAX_WORDS = 30, 8


def pages(words):
    out, cur = [], []
    def flush():
        nonlocal cur
        if cur:
            out.append({"start": cur[0]["start"], "end": cur[-1]["end"], "text": " ".join(w["text"] for w in cur)})
        cur = []
    for i, w in enumerate(words):
        prev = words[i - 1] if i else None
        n = len(" ".join(x["text"] for x in cur)) + len(w["text"]) + 1
        if cur and (n > MAX_CHARS or len(cur) >= MAX_WORDS or (prev and w["start"] - prev["end"] > 0.35)):
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


def main(src, stem):
    d = json.load(open(src, encoding="utf-8"))
    ps = [p for p in pages(d["words"]) if p["start"] < d["duration"]]
    for p in ps:
        p["end"] = min(p["end"], d["duration"])
    srt = "\n".join(f"{i}\n{ts(p['start'], ',')} --> {ts(p['end'], ',')}\n{p['text']}\n" for i, p in enumerate(ps, 1))
    vtt = "WEBVTT\n\n" + "\n".join(f"{ts(p['start'], '.')} --> {ts(p['end'], '.')}\n{p['text']}\n" for p in ps)
    open(stem + ".srt", "w", encoding="utf-8").write(srt)
    open(stem + ".vtt", "w", encoding="utf-8").write(vtt)
    print(f"{len(ps)} cụm -> {stem}.srt, {stem}.vtt")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "phu-de")
