"""Phân tích video mẫu: nhịp đổi cảnh, tốc độ nói, quãng nghỉ giữa các từ, 3 giây mở đầu, độ lớn âm,
ảnh toàn cảnh và ảnh mở đầu để nhìn kiểu phụ đề, bố cục. Từ đó gợi ý nhịp dựng cho dự án.

Chỉ đọc file trên máy, không tải video từ mạng: người dùng tự tải video mẫu (đúng quyền sử dụng) rồi đưa đường dẫn.
Chép lời chạy trên máy như bước transcribe.
"""
from __future__ import annotations

import re
import statistics as st
import time
from pathlib import Path

from . import media as M
from .bang import clock
from .env import SKILL_DIR, VEError, info, read_json, run, venv_python, warn, write_json
from .project import GRAPHICS_EVERY, PACES, Project
from .timeline import words_from_transcript

PACE_LABEL = {"nhanh": "nhanh", "vua": "vừa", "cham": "chậm"}
GRAPHICS_LABEL = {"it": "ít", "vua": "vừa", "nhieu": "nhiều"}


def _slug(s: str) -> str:
    import unicodedata

    s = unicodedata.normalize("NFKD", s).replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()[:40] or "mau"


def _pct(xs: list, q: float) -> float:
    if not xs:
        return 0.0
    xs = sorted(xs)
    k = min(len(xs) - 1, max(0, round(q * (len(xs) - 1))))
    return xs[k]


# ---------------------------------------------------------------- hình
def scene_changes(path: Path, work: Path, fps: int = 12) -> dict:
    """Điểm khác biệt giữa hai khung liền nhau (bộ lọc scene của ffmpeg, ảnh thu nhỏ 160px cho nhanh).

    Một lần đổi cảnh = cụm khung có điểm vượt ngưỡng, các khung cách nhau dưới 0,5 giây gộp làm một
    (chuyển cảnh, chữ bật lên kéo dài vài khung). Ngưỡng = max(0,1; 10 × trung vị) để chuyển động thường không bị tính.
    Cắt nhảy (jump cut) cùng khung hình gần như không đổi ảnh nên không đếm được ở đây; độ gắt của cắt nhảy đo bằng quãng nghỉ lời nói.
    """
    meta = work / "scene.txt"
    run(["ffmpeg", "-hide_banner", "-nostats", "-loglevel", "error", "-i", path, "-an", "-sn",
         "-vf", f"fps={fps},scale=160:-2,select='gte(scene,0)',metadata=mode=print:file={meta.name}", "-f", "null", "-"], cwd=work)
    txt = meta.read_text(encoding="utf-8", errors="replace") if meta.exists() else ""
    meta.unlink(missing_ok=True)
    ts = [float(x) for x in re.findall(r"pts_time:([\d.]+)", txt)]
    sc = [float(x) for x in re.findall(r"scene_score=([\d.]+)", txt)]
    return changes_from_scores(list(zip(ts, sc)))


def changes_from_scores(pairs: list) -> dict:
    if not pairs:
        return {"changes": [], "threshold": None, "median": None}
    med = st.median(s for _, s in pairs)
    thr = max(0.1, 10 * med)
    out, last = [], -9.0
    for t, s in pairs:
        if s < thr:
            continue
        if t - last < 0.5 and out:
            if s > out[-1][1]:
                out[-1] = (out[-1][0], s)
        else:
            out.append((t, s))
        last = t
    return {"changes": [round(t, 2) for t, _ in out], "threshold": round(thr, 3), "median": round(med, 4)}


def shot_stats(changes: list, dur: float) -> dict:
    n = len(changes)
    bounds = [0.0, *changes, dur]
    shots = [b - a for a, b in zip(bounds, bounds[1:]) if b - a > 0.05]
    return {"count": n, "perTenSec": round(n / max(dur, 1) * 10, 2), "avgShot": round(dur / (n + 1), 2),
            "medianShot": round(st.median(shots), 2) if shots else round(dur, 2), "inFirst3s": sum(1 for t in changes if t < 3.0)}


