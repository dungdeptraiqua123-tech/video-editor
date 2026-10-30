"""Xem trước, render, xuất file giao. Gọi Remotion trong bộ dựng đã cài (~/.video-editor/engine-<phiên bản>)."""
from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

from . import media as M
from . import subs
from .env import ENGINE, ENGINE_SRC, VEError, find_browser, info, npx, read_json, remotion_browser_ready, run, warn
from .project import Project, fingerprint
from .serve import media_server
from .env import write_json
import contextlib


def engine_ready() -> None:
    if not (ENGINE / "node_modules" / "remotion").exists():
        raise VEError("Bộ dựng chưa được cài.", "Chạy `video-editor setup` (một lần).")
    # đồng bộ mã nguồn bộ dựng từ skill sang bản đã cài (nhanh, chỉ vài file)
    for name in ("src", "remotion.config.ts", "tsconfig.json"):
        s, d = ENGINE_SRC / name, ENGINE / name
        if s.is_dir():
            if d.exists() and fingerprint(s) == fingerprint(d):
                continue
            shutil.rmtree(d, ignore_errors=True)
            shutil.copytree(s, d)
        elif not d.exists() or s.read_bytes() != d.read_bytes():
            shutil.copy2(s, d)


def _browser_args() -> list:
    if remotion_browser_ready():
        return []
    b = find_browser()
    return [f"--browser-executable={b}"] if b else []


def bundle() -> Path:
    """Đóng gói bộ dựng một lần, dùng lại cho mọi ảnh xem trước và lần render (đỡ 10–20 giây mỗi lệnh)."""
    engine_ready()
    out = ENGINE / "build"
    fp = fingerprint(ENGINE / "src", ENGINE / "remotion.config.ts")
    stamp = out / ".fp"
    if stamp.exists() and stamp.read_text() == fp:
        return out
    info("📦 đóng gói bộ dựng …")
    run([npx(), "remotion", "bundle", "src/index.ts", "--out-dir", out, "--log", "error"], cwd=ENGINE, quiet=True)
    stamp.write_text(fp)
    return out


def _data(prj: Project) -> Path:
    p = prj.work / "data.json"
    if not p.exists():
        raise VEError("Chưa có dữ liệu dựng.", f"Chạy `video-editor build {prj.root}` trước.")
    return p


@contextlib.contextmanager
def _props(prj: Project):
    """Dữ liệu render kèm địa chỉ máy chủ media tạm thời."""
    with media_server(prj.media) as base:
        d = read_json(_data(prj))
        d["mediaBase"] = base
        p = prj.work / "props-render.json"
        write_json(p, d, indent=None)
        yield p


def still(prj: Project, sec: float, out: Path, scale: float = 1.0, props: Path | None = None) -> Path:
    b = bundle()
    d = read_json(_data(prj))
    frame = max(0, min(int(round(sec * d["format"]["fps"])), int(d["duration"] * d["format"]["fps"]) - 1))
    with (contextlib.nullcontext(props) if props else _props(prj)) as pp:
        run([npx(), "remotion", "still", b, "Video", out, f"--frame={frame}", f"--props={pp}", f"--scale={scale}", "--log=error", *_browser_args()], cwd=ENGINE, quiet=True)
    return out


def key_moments(d: dict, limit: int = 16) -> list[tuple[float, str]]:
    """Các khoảnh khắc nên xem: mở đầu, mỗi khung đồ hoạ khi đã hiện đủ phần tử, thẻ chủ đề, phần kết."""
    ts = [(min(1.2, d["hookSec"] - 0.3), "mo-dau")]
    for i, b in enumerate(d["beats"]):
        ds = [v for k, v in _walk(b["g"]) if k == "d" or k.endswith("D")]
        t = b["start"] + (max(ds) + 0.7 if ds else 1.2)
        ts.append((min(t, b["end"] - 0.3), f"do-hoa-{i + 1}"))
    for i, tp in enumerate(d["topics"]):
        last = max([it["at"] for it in tp["items"]] or [tp["start"]])
        ts.append((min(last + 0.6, tp["end"] - 0.2), f"chu-de-{i + 1}"))
    ts.append((d["duration"] - d["outroSec"] + 1.5, "ket"))
    seen, out = set(), []
    for t, n in sorted(ts):
        k = round(t, 1)
        if n.startswith("chu-de") and t < d["hookSec"]:
            continue  # thẻ chủ đề bị thẻ mở đầu che
        if k not in seen and 0 <= t < d["duration"]:
            seen.add(k)
            out.append((t, n))
    if len(out) > limit:  # rải đều, luôn giữ mở đầu và kết
        idx = sorted({round(i * (len(out) - 1) / (limit - 1)) for i in range(limit)})
        out = [out[i] for i in idx]
    return out


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


