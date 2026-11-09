"""Soát bố cục tự động (không cần model ảnh): đọc số đo bộ dựng ghi khi chụp storyboard / ảnh soát motion
(engine/src/Probe.tsx → work/probe.json), đối chiếu luật, viết out/soat-bo-cuc.md để Hermes tự sửa trước khi gửi duyệt.

Bắt được: chữ bị cắt / tràn / ra ngoài khung, hai lớp đồ hoạ đè nhau, chữ bị ô mặt người nói che, đồ hoạ che mặt
người nói, đồ hoạ đè phụ đề, mã icon (lu:… / si:…) hiện thành chữ, cảnh mở ra trống / khung trống, chữ lẻ một từ cuối dòng.
"""
from __future__ import annotations

import re
from pathlib import Path

from .bang import clock
from .env import read_json, write_json

NAMES = {
    "tieu-de": "tiêu đề", "dong-nghieng": "dòng nghiêng", "chu": "chữ", "the": "thẻ", "cua-so": "cửa sổ",
    "bong-bong": "bong bóng chat", "y": "ý", "sticker": "sticker", "nut": "nút sơ đồ", "nhan": "nhãn",
    "the-chu-de": "thẻ chủ đề", "the-tieu-de": "tiêu đề khung đồ hoạ", "mo-dau": "tiêu đề mở đầu", "keu-goi": "câu kêu gọi",
    "o-mat": "ô mặt người nói", "cot": "cột so sánh", "nhanh": "nhánh", "dieu-kien": "điều kiện", "hoi": "câu hỏi",
    "dap": "câu trả lời", "cau-hoi": "câu hỏi", "tra-loi": "câu trả lời",
}
TEXT_KINDS = {"text", "cta", "hook", "topic"}
MIN_O = 0.35


def _area(r) -> float:
    return max(0.0, r[2]) * max(0.0, r[3])


def _inter(a, b) -> float:
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[0] + a[2], b[0] + b[2]), min(a[1] + a[3], b[1] + b[3])
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def _label(it: dict) -> str:
    n = NAMES.get(it.get("name") or "", it.get("name") or it.get("kind"))
    if it.get("kind") == "captions":
        n = "phụ đề"
    txt = (it.get("text") or "").strip()
    return f"{n} «{txt[:40]}»" if txt and it.get("kind") in TEXT_KINDS else n


def _group(it: dict) -> str:
    return f"scene:{it['scene']}" if it.get("scene") else it.get("kind", "")


def _where(d: dict, t: float, it: dict | None = None) -> str:
    if t < d.get("hookSec", 0):
        return "mở đầu"
    if t >= d["duration"] - d.get("outroSec", 0):
        return "phần kết"
    for i, b in enumerate(d.get("beats", [])):
        if b["start"] - 0.05 <= t < b["end"] + 0.05 and (not it or not it.get("scene") or (b["g"].get("scene") == it.get("scene"))):
            g = b["g"]
            return f"beats[{i}] " + (f"motion {g.get('scene')}" + (" (nổi)" if g.get("layer") == "overlay" else "") if g.get("type") == "motion" else (b.get("head") or g.get("type")))
    return "người nói"


