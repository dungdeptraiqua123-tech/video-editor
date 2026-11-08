"""Soát chữ nghe nhầm: tìm tên riêng Whisper hay nghe sai ("ChatCVT", "Asian Hermes", "Cloud" khi đang nói về AI)
và gợi ý dòng `fix` sẵn để dán vào project.json. Kiểm tra cả chữ trong đồ hoạ (`content`) vì đồ hoạ hay chép lại lời.

Nguồn gợi ý:
1. từ điển data/nghe-nham.json (+ soat.extra của dự án), có điều kiện ngữ cảnh cho từ thường (cloud, fed…);
2. so gần đúng với tên thương hiệu trong từ điển icon và whisper.terms (chữ Latin ≥ 5 ký tự, giống ≥ 75%).

Mặc định chỉ gợi ý. soat.auto = true thì tự áp dụng các mục của từ điển (không áp dụng mục so gần đúng).
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

from .env import SKILL_DIR, read_json
from .timeline import norm

DICT = SKILL_DIR / "data" / "nghe-nham.json"
WINDOW = 25  # số từ mỗi bên để xét ngữ cảnh
_VN = re.compile(r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", re.I)


def entries(cfg: dict) -> list[dict]:
    d = read_json(DICT) if DICT.exists() else {"muc": []}
    return list((cfg.get("soat") or {}).get("extra") or []) + d.get("muc", [])


def known_names(cfg: dict) -> list[str]:
    """Tên riêng để so gần đúng: nhãn thương hiệu trong từ điển icon + whisper.terms + đích của từ điển nghe nhầm."""
    names = list((cfg.get("whisper") or {}).get("terms") or [])
    try:
        from .icons import LEXICON

        lex = read_json(LEXICON)
        names += [e.get("label", "") for e in lex.get("brands", [])]
    except (OSError, ValueError):
        pass
    names += [e["dung"] for e in entries(cfg)]
    return sorted({n for n in names if n and len(n) >= 4})


def _tok(s: str) -> list[str]:
    return [norm(x) for x in s.split() if norm(x)]


def suggest(words: list, cfg: dict) -> list[dict]:
    """[{sai (chữ đang có), dung, start, count, kind: tu-dien|gan-dung}] gộp theo cặp sai→đúng, theo thứ tự xuất hiện."""
    texts = [w["text"] if isinstance(w, dict) else w.text for w in words]
    starts = [w["start"] if isinstance(w, dict) else w.start for w in words]
    low = [norm(t) for t in texts]
    found: dict[tuple, dict] = {}

    def add(i: int, n: int, dung: str, kind: str) -> None:
        sai = " ".join(t.strip(".,!?;:") for t in texts[i:i + n])
        if norm(sai).replace(" ", "") == norm(dung).replace(" ", "") and sai.replace(" ", "") == dung.replace(" ", ""):
            return
        key = (sai.lower(), dung)
        if key in found:
            found[key]["count"] += 1
        else:
            found[key] = {"sai": sai, "dung": dung, "start": round(starts[i], 2), "count": 1, "kind": kind}

    pats = []
    for e in entries(cfg):
        for s in e.get("sai", []):
            t = _tok(s)
            if t and t != _tok(e["dung"]):
                pats.append((t, e))
    pats.sort(key=lambda x: -len(x[0]))
    ctx_words = lambda i: " " + " ".join(low[max(0, i - WINDOW): i + WINDOW]) + " "
    used = set()
    for i in range(len(low)):
        if i in used:
            continue
        for t, e in pats:
            n = len(t)
            if low[i:i + n] != t:
                continue
            ctx = e.get("ngu_canh")
            if ctx and not any(f" {norm(c)} " in ctx_words(i).replace(" " + " ".join(t) + " ", " ") for c in ctx):
                continue
            add(i, n, e["dung"], "tu-dien")
            used.update(range(i, i + n))
            break

    names = known_names(cfg)
    lname = {n.lower().replace(" ", ""): n for n in names}
    for i, t in enumerate(texts):
        if i in used:
            continue
        raw = t.strip(".,!?;:\"'()")
        if len(raw) < 5 or _VN.search(raw) or not re.fullmatch(r"[A-Za-z0-9\-]+", raw) or raw.lower() in lname:
            continue
        best = difflib.get_close_matches(raw.lower(), list(lname), n=1, cutoff=0.75)
        if best:
            add(i, 1, lname[best[0]], "gan-dung")
    return sorted(found.values(), key=lambda x: x["start"])


def as_fix(sugs: list[dict]) -> list[list[str]]:
    return [[s["sai"], s["dung"]] for s in sugs]


def check_content(content: dict, sugs: list[dict]) -> list[str]:
    """Chữ nghe nhầm bị chép vào đồ hoạ (beats, topics, hook, punches)."""
    blob = json.dumps(content or {}, ensure_ascii=False).lower()
    return [f"đồ hoạ có chữ \"{s['sai']}\", có thể đúng là \"{s['dung']}\"" for s in sugs if s["sai"].lower() in blob]


def report_lines(sugs: list[dict]) -> list[str]:
    if not sugs:
        return []
    out = [f"🔤 {len(sugs)} chữ có thể nghe nhầm (đối chiếu lời nói rồi thêm vào \"fix\" trong project.json):"]
    for s in sugs[:12]:
        tag = "" if s["kind"] == "tu-dien" else " (gần giống tên đã biết, xác nhận trước khi sửa)"
        out.append(f"   \"{s['sai']}\" → \"{s['dung']}\" @{s['start']}s" + (f" ×{s['count']}" if s["count"] > 1 else "") + tag)
    out.append("   Dán vào fix: " + json.dumps(as_fix(sugs[:12]), ensure_ascii=False))
    return out
