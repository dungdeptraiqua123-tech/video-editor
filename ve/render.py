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
    for name in ("src", "remotion.config.ts", "tsconfig.json", "stills.mjs"):
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


def stills(prj: Project, shots: list[tuple[float, Path]], scale: float = 0.5, props: Path | None = None) -> list[Path]:
    """Chụp nhiều khung trong một lần mở trình duyệt; lỗi thì chụp từng ảnh bằng `remotion still`."""
    b = bundle()
    d = read_json(_data(prj))
    fps, last = d["format"]["fps"], int(d["duration"] * d["format"]["fps"]) - 1
    jobs = [{"frame": max(0, min(int(round(t * fps)), last)), "output": str(Path(o).resolve())} for t, o in shots]
    with (contextlib.nullcontext(props) if props else _props(prj)) as pp:
        jp = prj.work / "stills.json"
        write_json(jp, jobs)
        exe = "" if remotion_browser_ready() else (find_browser() or "")
        n = os.cpu_count() or 2
        p = run(["node", ENGINE / "stills.mjs", b, pp, jp, scale, max(1, min(4, n - 1)), exe], cwd=ENGINE, quiet=True, check=False)
        if p.returncode != 0 or not all(Path(j["output"]).exists() for j in jobs):
            warn("Chụp gộp không chạy được, chụp từng ảnh (chậm hơn).")
            for t, o in shots:
                if not Path(o).exists():
                    still(prj, t, Path(o), scale=scale, props=pp)
    return [Path(o) for _, o in shots]


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
    from .storyboard import require_approval

    data = _data(prj)
    require_approval(prj, data)
    final = prj.out / f"{prj.slug}.mp4"
    fp = fingerprint(read_json(data), ENGINE_SRC / "src", prj.media, prj.cfg.get("render"))
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
    from .storyboard import qa

    srt, vtt, n = subs.write(d, prj.out / f"{prj.slug}")
    cover = still(prj, min(1.2, d["hookSec"] - 0.3), prj.out / "anh-bia.jpg")
    check = qa(prj, final)
    table = prj.out / "bang-quy-chieu.md"
    if (prj.work / "bang-quy-chieu.md").exists():
        shutil.copy2(prj.work / "bang-quy-chieu.md", table)
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
        f"| Đã cắt | " + (", ".join(f"{k} {v:.1f}s" for k, v in rs.items() if v > 0.05) or "không") + " |",
        f"| Âm lượng | {lo['lufs']} LUFS, đỉnh {lo['peak']} dBFS (chuẩn -14 LUFS) |",
        f"| Đồ hoạ | {len(d['beats'])} khung, {len(d['topics'])} thẻ chủ đề |",
        f"| Phụ đề | {n} dòng, kiểu {d['captions']['style']} |",
        f"| Đồng bộ | {'✓ khớp' if sync_ok and last_sub <= fi['duration'] + 0.05 else '✗ LỆCH, cần kiểm tra'} |",
        f"| Thời gian render | {st.get('render', {}).get('seconds', '?')}s |",
        f"| Nhịp, mật độ đồ hoạ | {(prj.cfg.get('style') or {}).get('pace', 'vua')}, {(prj.cfg.get('style') or {}).get('graphics', 'vua')} |",
        f"| Âm thanh hiệu ứng | {'tắt' if not d.get('sfx') else 'file thu thật: ' + ', '.join(f'{k} ({Path(v).name})' for k, v in d['sfx']['files'].items())} |",
        f"| Storyboard | duyệt lúc {st.get('approve', {}).get('at', '?')} |",
        "",
        "## Tự kiểm tra khung hình",
        "",
        f"- {len(check['frames'])} khung lấy từ chính file video, xem ở `kiem-tra.jpg` và thư mục `kiem-tra/`.",
        *([f"- ⚠ {x}" for x in check["issues"]] or ["- Dò tự động: không thấy khung đen, hình đứng yên hay khoảng câm bất thường."]),
        "",
    ]
    rules = [r for r in prj.cfg.get("rules") or [] if str(r).strip()]
    if rules:
        lines += ["## Quy tắc riêng của video này", "", "Đối chiếu với các khung trong `kiem-tra.jpg` trước khi giao.", ""] + [f"- [ ] {r}" for r in rules] + [""]
    if placeholder:
        lines += ["> ⚠ Video đang dùng **giọng tạm (im lặng)** để duyệt bố cục. Tạo giọng thật bằng `video-editor tts` trước khi đăng.", ""]
    sug = tl.get("suggestions", {})
    if sug.get("stumble"):
        lines += ["## Chỗ có thể nói vấp (chưa cắt)", ""] + [f"- \"{s['text']}\" lúc {s['start']}s" for s in sug["stumble"]] + [""]
    if chk.get("warnings"):
        lines += ["## Cảnh báo khi dựng", ""] + [f"- {w}" for w in chk["warnings"]] + [""]
    lines += ["## File giao", "", f"- `{final.name}`: video", f"- `{srt.name}`, `{vtt.name}`: phụ đề rời", f"- `{cover.name}`: ảnh bìa",
              "- `storyboard.jpg`: storyboard đã duyệt", "- `kiem-tra.jpg`: khung hình tự kiểm tra từ video cuối",
              "- `bang-quy-chieu.md`: lịch xuất hiện các phần tử và từng chữ kèm thời gian video", ""]
    rp = prj.out / "bao-cao.md"
    rp.write_text("\n".join(lines), encoding="utf-8")
    prj.mark("export", fingerprint(final))
    info(f"✓ xuất: {srt.name}, {vtt.name} ({n} dòng), {cover.name}, {table.name}, {rp.name}")
    return [final, srt, vtt, cover, table, rp, prj.out / "kiem-tra.jpg"]