# ---------------------------------------------------------------- tiếng
def audio_pauses(src: Path, dur: float) -> dict:
    """Quãng nghỉ đo trên âm thanh (lọc dải tiếng nói, dưới -30 dB từ 0,12 giây). Dấu thời gian từng từ của Whisper
    thường dính liền nhau nên không dùng để đo nghỉ. Video có nhạc nền liên tục thì gần như không có quãng lặng: báo không đo được."""
    p = run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-vn", "-af", "highpass=f=120,lowpass=f=4000,silencedetect=n=-30dB:d=0.12",
             "-f", "null", "-"], quiet=True, check=False)
    ds = sorted(float(x) for x in re.findall(r"silence_duration: ([\d.]+)", p.stderr or ""))
    share = sum(ds) / max(dur, 1)
    return {"count": len(ds), "share": round(share, 3), "perTenSec": round(len(ds) / max(dur, 1) * 10, 2),
            "p50": round(_pct(ds, 0.5), 2), "p90": round(_pct(ds, 0.9), 2), "long": sum(1 for d in ds if d >= 0.6),
            "reliable": len(ds) >= 3 and share >= 0.02}


# ---------------------------------------------------------------- lời
def transcribe(src: Path, work: Path, lang: str, max_sec: float) -> list | None:
    from .doctor import model_cached, resolve_model

    vp = venv_python()
    if not vp.exists():
        warn("Chưa cài môi trường chép lời nên bỏ qua phần lời nói. Chạy `video-editor setup` để có đủ số đo.")
        return None
    # chỉ cần tốc độ nói và câu mở đầu: dùng mô hình nhanh nếu đã có trên máy
    model = "large-v3-turbo" if model_cached("large-v3-turbo") else resolve_model("auto")
    if not model_cached(model):
        info(f"(lần đầu: tải mô hình {model}, có thể mất vài phút)")
    wav = work / "audio.wav"
    run(["ffmpeg", "-y", "-loglevel", "error", "-t", f"{max_sec:.0f}", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav])
    out = work / "transcript.json"
    info(f"🎙 chép lời video mẫu bằng Whisper {model} …")
    p = run([vp, SKILL_DIR / "ve" / "whisper_worker.py", wav, out, model, lang], check=False, quiet=True)
    wav.unlink(missing_ok=True)
    if p.returncode != 0 or not out.exists():
        warn("Chép lời video mẫu không thành, bỏ qua phần lời nói (có thể video chỉ có nhạc).")
        return None
    return read_json(out)


def speech_stats(segs: list) -> dict | None:
    words = [w for w in words_from_transcript(segs) if w.text.strip()]
    if len(words) < 5:
        return None
    span = words[-1].end - words[0].start
    return {
        "words": len(words),
        "firstWordAt": round(words[0].start, 2),
        "wordsPerMin": round(len(words) / max(span, 1) * 60),
        "hook": " ".join(w.text for w in words if w.start < 3.0),
        "first10s": " ".join(w.text for w in words if w.start < 10.0),
    }


