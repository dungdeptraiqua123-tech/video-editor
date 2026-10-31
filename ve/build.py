"""Bước dựng dữ liệu: sửa lời → cắt (lặng, từ đệm, vấp, đoạn bỏ) → dò mốc đồ hoạ → kiểm tra → work/data.json."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from . import media as M
from .content import resolve_content
from .env import ENGINE_SRC, TEMPLATES, VEError, info, read_json, warn, write_json
from . import bang
from .project import GRAPHICS_EVERY, Project, _merge, cut_settings, fingerprint, pace_of
from .timeline import CutConfig, apply_fixes, build_timeline, words_from_transcript


def source_file(prj: Project) -> Path:
    """File âm thanh/video chính: video người nói, hoặc giọng đọc đã tạo từ kịch bản."""
    if prj.cfg.get("script"):
        for name in ("voice.mp3", "voice.m4a"):
            if (prj.work / name).exists():
                return prj.work / name
        raise VEError("Chưa có giọng đọc cho kịch bản.", f"Chạy `video-editor tts {prj.root}` trước.")
    p = prj.path(prj.cfg.get("input"))
    if not p:
        raise VEError("project.json chưa có input hoặc script.")
    return p


def _place(prj: Project, src: str, sub: str) -> str:
    """Đưa file ngoài vào media/ (liên kết cứng nếu được, không thì chép). Trả đường dẫn tương đối trong media/."""
    p = prj.path(src)
    if p is None or not p.exists():
        cand = prj.media / src
        if cand.exists():
            return src.replace("\\", "/")
        raise VEError(f"Không thấy file {src}.", "Đường dẫn tính từ thư mục dự án, hoặc ghi đường dẫn tuyệt đối.")
    try:
        p.relative_to(prj.media)
        return str(p.relative_to(prj.media)).replace("\\", "/")
    except ValueError:
        pass
    dst = prj.media / sub / p.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists() or dst.stat().st_size != p.stat().st_size:
        if dst.exists():
            dst.unlink()
        try:
            os.link(p, dst)
        except OSError:
            shutil.copy2(p, dst)
    return f"{sub}/{p.name}"


def brand_for(prj: Project) -> tuple[dict, dict]:
    tdir = TEMPLATES / prj.cfg["template"]
    if not (tdir / "brand.json").exists():
        raise VEError(f"Không có mẫu \"{prj.cfg['template']}\".", "Xem các mẫu: `video-editor templates`.")
    base = read_json(tdir / "brand.json")
    b = _merge(base, prj.cfg.get("brand") or {})
    cap_tpl = b.pop("captions", {})
    for key in ("logo",):
        if b.get(key):
            src = b[key] if Path(b[key]).is_absolute() or (prj.root / b[key]).exists() else str(tdir / b[key])
            b[key] = _place(prj, src, "brand")
    if b.get("font", {}).get("file"):
        f = b["font"]["file"]
        src = f if Path(f).is_absolute() or (prj.root / f).exists() else str(tdir / f)
        b["font"]["file"] = _place(prj, src, "brand")
    return b, cap_tpl


SFX_ROLES = ("whoosh", "impact", "riser", "click", "pop", "tick")


def sfx_for(prj: Project, place: bool = True):
    """Âm thanh hiệu ứng: file thu thật trong engine/public/sfx (Mixkit), hoặc file riêng của người dùng. Không tạo âm bằng code."""
    s = prj.cfg.get("sfx", True)
    if s is False or (isinstance(s, dict) and s.get("enabled") is False):
        return False
    s = s if isinstance(s, dict) else {}
    own = s.get("files") or {}
    bad = [k for k in own if k not in SFX_ROLES]
    if bad:
        raise VEError(f"sfx.files có khoá lạ: {', '.join(bad)}.", f"Dùng các khoá: {', '.join(SFX_ROLES)}.")
    files = {}
    for role in SFX_ROLES:
        f = own.get(role)
        if f is False or f == "":
            continue  # tắt riêng âm này
        if f:
            files[role] = _place(prj, f, "sfx-rieng") if place else f
        else:
            src = ENGINE_SRC / "public" / "sfx" / f"{role}.mp3"
            files[role] = _place(prj, str(src), "sfx") if place else f"sfx/{src.name}"
    return {"files": files, "volume": float(s.get("volume", 1.0))}


def build(prj: Project, force: bool = False, check_only: bool = False) -> dict:
    cfg = prj.cfg
    tpath = prj.work / "transcript.json"
    if not tpath.exists():
        step = "tts" if cfg.get("script") else "transcribe"
        raise VEError("Chưa có lời thoại (work/transcript.json).", f"Chạy `video-editor {step} {prj.root}` trước.")
    src = source_file(prj)
    pinfo = M.probe(src)
    words = apply_fixes(words_from_transcript(read_json(tpath), cfg.get("dropSegments")), cfg.get("fix", []))
    if not words:
        raise VEError("Lời thoại rỗng: không có từ nào để dựng.", "Kiểm tra file nguồn có tiếng nói, hoặc ngôn ngữ trong whisper.language.")
    try:
        tl = build_timeline(words, pinfo["duration"], CutConfig.from_dict(cut_settings(cfg)))
    except ValueError as e:
        raise VEError(str(e))

    W, H = prj.size
    faceless = prj.faceless
    has_video = pinfo["has_video"] and not faceless
    main = "cut.mp4" if has_video else "cut.m4a"

    # cắt file nguồn (bước nặng nhất của build, chỉ làm lại khi đầu vào hoặc đoạn giữ đổi)
    cut_fp = fingerprint(src, tl.segments, has_video)
    if not check_only:
        if force or not prj.fresh("cut", cut_fp) or not (prj.media / main).exists():
            info(f"✂ cắt {len(tl.segments)} đoạn, giữ {tl.duration:.1f}s / {pinfo['duration']:.1f}s …")
            M.cut(src, tl.segments, prj.media / main, has_video)
            prj.mark("cut", cut_fp)
        else:
            info("✂ bản cắt còn mới, dùng lại")
    duration = round(tl.duration, 3)

    # nội dung: đưa ảnh/clip sản phẩm vào media/
    content = dict(cfg.get("content") or {})
    missing = []
    beats = []
    for b in content.get("beats", []):
        b = dict(b)
        g = dict(b.get("g") or {})
        if g.get("type") == "media" and g.get("src"):
            try:
                g["src"] = _place(prj, g["src"], "assets")
            except VEError:
                missing.append(g["src"])
        b["g"] = g
        beats.append(b)
    content["beats"] = beats
    data, rep = resolve_content(content, tl.words, duration, tl, "faceless" if faceless else "talking", media_ok=lambda p: p not in missing,
                                zoom_every=pace_of(cfg)["zoomEvery"])

    brand, cap_tpl = brand_for(prj)
    cap = _merge({"enabled": True, "style": "glow", "position": None, "keywords": [], "maxChars": None, "maxWords": 8, "size": 1}, cap_tpl)
    cap = _merge(cap, cfg.get("captions") or {})
    cap["keywords"] = list(dict.fromkeys((cap_tpl.get("keywords") or []) + ((cfg.get("captions") or {}).get("keywords") or [])))
    if not cap.get("maxChars"):
        cap["maxChars"] = 44 if W / H > 1.3 else 30
    if cap["style"] not in ("glow", "box", "pop", "plain"):
        rep.err("captions.style", f"\"{cap['style']}\" không có. Chọn glow, box, pop hoặc plain")

    m = {"main": main, "hasVideo": has_video}
    if has_video:
        m.update(srcW=pinfo["width"], srcH=pinfo["height"], face=cfg.get("face") or {"x": 0.5, "y": 0.4})
    if cfg.get("background") and faceless:
        bp = prj.path(cfg["background"])
        bi = M.probe(bp) if bp and bp.suffix.lower() in M.VIDEO_EXT else {"duration": 9999}
        m["background"] = {"src": _place(prj, cfg["background"], "assets"), "duration": bi["duration"]}
    if cfg.get("music"):
        mu = cfg["music"] if isinstance(cfg["music"], dict) else {"file": cfg["music"]}
        m["music"] = {"src": _place(prj, mu["file"], "assets"), "volume": float(mu.get("volume", 0.08))}

    sfx = sfx_for(prj, place=not check_only)

    props = {
        "format": {"w": W, "h": H, "fps": int(cfg.get("fps", 30))},
        "duration": duration,
        "mode": "faceless" if faceless else "talking",
        "brand": brand,
        "captions": cap,
        "media": m,
        "sfx": sfx,
        "words": tl.words,
        **data,
        "ctaButtons": content.get("ctaButtons") or ["Theo dõi", "Thích", "Chia sẻ"],
    }
    removed_sec = {
        "khoảng lặng": round(pinfo["duration"] - tl.duration - sum(w["end"] - w["start"] for k in ("filler", "stumble", "drop") for w in tl.removed[k]), 2),
        "từ đệm": round(sum(w["end"] - w["start"] for w in tl.removed["filler"]), 2),
        "nói vấp": round(sum(w["end"] - w["start"] for w in tl.removed["stumble"]), 2),
        "đoạn bỏ": round(sum(w["end"] - w["start"] for w in tl.removed["drop"]), 2),
    }
    write_json(prj.work / "timeline.json", {"source": str(src), "sourceDuration": pinfo["duration"], "duration": duration, "segments": tl.segments, "removed": tl.removed, "removedSeconds": removed_sec, "suggestions": tl.suggestions})
    write_json(prj.work / "check.json", {"errors": rep.errors, "warnings": rep.warnings})

    for w_ in rep.warnings:
        warn(w_)
    dens = (cfg.get("style") or {}).get("graphics") or "vua"
    if dens in GRAPHICS_EVERY and duration > 20:
        want = max(1, round((duration - data["hookSec"] - data["outroSec"]) / GRAPHICS_EVERY[dens]))
        info(f"🎨 {len(data['beats'])} khung đồ hoạ / {duration:.0f}s; mật độ \"{dens}\" gợi ý khoảng {want} khung")
    bang.write(prj.work / "bang-quy-chieu.md", cfg["name"], words, tl, rep.events, cut_settings(cfg).get("keep"))
    if tl.suggestions["stumble"]:
        info(f"💡 {len(tl.suggestions['stumble'])} chỗ có thể là nói vấp (chưa cắt): " + "; ".join(f"\"{s['text']}\" @{s['start']}s" for s in tl.suggestions["stumble"][:6]))
        info("   Cắt hết: đặt cuts.stumbles = \"auto\". Cắt từng chỗ: thêm [giây đầu, giây cuối] vào cuts.drop.")
    if rep.errors:
        raise VEError("Nội dung chưa hợp lệ:\n  - " + "\n  - ".join(rep.errors), "Sửa project.json theo từng dòng trên rồi chạy lại `video-editor build`.")
    if not check_only:
        write_json(prj.work / "data.json", props, indent=None)
        prj.mark("build", fingerprint(read_json(prj.file), prj.media / main, tpath), duration=duration)
    info(f"✓ dữ liệu hợp lệ: {duration:.1f}s, {len(data['beats'])} khung đồ hoạ, {len(tl.words)} từ phụ đề" + (" (chỉ kiểm tra, chưa ghi)" if check_only else ""))
    return props


def write_transcript_text(prj: Project) -> Path:
    """Lời thoại dễ đọc kèm giây (theo file gốc) để viết nội dung đồ hoạ và tìm cụm từ neo."""
    segs = read_json(prj.work / "transcript.json")
    lines = []
    for s in segs:
        low = [w for w in s.get("words", []) if float(w.get("p", 1)) < 0.5]
        flag = f"   ⟵ nghe chưa chắc: {', '.join(w['w'].strip() for w in low[:5])}" if low else ""
        lines.append(f"[{s['start']:7.2f} – {s['end']:7.2f}] {s['text'].strip()}{flag}")
    out = prj.work / "loi-thoai.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    words = apply_fixes(words_from_transcript(segs, prj.cfg.get("dropSegments")), prj.cfg.get("fix", []))
    bang.write(prj.work / "bang-quy-chieu.md", prj.cfg["name"], words)
    return out
