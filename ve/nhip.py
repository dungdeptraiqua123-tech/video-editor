"""Dò nhịp nhạc nền (giây của từng phách) để hạt nền nảy và đổi khung khớp nhạc.

Cách làm đơn giản, chỉ dùng thư viện chuẩn của Python (lệnh video-editor chạy bằng Python hệ thống):
đường bao năng lượng → độ tăng năng lượng (onset) → tự tương quan tìm tempo 70–180 BPM → chọn pha phách khớp onset nhất.
Bài nhạc 3 phút mất khoảng 1–2 giây.
"""
from __future__ import annotations

import array
import math
import subprocess
import sys
from pathlib import Path

SR = 11025
HOP = 256


def _decode(path: Path, max_sec: float = 600) -> array.array:
    p = subprocess.run(["ffmpeg", "-v", "error", "-t", str(max_sec), "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
    a = array.array("f")
    a.frombytes(p.stdout[: len(p.stdout) // 4 * 4])
    if sys.byteorder == "big":
        a.byteswap()
    return a


def onset_envelope(x) -> list[float]:
    n = len(x) // HOP
    if n < 8:
        return []
    e = []
    for k in range(n):
        s = 0.0
        for v in x[k * HOP:(k + 1) * HOP]:
            s += v * v
        e.append(math.log1p(100 * math.sqrt(s / HOP)))
    d = [0.0] + [max(0.0, e[i] - e[i - 1]) for i in range(1, n)]
    # bỏ thành phần chậm: trừ trung bình trượt 16 khung
    w, out, acc = 16, [], 0.0
    pre = [0.0]
    for v in d:
        acc += v
        pre.append(acc)
    for i in range(n):
        a, b = max(0, i - w // 2), min(n, i + w // 2)
        out.append(max(0.0, d[i] - (pre[b] - pre[a]) / w))
    return out


def tempo_and_beats(env, fps: float) -> tuple[float, list[float]]:
    env = list(env)
    if len(env) < fps * 4 or max(env, default=0) <= 0:
        return 0.0, []
    lo, hi = int(fps * 60 / 180), int(fps * 60 / 70)
    n = len(env)
    def ac(lag: int) -> float:
        return sum(env[i] * env[i + lag] for i in range(n - lag)) / (n - lag)

    scores = {lag: ac(lag) for lag in range(lo - 1, hi + 2)}
    lag = max(range(lo, hi + 1), key=lambda k: scores[k])
    # chu kỳ lẻ khung: tìm đỉnh tự tương quan ở bội số m của chu kỳ (chính xác hơn m lần), để phách không trôi trong bài dài
    m = max(1, min(16, n // (3 * lag)))
    if m > 1:
        far = max(range(m * lag - m, m * lag + m + 1), key=ac)
        period = far / m
    else:
        period = float(lag)
    bpm = 60 * fps / period
    count = int((n - 1) / period) + 1

    def grid(ph: float) -> list[int]:
        return [i for i in (round(ph + k * period) for k in range(count)) if i < n]

    # pha: tổng onset tại các phách cách đều nhau, chọn độ lệch cho tổng lớn nhất
    ph = max(range(lag), key=lambda p: sum(env[i] for i in grid(p)))
    # chỉnh từng phách về đỉnh onset gần nhất (±3 khung) để bù sai số tempo
    beats = []
    for i in grid(ph):
        win = range(max(0, i - 3), min(n, i + 4))
        j = max(win, key=lambda k: env[k])
        beats.append(round((j if env[j] > 0 else i) / fps, 3))
    return round(bpm, 1), beats


def beats(path: Path) -> dict:
    """{"bpm": số phách/phút, "beats": [giây]} của file nhạc. Lỗi (file hỏng, thiếu ffmpeg) thì trả rỗng."""
    try:
        env = onset_envelope(_decode(Path(path)))
        bpm, bs = tempo_and_beats(env, SR / HOP)
        return {"bpm": bpm, "beats": bs}
    except Exception:  # noqa: BLE001 - nhịp nhạc chỉ là phần phụ, không làm hỏng bước dựng
        return {"bpm": 0.0, "beats": []}


def snap(times: list[float], grid: list[float], tol: float = 0.18) -> list[float]:
    """Kéo mỗi mốc về phách gần nhất nếu lệch không quá tol giây (đổi khung khớp nhạc mà không lệch lời)."""
    if not grid:
        return times
    import bisect

    out = []
    for t in times:
        i = bisect.bisect_left(grid, t)
        cand = [grid[j] for j in (i - 1, i) if 0 <= j < len(grid)]
        b = min(cand, key=lambda g: abs(g - t)) if cand else t
        out.append(round(b if abs(b - t) <= tol else t, 2))
    return out
