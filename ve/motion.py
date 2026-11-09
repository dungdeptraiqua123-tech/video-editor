"""Cảnh motion: cảnh có sẵn của skill + cảnh viết riêng cho dự án (motion/<tên>.tsx, xem huong-dan/motion.md).

Cảnh viết riêng được kiểm tra trước khi đóng gói:
- tên file: chữ thường không dấu, số, gạch nối; không trùng tên cảnh có sẵn;
- chỉ import từ "react", "remotion", "./kit" (motion kit của skill) và cảnh khác trong cùng thư mục "./<tên>";
- không gọi mạng / eval / require; phải `export default` một thành phần React.
Đóng gói theo dự án: chép cảnh vào bộ dựng đã cài (<engine>/du-an/<mã dự án>/), sinh file vào đăng ký cảnh,
`tsc` kiểm tra kiểu rồi `remotion bundle` ra <dự án>/work/bundle (dự án không có cảnh riêng dùng gói chung).
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

from .env import ENGINE, VEError, info, npx, run

# Tên các cảnh có sẵn: phải khớp registerScenes trong engine/src/motion/scenes.tsx (có test đối chiếu).
BUILTIN = {
    "tieu-de", "chat", "checklist", "dem-so", "song-am", "so-do", "tai-lieu", "terminal",
    "luoi-anh", "dong-ho", "thu-muc", "dong-thoi-gian", "chu-nghieng", "nhan-dan",
}
LAYERS = ("full", "overlay")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
IMPORT_RE = re.compile(r"""^\s*(?:import|export)\s[^;]*?\bfrom\s*["']([^"']+)["']|^\s*import\s*["']([^"']+)["']""", re.M)
FORBIDDEN = [
    (re.compile(r"\b(?:fetch|XMLHttpRequest|WebSocket|EventSource|importScripts|eval)\s*\("), "gọi mạng hoặc eval"),
    (re.compile(r"\bnew\s+Function\b"), "new Function"),
    (re.compile(r"\brequire\s*\("), "require()"),
    (re.compile(r"\bimport\s*\("), "import() động"),
    (re.compile(r"\b(?:localStorage|sessionStorage|indexedDB|document\.cookie)\b"), "bộ nhớ trình duyệt"),
]
MAX_BYTES = 60_000


def scene_dir(prj) -> Path:
    return prj.root / "motion"


def scene_files(prj) -> dict:
    d = scene_dir(prj)
    if not d.is_dir():
        return {}
    return {p.stem: p for p in sorted(d.glob("*.tsx"))}


def known(prj):
    """Hàm kiểm tra tên cảnh dùng được trong dự án (cảnh có sẵn hoặc file motion/<tên>.tsx)."""
    own = set(scene_files(prj))
    return lambda name: isinstance(name, str) and (name in BUILTIN or name in own)


def check_scenes(prj) -> list:
    """Lỗi của các file cảnh viết riêng (trước khi đóng gói). Rỗng = hợp lệ."""
    errs = []
    files = scene_files(prj)
    for name, p in files.items():
        where = f"motion/{p.name}"
        if not NAME_RE.match(name):
            errs.append(f"{where}: tên file chỉ dùng chữ thường không dấu, số và gạch nối (vd. cua-so-chat.tsx)")
        if name in BUILTIN:
            errs.append(f"{where}: trùng tên cảnh có sẵn \"{name}\", đặt tên khác")
        raw = p.read_bytes()
        if len(raw) > MAX_BYTES:
            errs.append(f"{where}: file {len(raw) // 1000} KB, quá lớn (≤ {MAX_BYTES // 1000} KB). Tách bớt hoặc dùng viên gạch của kit")
        code = raw.decode("utf-8", errors="replace")
        for m in IMPORT_RE.finditer(code):
            mod = m.group(1) or m.group(2)
            ok = mod in ("react", "remotion", "./kit") or (mod.startswith("./") and mod[2:].removesuffix(".tsx") in files)
            if not ok:
                errs.append(f"{where}: không được import \"{mod}\". Chỉ dùng \"react\", \"remotion\", \"./kit\" hoặc cảnh khác trong motion/")
        for rx, what in FORBIDDEN:
            if rx.search(code):
                errs.append(f"{where}: không được dùng {what} trong cảnh motion")
        if not re.search(r"^\s*export\s+default\b", code, re.M):
            errs.append(f"{where}: thiếu `export default` (thành phần cảnh)")
    return errs


def _stage_dir(prj) -> Path:
    return ENGINE / "du-an" / hashlib.sha1(str(prj.root).encode()).hexdigest()[:12]


def stage(prj) -> Path:
    """Chép cảnh của dự án vào bộ dựng đã cài và sinh file vào. Trả về thư mục đã dựng."""
    files = scene_files(prj)
    d = _stage_dir(prj)
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    for name, p in files.items():
        shutil.copy2(p, d / p.name)
    (d / "kit.ts").write_text(
        'export * from "../../src/motion/kit";\n'
        'export { M, rgba, shadow } from "../../src/motion/theme";\n'
        'export type { Scene, SceneProps, Safe } from "../../src/motion/registry";\n',
        encoding="utf-8",
    )
    names = list(files)
    idx = ['import { registerRoot } from "remotion";', 'import { RemotionRoot } from "../../src/Root";',
           'import { registerScenes } from "../../src/motion/registry";']
    idx += [f'import S{i} from "./{n}";' for i, n in enumerate(names)]
    idx += ["", "registerScenes({" + ", ".join(f"{json.dumps(n)}: S{i}" for i, n in enumerate(names)) + "});", "registerRoot(RemotionRoot);", ""]
    (d / "index.ts").write_text("\n".join(idx), encoding="utf-8")
    (d / "tsconfig.json").write_text(json.dumps({
        "extends": "../../tsconfig.json",
        "compilerOptions": {"noUnusedLocals": False},
        "include": ["./*.ts", "./*.tsx", "../../src"],
    }, indent=1), encoding="utf-8")
    return d


_TSC_LINE = re.compile(r"^(?P<file>[^(\s]+)\((?P<line>\d+),(?P<col>\d+)\): error (?P<code>TS\d+): (?P<msg>.*)$")


def typecheck(prj) -> list:
    """Kiểm tra kiểu cảnh viết riêng bằng tsc. Trả về lỗi dạng motion/<file>:<dòng>: <thông báo>."""
    if not scene_files(prj):
        return []
    d = stage(prj)
    r = run([npx(), "tsc", "-p", str(d / "tsconfig.json"), "--noEmit", "--pretty", "false"], cwd=ENGINE, quiet=True, check=False)
    out = (r.stdout or "") + (r.stderr or "")
    errs = []
    for line in out.splitlines():
        m = _TSC_LINE.match(line.strip())
        if not m:
            continue
        f = m.group("file").replace("\\", "/")
        if f.startswith("du-an/") or "/du-an/" in f:
            f = "motion/" + f.rsplit("/", 1)[-1]
        errs.append(f"{f}:{m.group('line')}: {m.group('msg')}")
    if r.returncode and not errs:
        errs.append("tsc báo lỗi: " + out.strip()[-600:])
    return errs[:30]


def bundle(prj, base_fp: str) -> Path:
    """Gói riêng cho dự án có cảnh motion viết riêng (tái dùng nếu không đổi gì)."""
    from .project import fingerprint

    out = prj.work / "bundle"
    fp = fingerprint(base_fp, scene_dir(prj))
    stamp = out / ".fp"
    if stamp.exists() and stamp.read_text() == fp:
        return out
    errs = check_scenes(prj)
    if errs:
        raise VEError("Cảnh motion viết riêng chưa hợp lệ:\n  - " + "\n  - ".join(errs), "Sửa các file trong motion/ rồi chạy lại.")
    d = stage(prj)
    info(f"📦 đóng gói bộ dựng kèm {len(scene_files(prj))} cảnh motion của dự án …")
    shutil.rmtree(out, ignore_errors=True)
    run([npx(), "remotion", "bundle", str(d / "index.ts"), "--out-dir", out, "--log", "error"], cwd=ENGINE, quiet=True)
    stamp.write_text(fp)
    return out


# ---------------------------------------------------------------- mô tả cảnh có sẵn (cho `motion list` và đạo diễn)

BUILTIN_INFO = {
    "tieu-de": ("mở chương, ý chính, câu chốt", "kicker, title, accent (dòng nghiêng), sub, dots{n,i,label}, say"),
    "chat": ("thao tác với AI / app chat: gõ lệnh, gửi, nhận trả lời", "title, accent, app, greet, ask, askSay, answer, answerSay, done, doneSay"),
    "checklist": ("các bước, lộ trình, danh sách tự tick", "kicker, title, accent, items[{text, say}], numbered"),
    "dem-so": ("con số, phần trăm, thời gian tăng/giảm", "title, accent, from, to, fmt int|pct|time, dur, say, prefix, suffix, label, strike, clock"),
    "song-am": ("cắt khoảng lặng, rút ngắn thời lượng", "title, accent, from, to (giây), say (lúc cắt), cuts[[a,b]]"),
    "so-do": ("công cụ kết nối, quy trình nhiều thành phần", "title, accent, center{label, icon}, nodes[{label, icon, say, done}]"),
    "tai-lieu": ("file / ghi chú / luật được viết ra", "title, accent, name, lines[{text, say, tag}]"),
    "terminal": ("lệnh, cài đặt, chạy công cụ", "title, accent, app, lines[{cmd | out, say}]"),
    "luoi-anh": ("nhiều ảnh / clip b-roll, ví dụ thực tế", "title, accent, items[{src, label, say}], cols"),
    "dong-ho": ("thời gian trước → sau, tiết kiệm thời gian", "kicker, before, after, say (lúc đổi), dur"),
    "thu-muc": ("gom tài liệu / video mẫu vào một chỗ", "title, accent, label, cards[{label, say}]"),
    "dong-thoi-gian": ("timeline dựng: cắt, phụ đề, motion, âm thanh", "title, accent, tracks[{label, segs[[a,b]]}], say, dur"),
    "chu-nghieng": ("(overlay) từ khoá cảm xúc nổi trên người nói", "small, big, say, y (0–1), size, color"),
    "nhan-dan": ("(overlay) sticker / logo bật vào kèm chú thích", "src, text, note, x, y (0–1), size, say"),
}

# Gợi ý đạo diễn: ý của câu → cảnh hợp (Hermes vẫn tự quyết, đây chỉ là điểm xuất phát).
INTENTS = [
    ("so-lieu", re.compile(r"\d|phần trăm|%|triệu|nghìn|ngàn|gấp|lần", re.I), "dem-so"),
    ("thoi-gian", re.compile(r"phút|tiếng|giờ|ngày|tuần|tháng|năm|trước đây|bây giờ|nhanh hơn|tiết kiệm", re.I), "dong-ho"),
    ("cac-buoc", re.compile(r"bước|đầu tiên|thứ hai|tiếp theo|sau đó|cuối cùng|lộ trình|quy trình", re.I), "checklist"),
    ("cong-cu", re.compile(r"\b(app|ứng dụng|claude|chatgpt|gpt|gemini|agent|công cụ|phần mềm|web|trang)\b", re.I), "chat"),
    ("lenh", re.compile(r"\b(lệnh|cài|setup|terminal|code|chạy)\b", re.I), "terminal"),
    ("ghi-chep", re.compile(r"\b(file|ghi|luật|quy tắc|tài liệu|note)\b", re.I), "tai-lieu"),
    ("cat-ghep", re.compile(r"\b(cắt|khoảng lặng|im lặng|ngừng nghỉ|nói vấp)\b", re.I), "song-am"),
    ("ket-noi", re.compile(r"\b(kết hợp|kết nối|cùng với|tích hợp)\b", re.I), "so-do"),
    ("so-sanh", re.compile(r"\b(so với|thay vì|không phải|khác với)\b", re.I), "tieu-de"),
    ("nhan-manh", re.compile(r"\b(quan trọng|bí mật|đặc biệt|chú ý|newbie|người mới)\b", re.I), "chu-nghieng"),
]


def suggest(sentence: str) -> list:
    """(ý, cảnh gợi ý) cho một câu lời thoại; rỗng = câu chuyển ý / nói chuyện, nên để mặt người nói."""
    return [(k, s) for k, rx, s in INTENTS if rx.search(sentence)]


def plan_sheet(prj) -> Path:
    """work/kich-ban-hinh.md: từng câu lời thoại kèm gợi ý ý/cảnh, để Hermes quyết định cảnh motion (bước đạo diễn)."""
    lt = prj.work / "loi-thoai.txt"
    if not lt.exists():
        raise VEError("Chưa có lời thoại.", f"Chạy `video-editor transcribe {prj.root}` trước.")
    rows = []
    for line in lt.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\[\s*([\d.]+)\s*–\s*([\d.]+)\]\s*(.+?)(\s+⟵.*)?$", line.strip())
        if not m:
            continue
        sent = m.group(3).strip()
        sg = suggest(sent)
        rows.append(f"| {m.group(1)}–{m.group(2)} | {sent} | {', '.join(k for k, _ in sg) or '—'} | {', '.join(dict.fromkeys(s for _, s in sg)) or 'người nói'} | |")
    lib = [f"- `{x['name']}` (điểm {x.get('score', 0)}): {x.get('y', '')}" for x in lib_items() if not x.get("off")][:20]
    txt = "\n".join([
        f"# Kịch bản hình: {prj.root.name}",
        "",
        "Điền cột **Quyết định**: tên cảnh (có sẵn / thư viện / `motion/<tên>.tsx` mới viết), `overlay` hay `full`, hoặc `người nói`.",
        "Gợi ý chỉ dựa vào từ khoá; đọc ý cả câu rồi tự quyết. Luật nhịp ở huong-dan/motion.md.",
        "",
        "| Giây (gốc) | Câu | Ý (gợi ý) | Cảnh gợi ý | Quyết định |",
        "|---|---|---|---|---|",
        *rows,
        "",
        "## Cảnh trong thư viện (đã dùng ở video trước, xếp theo điểm)",
        "",
        *(lib or ["(chưa có)"]),
        "",
    ])
    out = prj.work / "kich-ban-hinh.md"
    out.write_text(txt, encoding="utf-8")
    return out


# ---------------------------------------------------------------- thư viện cảnh (~/.video-editor/motion-lib)

def lib_dir() -> Path:
    from .env import HOME

    return HOME / "motion-lib"


def lib_items() -> list:
    d = lib_dir()
    out = []
    if d.is_dir():
        for m in sorted(d.glob("*/meta.json")):
            try:
                meta = json.loads(m.read_text(encoding="utf-8"))
            except ValueError:
                continue
            meta["name"] = m.parent.name
            out.append(meta)
    return sorted(out, key=lambda x: (-float(x.get("score", 0)), x["name"]))


def _words(s: str) -> set:
    from .timeline import norm

    return {w for w in re.split(r"[^\w]+", norm(s or "")) if len(w) > 1}


def find(query: str, n: int = 5) -> list:
    """Cảnh hợp ý nhất: cảnh có sẵn + cảnh trong thư viện, xếp theo độ trùng từ với ý/nhãn/mô tả rồi tới điểm."""
    q = _words(query)
    rows = [{"name": k, "kind": "co-san", "y": v[0], "params": v[1], "score": 0} for k, v in BUILTIN_INFO.items()]
    rows += [{**m, "kind": "thu-vien"} for m in lib_items() if not m.get("off")]
    for r in rows:
        hay = _words(" ".join([r.get("y", ""), " ".join(r.get("tags", [])), r.get("mo_ta", ""), r["name"].replace("-", " ")]))
        r["match"] = len(q & hay)
    rows = [r for r in rows if r["match"]]
    return sorted(rows, key=lambda r: (-r["match"], -float(r.get("score", 0))))[:n]


def save(prj, scene: str, y: str = "", tags: list | None = None, preview: Path | None = None, source: str = "du-an", auto: bool = False, mo_ta: str = "") -> Path:
    """Lưu cảnh viết riêng của dự án vào thư viện (ghi đè bản cũ cùng tên, giữ điểm cũ)."""
    import time

    src = scene_files(prj).get(scene)
    if not src:
        raise VEError(f"Dự án không có cảnh motion/{scene}.tsx.", "Chỉ lưu được cảnh viết riêng (cảnh có sẵn đã nằm trong skill).")
    d = lib_dir() / scene
    old = {}
    if (d / "meta.json").exists():
        old = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, d / "scene.tsx")
    if preview and Path(preview).is_file():
        shutil.copy2(preview, d / "preview.jpg")
    meta = {
        "y": y or old.get("y", ""),
        "tags": tags if tags is not None else old.get("tags", []),
        "mo_ta": mo_ta or old.get("mo_ta", ""),
        "source": old.get("source", source),
        "score": old.get("score", 0),
        "uses": int(old.get("uses", 0)) + 1,
        "notes": old.get("notes", []),
        "created": old.get("created", time.strftime("%Y-%m-%d")),
        "updated": time.strftime("%Y-%m-%d"),
    }
    if old.get("off"):
        meta["off"] = True
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


def use(prj, name: str, as_name: str | None = None) -> Path:
    """Chép cảnh trong thư viện vào motion/ của dự án để dùng (và sửa) như cảnh viết riêng."""
    src = lib_dir() / name / "scene.tsx"
    if not src.is_file():
        raise VEError(f"Thư viện không có cảnh \"{name}\".", "Xem danh sách: `video-editor motion list`.")
    dst = scene_dir(prj) / f"{as_name or name}.tsx"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def rate(name: str, delta: float, reason: str = "") -> dict:
    """Cộng/trừ điểm cảnh trong thư viện (duyệt: +1, bị góp ý: -1 kèm lý do)."""
    import time

    m = lib_dir() / name / "meta.json"
    if not m.exists():
        raise VEError(f"Thư viện không có cảnh \"{name}\".", "Xem danh sách: `video-editor motion list`.")
    meta = json.loads(m.read_text(encoding="utf-8"))
    meta["score"] = round(float(meta.get("score", 0)) + delta, 2)
    if reason:
        meta.setdefault("notes", []).append(f"{time.strftime('%Y-%m-%d')} {'+' if delta >= 0 else ''}{delta}: {reason}")
        meta["notes"] = meta["notes"][-12:]
    m.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return meta


def set_off(name: str, off: bool = True) -> None:
    m = lib_dir() / name / "meta.json"
    if not m.exists():
        raise VEError(f"Thư viện không có cảnh \"{name}\".", "Xem danh sách: `video-editor motion list`.")
    meta = json.loads(m.read_text(encoding="utf-8"))
    if off:
        meta["off"] = True
    else:
        meta.pop("off", None)
    m.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


def autosave(prj, approved: bool = False) -> list:
    """Khi người dùng duyệt storyboard: lưu mọi cảnh viết riêng của dự án vào thư viện, cộng điểm cảnh đã dùng."""
    beats = (prj.cfg.get("content") or {}).get("beats") or []
    heads = {}
    for b in beats:
        g = b.get("g") or {}
        if g.get("type") == "motion":
            heads.setdefault(g.get("scene"), b.get("head") or (g.get("params") or {}).get("title") or (g.get("params") or {}).get("y") or "")
    soat = prj.root / "out" / "motion-soat"
    saved = []
    for name in scene_files(prj):
        prev = sorted(soat.glob(f"*-{name}-*.jpg")) if soat.is_dir() else []
        save(prj, name, y=heads.get(name, ""), preview=prev[len(prev) // 2] if prev else None, auto=True)
        if approved:
            rate(name, 1, f"dùng trong video đã duyệt ({prj.root.name})")
        saved.append(name)
    return saved
