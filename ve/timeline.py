"""Hệ thời gian chung: sửa lời, chọn đoạn giữ/bỏ, đổi thời gian gốc sang thời gian sau khi cắt.

Mọi thứ hiển thị (phụ đề, đồ hoạ, zoom, file SRT) đều đi qua `Timeline.map`, nên cắt xong không lệch nhau.
Không phụ thuộc thư viện ngoài để kiểm thử được độc lập.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

PUNCT = ".,!?;:…\"'“”()[]"

# Từ đệm thường gặp khi nói tiếng Việt. Giữ danh sách thận trọng: "à", "ừ" nhiều khi có nghĩa nên không đưa vào.
DEFAULT_FILLERS = ["ờ", "ờm", "ừm", "ơ", "ưm", "hừm", "uh", "um", "uhm", "ehm"]

# Từ láy hợp lệ, không coi là nói vấp khi lặp ("từ từ", "dần dần"...).
REDUP_OK = {"từ", "dần", "nhiều", "lâu", "ngày", "năm", "tháng", "người", "đâu", "ai", "gì", "nào", "rồi", "vậy", "cứ", "luôn", "mãi", "chút", "xa", "gần", "khá", "hơi"}


def norm(t: str) -> str:
    return t.lower().strip(PUNCT + " ")


@dataclass
class Word:
    text: str
    start: float
    end: float
    p: float = 1.0

    @staticmethod
    def from_any(d: dict) -> "Word":
        # nhận cả định dạng transcript (w,s,e,p) lẫn định dạng dữ liệu (text,start,end)
        return Word(str(d.get("text", d.get("w", ""))).strip(), float(d.get("start", d.get("s", 0))), float(d.get("end", d.get("e", 0))), float(d.get("p", 1.0)))


def words_from_transcript(segs: list, drop_segments: list | None = None) -> list[Word]:
    drop = drop_segments or []
    out = []
    for s in segs:
        if any(abs(s["start"] - d) < 0.05 for d in drop):
            continue
        ws = s.get("words", [])
        # Whisper đánh dấu đầu từ bằng khoảng trắng; mẩu không có khoảng trắng là phần đuôi của từ trước
        # (số "85" + ".000", "300" + "-400"). Chỉ ghép khi đoạn dùng quy ước này.
        spaced = any(str(w.get("w", "")).startswith(" ") for w in ws)
        first = len(out)
        for w in ws:
            x = Word.from_any(w)
            if not (x.text and x.end >= x.start):
                continue
            raw = str(w.get("w", " "))
            if spaced and len(out) > first and raw[:1] not in (" ", "\t"):
                prev = out[-1]
                out[-1] = Word(prev.text + x.text, prev.start, max(prev.end, x.end), min(prev.p, x.p))
            else:
                out.append(x)
    out.sort(key=lambda w: w.start)
    return out


def _glue(toks: list[str]) -> list[str]:
    out: list[str] = []
    for t in toks:
        if out and t[:1] in ".,-–/" and t[1:2].isdigit():
            out[-1] += t
        else:
            out.append(t)
    return out


def apply_fixes(words: list[Word], fixes: list) -> list[Word]:
    """fixes: [["cụm sai", "cụm đúng"], ...]. Cụm đúng rỗng = xoá. So khớp không phân biệt hoa thường và dấu câu."""
    fx = []
    for bad, good in fixes:
        # cụm viết theo kiểu tách cũ ("3 -400") cũng khớp với từ đã ghép ("3-400")
        for toks in {tuple(bad.split()), tuple(_glue(bad.split()))}:
            if toks:
                fx.append(([norm(x) for x in toks], good.split()))
    out, i = [], 0
    while i < len(words):
        for bad, good in fx:
            n = len(bad)
            if [norm(w.text) for w in words[i:i + n]] == bad:
                seg = words[i:i + n]
                if good:
                    # giữ dấu câu cuối của cụm gốc nếu cụm sửa không ghi ("Sol," + ["Sol","Solana"] -> "Solana,")
                    tail = seg[-1].text[len(seg[-1].text.rstrip(PUNCT)):]
                    if tail and not good[-1].endswith(tuple(PUNCT)):
                        good = good[:-1] + [good[-1] + tail]
                    s0, e0 = seg[0].start, seg[-1].end
                    step = (e0 - s0) / len(good)
                    out += [Word(g, s0 + k * step, s0 + (k + 1) * step) for k, g in enumerate(good)]
                i += n
                break
        else:
            out.append(words[i])
            i += 1
    return out


def find_fillers(words: list[Word], fillers: list[str]) -> list[int]:
    fs = {norm(f) for f in fillers}
    return [i for i, w in enumerate(words) if norm(w.text) in fs]


def find_stumbles(words: list[Word], max_n: int = 3) -> list[tuple[int, int]]:
    """Cụm 1-3 từ bị nói lặp liền nhau ("thì thì", "là cái là cái"). Trả (đầu, cuối) của lần nói hỏng (lần đầu).
    Bỏ qua từ láy hợp lệ và trường hợp lặp có dấu câu ở giữa (thường là chủ ý nhấn mạnh)."""
    out, i = [], 0
    while i < len(words):
        hit = None
        for n in range(max_n, 0, -1):
            a = [norm(w.text) for w in words[i:i + n]]
            b = [norm(w.text) for w in words[i + n:i + 2 * n]]
            if len(b) == n and a == b and all(a):
                if n == 1 and a[0] in REDUP_OK:
                    continue
                if re.search(r"[.!?,]$", words[i + n - 1].text):
                    continue
                hit = (i, i + n - 1)
                break
        if hit:
            out.append(hit)
            i = hit[1] + 1
        else:
            i += 1
    return out


@dataclass
class CutConfig:
    gap: float = 0.55  # khoảng lặng dài hơn mức này thì cắt
    pad: float = 0.12  # chừa lại trước và sau mỗi từ
    tail: float = 0.3  # chừa thêm sau từ cuối
    fillers: str = "auto"  # auto | suggest | off
    filler_words: list = field(default_factory=lambda: list(DEFAULT_FILLERS))
    stumbles: str = "suggest"  # auto | suggest | off
    drop: list = field(default_factory=list)  # [[giây đầu, giây cuối], ...] theo video gốc
    keep: list = field(default_factory=list)  # nếu có: chỉ giữ các khoảng này
    silence: bool = True

    @staticmethod
    def from_dict(d: dict | None) -> "CutConfig":
        c = CutConfig()
        for k, v in (d or {}).items():
            if hasattr(c, k):
                setattr(c, k, v)
        return c


def _inside(t0: float, t1: float, ranges: list) -> bool:
    mid = (t0 + t1) / 2
    return any(a <= mid <= b for a, b in ranges)


@dataclass
class Timeline:
    segments: list  # [[đầu, cuối], ...] theo thời gian gốc, tăng dần, không chồng
    words: list  # từ còn giữ, thời gian sau khi cắt
    removed: dict  # loại -> danh sách {text,start,end} theo thời gian gốc
    suggestions: dict  # loại -> gợi ý chưa áp dụng
    src_duration: float

    @property
    def duration(self) -> float:
        return sum(b - a for a, b in self.segments)

    def map(self, t: float) -> float:
        """Thời gian gốc -> thời gian sau khi cắt. Điểm nằm trong đoạn bị cắt dồn về đầu đoạn kế tiếp."""
        acc = 0.0
        for a, b in self.segments:
            if t < a:
                return acc
            if t <= b:
                return acc + t - a
            acc += b - a
        return acc

    def unmap(self, t: float) -> float:
        acc = 0.0
        for a, b in self.segments:
            if t <= acc + (b - a):
                return a + (t - acc)
            acc += b - a
        return self.segments[-1][1] if self.segments else 0.0


def build_timeline(words: list[Word], src_duration: float, cfg: CutConfig) -> Timeline:
    removed: dict = {"filler": [], "stumble": [], "drop": [], "outside_keep": []}
    suggestions: dict = {"filler": [], "stumble": []}
    gone = set()

    fill = find_fillers(words, cfg.filler_words) if cfg.fillers != "off" else []
    for i in fill:
        (removed["filler"] if cfg.fillers == "auto" else suggestions["filler"]).append(i)
        if cfg.fillers == "auto":
            gone.add(i)
    if cfg.stumbles != "off":
        for a, b in find_stumbles(words):
            if cfg.stumbles == "auto":
                gone.update(range(a, b + 1))
                removed["stumble"].append((a, b))
            else:
                suggestions["stumble"].append((a, b))
    for i, w in enumerate(words):
        if cfg.drop and _inside(w.start, w.end, cfg.drop):
            gone.add(i)
            removed["drop"].append(i)
        elif cfg.keep and not _inside(w.start, w.end, cfg.keep):
            gone.add(i)
            removed["outside_keep"].append(i)

    kept = [w for i, w in enumerate(words) if i not in gone]
    if not kept:
        raise ValueError("Sau khi cắt không còn từ nào. Kiểm tra lại cuts.drop / cuts.keep.")

    if cfg.silence:
        segs: list = []
        for w in kept:
            s, e = max(0.0, w.start - cfg.pad), min(src_duration, w.end + cfg.pad)
            if segs and s - segs[-1][1] < cfg.gap - 2 * cfg.pad:
                segs[-1][1] = max(segs[-1][1], e)
            else:
                segs.append([s, e])
        segs[-1][1] = min(segs[-1][1] + cfg.tail, src_duration)
    else:
        segs = [[0.0, src_duration]]

    # cắt bỏ phần từ đã loại còn nằm trong đoạn giữ (từ đệm, vấp, drop) bằng cách khoét lỗ
    holes = [[words[i].start, words[i].end] for i in sorted(gone)]
    holes += [list(r) for r in cfg.drop]
    if cfg.keep:
        # ngoài keep là lỗ
        ks = sorted(cfg.keep)
        prev = 0.0
        for a, b in ks:
            if a > prev:
                holes.append([prev, a])
            prev = max(prev, b)
        holes.append([prev, src_duration])
    segs = _subtract(segs, holes, kept)

    tl = Timeline(segments=[[round(a, 3), round(b, 3)] for a, b in segs if b - a > 0.04], words=[], removed={}, suggestions={}, src_duration=src_duration)
    tl.words = [{"text": w.text, "start": round(tl.map(w.start), 3), "end": round(tl.map(w.end), 3)} for w in kept if _covered(w, tl.segments)]
    js = lambda idx: [{"text": words[i].text, "start": round(words[i].start, 2), "end": round(words[i].end, 2)} for i in idx]
    jr = lambda pairs: [{"text": " ".join(x.text for x in words[a:b + 1]), "start": round(words[a].start, 2), "end": round(words[b].end, 2)} for a, b in pairs]
    tl.removed = {"filler": js(removed["filler"]), "stumble": jr(removed["stumble"]), "drop": js(removed["drop"]), "outside_keep": len(removed["outside_keep"])}
    tl.suggestions = {"filler": js(suggestions["filler"]), "stumble": jr(suggestions["stumble"])}
    return tl


def _covered(w: Word, segs: list) -> bool:
    mid = (w.start + w.end) / 2
    return any(a <= mid <= b for a, b in segs)


def _subtract(segs: list, holes: list, kept: list[Word]) -> list:
    """segs trừ holes. Lỗ không được ăn vào từ còn giữ: co lỗ lại nếu chạm từ giữ."""
    out = [list(s) for s in segs]
    for h0, h1 in sorted(holes):
        # co lỗ để không cắt mất từ còn giữ
        for w in kept:
            if w.start < h1 and w.end > h0:
                if w.start <= h0 < w.end:
                    h0 = w.end
                if w.start < h1 <= w.end:
                    h1 = w.start
        if h1 - h0 <= 0.02:
            continue
        nxt = []
        for a, b in out:
            if h1 <= a or h0 >= b:
                nxt.append([a, b])
                continue
            if a < h0:
                nxt.append([a, h0])
            if h1 < b:
                nxt.append([h1, b])
        out = nxt
    return out