def analyze(d: dict, probes: list, shots: dict) -> list[dict]:
    """probes: các dòng VE_PROBE; shots: {đường dẫn ảnh: (giây, loại "storyboard" | "motion-1|2|3")}. → [{muc, where, t, msg}]"""
    fps = d["format"]["fps"]
    shots = {Path(k).as_posix(): v for k, v in (shots or {}).items()}
    issues: list[dict] = []

    def add(level, t, where, msg):
        issues.append({"muc": level, "t": round(t, 2), "where": where, "msg": msg})

    for pr in probes:
        if pr.get("error"):
            continue
        t = pr.get("frame", 0) / fps
        kind = shots.get(Path(pr.get("output", "")).as_posix(), (t, "storyboard"))[1]
        W, H = pr["w"], pr["h"]
        items = [it for it in pr.get("items", []) if it.get("o", 1) >= MIN_O and _area(it["r"]) > 4]
        for c in sorted(set(pr.get("codes") or [])):
            add("loi", t, _where(d, t), f"mã icon `{c}` hiện ra thành chữ trên hình (khoá này không phải ô icon, hoặc tên icon sai)")
        pip_on = any(it["kind"] == "pip" for it in items)
        for it in items:
            if it["kind"] in TEXT_KINDS and it.get("text"):
                if it.get("shown", 1) < 0.97:
                    add("loi", t, _where(d, t, it), f"{_label(it)} bị cắt mất {round((1 - it['shown']) * 100)}% (tràn khỏi khung hoặc ra ngoài màn hình)")
                elif it.get("over"):
                    add("loi", t, _where(d, t, it), f"{_label(it)} tràn ô chứa")
                last = (it.get("lastLine") or "").strip()
                if it.get("lines", 1) >= 2 and last and " " not in last and len(last) <= 7:
                    add("goi-y", t, _where(d, t, it), f"{_label(it)}: chữ \"{last}\" đứng lẻ một mình ở dòng cuối (rút gọn chữ hoặc đổi cách ngắt)")
        # đè nhau giữa các lớp (không tính phần tử nằm trong nhau); khung đã báo thì không báo lại từng chữ bên trong
        flagged: set = set()
        idx = {id(it): k for k, it in enumerate(pr.get("items", []))}
        for i, a in enumerate(items):
            for j in range(i + 1, len(items)):
                b = items[j]
                ia, ib = idx[id(a)], idx[id(b)]
                if ia in b.get("anc", []) or ib in a.get("anc", []) or {a["kind"], b["kind"]} <= {"box"}:
                    continue
                ov = _inter(a["r"], b["r"])
                small = min(_area(a["r"]), _area(b["r"]))
                kinds = {a["kind"], b["kind"]}
                if "pip" in kinds:
                    # ô mặt che dù chỉ một mẩu chữ cũng mất chữ
                    other = b if a["kind"] == "pip" else a
                    if other["kind"] in TEXT_KINDS and _area(other["r"]) and ov / _area(other["r"]) > 0.02:
                        add("loi", t, _where(d, t, other), f"{_label(other)} bị ô mặt người nói che")
                    continue
                if not small or ov / small < 0.12:
                    continue
                if "captions" in kinds:
                    other = b if a["kind"] == "captions" else a
                    if not flagged & set(other.get("anc", [])):
                        add("loi", t, _where(d, t, other), f"{_label(other)} đè lên phụ đề")
                    flagged.add(idx[id(other)])
                    continue
                if _group(a) == _group(b) and not ({"text"} <= kinds and a["kind"] == b["kind"]):
                    continue  # chữ nằm trên thẻ của chính cảnh: bình thường
                add("loi", t, _where(d, t, a), f"{_label(a)} và {_label(b)} đè lên nhau")
        # che mặt người nói (khi người nói toàn màn hình)
        face = pr.get("face")
        if face and not pip_on:
            fr = [face["x"], face["y"], face["w"], face["h"]]
            fa = _area(fr)
            for it in items:
                if it["kind"] in ("text", "box", "topic") and fa and _area(it["r"]):
                    inter = _inter(it["r"], fr)
                    if inter / fa > 0.18:
                        add("loi", t, _where(d, t, it), f"{_label(it)} che {round(inter / fa * 100)}% mặt người nói")
                    elif it["kind"] == "text" and inter / _area(it["r"]) > 0.3:
                        add("loi", t, _where(d, t, it), f"{_label(it)} nằm đè lên mặt người nói (đầu / trán / mắt)")
        # cảnh motion trống
        if kind.startswith("motion"):
            scene_items = [it for it in items if it.get("scene")]
            texts = [it for it in scene_items if it["kind"] in TEXT_KINDS and it.get("text")]
            shown = [sc for sc in pr.get("scenes", []) if sc.get("o", 1) >= MIN_O]
            if shown:
                texts = texts or [sc for sc in shown if sc.get("text")]
            if kind == "motion-1" and not texts:
                add("loi", t, _where(d, t), "cảnh mở ra chưa có chữ / nội dung chính (phải hiện trong 0,5 s đầu cảnh)")
            for it in scene_items:
                if it["kind"] == "box" and it.get("filled") is False and it.get("name") in ("cua-so", "the") and kind in ("motion-1", "motion-2"):
                    add("loi" if kind == "motion-2" else "goi-y", t, _where(d, t, it), f"{_label(it)} còn trống (chưa có nội dung bên trong)")
    # gộp lỗi lặp lại ở nhiều ảnh
    seen, out = {}, []
    for x in sorted(issues, key=lambda x: (x["t"])):
        key = (x["where"], re.sub(r"\d+%", "", x["msg"]))
        if key in seen:
            seen[key]["times"].append(x["t"])
            if x["muc"] == "loi":  # ảnh sau vẫn còn lỗi (ví dụ khung vẫn trống giữa cảnh) → nâng thành lỗi
                seen[key]["muc"] = "loi"
            continue
        x["times"] = [x["t"]]
        seen[key] = x
        out.append(x)
    return out