# ---------------------------------------------------------------- gợi ý
def suggest(shots: dict, speech: dict | None, dur: float, pauses: dict | None = None) -> dict:
    """Bỏ phiếu nhịp từ các số đo. Video gần như một cảnh liền (dưới 3 lần đổi cảnh) thì nhịp nằm ở lời, không tính phiếu hình."""
    votes, why = [], []
    if shots["count"] >= 3 or (dur < 20 and shots["count"] >= 2):
        a = shots["avgShot"]
        v = "nhanh" if a <= 2.5 else "cham" if a >= 6 else "vua"
        votes.append(v)
        why.append(f"trung bình {a:.1f} giây đổi cảnh một lần → {PACE_LABEL[v]}")
    else:
        why.append(f"gần như một cảnh liền ({shots['count']} lần đổi cảnh), nhịp nằm ở cách cắt lời")
    gap = None
    if pauses and pauses["reliable"]:
        g = pauses["p90"]
        v = "nhanh" if g <= 0.4 else "cham" if g >= 0.8 else "vua"
        votes.append(v)
        why.append(f"90% quãng nghỉ ngắn hơn {g:.2f} giây → {PACE_LABEL[v]}")
        sh_ = pauses["share"]
        v = "nhanh" if sh_ <= 0.1 else "cham" if sh_ >= 0.22 else "vua"
        votes.append(v)
        why.append(f"lặng {sh_ * 100:.0f}% thời lượng → {PACE_LABEL[v]}")
        gap = round(min(0.9, max(0.25, g + 0.05)), 2)
    elif pauses:
        why.append("có nhạc nền liên tục nên không đo được quãng nghỉ")
    if speech:
        w = speech["wordsPerMin"]
        v = "nhanh" if w >= 230 else "cham" if w <= 160 else "vua"
        votes.append(v)
        why.append(f"nói {w} chữ/phút → {PACE_LABEL[v]}")
    pace = max(("nhanh", "vua", "cham"), key=lambda p: (votes.count(p), p == "vua")) if votes else "vua"
    pt = shots["perTenSec"]
    # đồ hoạ bật lên cũng làm đổi ảnh: 1 lần mỗi 6–7 giây trở lên coi là nhiều (bản nháp dựng với "nhieu" đo được 1,84 lần/10 giây)
    graphics = "nhieu" if pt >= 1.5 else "it" if pt <= 0.6 else "vua"
    return {"pace": pace, "graphics": graphics, "gap": gap, "why": why,
            "zoomEvery": PACES[pace]["zoomEvery"], "graphicsEvery": GRAPHICS_EVERY[graphics]}


# ---------------------------------------------------------------- ảnh
def _grab(src: Path, t: float, dst: Path, portrait: bool) -> None:
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1", "-vf", "scale=-2:854" if portrait else "scale=760:-2", "-q:v", "3", dst])


def _said_at(segs: list | None, t: float) -> str:
    if not segs:
        return ""
    ws = [w for w in words_from_transcript(segs) if t - 1.2 <= w.start <= t + 1.8]
    s = " ".join(w.text for w in ws)
    return f"“{s[:66]}…”" if len(s) > 66 else (f"“{s}”" if s else "")


def sheets(src: Path, work: Path, pi: dict, changes: list, segs: list | None) -> dict:
    from .storyboard import _sheet

    portrait = pi["height"] > pi["width"]
    fdir = work / "khung"
    fdir.mkdir(exist_ok=True)
    dur = pi["duration"]
    # toàn cảnh: 12 khung rải đều; mở đầu: 6 khung trong 3 giây đầu
    full = [round(dur * (i + 0.5) / 12, 2) for i in range(12)]
    hook = [t for t in (0.1, 0.5, 1.0, 1.5, 2.2, 3.0) if t < dur]
    out = {}
    for name, times, title in (("toan-canh", full, "Toàn cảnh video mẫu"), ("mo-dau", hook, "3 giây đầu video mẫu")):
        tiles = []
        for i, t in enumerate(times, 1):
            p = fdir / f"{name}-{i:02d}.jpg"
            _grab(src, t, p, portrait)
            near = [c for c in changes if abs(c - t) < 0.6]
            tiles.append((f"khung/{p.name}", f"#{i} · {clock(t)}" + (" · ngay lúc đổi cảnh" if near else ""), _said_at(segs, t)))
        notes = [f"{Path(src).name} · {pi['width']}×{pi['height']} · {clock(dur)} · {len(changes)} lần đổi cảnh",
                 "Nhìn để chép: vị trí và kiểu phụ đề, màu, cỡ chữ, bố cục khuôn mặt, đồ hoạ, chữ tiêu đề mở đầu."]
        out[name] = str(_sheet(work / f"{name}.html", work / f"{name}.jpg", f"{title}: {Path(src).stem[:50]}", notes, tiles, portrait,
                               cols=(6 if portrait else 4) if name == "toan-canh" else (6 if portrait else 3)))
    return out


