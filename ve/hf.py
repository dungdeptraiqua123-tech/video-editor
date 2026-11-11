"""Bộ dựng HyperFrames: thay Remotion ở bước chụp ảnh, render, mở trình chỉnh sửa. Các bước khác của skill giữ nguyên.

Cách ghép:
- Đồ hoạ: vẫn là mã React trong engine/src. engine-hf/ đóng gói nó cho HyperFrames (gói "remotion" được thay bằng
  engine-hf/shim/remotion.tsx), chạy kiểu "hosted": vẽ lại khung theo thời gian HyperFrames đưa vào (sự kiện hf-seek).
- Video và âm thanh: thẻ <video>/<audio class="clip"> thật trong index.html, nên HyperFrames tự lấy khung hình, trộn
  tiếng, và Studio hiện chúng thành các track sửa được. Lịch âm hiệu ứng và độ hạ nhạc nền chép đúng theo Video.tsx.
- Dự án HyperFrames sinh ở <dự án>/work/hf/ (index.html, ve/, assets → media/). Mở bằng `video-editor studio`.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from .env import HOME, IS_WIN, SKILL_DIR, VERSION, VEError, find_browser, info, load_config, read_json, run, warn, which, write_json

ENGINE_HF_SRC = SKILL_DIR / "engine-hf"
ENGINE_HF = HOME / f"engine-hf-{VERSION}"
NAMES = ("remotion", "hyperframes")
VIDEO_EXT = re.compile(r"\.(mp4|mov|webm|m4v)$", re.I)
# tắt thu thập số liệu, kiểm tra bản mới và tự cài skill của HyperFrames: skill này không gửi gì ra ngoài (AN-TOAN.md)
HF_ENV = {"HYPERFRAMES_NO_TELEMETRY": "1", "HYPERFRAMES_NO_UPDATE_CHECK": "1", "HYPERFRAMES_SKIP_SKILLS": "1", "DO_NOT_TRACK": "1"}


def pinned() -> str:
    return read_json(ENGINE_HF_SRC / "package.json")["dependencies"]["hyperframes"]


# ---------------------------------------------------------------- chọn bộ dựng

def engine_name(prj=None) -> str:
    """Bộ dựng của dự án: project.json "engine", rồi biến VE_ENGINE, rồi cấu hình chung (`setup --engine`), mặc định remotion."""
    for v in ((prj.cfg.get("engine") if prj is not None else None), os.environ.get("VE_ENGINE"), load_config().get("engine")):
        if v:
            v = str(v).strip().lower()
            if v in ("hf", "hyper", "hyperframe"):
                v = "hyperframes"
            if v not in NAMES:
                raise VEError(f"Bộ dựng \"{v}\" không có.", "Chọn \"remotion\" hoặc \"hyperframes\" (project.json \"engine\", hoặc `setup --engine`).")
            return v
    return "remotion"


def is_hf(prj=None) -> bool:
    return engine_name(prj) == "hyperframes"


# ---------------------------------------------------------------- cài đặt

def ready() -> bool:
    return (ENGINE_HF / "node_modules" / "hyperframes").exists() and (ENGINE_HF / "node_modules" / "esbuild").exists()


def _cli() -> list:
    """Lệnh HyperFrames đã ghim trong bộ dựng (không gọi npx, không tải bản khác)."""
    pkg = ENGINE_HF / "node_modules" / "hyperframes"
    bin_ = read_json(pkg / "package.json").get("bin")
    rel = bin_ if isinstance(bin_, str) else (bin_ or {}).get("hyperframes") or next(iter((bin_ or {}).values()), None)
    if not rel:
        raise VEError("Bộ dựng HyperFrames cài chưa đủ.", "Chạy `video-editor setup --engine hyperframes`.")
    return [which("node") or "node", str(pkg / rel)]


def hf(args: list, cwd: Path | None = None, quiet: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    return run([*_cli(), *args], cwd=cwd, quiet=quiet, check=check, env=HF_ENV)


def sync() -> None:
    """Chép mã đồ hoạ (engine/src) và phần riêng của HyperFrames (engine-hf/) vào bộ dựng đã cài."""
    from .project import fingerprint

    ENGINE_HF.mkdir(parents=True, exist_ok=True)
    pairs = [(SKILL_DIR / "engine" / "src", ENGINE_HF / "src"), (ENGINE_HF_SRC / "shim", ENGINE_HF / "shim")]
    for s, d in pairs:
        if d.exists() and fingerprint(s) == fingerprint(d):
            continue
        shutil.rmtree(d, ignore_errors=True)
        shutil.copytree(s, d)
    for name in ("entry.tsx", "build.mjs", "probe.mjs", "tsconfig.json"):
        s, d = ENGINE_HF_SRC / name, ENGINE_HF / name
        if not d.exists() or s.read_bytes() != d.read_bytes():
            shutil.copy2(s, d)


def install() -> None:
    info(f"▶ cài bộ dựng HyperFrames {pinned()}: {ENGINE_HF}")
    sync()
    for name in ("package.json", "package-lock.json"):
        if (ENGINE_HF_SRC / name).exists():
            shutil.copy2(ENGINE_HF_SRC / name, ENGINE_HF / name)
    npm = (which("npm.cmd") or which("npm")) if IS_WIN else which("npm")
    if not npm:
        raise VEError("Không tìm thấy npm.", "Cài Node.js 22 LTS từ nodejs.org rồi chạy lại.")
    lock = (ENGINE_HF / "package-lock.json").exists()
    run([npm, "ci" if lock else "install", "--no-audit", "--no-fund", "--loglevel=error"], cwd=ENGINE_HF, quiet=True, env=HF_ENV)
    hf(["telemetry", "disable"], cwd=ENGINE_HF, check=False)
    p = hf(["browser", "ensure"], cwd=ENGINE_HF, check=False)
    if p.returncode != 0:
        warn("HyperFrames chưa tải được Chrome để render: " + ((p.stderr or p.stdout or "").strip().splitlines() or ["?"])[-1])


def browser() -> str | None:
    """Chrome HyperFrames dùng (đã tải ở setup), hoặc trình duyệt tìm thấy trên máy."""
    if ready():
        p = hf(["browser", "path"], cwd=ENGINE_HF, check=False)
        cand = (p.stdout or "").strip().splitlines()
        if p.returncode == 0 and cand and Path(cand[-1].strip()).exists():
            return cand[-1].strip()
    return find_browser()


def require() -> None:
    if not ready():
        raise VEError("Bộ dựng HyperFrames chưa được cài.", "Chạy `video-editor setup --engine hyperframes` (một lần).")
    sync()


# ---------------------------------------------------------------- đóng gói đồ hoạ

def _stage_scenes(prj) -> Path | None:
    """Cảnh motion viết riêng của dự án: chép vào bộ dựng, sinh index.ts export SCENES (giống motion.stage của Remotion)."""
    from . import motion as MOTION
    import hashlib

    files = MOTION.scene_files(prj)
    if not files:
        return None
    errs = MOTION.check_scenes(prj)
    if errs:
        raise VEError("Cảnh motion viết riêng chưa hợp lệ:\n  - " + "\n  - ".join(errs), "Sửa các file trong motion/ rồi chạy lại.")
    d = ENGINE_HF / "du-an" / hashlib.sha1(str(prj.root).encode()).hexdigest()[:12]
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    for p in files.values():
        shutil.copy2(p, d / p.name)
    (d / "kit.ts").write_text(
        'export * from "../../src/motion/kit";\n'
        'export { M, rgba, shadow } from "../../src/motion/theme";\n'
        'export type { Scene, SceneProps, Safe } from "../../src/motion/registry";\n',
        encoding="utf-8",
    )
    names = list(files)
    idx = ['import type { Scene } from "../../src/motion/registry";']
    idx += [f'import S{i} from "./{n}";' for i, n in enumerate(names)]
    idx += ["", "// eslint-disable-next-line @typescript-eslint/no-explicit-any",
            "export const SCENES: Record<string, Scene<any>> = {" + ", ".join(f"{json.dumps(n)}: S{i}" for i, n in enumerate(names)) + "};", ""]
    (d / "index.ts").write_text("\n".join(idx), encoding="utf-8")
    (d / "tsconfig.json").write_text(json.dumps({
        "extends": "../../tsconfig.json",
        "compilerOptions": {"noUnusedLocals": False, "baseUrl": "../..", "paths": {"remotion": ["./shim/remotion.tsx"]}},
        "include": ["./*.ts", "./*.tsx", "../../src", "../../shim"],
        "exclude": ["../../src/Root.tsx", "../../src/index.ts"],
    }, indent=1), encoding="utf-8")
    return d


def typecheck(prj) -> list:
    """Kiểm tra kiểu cảnh viết riêng (như motion.typecheck, nhưng với lớp thay "remotion" của HyperFrames)."""
    from . import motion as MOTION

    if not MOTION.scene_files(prj):
        return []
    require()
    d = _stage_scenes(prj)
    tsc = ENGINE_HF / "node_modules" / "typescript" / "bin" / "tsc"
    r = run([which("node") or "node", tsc, "-p", d / "tsconfig.json", "--noEmit", "--pretty", "false"], cwd=ENGINE_HF, quiet=True, check=False)
    errs = []
    for line in ((r.stdout or "") + (r.stderr or "")).splitlines():
        m = MOTION._TSC_LINE.match(line.strip())
        if m:
            f = m.group("file").replace("\\", "/")
            if "/du-an/" in f or f.startswith("du-an/"):
                f = "motion/" + f.rsplit("/", 1)[-1]
            errs.append(f"{f}:{m.group('line')}: {m.group('msg')}")
    return errs[:30]


def bundle(prj) -> Path:
    """Gói đồ hoạ (ve.js, ve.css, phông chữ). Gói chung cho mọi dự án; dự án có cảnh motion riêng dùng gói riêng."""
    from . import motion as MOTION
    from .project import fingerprint

    require()
    own = bool(MOTION.scene_files(prj))
    out = prj.work / "hf-bundle" if own else ENGINE_HF / "build"
    fp = fingerprint(ENGINE_HF / "src", ENGINE_HF / "shim", ENGINE_HF / "entry.tsx", ENGINE_HF / "build.mjs", *( [MOTION.scene_dir(prj)] if own else []))
    stamp = out / ".fp"
    if stamp.exists() and stamp.read_text() == fp:
        return out
    scenes = _stage_scenes(prj) if own else None
    info("📦 đóng gói đồ hoạ cho HyperFrames …" if not own else f"📦 đóng gói đồ hoạ kèm {len(MOTION.scene_files(prj))} cảnh motion của dự án …")
    args = [which("node") or "node", ENGINE_HF / "build.mjs", out]
    if scenes:
        args.append(scenes / "index.ts")
    p = run(args, cwd=ENGINE_HF, quiet=True, check=False)
    if p.returncode != 0:
        raise VEError("Đóng gói đồ hoạ lỗi:\n" + ((p.stderr or "") + (p.stdout or "")).strip()[-1500:],
                      "Cảnh motion viết riêng lỗi thì sửa file trong motion/ (xem dòng lỗi). Lỗi khác: chạy lại `video-editor setup --engine hyperframes`.")
    stamp.write_text(fp)
    return out


# ---------------------------------------------------------------- lịch âm thanh và video (chép theo Video.tsx)

def _element_times(o) -> list:
    """Thời điểm (giây từ lúc khung mở) các phần tử trong khung đồ hoạ bật ra: mọi khoá d / xxxD (như elementTimes)."""
    if isinstance(o, list):
        return [x for v in o for x in _element_times(v)]
    if not isinstance(o, dict):
        return []
    out = []
    for k, v in o.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if k == "d" or re.search(r"[a-z]D$", k):
                out.append(float(v))
        else:
            out += _element_times(v)
    return out


def _speech_spans(words: list) -> list:
    out = []
    for w in words:
        if out and w["start"] - out[-1][1] < 0.45:
            out[-1][1] = max(out[-1][1], w["end"])
        else:
            out.append([w["start"], w["end"]])
    return out


def sfx_events(d: dict) -> list:
    """Âm hiệu ứng: (vai, giây bắt đầu, số khung, âm lượng). Đúng lịch và mức của Video.tsx."""
    sfx = d.get("sfx")
    if not sfx:
        return []
    files, sv, fps = sfx.get("files") or {}, float(sfx.get("volume", 1)), d["format"]["fps"]
    total = max(1, round(d["duration"] * fps))
    outro_from = total - round(d.get("outroSec", 0) * fps)
    faceless = d.get("mode") == "faceless" or not d["media"].get("hasVideo")
    ev = []

    def add(role, frame, frames, vol):
        if role in files and frame < total:
            ev.append((role, max(0, frame), min(frames, total - max(0, frame)), round(vol * sv, 4)))

    for b in d.get("beats", []):
        add("whoosh", max(0, round(b["start"] * fps) - 6), 24, 0.17)
        for x in _element_times(b["g"]):
            if x > 0.25:
                add("pop", round((b["start"] + x) * fps), 15, 0.22)
    if not faceless:
        for tp in d.get("topics", []):
            for it in tp.get("items", []):
                if it["at"] >= d.get("hookSec", 0) and it["at"] * fps < outro_from:
                    add("tick", round(it["at"] * fps), 15, 0.5)
    add("impact", 0, min(40, round(d.get("hookSec", 0) * fps)), 0.19)
    for pp in d.get("pops") or []:
        add("pop", round(pp["t"] * fps), 15, 0.2)
    for pu in d.get("punches") or []:
        add("impact", round(pu["t"] * fps), 30, 0.22)
    add("riser", max(0, outro_from - 30), 40, 0.21)
    add("click", outro_from + 30, 20, 0.41)
    return [(role, f / fps, n / fps, v) for role, f, n, v in ev if n > 0]


def music_lane(d: dict, clip_start: float, clip_end: float, limit: int = 500) -> list:
    """Đường âm lượng nhạc nền trong một đoạn nhạc (giây tính từ đầu đoạn): hạ khi có người nói, tăng/giảm dần ở đầu, cuối video."""
    m = d["media"]["music"]
    duck = float(m.get("duck", 0.35) if m.get("duck") is not None else 0.35)
    fade = float(m.get("fade", 1.5) if m.get("fade") is not None else 1.5)
    end = d["duration"]
    gap = 0.45
    while True:
        spans = []
        for a, b in _speech_spans(d.get("words", [])):
            if spans and a - spans[-1][1] < gap:
                spans[-1][1] = max(spans[-1][1], b)
            else:
                spans.append([a, b])

        def k(t):
            near = 9.0
            for a, b in spans:
                near = min(near, a - t if t < a else (t - b if t > b else 0.0))
            kk = duck if near <= 0 else (1.0 if near >= 0.25 else duck + (1 - duck) * near / 0.25)
            edge = min(1.0, t / max(0.01, fade), (end - t) / max(0.01, fade))
            return max(0.0, kk * edge)

        pts = {clip_start, clip_end}
        for a, b in spans:
            pts.update((a - 0.25, a, b, b + 0.25))
        for i in range(len(spans) - 1):
            pts.add((spans[i][1] + spans[i + 1][0]) / 2)
        n = 8
        pts.update(fade * j / n for j in range(n + 1))
        pts.update(end - fade * j / n for j in range(n + 1))
        ts = sorted(t for t in pts if clip_start <= t <= clip_end)
        if len(ts) <= limit or gap > 30:
            break
        gap *= 1.6  # quá nhiều điểm: gộp các quãng nói gần nhau
    return [{"t": round(t - clip_start, 3), "v": round(k(t), 4)} for t in ts][:limit]


def _media_dur(p: Path) -> float | None:
    try:
        from . import media as M

        return float(M.probe(p)["duration"])
    except Exception:  # noqa: BLE001
        return None


def _videos_in(o) -> list:
    if isinstance(o, str):
        return [o] if VIDEO_EXT.search(o) else []
    if isinstance(o, list):
        return [x for v in o for x in _videos_in(v)]
    if isinstance(o, dict):
        return [x for v in o.values() for x in _videos_in(v)]
    return []


def plan_media(prj, d: dict) -> tuple[list, list]:
    """Thẻ video và âm thanh cho index.html: [(id, src, start, dur, thuộc tính)], theo đúng Video.tsx."""
    fps = d["format"]["fps"]
    D = max(1, round(d["duration"] * fps)) / fps
    fr = lambda s: round(s * fps) / fps  # noqa: E731
    media = d["media"]
    faceless = d.get("mode") == "faceless" or not media.get("hasVideo")
    vids, auds = [], []
    if not faceless and media.get("main") and media.get("srcW") and media.get("srcH"):
        vids.append(("v-main", media["main"], 0.0, D, {"data-has-audio": "true"}))
    if faceless and media.get("main"):
        auds.append(("a-main", media["main"], 0.0, D, {"data-volume": "1"}))
    bg = media.get("background")
    if faceless and bg and VIDEO_EXT.search(bg["src"]):
        bd = max(1, int(bg["duration"] * fps)) / fps
        k = 0
        while k * bd < D - 1e-6:
            vids.append((f"v-nen-{k + 1}", bg["src"], k * bd, min(bd, D - k * bd), {"muted": ""}))
            k += 1
    for i, b in enumerate(d.get("beats", []), 1):
        s = fr(b["start"])
        dur = max(1, round((b["end"] - b["start"]) * fps)) / fps
        for j, src in enumerate(dict.fromkeys(_videos_in(b["g"])), 1):
            if (prj.media / src).exists():
                vids.append((f"v-khung{i}-{j}", src, s, min(dur, D - s), {"muted": ""}))
    for n, (role, t, dur, vol) in enumerate(sfx_events(d), 1):
        auds.append((f"sfx-{role}-{n}", d["sfx"]["files"][role], round(t, 4), round(dur, 4), {"data-volume": str(vol)}))
    m = media.get("music")
    if m:
        mlen = _media_dur(prj.media / m["src"])
        start = float(m.get("start") or 0)
        seg = (mlen - start) if mlen and mlen - start > 0.5 else D
        k, t = 0, 0.0
        while t < D - 1e-6:
            dur = min(seg, D - t)
            lane = music_lane(d, t, t + dur)
            auds.append((f"nhac-nen-{k + 1}", m["src"], round(t, 4), round(dur, 4), {
                "data-media-start": str(round(start, 4)),
                "data-volume": str(round(float(m.get("volume", 0.15)), 4)),
                "data-automation": json.dumps({"version": 1, "lanes": [{"target": "volume", "points": lane}]}, separators=(",", ":")),
            }))
            t += dur
            k += 1
    return vids, auds


# ---------------------------------------------------------------- dự án HyperFrames

def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def _src(p: str) -> str:
    from urllib.parse import quote

    return "assets/" + "/".join(quote(x) for x in p.split("/"))


def _link_assets(hfdir: Path, media: Path) -> None:
    a = hfdir / "assets"
    if a.is_symlink() or a.exists():
        try:
            if a.resolve() == media.resolve():
                return
        except OSError:
            pass
        if a.is_symlink() or a.is_file():
            a.unlink()
        else:
            shutil.rmtree(a)
    try:
        a.symlink_to(media.resolve(), target_is_directory=True)
    except OSError:
        if IS_WIN:
            r = subprocess.run(["cmd", "/c", "mklink", "/J", str(a), str(media.resolve())], capture_output=True)
            if r.returncode == 0:
                return
        # không tạo được liên kết: chép (tốn chỗ nhưng chạy được)
        shutil.copytree(media, a)


def project(prj) -> Path:
    """Sinh (hoặc cập nhật) dự án HyperFrames trong work/hf/. Trả về thư mục."""
    from .render import _data

    d = read_json(_data(prj))
    out = bundle(prj)
    hfdir = prj.work / "hf"
    (hfdir / "ve").mkdir(parents=True, exist_ok=True)
    for f in out.iterdir():
        if f.name.startswith("."):
            continue
        t = hfdir / "ve" / f.name
        if f.is_dir():
            shutil.rmtree(t, ignore_errors=True)
            shutil.copytree(f, t)
        elif not t.exists() or t.read_bytes() != f.read_bytes():
            shutil.copy2(f, t)
    _link_assets(hfdir, prj.media)
    props = dict(d)
    props["mediaBase"] = "assets/"
    props.pop("probe", None)
    write_json(hfdir / "ve" / "props.json", props, indent=None)
    (hfdir / "ve" / "props.js").write_text("window.__VE_PROPS = " + json.dumps(props, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    vids, auds = plan_media(prj, d)
    W, H, fps = d["format"]["w"], d["format"]["h"], d["format"]["fps"]
    # thời lượng đúng số khung như Remotion (làm tròn), không để HyperFrames làm tròn lên thêm một khung
    D = max(1, round(d["duration"] * fps)) / fps
    vids = [(i, s, st, min(du, D - st), a) for i, s, st, du, a in vids if st < D - 1e-6]
    auds = [(i, s, st, min(du, D - st), a) for i, s, st, du, a in auds if st < D - 1e-6]
    clips = [{"id": i, "src": _src(s), "start": st, "end": st + du} for i, s, st, du, _ in vids]
    (hfdir / "ve" / "clips.js").write_text("window.__VE_CLIPS = " + json.dumps(clips, ensure_ascii=False) + ";\n", encoding="utf-8")

    def attrs(a: dict) -> str:
        return "".join(f" {k}" if v == "" else f' {k}="{_esc(v)}"' for k, v in a.items())

    vtags = "\n".join(
        f'      <video id="{i}" class="clip" src="{_esc(_src(s))}" data-start="{st:g}" data-duration="{du:g}" data-track-index="{n}" playsinline{attrs(a)}></video>'
        for n, (i, s, st, du, a) in enumerate(vids))
    atags = "\n".join(
        f'    <audio id="{i}" class="clip" src="{_esc(_src(s))}" data-start="{st:g}" data-duration="{du:g}" data-track-index="{len(vids) + 2 + n}"{attrs(a)}></audio>'
        for n, (i, s, st, du, a) in enumerate(auds))
    title = _esc(str(prj.cfg.get("name") or prj.slug))
    html = f"""<!doctype html>
