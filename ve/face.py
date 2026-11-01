"""Tự bám mặt người nói khi khổ ra khác khổ gốc (16:9 → 9:16): dò mặt 4 lần mỗi giây trên bản cắt,
làm mượt trong từng đoạn giữ (không trôi qua chỗ cắt nhảy), xuất đường đi của tâm khung cho bộ dựng.

Bộ dò chạy trong môi trường Python riêng (OpenCV, bộ dò Haar có sẵn trong gói). Không thấy mặt đủ nhiều thì giữ khung cố định.
"""
from __future__ import annotations

import statistics as st
from pathlib import Path

from .env import SKILL_DIR, info, read_json, run, venv_python, warn, write_json
from .project import Project, fingerprint

VERSION = 2
MIN_COVERAGE = 0.5


def wanted(cfg: dict, src_w: int, src_h: int, out_w: int, out_h: int) -> bool:
    """face.track: "auto" (mặc định) bám mặt khi khung gốc rộng hơn khổ ra quá 5% (16:9 → 9:16, 1:1, 4:5); true luôn bám; false tắt.

    Khung gốc hẹp hơn khổ ra (quay dọc mà xuất 16:9) thì không cắt: phủ kín sẽ phóng to gấp ba, nên giữ trọn khung như cũ.
    """
    ft = (cfg.get("face") or {}).get("track", "auto")
    if ft in (False, "off", "tat"):
        return False
    if ft in (True, "on", "bat"):
        return True
    return (src_w / src_h) / (out_w / out_h) > 1.05


def boundaries(segments: list) -> list[float]:
    """Mốc nối giữa các đoạn giữ, tính theo thời gian bản cắt."""
    out, t = [], 0.0
    for a, b in segments[:-1]:
        t += b - a
        out.append(round(t, 3))
    return out


def _median_filter(xs: list, k: int = 5) -> list:
    h = k // 2
    return [st.median(xs[max(0, i - h):i + h + 1]) for i in range(len(xs))]


def _ema2(xs: list, a: float) -> list:
    """Làm mượt hai chiều (xuôi rồi ngược) để không trễ pha."""
    if not xs:
        return xs
    f = [xs[0]]
    for x in xs[1:]:
        f.append(f[-1] + a * (x - f[-1]))
    b = [f[-1]]
    for x in reversed(f[:-1]):
        b.append(b[-1] + a * (x - b[-1]))
    return b[::-1]


def _deadzone(xs: list, dz: float) -> list:
    """Khung đứng yên khi mặt chỉ xê dịch nhỏ; ra khỏi vùng chết thì đi theo (liền mạch, không giật)."""
    if not xs:
        return xs
    c, out = xs[0], []
    for x in xs:
        d = x - c
        if abs(d) > dz:
            c += d - dz if d > 0 else d + dz
        out.append(c)
    return out


def _pick(boxes: list, prev: tuple | None) -> list | None:
    if not boxes:
        return None
    if prev is None:
        return max(boxes, key=lambda b: b[2] * b[3])
    # bám người đang theo: gần tâm trước nhất, ưu tiên mặt lớn
    return min(boxes, key=lambda b: ((b[0] + b[2] / 2 - prev[0]) ** 2 + (b[1] + b[3] * 0.4 - prev[1]) ** 2) ** 0.5 - 0.5 * b[2])


def smooth(samples: list, cuts: list[float], fps: float) -> dict:
    """samples: [[t, [[x, y, w, h], ...]], ...] theo thời gian bản cắt. Trả đường đi [[t, x, y], ...] và độ phủ."""
    if not samples:
        return {"coverage": 0.0, "track": [], "median": None}
    edges = [0.0, *cuts, samples[-1][0] + 1.0]
    track, hits, allpts = [], 0, []
    last = None
    for s0, s1 in zip(edges, edges[1:]):
        seg = [x for x in samples if s0 - 1e-6 <= x[0] < s1 - 1e-6]
        if not seg:
            continue
        pts, prev = [], None
        sizes = sorted(b[3] for _, bs in seg for b in bs)
        med_h = sizes[len(sizes) // 2] if sizes else None
        for t, boxes in seg:
            # bỏ khung dò nhầm: cỡ mặt khác hẳn cỡ thường gặp trong đoạn
            boxes = [b for b in boxes if med_h is None or 0.5 * med_h <= b[3] <= 2 * med_h]
            b = _pick(boxes, prev)
            if b:
                prev = (b[0] + b[2] / 2, b[1] + b[3] * 0.4)
                pts.append(prev)
                hits += 1
            else:
                pts.append(None)
        if not any(pts):
            fill = last or (0.5, 0.4)
            pts = [fill] * len(pts)
        else:
            # lấp chỗ không thấy mặt bằng vị trí gần nhất
            first = next(p for p in pts if p)
            cur = first
            for i, p in enumerate(pts):
                cur = p or cur
                pts[i] = cur
        # vùng chết 0,02 bề ngang: đứng yên không rung, đi theo kịp (đo trên clip thử: lệch trung bình 0,012, tối đa 0,063)
        xs = _deadzone(_ema2(_median_filter([p[0] for p in pts]), 0.3), 0.02)
        ys = _deadzone(_ema2(_median_filter([p[1] for p in pts]), 0.3), 0.025)
        xs, ys = _ema2(xs, 0.4), _ema2(ys, 0.4)
        if track and s0 > 0:
            # nhảy thẳng sang vị trí mới đúng chỗ cắt
            track.append([round(max(s0 - 0.02, track[-1][0] + 0.001), 3), track[-1][1], track[-1][2]])
        for (t, _), x, y in zip(seg, xs, ys):
            track.append([round(max(t, s0), 3), round(x, 4), round(y, 4)])
        allpts += list(zip(xs, ys))
        last = (xs[-1], ys[-1])
    cov = hits / len(samples)
    med = [round(st.median(p[0] for p in allpts), 4), round(st.median(p[1] for p in allpts), 4)] if allpts else None
    return {"coverage": round(cov, 3), "track": track, "median": med, "fps": fps}


def track(prj: Project, video: Path, segments: list, force: bool = False) -> dict | None:
    """Dò và làm mượt; lưu work/face.json, chỉ chạy lại khi bản cắt đổi."""
    out = prj.work / "face.json"
    cuts = boundaries(segments)
    fp = fingerprint(video, cuts, VERSION)
    if not force and prj.fresh("face", fp) and out.exists():
        return read_json(out)
    vp = venv_python()
    if not vp.exists():
        warn("Chưa cài môi trường Python riêng nên chưa bám mặt được, giữ khung cố định. Chạy `video-editor setup`.")
        return None
    raw = prj.work / "face-raw.json"
    info("🙂 dò mặt người nói để bám khung …")
    p = run([vp, SKILL_DIR / "ve" / "face_worker.py", video, raw, "4"], check=False, quiet=True)
    if p.returncode != 0 or not raw.exists():
        err = (p.stderr or "").strip().splitlines()
        if any("No module named 'cv2'" in e for e in err):
            warn("Thiếu OpenCV trong môi trường chép lời nên chưa bám mặt được, giữ khung cố định. Chạy lại `video-editor setup` để cài.")
        else:
            warn("Dò mặt bị lỗi, giữ khung cố định." + (f" ({err[-1][:160]})" if err else ""))
        return None
    r = read_json(raw)
    res = smooth(r["samples"], cuts, r["fps"])
    res.update(srcW=r["w"], srcH=r["h"])
    write_json(out, res)
    raw.unlink(missing_ok=True)
    prj.mark("face", fp, coverage=res["coverage"])
    return res