# ---------------------------------------------------------------- chạy
def analyze(src: str | Path, work: Path, lang: str = "vi", speech: bool = True, max_sec: float = 180) -> dict:
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]+:/", str(src)) or str(src).startswith("www."):
        raise VEError("Chỉ phân tích video đã có trên máy.", "Tải video mẫu về máy (đúng quyền sử dụng) rồi đưa đường dẫn file, ví dụ `video-editor mau ~/Downloads/mau.mp4`.")
    src = Path(src).expanduser().resolve()
    pi = M.probe(src)
    if not pi["has_video"]:
        raise VEError(f"{src.name} không có hình.", "Video mẫu cần có hình để đo nhịp đổi cảnh.")
    work.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    dur = pi["duration"]
    info(f"🔎 đo đổi cảnh {clock(dur)} …")
    sc = scene_changes(src, work)
    shots = shot_stats(sc["changes"], dur)
    segs = transcribe(src, work, lang, max_sec) if speech and pi["has_audio"] else None
    sp = speech_stats(segs) if segs else None
    pz = audio_pauses(src, dur) if pi["has_audio"] else None
    loud = M.loudness(src) if pi["has_audio"] else {"lufs": None, "peak": None}
    sug = suggest(shots, sp, dur, pz)
    info("🖼 chụp ảnh toàn cảnh và 3 giây đầu …")
    imgs = sheets(src, work, pi, sc["changes"], segs)
    res = {"source": str(src), "duration": dur, "width": pi["width"], "height": pi["height"], "fps": pi.get("fps"),
           "scene": sc, "shots": shots, "speech": sp, "pauses": pz, "loudness": loud, "suggest": sug, "images": imgs,
           "speechLimitedTo": max_sec if sp and dur > max_sec else None, "seconds": round(time.time() - t0)}
    write_json(work / "phan-tich.json", res)
    report(res, work / "phan-tich.md")
    return res


