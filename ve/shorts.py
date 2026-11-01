"""Cắt video dài thành nhiều short: chấm điểm các đoạn 25–60 giây trong lời thoại, đề xuất đoạn hay nhất,
rồi tạo mỗi đoạn thành một dự án riêng dùng lại bản chép lời (không chép lại cả video dài).

Điểm chỉ dựa trên lời thoại và quãng nghỉ, không gọi dịch vụ ngoài. Đây là bước lọc thô: trợ lý AI đọc lại
danh sách, bỏ đoạn lạc đề, sửa tiêu đề, rồi mới đưa người dùng chọn.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .bang import clock
from .env import VEError, info, read_json, write_json
from .project import DEFAULT, Project, fingerprint
from .timeline import DEFAULT_FILLERS, apply_fixes, norm, words_from_transcript

# Từ hay gặp ở câu mở đầu thu hút: cảnh báo, nhấn mạnh, câu hỏi, biến động mạnh.
# Chỉ giữ từ mang nghĩa nhấn mạnh; từ chung chung ("phải", "tăng", "tin") gặp ở câu nào cũng có nên không tính.
HOOK_WORDS = ["lưu ý", "chú ý", "quan trọng", "cẩn thận", "cảnh báo", "tại sao", "vì sao", "bí mật", "sai lầm", "đừng", "cơ hội",
              "rủi ro", "mấu chốt", "cực kỳ", "nhất định", "sập", "bùng nổ", "bất ngờ", "sự thật", "kỷ lục", "đỉnh", "đáy",
              "nguy hiểm", "thua lỗ", "lời khuyên", "bí quyết", "ít ai biết", "không ai nói"]
ADDRESS = ["bạn", "các bạn", "anh em", "mọi người", "anh chị", "các anh chị"]
# Lời bảo người xem làm gì: "bạn hãy", "anh em nên"… mở short rất mạnh
IMPERATIVE = ["hãy", "nên", "đừng", "phải nhớ", "nhớ là"]
# Mở đầu bằng các từ này thường là câu nối tiếp ý trước, cắt ra đứng riêng sẽ hụt
BAD_START = {"thì", "và", "nhưng", "là", "mà", "nên", "để", "hay", "cũng", "với", "của", "còn"}
# Từ nối có thể bỏ ở đầu short khi ngay sau là một ý mới ("và bạn hãy lưu ý…" → "bạn hãy lưu ý…")
SKIPPABLE = {"và", "thì", "rồi", "nhưng", "còn", "ok", "okay", "à", "ừ", "vâng"}
# Từ mở một ý mới
TOPIC_START = {"rồi", "bây", "hiện", "hôm", "đầu", "tiếp", "bạn", "anh", "mọi", "các", "nếu", "tại", "vì", "điều", "lưu", "chú", "chúng"}
BAD_END = {"và", "thì", "là", "của", "mà", "với", "để", "nhưng", "hay", "cái", "những", "các", "một", "này"}
INTRO = ["xin chào", "chào mừng", "hello", "quay trở lại với"]
OUTRO = ["cảm ơn", "hẹn gặp", "đăng ký", "theo dõi kênh", "subscribe", "bấm like", "chia sẻ video"]


@dataclass
class Unit:
    """Một vế lời thoại: đoạn của Whisper, hoặc phần của đoạn dài tách ở chỗ ngắt câu/quãng nghỉ.

    lead: số từ nối ở đầu có thể bỏ khi short bắt đầu từ vế này ("và bạn hãy…" bỏ "và").
    """
    start: float
    end: float
    text: str
    words: list = field(default_factory=list)
    lead: int = 0


@dataclass
class Cand:
    a: int
    b: int
    start: float
    end: float
    score: float
    parts: dict
    reasons: list
    hook: str
    text: str
    lead: int = 0

    @property
    def dur(self) -> float:
        return self.end - self.start


def _lead(ws: list) -> int:
    """Số từ nối đầu vế có thể bỏ: chỉ bỏ khi từ ngay sau mở một ý mới (xưng hô, "hiện tại", "lưu ý"…)."""
    k = 0
    while k < min(2, len(ws) - 1) and norm(ws[k].text) in SKIPPABLE:
        k += 1
    if k and (norm(ws[k].text) in TOPIC_START or _count(" ".join(w.text for w in ws[k:k + 3]), ADDRESS + HOOK_WORDS)):
        return k
    return 0


def _split(ws: list, long_sec: float = 6.0, gap: float = 0.45) -> list[list]:
    """Tách đoạn Whisper dài thành vế: sau dấu chấm/hỏi/than, hoặc ở quãng nghỉ giữa hai từ."""
    if not ws or ws[-1].end - ws[0].start <= long_sec:
        return [ws]
    out, cur = [], [ws[0]]
    for prev, w in zip(ws, ws[1:]):
        if (re.search(r"[.!?…]$", prev.text.strip()) or w.start - prev.end >= gap) and cur[-1].end - cur[0].start >= 1.5:
            out.append(cur)
            cur = []
        cur.append(w)
    out.append(cur)
    return out


def units_from(segs: list, fixes: list | None = None, drop_segments: list | None = None) -> list[Unit]:
    words = apply_fixes(words_from_transcript(segs, drop_segments), fixes or [])
    out = []
    for s in segs:
        a, b = float(s["start"]), float(s["end"])
        ws = [w for w in words if a - 0.01 <= (w.start + w.end) / 2 <= b + 0.01]
        for part in _split(ws):
            if part:
                out.append(Unit(part[0].start, part[-1].end, " ".join(w.text for w in part), part, _lead(part)))
    out.sort(key=lambda u: u.start)
    return out


def _flat(text: str) -> str:
    return " " + re.sub(r"[^\w\s]", " ", text.lower()).replace("_", " ") + " "


def _count(text: str, phrases: list) -> list:
    f = _flat(text)
    return [p for p in phrases if f" {p} " in f]


def _numbers(text: str) -> int:
    return len(re.findall(r"\d[\d.,]*", text))


def _last_word(u: Unit) -> str:
    return norm(u.words[-1].text) if u.words else ""


def score_window(units: list[Unit], a: int, b: int, lo: float, hi: float, target: float, fillers=DEFAULT_FILLERS) -> Cand:
    us = units[a:b + 1]
    lead = us[0].lead
    words = us[0].words[lead:] + [w for u in us[1:] for w in u.words]
    start, end = words[0].start, us[-1].end
    dur = end - start
    text = " ".join(w.text for w in words)
    gap_before = us[0].start - units[a - 1].end if a > 0 else 2.0
    gap_after = units[b + 1].start - end if b + 1 < len(units) else 2.0
    reasons = []

    # 1. đầu đoạn là đầu một ý
    fw = norm(words[0].text)
    s_start = min(1.0, gap_before / 0.6) * 0.6 + (0.4 if fw in TOPIC_START or lead else 0.2)
    if lead:
        s_start = max(s_start, 0.75)
        reasons.append(f"bỏ từ nối \"{' '.join(w.text for w in us[0].words[:lead])}\" ở đầu, mở thẳng vào ý mới")
    if fw in BAD_START:
        s_start -= 0.35
    if gap_before >= 0.4 and not lead:
        reasons.append("bắt đầu sau một quãng nghỉ, đúng đầu ý mới")

    # 2. câu mở đầu (6 giây đầu) có móc
    head = " ".join(w.text for w in words if w.start < start + 6)
    kw = _count(head, HOOK_WORDS)
    nums = _numbers(head)
    q = "?" in head
    addr = bool(_count(head, ADDRESS))
    imp = bool(addr and _count(head, IMPERATIVE))
    s_hook = min(1.0, 0.3 * min(len(kw), 2) + 0.2 * min(nums, 2) + 0.3 * q + 0.15 * addr + 0.2 * imp)
    if kw:
        reasons.append("mở bằng từ gây chú ý: " + ", ".join(f"\"{k}\"" for k in kw[:3]))
    if imp:
        reasons.append("nói thẳng với người xem (\"bạn hãy…\", \"anh em nên…\")")
    if nums and not kw:
        reasons.append("mở bằng con số")
    if q:
        reasons.append("mở bằng câu hỏi")

    # 3. mật độ thông tin: con số, từ khoá trên mỗi 10 giây
    n_all = _numbers(text)
    kw_all = _count(text, HOOK_WORDS)
    s_info = min(1.0, (n_all / max(dur, 1) * 10) / 1.5 * 0.6 + (len(kw_all) / max(dur, 1) * 10) / 1.5 * 0.4)
    if n_all >= 3:
        reasons.append(f"có {n_all} con số, nhiều thông tin cụ thể")

    # 4. cuối đoạn trọn ý
    lw = _last_word(us[-1])
    s_end = min(1.0, gap_after / 0.6) * 0.7 + (0.3 if re.search(r"[.!?…]\s*$", us[-1].text) else 0.15)
    if lw in BAD_END:
        s_end -= 0.4
    if gap_after >= 0.4 and lw not in BAD_END:
        reasons.append("kết thúc trọn ý, có quãng nghỉ sau")

    # 5. sạch: ít từ đệm, ít chữ nghe chưa chắc
    fl = sum(1 for w in words if norm(w.text) in fillers)
    low = sum(1 for w in words if w.p < 0.5)
    s_clean = max(0.0, 1 - (fl + low) / max(len(words), 1) * 4)

    # 6. độ dài gần mức mong muốn
    s_len = max(0.0, 1 - abs(dur - target) / max(hi - lo, 1))

    score = 100 * (0.2 * s_start + 0.25 * s_hook + 0.2 * s_info + 0.15 * s_end + 0.1 * s_clean + 0.1 * s_len)
    if _count(text, INTRO):
        score -= 20
        reasons.append("trừ điểm: có câu chào mở video")
    if _count(text, OUTRO):
        score -= 15
        reasons.append("trừ điểm: có câu chào kết video")
    first = " ".join(w.text for w in us[0].words[lead:])
    hook = first if us[0].end - start >= 2.5 or len(us) == 1 else f"{first} {us[1].text}"
    parts = {"start": round(s_start, 2), "hook": round(s_hook, 2), "info": round(s_info, 2), "end": round(s_end, 2), "clean": round(s_clean, 2), "len": round(s_len, 2)}
    return Cand(a, b, start, end, round(max(0.0, min(100.0, score)), 1), parts, reasons, hook.strip(), text.strip(), lead)


def candidates(units: list[Unit], lo: float = 25, hi: float = 60, target: float | None = None) -> list[Cand]:
    target = target or (lo + hi) / 2
    out = []
    for a in range(len(units)):
        for b in range(a, len(units)):
            d = units[b].end - units[a].start
            if d > hi:
                break
            if d >= lo:
                out.append(score_window(units, a, b, lo, hi, target))
    return out


def pick(cands: list[Cand], n: int = 8, max_overlap: float = 1.0) -> list[Cand]:
    """Lấy các đoạn điểm cao nhất, hai short không lặp lời của nhau (chồng tối đa max_overlap giây)."""
    chosen: list[Cand] = []
    for c in sorted(cands, key=lambda c: -c.score):
        ok = all(min(c.end, x.end) - max(c.start, x.start) <= max_overlap for x in chosen)
        if ok:
            chosen.append(c)
        if len(chosen) >= n:
            break
    return sorted(chosen, key=lambda c: c.start)


def _title(hook: str, n: int = 10) -> str:
    ws = hook.split()
    return " ".join(ws[:n]) + ("…" if len(ws) > n else "")


def suggest(prj: Project, n: int = 8, lo: float = 25, hi: float = 60) -> list[dict]:
    tp = prj.work / "transcript.json"
    if not tp.exists():
        raise VEError("Chưa có lời thoại của video dài.", f"Chạy `video-editor transcribe {prj.root}` trước (video 1 giờ chép mất khoảng 1 giờ trên máy 4 nhân).")
    if lo < 5 or hi <= lo:
        raise VEError(f"Độ dài short không hợp lệ: {lo}–{hi} giây.", "Ví dụ: --min 25 --max 60.")
    units = units_from(read_json(tp), prj.cfg.get("fix"), prj.cfg.get("dropSegments"))
    if not units:
        raise VEError("Lời thoại rỗng.", "Kiểm tra lại bước chép lời.")
    total = units[-1].end - units[0].start
    if total < lo:
        raise VEError(f"Video chỉ có {total:.0f} giây lời thoại, ngắn hơn một short ({lo:.0f} giây).", "Giảm --min, hoặc dựng thẳng cả video.")
    picks = pick(candidates(units, lo, hi), n)
    res = []
    for i, c in enumerate(picks, 1):
        # nới đầu, cuối một chút cho khỏi cụt hơi, không lấn sang câu kề
        before = units[c.a].words[c.lead - 1].end if c.lead else (units[c.a - 1].end if c.a > 0 else 0.0)
        s = max(c.start - 0.12, before)
        e = min(c.end + 0.3, units[c.b + 1].start if c.b + 1 < len(units) else c.end + 0.3)
        res.append({"i": i, "start": round(s, 2), "end": round(e, 2), "duration": round(e - s, 1), "score": c.score, "title": _title(c.hook),
                    "hook": c.hook, "reasons": c.reasons, "parts": c.parts, "text": c.text})
    write_json(prj.work / "shorts.json", {"min": lo, "max": hi, "shorts": res})
    _report(prj, res, lo, hi, total)
    return res


def _report(prj: Project, res: list, lo: float, hi: float, total: float) -> Path:
    out = [f"# Đề xuất short từ: {prj.cfg.get('name') or prj.root.name}", "",
           f"Video dài {clock(total)} lời thoại. {len(res)} đoạn {lo:.0f}–{hi:.0f} giây có điểm cao nhất, không chồng lên nhau.",
           "Điểm (0–100) chấm theo: đầu đoạn là đầu ý mới, câu mở đầu có móc, mật độ con số và từ khoá, cuối đoạn trọn ý, ít từ đệm, độ dài vừa.",
           "Điểm chỉ là bước lọc thô theo lời thoại. Đọc lại từng đoạn, bỏ đoạn lạc đề hoặc cần ngữ cảnh phía trước.", "",
           "| # | Gốc | Dài | Điểm | Câu mở đầu | Vì sao chọn |", "|---|---|---|---|---|---|"]
    for r in res:
        out.append(f"| {r['i']} | {clock(r['start'])}–{clock(r['end'])} | {r['duration']:.0f}s | {r['score']:.0f} | {r['hook'].replace('|', '/')} | {'; '.join(r['reasons']) or '—'} |")
    out += ["", "## Lời thoại từng đoạn", ""]
    for r in res:
        out += [f"### {r['i']}. {r['title']} ({clock(r['start'])}–{clock(r['end'])}, {r['duration']:.0f}s, {r['score']:.0f} điểm)", "", r["text"], ""]
    out += ["## Bước tiếp", "", f"Tạo dự án cho đoạn đã chọn: `video-editor shorts {prj.root} --tao 1,3`.",
            f"Mốc tự chọn (giây gốc): `video-editor shorts {prj.root} --tao 35.4-69`.", ""]
    p = prj.work / "de-xuat-short.md"
    p.write_text("\n".join(out), encoding="utf-8")
    return p


def _parse_pick(tok: str, saved: list) -> tuple[float, float, str]:
    tok = tok.strip()
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", tok)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        if b - a < 3:
            raise VEError(f"Đoạn {tok} quá ngắn.", "Ghi mốc theo giây gốc, ví dụ 35.4-69.")
        return a, b, ""
    if tok.isdigit():
        k = int(tok)
        r = next((x for x in saved if x["i"] == k), None)
        if not r:
            raise VEError(f"Không có đoạn số {k} trong đề xuất.", "Xem work/de-xuat-short.md, hoặc chạy lại `video-editor shorts <dự án>`.")
        return r["start"], r["end"], r["title"]
    raise VEError(f"Không hiểu \"{tok}\".", "Ghi số thứ tự đoạn (1,3) hoặc mốc giây (35.4-69).")


def _slug(s: str) -> str:
    import unicodedata

    s = unicodedata.normalize("NFKD", s).replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()[:40] or "short"


def make(prj: Project, picks: str, into: Path | None = None) -> list[Path]:
    """Tạo mỗi đoạn thành một dự án short: cùng file nguồn, chỉ giữ đoạn đó, dùng lại lời thoại đã chép."""
    from .doctor import resolve_model

    if prj.cfg.get("script") or not prj.cfg.get("input"):
        raise VEError("Dự án này không có video nguồn.", "Cắt short chỉ dùng cho dự án từ video người nói (init --input).")
    tp = prj.work / "transcript.json"
    if not tp.exists():
        raise VEError("Chưa có lời thoại của video dài.", f"Chạy `video-editor transcribe {prj.root}` trước.")
    saved = read_json(prj.work / "shorts.json").get("shorts", []) if (prj.work / "shorts.json").exists() else []
    segs = read_json(tp)
    base = into or (prj.root / "shorts")
    made = []
    for tok in [t for t in picks.split(",") if t.strip()]:
        a, b, title = _parse_pick(tok, saved)
        n = len([d for d in base.glob("*") if (d / "project.json").exists()]) + 1 if base.exists() else 1
        root = base / f"{n:02d}-{_slug(title or f'{a:.0f}-{b:.0f}')}"
        if (root / "project.json").exists():
            raise VEError(f"{root} đã có dự án.")
        cfg = json.loads(json.dumps(prj.cfg))
        cfg["name"] = f"{prj.cfg.get('name') or prj.root.name} · short {n:02d}" + (f": {title}" if title else "")
        cfg["input"] = str(prj.path(prj.cfg["input"]))
        cfg["cuts"] = dict(cfg.get("cuts") or {})
        cfg["cuts"]["keep"] = [[round(a, 2), round(b, 2)]]
        cfg["cuts"]["drop"] = [d for d in (cfg["cuts"].get("drop") or []) if d[1] > a and d[0] < b]
        cfg["content"] = json.loads(json.dumps(DEFAULT["content"]))
        cfg["source"] = {"project": str(prj.root), "start": round(a, 2), "end": round(b, 2)}
        # đường dẫn tương đối tính từ dự án dài: đổi sang tuyệt đối để dự án short vẫn tìm thấy
        if cfg.get("background"):
            cfg["background"] = str(prj.path(cfg["background"]))
        if isinstance(cfg.get("music"), dict) and cfg["music"].get("file"):
            cfg["music"]["file"] = str(prj.path(cfg["music"]["file"]))
        elif cfg.get("music"):
            cfg["music"] = str(prj.path(cfg["music"]))
        root.mkdir(parents=True, exist_ok=True)
        write_json(root / "project.json", cfg)
        child = Project(root)
        # chỉ giữ lời thoại quanh đoạn (đủ cho bảng quy chiếu), đánh dấu đã chép để không chép lại cả video dài
        write_json(child.work / "transcript.json", [s for s in segs if s["end"] > a - 2 and s["start"] < b + 2])
        src = child.path(cfg["input"])
        model = resolve_model(cfg["whisper"].get("model"))
        child.mark("transcribe", fingerprint(src, model, cfg["whisper"].get("language", "vi")), source="short", parent=str(prj.root))
        from .build import write_transcript_text

        write_transcript_text(child)
        made.append(root)
        info(f"✓ short {n:02d}: {clock(a)}–{clock(b)} ({b - a:.0f}s) → {root}")
    if made:
        info("  Mỗi short là một dự án riêng: viết content (hook, beats, topics) rồi build → preview → duyệt → render như video thường.")
    return made
