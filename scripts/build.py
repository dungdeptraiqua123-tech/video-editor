import json, subprocess, sys
SRC = sys.argv[1]
DUR = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC]))
t = json.load(open("transcript.json"))
cfg = json.load(open("beats.json"))
# đoạn Whisper bịa / lặp lại cần bỏ: ghi giây bắt đầu của đoạn vào beats.json "dropSegments"
DROP = cfg.get("dropSegments", [])
words = []
for s in t:
    if any(abs(s["start"] - d) < 0.05 for d in DROP):
        continue
    for w in s["words"]:
        words.append({"text": w["w"].strip(), "start": w["s"], "end": w["e"]})

# sửa lỗi nhận dạng, khai báo trong beats.json "fix": [["cụm sai", "cụm đúng"], ...]; cụm đúng rỗng = xoá
FIX = [tuple(x) for x in cfg.get("fix", [])]
def apply(words):
    out = []; i = 0
    while i < len(words):
        for bad, good in FIX:
            b = bad.split(); n = len(b)
            if [w["text"] for w in words[i:i+n]] == b:
                g = good.split()
                if g:
                    seg = words[i:i+n]; s0, e0 = seg[0]["start"], seg[-1]["end"]
                    step = (e0 - s0) / len(g)
                    out += [{"text": x, "start": s0 + k*step, "end": s0 + (k+1)*step} for k, x in enumerate(g)]
                i += n; break
        else:
            out.append(words[i]); i += 1
    return out
words = apply(words)

# đoạn giữ lại: gộp các từ, cắt khoảng lặng > 0,55s (đệm 0,12s)
PAD, GAP = 0.12, 0.55
keep = []
for w in words:
    s, e = max(0, w["start"] - PAD), w["end"] + PAD
    if keep and s - keep[-1][1] < GAP - 2*PAD: keep[-1][1] = max(keep[-1][1], e)
    else: keep.append([s, e])
keep[-1][1] = min(keep[-1][1] + 0.3, DUR)
def m(x):  # thời gian gốc -> thời gian sau khi cắt
    acc = 0
    for s, e in keep:
        if x < s: return acc
        if x <= e: return acc + x - s
        acc += e - s
    return acc
dur_cut = sum(e - s for s, e in keep)
print("cut", round(DUR - dur_cut, 2), "s; new", round(dur_cut, 2), file=sys.stderr)

json.dump({"keep": [[round(a,3), round(b,3)] for a, b in keep], "words_goc": words}, open("doan-giu-lai.json", "w"), ensure_ascii=False)
sel = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in keep)
import os
if not os.environ.get("SKIP_CUT"):
  subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", SRC,
    "-vf", f"select='{sel}',setpts=N/FRAME_RATE/TB", "-af", f"aselect='{sel}',asetpts=N/SR/TB,loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000",
    "-c:v", "libx264", "-crf", "17", "-preset", "fast", "-c:a", "aac", "-b:a", "192k", "public/cut.mp4"], check=True)

OUTRO = 3.6
cw = [{"text": w["text"], "start": round(m(w["start"]), 3), "end": round(m(w["end"]), 3)} for w in words]
beats_src = cfg

LEAD = 0.08  # hiện sớm hơn từ khoá một chút để mắt kịp bắt
norm = lambda x: x.lower().strip(".,!?;:")
def said(phrase, lo, hi):
    """Thời điểm (giây, video gốc) từ khoá được nói lần đầu trong khoảng [lo, hi]."""
    ph = [norm(x) for x in phrase.split()]
    for i in range(len(words) - len(ph) + 1):
        if lo <= words[i]["start"] <= hi and [norm(w["text"]) for w in words[i:i+len(ph)]] == ph:
            return words[i]["start"]
    raise SystemExit(f"Không tìm thấy từ khoá '{phrase}' trong khoảng {lo}-{hi}s")

def resolve(obj, lo, hi, base):
    """Đổi mọi khoá say/xxxSay thành d/xxxD: số giây tính từ lúc đồ hoạ mở (theo bản đã cắt)."""
    if isinstance(obj, list):
        return [resolve(x, lo, hi, base) for x in obj]
    if not isinstance(obj, dict):
        return obj
    out = {}
    for k, v in obj.items():
        if k == "say" or k.endswith("Say"):
            key = "d" if k == "say" else k[:-3] + "D"
            out[key] = round(max(0, m(said(v, lo, hi)) - LEAD - base), 2)
        else:
            out[k] = resolve(v, lo, hi, base)
    return out

beats = []
for b in beats_src["beats"]:
    s0 = round(m(b["start"]), 2)
    beats.append({"start": s0, "end": round(m(b["end"]), 2), "g": resolve(b["g"], b["start"] - 1, b["end"] + 0.5, s0)})
zooms = [round(m(z), 2) for z in beats_src["zooms"]]
tp = beats_src["topics"]
topics = [{"start": round(m(x["start"]), 2), "end": round(m(tp[i+1]["start"]) if i+1 < len(tp) else dur_cut, 2), "kicker": x["kicker"], "title": x["title"],
           "items": [{"at": round(m(said(it["say"], x["start"], tp[i+1]["start"] + 3 if i+1 < len(tp) else 999)) - LEAD, 2), "text": it["text"]} for it in x["items"]]} for i, x in enumerate(tp)]
for b, src in zip(beats, beats_src["beats"]): b["head"] = src["head"]
data = {"brand": beats_src["brand"], "topics": topics, "hook": beats_src["hook"], "duration": round(dur_cut, 2), "words": cw, "beats": beats, "zooms": zooms, "cta": beats_src["cta"]}
json.dump(data, open("src/data.json", "w"), ensure_ascii=False)