def report(prj, d: dict, probes: list, shots: dict) -> list[dict]:
    """Ghi out/soat-bo-cuc.md (+ work/soat-bo-cuc.json) và trả về danh sách lỗi."""
    issues = analyze(d, probes, shots)
    write_json(prj.work / "soat-bo-cuc.json", issues)
    errs = [x for x in issues if x["muc"] == "loi"]
    hints = [x for x in issues if x["muc"] != "loi"]
    lines = [f"# Soát bố cục tự động: {prj.cfg.get('name') or prj.root.name}", "",
             f"Đo trên {len(probes)} ảnh (storyboard + ảnh soát motion). "
             + ("**Không thấy lỗi bố cục.**" if not issues else f"**{len(errs)} lỗi phải sửa**, {len(hints)} gợi ý."), ""]
    if errs:
        lines += ["## Lỗi phải sửa trước khi gửi duyệt", ""]
        lines += [f"- {', '.join(clock(t) for t in x['times'][:4])} · {x['where']}: {x['msg']}" for x in errs]
        lines += [""]
    if hints:
        lines += ["## Gợi ý", ""] + [f"- {', '.join(clock(t) for t in x['times'][:4])} · {x['where']}: {x['msg']}" for x in hints] + [""]
    if issues:
        lines += ["## Cách sửa thường dùng", "",
                  "- Chữ bị cắt / tràn: rút gọn chữ (tiêu đề ≤ 26 ký tự, dòng nghiêng ≤ 22), hoặc bỏ `w` cố định để tiêu đề tự co.",
                  "- Che mặt / đè phụ đề ở cảnh nổi: chuyển cảnh sang `\"layer\": \"full\"` (ô mặt ở góc) hoặc dùng cảnh gọn hơn.",
                  "- Hai lớp đè nhau: dời một khung, rút ngắn khung trước, hoặc bỏ khung trùng ý.",
                  "- Mã icon hiện thành chữ: đặt mã `lu:` / `si:` vào khoá `icon`; tên icon phải có thật.",
                  "- Cảnh trống: neo `say` của phần tử chính vào từ ở ĐẦU cảnh, hoặc cho cửa sổ có nội dung ngay khi mở.", ""]
    (prj.out / "soat-bo-cuc.md").write_text("\n".join(lines), encoding="utf-8")
    return issues


def load_probes(path: Path) -> list:
    try:
        return read_json(path) if path.exists() else []
    except ValueError:
        return []