def preview(prj: Project, draft: bool = False) -> list[Path]:
    d = read_json(_data(prj))
    pv = prj.out / "xem-truoc"
    shutil.rmtree(pv, ignore_errors=True)
    pv.mkdir(parents=True)
    shots = []
    t0 = time.time()
    moments = key_moments(d)
    with _props(prj) as pp:
        for t, name in moments:
            p = pv / f"{len(shots) + 1:02d}-{name}-{t:05.1f}s.jpg"
            still(prj, t, p, scale=0.5, props=pp)
            shots.append(p)
            info(f"  🖼 {p.name}")
    sheet = prj.out / "xem-truoc.jpg"
    cols = 4 if d["format"]["w"] < d["format"]["h"] else 3
    rows = (len(shots) + cols - 1) // cols
    run(["ffmpeg", "-y", "-loglevel", "error", "-pattern_type", "glob", "-i", str(pv / "*.jpg"), "-vf", f"scale=-1:480,tile={cols}x{rows}:padding=8:color=black", "-frames:v", "1", sheet] if os.name != "nt" else
        ["ffmpeg", "-y", "-loglevel", "error", *sum([["-i", s] for s in shots], []), "-filter_complex", "".join(f"[{i}]scale=-1:480[s{i}];" for i in range(len(shots))) + "".join(f"[s{i}]" for i in range(len(shots))) + f"hstack=inputs={len(shots)}", sheet], check=False)
    info(f"✓ {len(shots)} ảnh xem trước trong {time.time() - t0:.0f}s → {sheet}")
    out = [sheet, *shots]
    if draft:
        p = prj.out / "ban-nhap.mp4"
        info("🎞 render bản nháp nửa độ phân giải …")
        _render(prj, p, scale=0.5, crf=30)
        out.append(p)
        info(f"✓ bản nháp → {p}")
    return out


def _render(prj: Project, out: Path, scale: float = 1.0, crf: int | None = None) -> None:
    b = bundle()
    cfg = prj.cfg.get("render") or {}
    with _props(prj) as pp:
        args = [npx(), "remotion", "render", b, "Video", out, f"--props={pp}", f"--crf={crf or cfg.get('crf', 20)}", "--audio-bitrate=192k", f"--scale={scale}", *_browser_args()]
        # Remotion mặc định chỉ dùng nửa số nhân; dùng gần hết nhân nhanh hơn ~25% (đo trên máy 4 nhân)
        n = os.cpu_count() or 2
        args.append(f"--concurrency={cfg.get('concurrency') or (n if n <= 4 else min(16, n - 1))}")
        _run_progress(args)


