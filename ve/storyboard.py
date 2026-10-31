"""Storyboard để người dùng duyệt trước khi render, và bảng tự kiểm tra khung hình của video cuối.

Storyboard: ảnh chụp ở các thời điểm ngẫu nhiên rải đều theo độ dài video (mỗi khung đồ hoạ có ít nhất một ảnh),
mỗi ảnh có tiêu đề: thời điểm, cảnh gì, lời đang nói. Người dùng đồng ý thì `video-editor approve`, render mới chạy.
Tự kiểm tra: lấy khung hình từ chính file MP4 đã render ở cùng các thời điểm và lúc từng phần tử hiện,
kèm dò khung đen, hình đứng, khoảng câm, rồi ghi vào báo cáo.
"""
from __future__ import annotations

import hashlib
import html
import random
import re
import shutil
import subprocess
import time
from pathlib import Path

from .bang import clock
from .env import VEError, browser_exe, info, read_json, run, warn, write_json
from .project import Project, fingerprint, rules_text


def frame_count(duration: float) -> int:
    """Số ảnh storyboard: khoảng một ảnh mỗi 8 giây, tối thiểu 6, tối đa 24."""
    return max(6, min(24, round(duration / 8)))


def _full_moment(b: dict) -> float:
    ds = [v for k, v in _walk(b["g"]) if k == "d" or k.endswith("D")]
    return min(b["start"] + (max(ds) + 0.7 if ds else 1.2), b["end"] - 0.3)


def _walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (int, float)):
                yield k, v
            else:
                yield from _walk(v)
    elif isinstance(o, list):
        for x in o:
            yield from _walk(x)


def sample_times(d: dict, seed: int) -> list[float]:
    """Thời điểm ngẫu nhiên, mỗi ô thời gian bằng nhau một ảnh (không dồn cục), thêm ảnh cho khung đồ hoạ chưa được chụp."""
    dur = float(d["duration"])
    n = frame_count(dur)
    rng = random.Random(seed)
    lo, hi = 0.4, max(0.5, dur - 0.4)
    step = (hi - lo) / n
    ts = [lo + (i + rng.uniform(0.15, 0.85)) * step for i in range(n)]
    for b in d.get("beats", []):
        if not any(b["start"] <= t <= b["end"] for t in ts):
            ts.append(_full_moment(b))
    return sorted(round(t, 2) for t in ts)


def describe(d: dict, t: float) -> tuple[str, str]:
    """(cảnh đang hiện, lời đang nói quanh thời điểm t)."""
    if t < d["hookSec"]:
        scene = f"Mở đầu: {d['hook'].get('title', '')}"
    elif t >= d["duration"] - d["outroSec"]:
        scene = f"Kết: {d.get('cta', '')}"
    else:
        b = next((b for b in d.get("beats", []) if b["start"] <= t < b["end"]), None)
        tp = next((x for x in d.get("topics", []) if x["start"] <= t < x["end"]), None)
        if b:
            g = b["g"]
            scene = f"Đồ hoạ: {b.get('head') or g.get('title') or g.get('text') or g.get('label') or g.get('type')}"
        elif tp and d.get("mode") != "faceless":
            scene = f"Người nói + thẻ: {tp.get('title', '')}"
        else:
            scene = "Người nói" if d.get("mode") != "faceless" else "Nền + phụ đề"
    near = [w["text"] for w in d.get("words", []) if t - 1.3 <= w["start"] <= t + 1.0]
    said = " ".join(near)
    if len(said) > 70:
        said = said[:68].rsplit(" ", 1)[0] + "…"
    return scene, (f"“{said}”" if said else "")