<!-- Sinh tự động bởi video-editor (bộ dựng HyperFrames) từ work/data.json. Sửa nội dung trong project.json rồi build lại;
     sửa ở đây (hoặc trong Studio) sẽ bị ghi đè ở lần build/preview/render sau. -->
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>{title}</title>
    <script src="ve/gsap.min.js"></script>
    <link rel="stylesheet" href="ve/ve.css" />
    <style>
      * {{ box-sizing: border-box; }}
      html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: #000; }}
      #root {{ position: relative; width: {W}px; height: {H}px; overflow: hidden; }}
      #ve-stage {{ position: absolute; inset: 0; }}
      #ve-park {{ position: absolute; left: 0; top: 0; width: 1px; height: 1px; overflow: hidden; opacity: 0; pointer-events: none; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{D:g}" data-width="{W}" data-height="{H}">
      <div id="ve-stage" class="clip" data-start="0" data-duration="{D:g}" data-track-index="{len(vids) + 1}" data-track-kind="graphics" data-layout-ignore></div>
      <div id="ve-park" data-layout-ignore>
{vtags}
      </div>
{atags}
    </div>
    <script src="ve/clips.js"></script>
    <script src="ve/props.js"></script>
    <script src="ve/ve.js"></script>
    <script>
      // đồ hoạ tự vẽ theo hf-seek (ve.js); timeline này chỉ báo thời lượng cho HyperFrames
      const tl = gsap.timeline({{ paused: true }});
      tl.set({{}}, {{}}, {D:g});
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    ix = hfdir / "index.html"
    if not ix.exists() or ix.read_text(encoding="utf-8") != html:
        ix.write_text(html, encoding="utf-8")
    if not (hfdir / "hyperframes.json").exists():
        write_json(hfdir / "hyperframes.json", {"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}, "media": {"autoProxy": True}})
    if not (hfdir / "meta.json").exists():
        write_json(hfdir / "meta.json", {"id": prj.slug, "name": prj.cfg.get("name") or prj.slug, "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    return hfdir


# ---------------------------------------------------------------- ảnh, đo bố cục, render

def stills(prj, shots: list, scale: float = 0.5, probe: Path | None = None) -> list:
    """Chụp nhiều ảnh trong một lần (`hyperframes snapshot --at`), thu nhỏ thành JPG; probe: đo bố cục từng ảnh."""
    hfdir = project(prj)
    d = read_json(hfdir / "ve" / "props.json")
    fps = d["format"]["fps"]
    last = max(0, round(d["duration"] * fps) - 1)
    snap = prj.work / "hf-snap"
    shutil.rmtree(snap, ignore_errors=True)
    times = [min(last, max(0, round(t * fps))) / fps for t, _ in shots]
    uniq = sorted(set(times))
    p = hf(["snapshot", str(hfdir), "--at", ",".join(f"{t:.4f}" for t in uniq), "--no-end", "--output", str(snap), "--json"], cwd=hfdir, check=False)
    pngs = {}
    try:
        j = json.loads((p.stdout or "").strip().splitlines()[-1]) if p.stdout and p.stdout.strip() else {}
    except ValueError:
        j = {}
    found = sorted(snap.glob("*.png")) if snap.exists() else []
    paths = [Path(x) if not isinstance(x, dict) else Path(x.get("path", "")) for x in (j.get("paths") or j.get("frames") or [])]
    paths = [x for x in paths if x.suffix == ".png" and x.exists()] or found
    for t, png in zip(uniq, sorted(paths, key=_snap_time)):
        pngs[round(t, 4)] = png
    if p.returncode != 0 or len(pngs) < len(uniq):
        raise VEError("Chụp ảnh bằng HyperFrames lỗi:\n" + ((p.stderr or "") + (p.stdout or "")).strip()[-1500:],
                      "Chạy `video-editor doctor`; nếu thiếu Chrome: `video-editor setup --engine hyperframes`.")
    W, H = d["format"]["w"], d["format"]["h"]
    for (t, o), tt in zip(shots, times):
        Path(o).parent.mkdir(parents=True, exist_ok=True)
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", pngs[round(tt, 4)], "-vf", f"scale={max(2, round(W * scale / 2) * 2)}:{max(2, round(H * scale / 2) * 2)}", "-q:v", "3", o])
    if probe:
        Path(probe).unlink(missing_ok=True)
        jobs = prj.work / "hf-probe-jobs.json"
        write_json(jobs, [{"t": tt, "output": str(Path(o).resolve())} for (_, o), tt in zip(shots, times)])
        exe = browser()
        if exe:
            r = run([which("node") or "node", ENGINE_HF / "probe.mjs", hfdir, jobs, probe, exe], cwd=ENGINE_HF, quiet=True, check=False)
            if r.returncode != 0:
                warn("Không đo được bố cục: " + ((r.stderr or r.stdout or "").strip().splitlines() or ["?"])[-1])
    return [Path(o) for _, o in shots]


def _snap_time(p: Path) -> float:
    m = re.search(r"(\d+(?:\.\d+)?)s", p.stem)
    return float(m.group(1)) if m else 0.0


def still(prj, sec: float, out: Path, scale: float = 1.0) -> Path:
    return stills(prj, [(sec, out)], scale=scale)[0]


def render_to(prj, out: Path, scale: float = 1.0, crf: int | None = None) -> None:
    """Render bằng HyperFrames (Chrome trên máy, cùng một file index.html với Studio)."""
    hfdir = project(prj)
    cfg = prj.cfg.get("render") or {}
    fps = read_json(hfdir / "ve" / "props.json")["format"]["fps"]
    # HyperFrames render đúng cỡ khung của index.html: bản nháp (scale < 1) vẫn đủ cỡ, chỉ nén mạnh hơn (crf cao)
    del scale
    args = ["render", str(hfdir), "--output", str(out), "--fps", str(fps), "--crf", str(crf or cfg.get("crf", 20))]
    if cfg.get("concurrency"):
        args += ["--workers", str(int(cfg["concurrency"]))]
    t0 = time.time()
    p = subprocess.Popen([*_cli(), *args], cwd=hfdir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         encoding="utf-8", errors="replace", env=dict(os.environ, **HF_ENV))
    tail, last = [], -10
    for line in p.stdout:
        tail = (tail + [line.rstrip()])[-30:]
        m = re.search(r"(\d{1,3}(?:\.\d+)?)%", line)
        if m:
            pct = int(float(m.group(1)))
            if pct >= last + 10:
                last = pct - pct % 10
                info(f"  {last:3d}%  ({time.time() - t0:.0f}s)")
    if p.wait() != 0 or not out.exists():
        raise VEError("Render HyperFrames lỗi.\n" + "\n".join(tail), "Xem các dòng trên. Chạy `video-editor doctor`; lỗi thường gặp ở huong-dan/loi-thuong-gap.md.")


def studio(prj, port: int | None = None, stop: bool = False) -> None:
    """Mở HyperFrames Studio trên dự án đã sinh (xem, tua, chỉnh thử). Studio chạy nền; `studio --stop` để tắt."""
    hfdir = prj.work / "hf"
    if stop:
        subprocess.run([*_cli(), "preview", str(hfdir), "--stop"], cwd=prj.work, env=dict(os.environ, **HF_ENV))
        return
    hfdir = project(prj)
    info(f"🎛 mở HyperFrames Studio cho {hfdir}")
    info("  Đây là bản sinh từ project.json: xem, tua, chỉnh thử thoải mái. Muốn giữ thay đổi thì ghi vào project.json rồi build lại,")
    info(f"  vì build/preview/render sau sẽ sinh lại index.html. Tắt Studio: video-editor studio {prj.root} --stop")
    args = [*_cli(), "preview", str(hfdir)]
    if port:
        args += ["--port", str(port)]
    subprocess.run(args, cwd=hfdir, env=dict(os.environ, **HF_ENV))
