"""Icon tự hiện theo lời: người nói nhắc "Claude" thì logo Claude bật lên, nhắc "ngân hàng" thì icon ngân hàng.

Từ điển ở data/icon-tu-dien.json (thương hiệu + khái niệm), dự án thêm/bớt qua khoá `icons` trong project.json.
Hình icon lấy từ gói npm trong bộ dựng đã cài: simple-icons (logo, CC0) và lucide-static (icon nét, ISC),
nhúng thẳng vào dữ liệu render nên khi render không cần mạng.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .env import ENGINE, SKILL_DIR, read_json, warn
from .timeline import PUNCT, norm

LEXICON = SKILL_DIR / "data" / "icon-tu-dien.json"
LEAD = 0.12  # icon bật trước từ khoá một chút để mắt kịp bắt

DEFAULTS = {"auto": True, "pops": True, "inline": True, "concepts": True, "gap": None, "repeat": 12.0, "extra": [], "off": []}
# khoảng cách tối thiểu giữa hai lần bật icon lớn, theo nhịp dựng
GAP_BY_PACE = {"nhanh": 1.8, "vua": 2.5, "cham": 4.0}


def settings(cfg: dict) -> dict:
    ic = cfg.get("icons")
    if ic is False:
        return dict(DEFAULTS, auto=False, pops=False, inline=False)
    out = dict(DEFAULTS)
    out.update({k: v for k, v in (ic or {}).items() if v is not None})
    if out["gap"] is None:
        out["gap"] = GAP_BY_PACE.get((cfg.get("style") or {}).get("pace") or "vua", 2.5)
    return out


def lexicon(cfg: dict) -> list[dict]:
    """Danh sách mục {icon, label, match, file?, color?} theo thứ tự ưu tiên: mục riêng của dự án, thương hiệu, khái niệm."""
    s = settings(cfg)
    lex = read_json(LEXICON) if LEXICON.exists() else {"brands": [], "concepts": []}
    entries = [dict(e, kind="extra") for e in s["extra"]]
    if s["auto"]:
        entries += [dict(e, kind="brand") for e in lex.get("brands", [])]
        if s["concepts"]:
            entries += [dict(e, kind="concept") for e in lex.get("concepts", [])]
    off = {str(x).lower() for x in s["off"]}
    return [e for e in entries if e.get("match") and not ({str(e.get("icon", "")).lower(), str(e.get("label", "")).lower()} & off or any(m.lower().lstrip("=") in off for m in e["match"]))]


def _raw(t: str) -> str:
    return t.strip(PUNCT + " ")


def _phrases(entries: list[dict]) -> list[tuple[list[str], dict]]:
    """Mỗi cụm khớp thành danh sách token; cụm dài thử trước để "bitcoin cash" thắng "bitcoin"."""
    out = []
    for e in entries:
        for m in e["match"]:
            exact = m.startswith("=")
            toks = [("=" + t) if exact else norm(t) for t in m.lstrip("=").split()]
            if toks:
                out.append((toks, e))
    out.sort(key=lambda x: -len(x[0]))
    return out


def find(words: list[dict], entries: list[dict]) -> list[dict]:
    """Mọi chỗ nhắc tới icon: [{i (chỉ số từ đầu), n (số từ), start, entry}], không chồng nhau."""
    phrases = _phrases(entries)
    low = [norm(w["text"]) for w in words]
    raw = [_raw(w["text"]) for w in words]
    hits, i = [], 0
    while i < len(words):
        for toks, e in phrases:
            n = len(toks)
            if i + n > len(words):
                continue
            if all((raw[i + k] == t[1:]) if t.startswith("=") else (low[i + k] == t) for k, t in enumerate(toks)):
                hits.append({"i": i, "n": n, "start": words[i]["start"], "entry": e})
                i += n - 1
                break
        i += 1
    return hits


def plan(words: list[dict], cfg: dict, beats: list[dict], duration: float, hook_sec: float, outro_sec: float) -> tuple[list[dict], dict, list[dict]]:
    """Chọn icon bật lên (giãn đều, không lặp liên tục, tránh lúc đang hiện khung đồ hoạ và phần mở/kết).

    Trả về (pops [{t, id, word}], {chỉ số từ: id} để gắn icon nhỏ vào phụ đề, các mục đã dùng).
    """
    s = settings(cfg)
    if not (s["pops"] or s["inline"]):
        return [], {}, []
    hits = find(words, lexicon(cfg))
    pops, inline, used = [], {}, {}
    last_any, last_same, last_inline = -1e9, {}, {}
    for h in hits:
        e = h["entry"]
        iid = e.get("icon") or ("file:" + str(e.get("file")))
        used[iid] = e
        t = h["start"]
        if s["inline"] and t - last_inline.get(iid, -1e9) >= 4.0:
            inline[h["i"]] = iid
            last_inline[iid] = t
        if not s["pops"]:
            continue
        if t < hook_sec + 0.2 or t > duration - outro_sec - 1.2:
            continue
        if any(b["start"] - 0.4 <= t <= b["end"] + 0.2 for b in beats):
            continue
        if t - last_any < s["gap"] or t - last_same.get(iid, -1e9) < float(s["repeat"]):
            continue
        pops.append({"t": round(max(0.0, t - LEAD), 2), "id": iid, "word": " ".join(w["text"] for w in words[h["i"]:h["i"] + h["n"]])})
        last_any, last_same[iid] = t, t
    return pops, inline, [dict(e, id=k) for k, e in used.items()]


_SI_DATA: dict | None = None


def _si_hex(slug: str, base: Path) -> str | None:
    global _SI_DATA
    if _SI_DATA is None:
        p = base / "simple-icons" / "data" / "simple-icons.json"
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            items = d if isinstance(d, list) else d.get("icons", [])
            _SI_DATA = {}
            for x in items:
                sl = x.get("slug") or re.sub(r"[^a-z0-9]", "", x["title"].lower())
                _SI_DATA[sl] = x.get("hex")
        except (OSError, ValueError):
            _SI_DATA = {}
    return _SI_DATA.get(slug)


def svg_data(iid: str, entry: dict, modules: Path | None = None) -> dict | None:
    """Đọc hình icon từ node_modules của bộ dựng: {kind: brand|line, body (phần trong thẻ svg), viewBox, color, label}."""
    base = modules or (ENGINE / "node_modules")
    kind, _, name = iid.partition(":")
    if kind == "si":
        p = base / "simple-icons" / "icons" / f"{name}.svg"
        if not p.exists():
            return None
        d = re.search(r'<path d="([^"]+)"', p.read_text(encoding="utf-8"))
        if not d:
            return None
        hexc = entry.get("color") or ("#" + (_si_hex(name, base) or "888888"))
        return {"kind": "brand", "body": f'<path d="{d.group(1)}"/>', "viewBox": "0 0 24 24", "color": hexc, "label": entry.get("label", "")}
    if kind == "lu":
        p = base / "lucide-static" / "icons" / f"{name}.svg"
        if not p.exists():
            return None
        txt = p.read_text(encoding="utf-8")
        m = re.search(r"<svg[^>]*>(.*)</svg>", txt, re.S)
        if not m:
            return None
        body = re.sub(r"\s+", " ", m.group(1)).strip()
        return {"kind": "line", "body": body, "viewBox": "0 0 24 24", "color": entry.get("color"), "label": entry.get("label", "")}
    return None


def resolve(words: list[dict], cfg: dict, beats: list[dict], duration: float, hook_sec: float, outro_sec: float, place_file=None, modules: Path | None = None) -> tuple[list[dict], dict, dict]:
    """Kế hoạch icon + hình icon cho dữ liệu render. place_file(src) đưa logo riêng (file ảnh) vào media/."""
    pops, inline, used = plan(words, cfg, beats, duration, hook_sec, outro_sec)
    table, missing = {}, []
    for e in used:
        iid = e["id"]
        if iid.startswith("file:"):
            src = e.get("file")
            try:
                table[iid] = {"kind": "img", "src": place_file(src) if place_file else src, "color": e.get("color"), "label": e.get("label", "")}
            except Exception:  # noqa: BLE001 - thiếu file thì bỏ icon đó, báo một dòng
                missing.append(str(src))
            continue
        d = svg_data(iid, e, modules)
        if d:
            table[iid] = d
        else:
            missing.append(iid)
    if missing:
        warn("Không đọc được icon: " + ", ".join(sorted(set(missing))) + ". Chạy lại `video-editor setup` nếu bộ dựng chưa có simple-icons/lucide-static; tên icon xem trong data/icon-tu-dien.json.")
    pops = [p for p in pops if p["id"] in table]
    inline = {i: v for i, v in inline.items() if v in table}
    return pops, inline, table