def _sheet(page: Path, image: Path, title: str, notes: list[str], tiles: list[tuple[str, str, str]], portrait: bool) -> Path:
    """Trang HTML ghép ảnh kèm tiêu đề, chụp thành JPG bằng trình duyệt render. Không có trình duyệt thì ghép ảnh không chữ bằng ffmpeg."""
    tw, th = (240, 427) if portrait else (400, 225)
    cols = 5 if portrait else 3
    cap_h, gap, pad = 92, 14, 24
    rows = (len(tiles) + cols - 1) // cols
    head_h = 70 + 22 * len(notes)
    W = pad * 2 + cols * tw + (cols - 1) * gap
    H = pad * 2 + head_h + rows * (th + cap_h) + (rows - 1) * gap
    cells = "".join(
        f'<figure><img src="{html.escape(src)}"><figcaption><b>{html.escape(t1)}</b><span>{html.escape(t2)}</span></figcaption></figure>'
        for src, t1, t2 in tiles)
    page.write_text(f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>{html.escape(title)}</title><style>
*{{box-sizing:border-box;margin:0}} body{{background:#0f1218;color:#e8ecf2;font:14px/1.35 system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans",sans-serif;padding:{pad}px;width:{W}px}}
header{{height:{head_h}px}} h1{{font-size:22px;margin-bottom:8px}} header p{{color:#aab3c2;font-size:13px;height:22px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
main{{display:grid;grid-template-columns:repeat({cols},{tw}px);gap:{gap}px}}
figure{{width:{tw}px;background:#1a1f29;border-radius:8px;overflow:hidden}} img{{display:block;width:{tw}px;height:{th}px;object-fit:cover;background:#000}}
figcaption{{height:{cap_h}px;padding:6px 8px;font-size:12px}} figcaption b{{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;color:#fff;margin-bottom:2px}}
figcaption span{{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;color:#aab3c2}}
</style></head><body><header><h1>{html.escape(title)}</h1>{"".join(f"<p>{html.escape(n)}</p>" for n in notes)}</header><main>{cells}</main></body></html>""", encoding="utf-8")
    b = browser_exe()
    png = image.with_suffix(".png")
    if b:
        p = subprocess.run([b, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                            f"--window-size={W},{H}", f"--screenshot={png}", page.resolve().as_uri()], capture_output=True, timeout=120)
        if p.returncode == 0 and png.exists():
            run(["ffmpeg", "-y", "-loglevel", "error", "-i", png, "-q:v", "3", image])
            png.unlink()
            return image
    warn("Không chụp được trang storyboard bằng trình duyệt, ghép ảnh không kèm tiêu đề (tiêu đề xem trong file .html).")
    srcs = [page.parent / s for s, _, _ in tiles]
    inputs = sum([["-i", s] for s in srcs], [])
    rows_f = "".join(f"[{i}]scale={tw}:{th}[s{i}];" for i in range(len(srcs)))
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex",
         rows_f + "".join(f"[s{i}]" for i in range(len(srcs))) + f"xstack=inputs={len(srcs)}:layout=" +
         "|".join(f"{(i % cols) * tw}_{(i // cols) * th}" for i in range(len(srcs))) + ":fill=black" if len(srcs) > 1 else f"[0]scale={tw}:{th}", image])
    return image


def preview(prj: Project, draft: bool = False, seed: int | None = None) -> list[Path]:
    from .render import _data, _render, stills

    dpath = _data(prj)
    d = read_json(dpath)
    fp = fingerprint(dpath)
    if seed is None:
        seed = int(hashlib.sha1(fp.encode()).hexdigest()[:8], 16)
    sb = prj.out / "storyboard"
    shutil.rmtree(sb, ignore_errors=True)
    sb.mkdir(parents=True)
    times = sample_times(d, seed)
    t0 = time.time()
    info(f"🎞 storyboard {len(times)} ảnh cho video {d['duration']:.0f}s …")
    shots = [(t, sb / f"{i:02d}-{clock(t).replace(':', 'm').replace('.', 's')}.jpg") for i, t in enumerate(times, 1)]
    stills(prj, shots, scale=0.5)
    tiles = []
    for i, (t, p) in enumerate(shots, 1):
        scene, said = describe(d, t)
        tiles.append((f"storyboard/{p.name}", f"#{i} · {clock(t)} · {scene}", said))
    W, H = d["format"]["w"], d["format"]["h"]
    notes = [f"{prj.cfg['format']} · {clock(d['duration'])} · {len(d['beats'])} khung đồ hoạ · {len(d['topics'])} thẻ chủ đề · ảnh chọn ngẫu nhiên (seed {seed})"]
    notes += [f"Quy tắc riêng: {r}" for r in prj.cfg.get("rules") or []][:4]
    sheet = _sheet(prj.out / "storyboard.html", prj.out / "storyboard.jpg", f"Storyboard duyệt: {prj.cfg.get('name') or prj.slug}", notes, tiles, W < H)
    prj.mark("preview", fp, times=times, seed=seed)
    info(f"✓ {len(times)} ảnh trong {time.time() - t0:.0f}s → {sheet}")
    info("  Tự xem từng ảnh trước (chữ tràn, che mặt, sai màu, sai quy tắc riêng), rồi gửi người dùng duyệt.")
    info(f"  Người dùng đồng ý: `video-editor approve {prj.root}`. Muốn bộ ảnh khác: `preview --seed <số>`.")
    out = [sheet, *[sb / Path(s).name for s, _, _ in tiles]]
    if draft:
        p = prj.out / "ban-nhap.mp4"
        info("🎞 render bản nháp nửa độ phân giải …")
        _render(prj, p, scale=0.5, crf=30)
        out.append(p)
        info(f"✓ bản nháp → {p}")
    return out


def approve(prj: Project, note: str = "") -> None:
    from .render import _data

    fp = fingerprint(_data(prj))
    st = prj.state().get("preview")
    if not st:
        raise VEError("Chưa có storyboard để duyệt.", f"Chạy `video-editor preview {prj.root}` rồi gửi out/storyboard.jpg cho người dùng.")
    if st["fp"] != fp:
        raise VEError("Storyboard đã cũ: nội dung đã đổi sau lần xem trước.", f"Chạy lại `video-editor preview {prj.root}` và gửi người dùng duyệt bản mới.")
    prj.mark("approve", fp, note=note)
    info("✓ storyboard đã được duyệt, có thể render.")


def require_approval(prj: Project, data: Path) -> None:
    if not prj.fresh("approve", fingerprint(data)):
        old = prj.state().get("approve")
        why = "nội dung đã đổi sau lần duyệt" if old else "chưa được duyệt"
        raise VEError(f"Storyboard {why}: chưa render.",
                      f"Chạy `video-editor preview {prj.root}`, tự xem rồi gửi out/storyboard.jpg cho người dùng. Họ đồng ý thì `video-editor approve {prj.root}`.")


def _detect(final: Path) -> dict:
    """Một lượt ffmpeg: khung đen, hình đứng yên, khoảng câm."""
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(final), "-vf", "scale=270:-2,blackdetect=d=0.4:pix_th=0.10,freezedetect=n=0.003:d=2",
                        "-af", "silencedetect=n=-45dB:d=1.2", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = p.stderr
    num = r"(-?[\d.]+)"
    black = [(float(a), float(b)) for a, b in re.findall(rf"black_start:{num} black_end:{num}", log)]
    fs = [float(x) for x in re.findall(rf"freeze_start: {num}", log)]
    fe = [float(x) for x in re.findall(rf"freeze_end: {num}", log)]
    ss = [float(x) for x in re.findall(rf"silence_start: {num}", log)]
    se = [float(x) for x in re.findall(rf"silence_end: {num}", log)]
    return {"black": black, "freeze": list(zip(fs, fe + [None] * (len(fs) - len(fe)))), "silence": list(zip(ss, se + [None] * (len(ss) - len(se))))}


def qa(prj: Project, final: Path) -> dict:
    """Tự kiểm tra video cuối: ảnh từ chính file MP4 + dò lỗi tự động. Kết quả ở work/qa.json và out/kiem-tra.jpg."""
    from .render import _data

    d = read_json(_data(prj))
    fp = fingerprint(final)
    st = prj.state()
    if st.get("qa", {}).get("fp") == fp and (prj.work / "qa.json").exists() and (prj.out / "kiem-tra.jpg").exists():
        return read_json(prj.work / "qa.json")
    t0 = time.time()
    times = list(st.get("preview", {}).get("times") or sample_times(d, 1))
    # thêm lúc từng khung đồ hoạ hiện đủ, mở đầu và kết, để chắc mọi phần tử đã được nhìn
    times += [_full_moment(b) for b in d.get("beats", [])] + [min(1.2, d["hookSec"] - 0.3), d["duration"] - d["outroSec"] + 1.5]
    picked: list[float] = []
    for t in sorted(times):
        if 0 <= t < d["duration"] - 0.05 and all(abs(t - x) > 0.6 for x in picked):
            picked.append(round(t, 2))
    kd = prj.out / "kiem-tra"
    shutil.rmtree(kd, ignore_errors=True)
    kd.mkdir(parents=True)
    tiles = []
    for i, t in enumerate(picked, 1):
        p = kd / f"{i:02d}.jpg"
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", final, "-frames:v", "1", "-vf", "scale=-2:854", "-q:v", "3", p])
        scene, said = describe(d, t)
        tiles.append((f"kiem-tra/{p.name}", f"#{i} · {clock(t)} · {scene}", said))
    det = _detect(final)
    issues = []
    dur = d["duration"]
    for a, b in det["black"]:
        issues.append(f"Khung đen {clock(a)}–{clock(b)}")
    for a, b in det["freeze"]:
        if d.get("mode") != "faceless":
            issues.append(f"Hình đứng yên từ {clock(a)}" + (f" tới {clock(b)}" if b else " tới hết"))
    placeholder = prj.cfg.get("voice", {}).get("provider") == "placeholder"
    if not placeholder:
        for a, b in det["silence"]:
            if a < dur - d["outroSec"] - 0.5:
                issues.append(f"Không có tiếng {clock(a)}–{clock(b) if b else 'hết'} (quá 1,2 giây)")
    notes = [f"Ảnh lấy từ chính file {final.name}: {len(picked)} thời điểm (storyboard đã duyệt + lúc từng khung đồ hoạ hiện đủ)",
             "Dò tự động: " + ("; ".join(issues) if issues else "không thấy khung đen, hình đứng yên hay khoảng câm bất thường")]
    sheet = _sheet(prj.out / "kiem-tra.html", prj.out / "kiem-tra.jpg", f"Tự kiểm tra video cuối: {prj.cfg.get('name') or prj.slug}", notes, tiles, d["format"]["w"] < d["format"]["h"])
    res = {"frames": [{"t": t, "title": t1, "said": t2, "file": f"out/{s}"} for (s, t1, t2), t in zip(tiles, picked)], "issues": issues, "sheet": str(sheet)}
    write_json(prj.work / "qa.json", res)
    prj.mark("qa", fp)
    info(f"🔎 tự kiểm tra {len(picked)} khung hình trong {time.time() - t0:.0f}s → {sheet}")
    for x in issues:
        warn(x)
    info("  Mở out/kiem-tra.jpg (và ảnh lớn trong out/kiem-tra/) xem từng khung trước khi gửi người dùng.")
    if rules_text(prj.cfg):
        info("  Đối chiếu từng quy tắc riêng (in ở đầu lệnh) với các khung hình.")
    return res