def _run_progress(args: list) -> None:
    """Chạy render, chỉ in tiến độ mỗi 10% (log gốc của Remotion in từng khung, quá dài)."""
    import re
    import subprocess

    p = subprocess.Popen([str(a) for a in args], cwd=ENGINE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    last, tail, t0 = -10, [], time.time()
    for line in p.stdout:
        tail = (tail + [line.rstrip()])[-25:]
        m = re.search(r"Rendered (\d+)/(\d+)", line)
        if m:
            pct = int(m.group(1)) * 100 // max(1, int(m.group(2)))
            if pct >= last + 10:
                last = pct - pct % 10
                info(f"  {last:3d}%  ({time.time() - t0:.0f}s)")
    if p.wait() != 0:
        raise VEError("Render lỗi.\n" + "\n".join(tail), "Xem các dòng trên. Lỗi thường gặp ở huong-dan/loi-thuong-gap.md.")


def render(prj: Project, force: bool = False) -> Path:
    data = _data(prj)
    final = prj.out / f"{prj.slug}.mp4"
    fp = fingerprint(data, ENGINE_SRC / "src", prj.media, prj.cfg.get("render"))
    if not force and prj.fresh("render", fp) and final.exists():
        info(f"✓ video còn mới, bỏ qua render: {final}")
        return final
    raw = prj.work / "render.mp4"
    t0 = time.time()
    info(f"🎬 render {read_json(data)['duration']:.0f}s video …")
    _render(prj, raw)
    # chỉ chuyển vùng chứa và bật faststart, không nén lại lần hai
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-c", "copy", "-movflags", "+faststart", final])
    raw.unlink(missing_ok=True)
    took = time.time() - t0
    prj.mark("render", fp, seconds=round(took))
    info(f"✓ render xong sau {took / 60:.1f} phút → {final}")
    return final


def export(prj: Project) -> list[Path]:
    d = read_json(_data(prj))
    final = prj.out / f"{prj.slug}.mp4"
    if not final.exists():
        raise VEError("Chưa có video.", f"Chạy `video-editor render {prj.root}` trước.")
    srt, vtt, n = subs.write(d, prj.out / f"{prj.slug}")
    cover = still(prj, min(1.2, d["hookSec"] - 0.3), prj.out / "anh-bia.jpg")
    fi = M.probe(final)
    lo = M.loudness(final)
    tl = read_json(prj.work / "timeline.json")
    chk = read_json(prj.work / "check.json") if (prj.work / "check.json").exists() else {"warnings": []}
    st = prj.state()

    # kiểm tra đồng bộ: video ra đúng thời lượng dữ liệu, phụ đề không vượt video
    fps = d["format"]["fps"]
    sync_ok = abs(fi["duration"] - d["duration"]) <= 2 / fps + 0.05
    last_sub = max((w["end"] for w in d["words"]), default=0)
    if not sync_ok:
        warn(f"Thời lượng video {fi['duration']:.2f}s lệch dữ liệu {d['duration']:.2f}s")
    placeholder = (prj.work / "voice.m4a").exists() and prj.cfg.get("voice", {}).get("provider") == "placeholder"

    rs = tl.get("removedSeconds", {})
    lines = [
        f"# Báo cáo: {prj.cfg.get('name') or prj.slug}",
        "",
        "| Mục | Giá trị |",
        "|---|---|",
        f"| File | `{final.name}` ({final.stat().st_size / 1e6:.1f} MB) |",
        f"| Khổ hình | {prj.cfg['format']} ({fi.get('width')}×{fi.get('height')}, {fps} fps) |",
        f"| Thời lượng | {fi['duration']:.1f}s (nguồn {tl['sourceDuration']:.1f}s, đã cắt {tl['sourceDuration'] - tl['duration']:.1f}s) |",
        f"| Đã cắt | " + ", ".join(f"{k} {v:.1f}s" for k, v in rs.items() if v > 0.05) + " |",
        f"| Âm lượng | {lo['lufs']} LUFS, đỉnh {lo['peak']} dBFS (chuẩn -14 LUFS) |",
        f"| Đồ hoạ | {len(d['beats'])} khung, {len(d['topics'])} thẻ chủ đề |",
        f"| Phụ đề | {n} dòng, kiểu {d['captions']['style']} |",
        f"| Đồng bộ | {'✓ khớp' if sync_ok and last_sub <= fi['duration'] + 0.05 else '✗ LỆCH, cần kiểm tra'} |",
        f"| Thời gian render | {st.get('render', {}).get('seconds', '?')}s |",
        "",
    ]
    if placeholder:
        lines += ["> ⚠ Video đang dùng **giọng tạm (im lặng)** để duyệt bố cục. Tạo giọng thật bằng `video-editor tts` trước khi đăng.", ""]
    sug = tl.get("suggestions", {})
    if sug.get("stumble"):
        lines += ["## Chỗ có thể nói vấp (chưa cắt)", ""] + [f"- \"{s['text']}\" lúc {s['start']}s" for s in sug["stumble"]] + [""]
    if chk.get("warnings"):
        lines += ["## Cảnh báo khi dựng", ""] + [f"- {w}" for w in chk["warnings"]] + [""]
    lines += ["## File giao", "", f"- `{final.name}`: video", f"- `{srt.name}`, `{vtt.name}`: phụ đề rời", f"- `{cover.name}`: ảnh bìa", "- `xem-truoc.jpg`: ảnh các khoảnh khắc chính (nếu đã chạy preview)", ""]
    rp = prj.out / "bao-cao.md"
    rp.write_text("\n".join(lines), encoding="utf-8")
    prj.mark("export", fingerprint(final))
    info(f"✓ xuất: {srt.name}, {vtt.name} ({n} dòng), {cover.name}, {rp.name}")
    return [final, srt, vtt, cover, rp]
