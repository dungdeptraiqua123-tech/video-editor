"""Nội dung đồ hoạ: kiểm tra cấu trúc, dò cụm từ trong lời thoại thành mốc thời gian (theo bản đã cắt).

Quy ước thời gian trong project.json:
- số = giây theo lời thoại gốc (như trong work/loi-thoai.txt), tự đổi sang thời gian sau khi cắt;
- chuỗi = cụm từ trong lời thoại, mốc là lúc cụm đó được nói (cách đáng tin nhất, không lệch khi cắt lại).
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from .timeline import norm

LEAD = 0.08  # đồ hoạ bật trước từ khoá 0,08 giây để mắt kịp bắt
BEAT_PRE = 0.25  # khung đồ hoạ mở trước câu nói một chút
BEAT_POST = 0.4
DEFAULT_DUR = 4.0
MAX_COVER = 0.6  # video người nói: khung đồ hoạ che quá tỉ lệ này của phần thân thì cảnh báo
TOPIC_MIN_SHOWN = 2.5  # thẻ chủ đề cần hiện rõ ít nhất chừng này giây (không bị khung đồ hoạ che)
VISUAL_WORDS = re.compile(r"\b(app|ứng dụng|giao diện|màn hình|dashboard|website|trang web|phần mềm|sản phẩm)\b", re.I)

ICONS = {"btc", "up", "down", "bank", "warn", "target", "chart", "wallet", "clock", "fire", "shield", "people", "dollar", "check"}

# trường bắt buộc và giới hạn độ dài chữ cho từng loại đồ hoạ
SCHEMA = {
    "price": {"req": {"label": str, "value": (int, float)}},
    "chart": {"req": {"title": str, "points": list}},
    "levels": {"req": {"title": str, "levels": list}},
    "list": {"req": {"title": str, "items": list}},
    "stat": {"req": {"icon": str, "big": str, "label": str}},
    "title": {"req": {"kicker": str, "text": str}},
    "media": {"req": {"src": str}},
    "compare": {"req": {"title": str, "left": dict, "right": dict}},
    "timeline": {"req": {"title": str, "items": list}},
    "progress": {"req": {"title": str, "items": list}},
    "quote": {"req": {"text": str}},
    "table": {"req": {"title": str, "cols": list, "rows": list}},
    "countdown": {"req": {"title": str, "items": list}},
}
MAXLEN = {"label": 28, "title": 34, "text": 40, "big": 10, "kicker": 28, "head": 30}


@dataclass
class Report:
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    # lịch xuất hiện: {"t": giây trong video đã cắt, "what": phần tử, "say": cụm neo}
    events: list = field(default_factory=list)

    def at(self, t: float, what: str, say=None) -> None:
        anchor = f"\"{say}\"" if isinstance(say, str) else (f"giây {say} của file gốc" if isinstance(say, (int, float)) else "")
        self.events.append({"t": round(float(t), 2), "what": what, "say": anchor})

    def err(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


def _same(ph: str, tok: str) -> bool:
    """Từ khoá khớp cả từ, phần đầu của số ("85" khớp "85.000") hoặc một vế của khoảng ("400" khớp "300-400")."""
    if ph == tok:
        return True
    k = len(ph)
    return len(tok) > k and ((tok.startswith(ph) and tok[k] in ".,-–/") or (tok.endswith(ph) and tok[-k - 1] in "-–/"))


class Finder:
    """Tìm cụm từ trong danh sách từ (thời gian sau khi cắt)."""

    def __init__(self, words: list):
        self.words = words
        self.toks = [norm(w["text"]) for w in words]

    def find(self, phrase: str, lo: float = 0.0, hi: float = 1e9) -> tuple[float, float] | None:
        ph = [norm(x) for x in str(phrase).split() if norm(x)]
        if not ph:
            return None
        n = len(ph)
        for i in range(len(self.toks) - n + 1):
            w = self.words[i]
            if lo <= w["start"] <= hi and all(_same(a, b) for a, b in zip(ph, self.toks[i:i + n])):
                return w["start"], self.words[i + n - 1]["end"]
        return None

    def near(self, phrase: str, k: int = 3) -> list[str]:
        n = max(1, len(str(phrase).split()))
        grams = {" ".join(w["text"] for w in self.words[i:i + n]) for i in range(len(self.words) - n + 1)}
        return difflib.get_close_matches(str(phrase), list(grams), n=k, cutoff=0.5)


def _time(v, tl, finder: Finder, rep: Report, where: str, lo: float, end: bool = False):
    if isinstance(v, (int, float)):
        t = tl.map(float(v)) if tl else float(v)
        return t
    if isinstance(v, str):
        hit = finder.find(v, lo) or finder.find(v)
        if not hit:
            sug = finder.near(v)
            rep.err(where, f"không tìm thấy cụm \"{v}\" trong lời thoại" + (f". Gần giống: {', '.join(repr(s) for s in sug)}" if sug else ""))
            return None
        return hit[1] if end else hit[0]
    rep.err(where, f"mốc thời gian phải là số giây hoặc cụm từ, đang là {v!r}")
    return None


def _resolve_anchors(obj, finder: Finder, lo: float, hi: float, base: float, rep: Report, where: str):
    """Đổi khoá say/xxxSay thành d/xxxD: số giây tính từ lúc khung đồ hoạ mở."""
    if isinstance(obj, list):
        return [_resolve_anchors(x, finder, lo, hi, base, rep, f"{where}[{i}]") for i, x in enumerate(obj)]
    if not isinstance(obj, dict):
        return obj
    out = {}
    for k, v in obj.items():
        if k == "say" or k.endswith("Say"):
            key = "d" if k == "say" else k[:-3] + "D"
            hit = finder.find(v, lo, hi)
            if not hit:
                sug = finder.near(v)
                rep.err(where, f"từ khoá \"{v}\" không được nói trong lúc khung này hiện ({lo:.1f}–{hi:.1f}s)" + (f". Gần giống: {', '.join(repr(s) for s in sug)}" if sug else ""))
                continue
            out[key] = round(max(0.0, hit[0] - LEAD - base), 2)
            field_ = k[:-3] if k != "say" else None
            label = obj.get(field_) if field_ else next((obj[x] for x in ("text", "label", "value", "big", "title") if obj.get(x) not in (None, "")), "")
            rep.at(base + out[key], f"{where} · {label}" if label != "" else where, v)
        else:
            out[k] = _resolve_anchors(v, finder, lo, hi, base, rep, where)
    return out


def check_graphic(g: dict, where: str, rep: Report, media_ok=lambda p: True) -> None:
    t = g.get("type")
    if t not in SCHEMA:
        rep.err(where, f"loại đồ hoạ \"{t}\" không có. Chọn một trong: {', '.join(SCHEMA)}")
        return
    for k, typ in SCHEMA[t]["req"].items():
        if k not in g:
            rep.err(where, f"thiếu trường \"{k}\" (bắt buộc với loại {t})")
        elif not isinstance(g[k], typ):
            rep.err(where, f"trường \"{k}\" sai kiểu")
    for k, lim in MAXLEN.items():
        lim = 44 if (t, k) == ("stat", "label") else 140 if (t, k) == ("quote", "text") else lim
        if isinstance(g.get(k), str) and len(g[k]) > lim:
            rep.warn(where, f"\"{k}\" dài {len(g[k])} ký tự (nên ≤ {lim}), có thể tràn khung")
    if t == "chart" and isinstance(g.get("points"), list):
        if len(g["points"]) < 2 or not all(isinstance(x, (int, float)) for x in g["points"]):
            rep.err(where, "points cần ít nhất 2 số")
        for tag in g.get("tags", []):
            if not 0 <= tag.get("i", -1) < len(g["points"]):
                rep.err(where, f"tag \"{tag.get('text')}\" có i ngoài khoảng 0–{len(g['points']) - 1}")
    if t == "levels" and isinstance(g.get("levels"), list):
        if not 1 <= len(g["levels"]) <= 5:
            rep.warn(where, "nên có 1–5 mốc")
        for l in g["levels"]:
            if l.get("kind") not in ("res", "sup", "now"):
                rep.err(where, f"mốc \"{l.get('value')}\" cần kind là res, sup hoặc now")
    if t == "list" and isinstance(g.get("items"), list):
        if not 1 <= len(g["items"]) <= 4:
            rep.warn(where, "danh sách nên có 1–4 dòng")
        for it in g["items"]:
            if it.get("icon", "check") not in ICONS:
                rep.err(where, f"icon \"{it.get('icon')}\" không có. Chọn: {', '.join(sorted(ICONS))}")
            if len(it.get("text", "")) > 32:
                rep.warn(where, f"dòng \"{it.get('text')}\" dài hơn 32 ký tự")
    if t == "stat" and g.get("icon") not in ICONS:
        rep.err(where, f"icon \"{g.get('icon')}\" không có. Chọn: {', '.join(sorted(ICONS))}")
    if t == "media" and isinstance(g.get("src"), str) and not media_ok(g["src"]):
        rep.err(where, f"không thấy file \"{g['src']}\" trong thư mục media của dự án")
    if t == "compare":
        for side in ("left", "right"):
            sd = g.get(side)
            if isinstance(sd, dict):
                for k in ("label", "value"):
                    if not isinstance(sd.get(k), str) or not sd.get(k):
                        rep.err(where, f"{side}.{k} cần là chữ (ví dụ \"label\": \"Hôm qua\", \"value\": \"$85K\")")
                if len(str(sd.get("value", ""))) > 9:
                    rep.warn(where, f"{side}.value \"{sd.get('value')}\" dài hơn 9 ký tự, có thể tràn ô")
                if sd.get("icon") and sd["icon"] not in ICONS:
                    rep.err(where, f"icon \"{sd['icon']}\" không có. Chọn: {', '.join(sorted(ICONS))}")
        if g.get("winner") not in (None, "left", "right"):
            rep.err(where, "winner chỉ nhận \"left\" hoặc \"right\"")
    if t in ("timeline", "countdown") and isinstance(g.get("items"), list):
        if not 2 <= len(g["items"]) <= 5:
            rep.warn(where, "nên có 2–5 mục")
        for it in g["items"]:
            if t == "timeline" and not it.get("when"):
                rep.err(where, f"mục \"{it.get('text')}\" thiếu \"when\" (mốc thời gian, ví dụ \"2024\", \"Tháng 10\")")
            if len(it.get("text", "")) > 36:
                rep.warn(where, f"dòng \"{it.get('text')}\" dài hơn 36 ký tự")
    if t == "progress" and isinstance(g.get("items"), list):
        if not 1 <= len(g["items"]) <= 4:
            rep.warn(where, "nên có 1–4 thanh")
        for it in g["items"]:
            if not isinstance(it.get("value"), (int, float)):
                rep.err(where, f"\"{it.get('label')}\" cần value là số (ví dụ 65 cho 65%)")
            if not it.get("label"):
                rep.err(where, "mỗi thanh cần label")
    if t == "table" and isinstance(g.get("cols"), list) and isinstance(g.get("rows"), list):
        if not 2 <= len(g["cols"]) <= 4:
            rep.warn(where, "bảng nên có 2–4 cột")
        if not 1 <= len(g["rows"]) <= 5:
            rep.warn(where, "bảng nên có 1–5 dòng")
        for r in g["rows"]:
            cells = r.get("cells") if isinstance(r, dict) else None
            if not isinstance(cells, list) or len(cells) != len(g["cols"]):
                rep.err(where, f"mỗi dòng cần \"cells\" có đúng {len(g['cols'])} ô (bằng số cột)")
                break


def _max_d(x) -> float:
    if isinstance(x, dict):
        return max([float(v) for k, v in x.items() if k.endswith("d") and k[:-1] in ("", "label", "change") and isinstance(v, (int, float))] + [_max_d(v) for v in x.values()] + [0.0])
    if isinstance(x, list):
        return max([_max_d(v) for v in x] + [0.0])
    return 0.0


def _check_density(g: dict, head: str, dur: float, prev: list, where: str, rep: Report) -> None:
    """Khung ít nội dung mà hiện lâu (màn hình gần như đứng yên), tiêu đề trùng khung liền trước."""
    import difflib

    t = g.get("type")
    n = len(g.get("items") or g.get("levels") or g.get("rows") or [])
    if t in ("list", "levels", "progress", "countdown", "timeline", "table") and n <= 1 and dur > 4:
        rep.warn(where, f"chỉ có 1 ý mà hiện {dur:.1f}s, màn hình gần như đứng yên. Thêm ý (mỗi ý neo một cụm lời), hoặc đổi sang stat / chữ đập (punches)")
    if t == "title" and dur > 4.5:
        rep.warn(where, f"thẻ chữ đứng yên {dur:.1f}s. Rút còn ≤ 4s, hoặc đổi sang list/timeline có ý hiện dần theo lời, hoặc ảnh thật (media)")
    idle = dur - _max_d(g)
    if idle > 6 and t not in ("chart", "media", "quote", "price"):
        rep.warn(where, f"ý cuối hiện xong còn đứng yên {idle:.1f}s. Rút ngắn khung (end sớm hơn) hoặc thêm ý neo vào lời phía sau")
    if prev and head and prev[-1].get("head"):
        a, b = head.lower(), prev[-1]["head"].lower()
        if a == b or difflib.SequenceMatcher(None, a, b).ratio() >= 0.6 or a.split()[:2] == b.split()[:2]:
            rep.warn(where, f"tiêu đề \"{head}\" gần giống khung liền trước (\"{prev[-1]['head']}\"). Gộp hai khung hoặc đặt tiêu đề khác để người xem thấy đã sang ý mới")


def resolve_content(content: dict, words: list, duration: float, tl=None, mode: str = "talking", media_ok=lambda p: True, zoom_every: float = 3.0) -> tuple[dict, Report]:
    """Trả về (dữ liệu đã có mốc thời gian theo bản cắt, báo cáo lỗi/cảnh báo)."""
    rep = Report()
    finder = Finder(words)
    hook_sec = float(content.get("hookSec", 3.2))
    outro_sec = float(content.get("outroSec", 3.6))
    if not content.get("hook", {}).get("title"):
        rep.warn("hook", "chưa có tiêu đề mở đầu (hook.title)")
    elif len(content["hook"]["title"]) > 40:
        rep.warn("hook", "tiêu đề mở đầu dài hơn 40 ký tự")

    beats, cursor = [], 0.0
    for i, b in enumerate(content.get("beats", [])):
        where = f"beats[{i}]" + (f" \"{b.get('head', '')}\"" if b.get("head") else "")
        g = b.get("g")
        if not isinstance(g, dict):
            rep.err(where, "thiếu khối đồ hoạ g")
            continue
        check_graphic(g, where, rep, media_ok)
        if len(b.get("head", "")) > MAXLEN["head"]:
            rep.warn(where, f"head dài {len(b['head'])} ký tự (nên ≤ {MAXLEN['head']})")
        s = _time(b.get("start"), tl, finder, rep, where + ".start", cursor)
        if s is None:
            continue
        if isinstance(b.get("start"), str):
            s -= BEAT_PRE
        if "end" in b:
            e = _time(b["end"], tl, finder, rep, where + ".end", s, end=True)
            if e is None:
                continue
            if isinstance(b["end"], str):
                e += BEAT_POST
        else:
            e = s + float(b.get("dur", DEFAULT_DUR))
        s = max(0.0, s)
        if e <= s:
            rep.err(where, f"kết thúc ({e:.2f}s) không sau bắt đầu ({s:.2f}s)")
            continue
        if e > duration - outro_sec + 0.2:
            rep.warn(where, f"chạm phần kết ({e:.1f}s > {duration - outro_sec:.1f}s), đã cắt bớt")
            e = duration - outro_sec
        if s < hook_sec + 0.2:
            rep.warn(where, f"bắt đầu lúc {s:.1f}s, chồng lên thẻ mở đầu ({hook_sec}s), đã dời tới {hook_sec + 0.2:.1f}s để hai lớp chữ không đè nhau")
            s = hook_sec + 0.2
            if e - s < 1.0:
                rep.err(where, "sau khi dời khỏi phần mở đầu chỉ còn dưới 1 giây. Neo khung vào câu nói sau phần mở đầu")
                continue
        if e - s < 1.5:
            rep.warn(where, f"chỉ hiện {e - s:.1f}s, người xem khó đọc kịp")
        if e - s > 25:
            rep.warn(where, f"hiện {e - s:.0f}s, quá dài cho một khung")
        if beats and s < beats[-1]["end"]:
            rep.warn(where, f"chồng lên khung trước ({s:.1f}s < {beats[-1]['end']:.1f}s), đã đẩy lùi")
            s = beats[-1]["end"] + 0.05
            if e <= s:
                rep.err(where, "bị khung trước che hết")
                continue
        cursor = s
        rep.at(s, f"{where} mở: {g.get('title') or g.get('text') or g.get('label') or g.get('type')}", b.get("start"))
        rep.at(e, f"{where} đóng", b.get("end"))
        gg = _resolve_anchors(g, finder, s - 1.0, e + 0.5, s, rep, f"  {where}")
        _check_density(gg, b.get("head", ""), e - s, beats, where, rep)
        if g.get("type") != "media" and VISUAL_WORDS.search(" ".join(str(x) for x in (b.get("head", ""), g.get("title", ""), g.get("text", ""), g.get("kicker", ""), b.get("start", "")) if isinstance(x, str))):
            rep.warn(where, "đang nói về app/giao diện/sản phẩm mà chỉ có thẻ chữ. Người xem cần thấy thật: dùng khung media với ảnh chụp màn hình hoặc clip quay màn hình")
        beats.append({"start": round(s, 2), "end": round(e, 2), "head": b.get("head", ""), "g": gg})

    topics = []
    tps = content.get("topics", [])
    starts = [_time(t.get("start"), tl, finder, rep, f"topics[{i}].start", 0) for i, t in enumerate(tps)]
    for i, t in enumerate(tps):
        if starts[i] is None:
            continue
        end = next((x for x in starts[i + 1:] if x is not None), duration - outro_sec)
        items = []
        for k, it in enumerate(t.get("items", [])):
            hit = finder.find(it.get("say", ""), starts[i] - 0.5, end + 3)
            if not hit:
                rep.err(f"topics[{i}].items[{k}]", f"không tìm thấy \"{it.get('say')}\" trong đoạn của chủ đề")
                continue
            if hit[0] > end:
                rep.warn(f"topics[{i}].items[{k}]", f"\"{it.get('say')}\" được nói lúc {hit[0]:.1f}s, sau khi thẻ đã ẩn ({end:.1f}s), ý này sẽ không hiện")
            items.append({"at": round(hit[0] - LEAD, 2), "text": it.get("text", "")})
            rep.at(hit[0] - LEAD, f"  topics[{i}].items[{k}] · {it.get('text', '')}", it.get("say"))
        if end - starts[i] < 1.5:
            rep.warn(f"topics[{i}]", f"thẻ chỉ hiện {max(0, end - starts[i]):.1f}s (bị chủ đề sau hoặc phần kết chặn)")
        topics.append({"start": round(starts[i], 2), "end": round(end, 2), "kicker": t.get("kicker", ""), "title": t.get("title", ""), "items": items})
        rep.at(starts[i], f"topics[{i}] thẻ chủ đề: {t.get('title', '')}", t.get("start"))

    def _covered(a: float, b: float) -> float:
        return sum(max(0.0, min(b, x["end"]) - max(a, x["start"])) for x in beats)

    for i, tp in enumerate(topics):
        a = max(tp["start"], hook_sec)
        shown = max(0.0, tp["end"] - a) - _covered(a, tp["end"])
        if tp["end"] - a >= 1.5 and shown < TOPIC_MIN_SHOWN:
            rep.warn(f"topics[{i}] \"{tp['title']}\"", f"thẻ chủ đề chỉ hiện rõ {shown:.1f}s (còn lại bị khung đồ hoạ che). Neo khung đồ hoạ đầu tiên của chủ đề muộn hơn để thẻ hiện ≥ {TOPIC_MIN_SHOWN}s")
    body = duration - hook_sec - outro_sec
    if mode == "talking" and body > 6 and beats:
        cover = _covered(hook_sec, duration - outro_sec) / body
        if cover > MAX_COVER:
            rep.warn("content.beats", f"khung đồ hoạ phủ {cover * 100:.0f}% thời lượng, người nói bị thu nhỏ gần hết video (nên ≤ {MAX_COVER * 100:.0f}%). Giữ khung cho số liệu/ý chính, phần còn lại để mặt người nói với chữ đập (punches) hoặc icon theo lời")

    punches = []
    for i, pu in enumerate(content.get("punches", [])):
        where = f"punches[{i}]"
        if not pu.get("text"):
            rep.err(where, "thiếu \"text\" (chữ lớn sẽ đập lên màn hình)")
            continue
        if len(pu["text"]) > 12:
            rep.warn(where, f"\"{pu['text']}\" dài {len(pu['text'])} ký tự (nên ≤ 12 để chữ đủ to)")
        hit = finder.find(pu.get("say", ""))
        if not hit:
            sug = finder.near(pu.get("say", ""))
            rep.err(where, f"không tìm thấy \"{pu.get('say')}\" trong lời thoại" + (f". Gần giống: {', '.join(repr(x) for x in sug)}" if sug else ""))
            continue
        tt = round(max(0.0, hit[0] - LEAD), 2)
        if any(b["start"] - 0.3 <= tt <= b["end"] for b in beats):
            rep.warn(where, f"\"{pu['text']}\" rơi vào lúc đang hiện khung đồ hoạ ({tt:.1f}s) nên bị ẩn")
        if punches and tt - punches[-1]["t"] < 1.6:
            rep.warn(where, f"cách chữ đập trước chỉ {tt - punches[-1]['t']:.1f}s, đã bỏ")
            continue
        punches.append({"t": tt, "text": pu["text"], **({"sub": pu["sub"]} if pu.get("sub") else {}), **({"tone": pu["tone"]} if pu.get("tone") else {})})
        rep.at(tt, f"{where} chữ đập: {pu['text']}", pu.get("say"))

    z = content.get("zooms", "auto")
    zooms = auto_zooms(words, beats, zoom_every) if z == "auto" and mode == "talking" else [round(tl.map(x) if tl else x, 2) for x in (z if isinstance(z, list) else [])]

    data = {
        "hook": content.get("hook", {"title": ""}),
        "cta": content.get("cta", ""),
        "hookSec": hook_sec,
        "outroSec": outro_sec,
        "beats": beats,
        "topics": topics,
        "zooms": zooms,
        "punches": punches,
    }
    if duration < hook_sec + outro_sec + 2:
        rep.err("video", f"chỉ dài {duration:.1f}s, không đủ chỗ cho mở đầu và kết")
    rep.at(0, f"mở đầu: {data['hook'].get('title', '')}")
    rep.at(duration - outro_sec, f"kết: {data['cta']}")
    rep.events.sort(key=lambda e: e["t"])
    return data, rep


def auto_zooms(words: list, beats: list, every: float = 3.0) -> list:
    """Đổi khung rộng/chặt ở đầu câu, cách nhau ít nhất `every` giây, tránh lúc đang hiện đồ hoạ."""
    out, last = [], -1e9
    for i, w in enumerate(words):
        starts_sentence = i == 0 or words[i - 1]["text"].rstrip().endswith((".", "!", "?", ",")) or w["start"] - words[i - 1]["end"] > 0.35
        if not starts_sentence or w["start"] - last < every:
            continue
        if any(b["start"] - 0.5 <= w["start"] <= b["end"] + 0.5 for b in beats):
            continue
        out.append(round(w["start"], 2))
        last = w["start"]
    return out