def report(r: dict, path: Path) -> Path:
    sh, sp, sg, ld, pz = r["shots"], r["speech"], r["suggest"], r["loudness"], r.get("pauses")
    aspect = "dọc 9:16" if r["height"] > r["width"] * 1.5 else "ngang 16:9" if r["width"] > r["height"] * 1.5 else f"{r['width']}×{r['height']}"
    L = [f"# Phân tích video mẫu: {Path(r['source']).name}", "",
         f"{clock(r['duration'])}, khổ {aspect}, {r['fps']} khung/giây. Đo trong {r['seconds']} giây.", "",
         "## Gợi ý cho dự án", "",
         "| Mục | Gợi ý | Ghi vào project.json |", "|---|---|---|",
         f"| Nhịp dựng | {PACE_LABEL[sg['pace']]} | `style.pace = \"{sg['pace']}\"` |",
         f"| Mật độ đồ hoạ | {GRAPHICS_LABEL[sg['graphics']]} (khoảng {sg['graphicsEvery']} giây một khung) | `style.graphics = \"{sg['graphics']}\"` |"]
    if sg["gap"]:
        L.append(f"| Cắt lặng | quãng nghỉ dài hơn {sg['gap']:.2f} giây thì cắt | `cuts.gap = {sg['gap']}` |")
    L += ["", "Vì sao: " + "; ".join(sg["why"]) + ".", "",
          "## Số đo", "",
          "| Số đo | Giá trị |", "|---|---|",
          f"| Số lần đổi cảnh (cắt cảnh, chuyển cảnh, đồ hoạ bật lên) | {sh['count']} |",
          f"| Đổi cảnh mỗi 10 giây | {sh['perTenSec']} |",
          f"| Độ dài cảnh trung bình / trung vị | {sh['avgShot']} giây / {sh['medianShot']} giây |",
          f"| Đổi cảnh trong 3 giây đầu | {sh['inFirst3s']} |"]
    if sp:
        L += [f"| Tốc độ nói | {sp['wordsPerMin']} chữ/phút |",
              f"| Tiếng nói đầu tiên ở giây | {sp['firstWordAt']} |"]
    if pz and pz["reliable"]:
        L += [f"| Quãng nghỉ (từ 0,12 giây) | {pz['count']} lần, {pz['perTenSec']} lần mỗi 10 giây, lặng {pz['share'] * 100:.0f}% thời lượng |",
              f"| Độ dài quãng nghỉ: trung vị / 90% ngắn hơn | {pz['p50']} giây / {pz['p90']} giây |",
              f"| Nghỉ dài (từ 0,6 giây) | {pz['long']} lần |"]
    elif pz:
        L.append("| Quãng nghỉ | không đo được (nhạc nền liên tục) |")
    if ld.get("lufs") is not None:
        L.append(f"| Độ lớn âm | {ld['lufs']:.1f} LUFS, đỉnh {ld['peak']:.1f} dBFS |")
    if r.get("speechLimitedTo"):
        L.append(f"| Ghi chú | phần lời chỉ đo {r['speechLimitedTo']:.0f} giây đầu |")
    L += ["", "Cắt nhảy giữ nguyên khung hình gần như không đổi ảnh nên không tính vào số lần đổi cảnh. Độ gắt của cắt nhảy xem ở quãng nghỉ.", ""]
    if sp:
        L += ["## Câu mở đầu", "", f"3 giây đầu nói: “{sp['hook'] or '(chưa nói gì)'}”", "", f"10 giây đầu: {sp['first10s']}", ""]
    L += ["## Ảnh để nhìn kiểu dựng", "",
          f"- Toàn cảnh 12 khung: `{Path(r['images']['toan-canh']).name}`",
          f"- 3 giây đầu: `{Path(r['images']['mo-dau']).name}`", "",
          "Trợ lý AI mở hai ảnh này, ghi lại rồi đối chiếu với các lựa chọn của bộ dựng:", "",
          "| Nhìn thấy trong video mẫu | Chọn |", "|---|---|",
          "| Phụ đề chữ to có viền sáng, từ đang nói đổi màu | `captions.style = \"glow\"` |",
          "| Phụ đề nằm trong hộp nền đặc | `captions.style = \"box\"` |",
          "| Từng từ nảy lên | `captions.style = \"pop\"` |",
          "| Chữ trơn, không hiệu ứng | `captions.style = \"plain\"` |",
          "| Phụ đề ở giữa màn hình / phía dưới | `captions.position` |",
          "| Mỗi dòng 2–4 từ / cả câu | `captions.maxWords` |",
          "| Có tiêu đề lớn trong 3 giây đầu | viết `content.hook.title` cùng kiểu |",
          "| Màu chủ đạo, font | `brand` hoặc chọn mẫu khác (`video-editor templates`) |", "",
          "Chỉ học nhịp và cách trình bày. Không chép nguyên lời, hình, logo hay nhạc của video mẫu.", ""]
    path.write_text("\n".join(L), encoding="utf-8")
    return path


def apply(prj: Project, r: dict, rel: str, set_style: bool) -> list[str]:
    """Ghi video mẫu vào style.reference. Có set_style thì ghi luôn nhịp, mật độ đồ hoạ, mức cắt lặng gợi ý."""
    sg, sh = r["suggest"], r["shots"]
    sp = r["speech"] or {}
    summary = f"{Path(r['source']).name}: nhịp {PACE_LABEL[sg['pace']]}, {sh['avgShot']}s/cảnh" + (f", {sp['wordsPerMin']} chữ/phút" if sp else "") + f" (xem {rel})"
    prj.cfg.setdefault("style", {})["reference"] = summary
    changed = [f"style.reference = \"{summary}\""]
    if set_style:
        prj.cfg["style"]["pace"] = sg["pace"]
        prj.cfg["style"]["graphics"] = sg["graphics"]
        changed += [f"style.pace = \"{sg['pace']}\"", f"style.graphics = \"{sg['graphics']}\""]
        if sg["gap"]:
            prj.cfg.setdefault("cuts", {})["gap"] = sg["gap"]
            changed.append(f"cuts.gap = {sg['gap']}")
        prj.invalidate("build", "render", "export")
    prj.save()
    return changed
