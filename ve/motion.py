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
    "so-sanh", "re-nhanh", "luu-y", "hoi-dap",
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
    from . import hf as HF

    if HF.is_hf(prj):
        return HF.typecheck(prj)
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
    "so-sanh": ("so sánh A với B, chọn một bên (sàn hay ví, cách cũ hay cách mới)", "kicker, title, accent, a{label, icon, items[], badge}, b{…}, say, pick a|b, pickSay, verdict, verdictSay, vs"),
    "re-nhanh": ("rẽ nhánh: nếu … thì … / còn không thì …", "title, accent, cond, condSay, yes{label, text, icon, say}, no{…}, yesLabel, noLabel"),
    "luu-y": ("lưu ý / mẹo / cảnh báo một ý quan trọng", "kind luu-y|meo|canh-bao, label, title, text, textSay, icon, say, headline, accent"),
    "hoi-dap": ("câu hỏi (người xem / người hỏi) rồi câu trả lời, KHÔNG có app chat", "who, q, qSay, a, aSay, answerLabel, title, accent"),
}

# Ví dụ khung cho từng cảnh có sẵn: dán vào content.beats[].g (say / xxxSay = cụm lời đúng chữ trong loi-thoai.txt, build đổi thành giây).
# Mọi khoá trong params đều tuỳ chọn; bỏ khoá thì cảnh dùng mặc định (ghi trong DEFAULTS).
EXAMPLES = {
    "tieu-de": {"layer": "full", "params": {"kicker": "Phần 1", "title": "Đầu tư dài hạn", "accent": "để ở đâu?", "sub": "2–3 năm trở lên",
                                            "say": "đầu tư dài", "subSay": "hai ba năm"}},
    "chat": {"layer": "full", "params": {"title": "Hỏi AI", "accent": "một câu là xong", "app": "ChatGPT", "greet": "Chào bạn!",
                                         "ask": "Viết kịch bản 30 giây", "askSay": "viết kịch bản", "answer": "Đây là kịch bản…",
                                         "answerSay": "trả lời", "done": "Xong trong 10 giây", "doneSay": "xong"}},
    "checklist": {"layer": "full", "params": {"kicker": "Lộ trình", "title": "Học edit video", "accent": "trong 7 ngày", "numbered": True,
                                              "items": [{"text": "Cài Claude Code", "say": "cài Claude"}, {"text": "Tạo CLAUDE.md", "say": "tạo file"}]}},
    "dem-so": {"layer": "full", "params": {"title": "Thời gian dựng", "accent": "giảm mạnh", "from": 240, "to": 30, "fmt": "time",
                                           "dur": 1.4, "say": "còn 30 phút", "label": "cho mỗi video", "strike": False, "clock": False}},
    "song-am": {"layer": "full", "params": {"title": "Cắt khoảng lặng", "accent": "tự động", "from": 30, "to": 21, "say": "cắt hết",
                                            "label": "Độ dài video", "cuts": [[0.22, 0.3], [0.52, 0.6]]}},
    "so-do": {"layer": "full", "params": {"title": "Một hệ thống", "accent": "nhiều công cụ", "center": {"label": "Hermes", "icon": "lu:bot"},
                                          "nodes": [{"label": "Claude", "icon": "si:anthropic", "say": "Claude"}, {"label": "Remotion", "icon": "lu:clapperboard", "say": "Remotion", "done": True},
                                                    {"label": "VPS", "icon": "lu:server", "say": "VPS"}]}},
    "tai-lieu": {"layer": "full", "params": {"title": "Ghi luật", "accent": "một lần", "name": "GHI-NHO.md",
                                             "lines": [{"text": "Phụ đề chữ to", "say": "phụ đề"}, {"text": "Không dùng màu đỏ", "say": "màu đỏ", "tag": "luật mới"}]}},
    "terminal": {"layer": "full", "params": {"title": "Cài đặt", "accent": "một lệnh", "app": "Terminal",
                                             "lines": [{"cmd": "npm i -g claude", "say": "cài"}, {"out": "✓ xong", "say": "xong"}]}},
    "luoi-anh": {"layer": "full", "params": {"title": "Ví dụ thật", "accent": "từ kênh", "cols": 3,
                                             "items": [{"src": "media/a.jpg", "label": "Video 1", "say": "ví dụ"}, {"src": "media/b.mp4", "label": "Video 2"}]}},
    "dong-ho": {"layer": "full", "params": {"kicker": "Trước → sau", "before": "3–4 tiếng", "after": "20 phút", "say": "chỉ còn", "dur": 1.8}},
    "thu-muc": {"layer": "full", "params": {"title": "Gom tài liệu", "accent": "một chỗ", "label": "tham-khao/",
                                            "cards": [{"label": "video-mau.mp4", "say": "video mẫu"}, {"label": "kich-ban.md", "say": "kịch bản"}]}},
    "dong-thoi-gian": {"layer": "full", "params": {"title": "Quy trình dựng", "accent": "tự động", "say": "dựng", "dur": 1.6,
                                                   "tracks": [{"label": "Cắt", "segs": [[0, 0.3], [0.4, 1]]}, {"label": "Phụ đề", "segs": [[0, 1]]}]}},
    "chu-nghieng": {"layer": "overlay", "params": {"small": "dành cho", "big": "người mới", "say": "người mới", "y": 0.16}},
    "nhan-dan": {"layer": "overlay", "params": {"src": "media/logo.png", "note": "là em đây", "x": 0.12, "y": 0.2, "size": 240, "say": "là em"}},
    "so-sanh": {"layer": "full", "params": {"kicker": "Đầu tư dài hạn", "title": "Để coin ở đâu?", "say": "sàn hay ví",
                                            "a": {"label": "Sàn giao dịch", "icon": "lu:building-2", "items": [{"text": "Có staking", "say": "staking"}]},
                                            "b": {"label": "Ví cá nhân", "icon": "lu:wallet", "items": [{"text": "Tự giữ khoá", "say": "ví cá nhân"}], "badge": "Nên chọn"},
                                            "pick": "b", "pickSay": "nên để ở ví cá nhân", "verdict": "Giữ lâu → ví cá nhân"}},
    "re-nhanh": {"layer": "full", "params": {"title": "Để đâu cho đúng?", "cond": "Coin có staking / sinh lời trên sàn?", "condSay": "trên sàn",
                                             "yes": {"label": "Để trên sàn", "text": "staking, dòng tiền thụ động", "icon": "lu:building-2", "say": "thì em để trên sàn"},
                                             "no": {"label": "Rút về ví lạnh", "text": "Bitcoin, giữ lâu", "icon": "lu:snowflake", "say": "còn không thì"}}},
    "luu-y": {"layer": "full", "params": {"kind": "canh-bao", "title": "Đừng để hết trên sàn", "text": "sàn có thể bị hack hoặc khoá rút", "say": "đừng để"}},
    "hoi-dap": {"layer": "full", "params": {"who": "Bạn hỏi", "q": "Đầu tư 2–3 năm: sàn hay ví?", "qSay": "anh ơi cho em hỏi",
                                            "a": "Ví cá nhân, an toàn hơn", "aSay": "nên để ở ví cá nhân"}},
}

# Mặc định của cảnh có sẵn khi bỏ khoá (đọc từ engine/src/motion/scenes.tsx; có test đối chiếu tên khoá với EXAMPLES).
DEFAULTS = {
    "tieu-de": "size 112; sub hiện sau tiêu đề 0,6 s; dots {n, i, label} = chấm tiến độ",
    "chat": "app \"Claude\"; ask gõ 18 ký tự/s rồi gửi; h (cao cửa sổ) 640; overlay = cửa sổ không tiêu đề",
    "checklist": "mỗi ý không say thì tick cách nhau 0,6 s; itemSize 46; overlay = thẻ giấy nhỏ có title",
    "dem-so": "from 0, to 100, fmt int (time = giây hiện m:ss, pct = %), dur 1,4 s, decimals 0, numSize 200; clock = thêm đồng hồ quay",
    "song-am": "from 30, to 21 (giây); say = lúc cắt (mặc định 1,2 s); cuts = các khoảng 0–1 trên sóng âm",
    "so-do": "tối đa 4 nodes; done = hiện tick sau 0,6 s; center.icon mặc định ✳",
    "tai-lieu": "name \"CLAUDE.md\"; mỗi dòng không say cách nhau 0,5 s; tag = nhãn nhỏ cạnh dòng",
    "terminal": "app \"Terminal\"; h 620; mỗi dòng cmd (gõ) hoặc out (kết quả)",
    "luoi-anh": "cols 3; src là file trong media/ (ảnh hoặc clip)",
    "dong-ho": "say = lúc chữ trước đổi sang chữ sau (mặc định 1,4 s); kim quay 4 vòng",
    "thu-muc": "label \"tham-khao/\"; thẻ rơi vào cách nhau 0,5 s",
    "dong-thoi-gian": "segs = khoảng 0–1 trên rãnh; tracks[].color tuỳ chọn",
    "chu-nghieng": "y 0.16 (tỉ lệ chiều cao), size 104, color trắng; chỉ dùng layer overlay",
    "nhan-dan": "x 0.12, y 0.2 (tỉ lệ khung), size 240; src ảnh, hoặc text = mã icon lu:/si: hay chữ ngắn; chỉ dùng layer overlay",
    "so-sanh": "items là chữ hoặc {text, say}; pick tô viền màu nhấn bên được chọn, bên kia mờ đi; badge mặc định \"Nên chọn\"; vs \"VS\"; overlay = hai cột dưới mặt người nói",
    "re-nhanh": "nhánh yes màu xanh, no màu nhấn; mỗi nhánh hiện đúng lúc nói (yes.say / no.say); yesLabel \"Có\", noLabel \"Không\"",
    "luu-y": "kind luu-y (ghim, màu nhấn) | meo (bóng đèn, xanh) | canh-bao (tam giác, đỏ); icon lu:/si: thay icon mặc định; headline = tiêu đề lớn phía trên (full)",
    "hoi-dap": "who \"Câu hỏi\"; câu trả lời hiện lúc aSay (tối thiểu 0,5 s sau câu hỏi); dùng thay chat khi không có app",
}

_KIT_RE = re.compile(r"^export const (\w+): React\.FC<(.*)> = ", re.M)

ANIM_REF = [
    "`useSec()` → giây từ lúc cảnh mở",
    "`useSpring(at, {damping, stiffness, mass}?)` → 0 → 1 có nảy, bắt đầu lúc `at`",
    "`prog(t, a, b, easing?)` → 0 → 1 mượt từ giây a tới b (kẹp hai đầu)",
    "`rand(seed)` → số 0–1 ổn định (KHÔNG dùng Math.random)",
    "`easeOut`, `easeInOut` (Easing của remotion)",
    "`M` = màu/font hiện tại: bg, paper, ink, mute, line, accent, accent2, ok, serif, sans, mono, look (sang|toi)",
    "`rgba(hex, a)`, `shadow(k)` → chuỗi CSS",
    "`overlaySlot(safe, cao, tốiThiểu?)` → {y, h}: chỗ đặt khối ở layer overlay tránh mặt người nói (safe.face)",
    "`fitSize(chữ, bềRộng, cỡ, sốDòng?)` → cỡ chữ vừa khung (Headline tự làm khi không truyền w)",
    "Icon: `<Glyph name=\"lu:wallet\" size={64} />` (lu: Lucide, si: Simple Icons, ảnh media/…). KHÔNG dùng emoji (máy chủ có thể thiếu font emoji)",
]

# Cảnh hay bị dùng sai (đã gặp ở video thật): in vào kịch bản hình để Hermes tránh.
DONT = [
    "`chat` khi câu KHÔNG nói về thao tác với app / AI / chatbot thật → dùng `hoi-dap` (câu hỏi người xem) hoặc `luu-y`",
    "`so-do` cho hai lựa chọn → dùng `so-sanh`; câu \"nếu… thì… / còn không thì…\" → `re-nhanh`",
    "`chu-nghieng` quá 1 lần trong video ngắn (dưới 60 s), hoặc chữ nổi đè lên đầu người nói",
    "Cảnh nổi (overlay) có cửa sổ / thẻ lớn: dễ che mặt → dùng layer full (ô mặt người nói ở góc)",
    "Chữ trên hình chép lỗi nghe nhầm của Whisper (coi → coin, stacking → staking…): chữ hiển thị phải đúng chính tả, chỉ `say` mới chép đúng chữ Whisper",
    "Mã icon `lu:` / `si:` ở chỗ không phải icon (label, text) → hiện ra thành chữ",
    "Cảnh mở ra trống (cửa sổ rỗng, chờ hơn 0,5 s mới có nội dung)",
]

SCENE_TEMPLATE = '''import React from "react";
import { Headline, Window, Card, Cursor, ChatBubble, prog, useSec, SceneProps } from "./kit";

type P = { title?: string; accent?: string; file?: string; dropD?: number }; // "dropSay" trong content → dropD (giây)

const KeoThaFile: React.FC<SceneProps<P>> = ({ p, W, safe, layer }) => {
  const t = useSec();
  const drop = p.dropD ?? 1.6;
  const fly = prog(t, drop - 0.9, drop);
  return (
    <>
      {layer === "full" ? <Headline x={safe.left} y={safe.top + 40} title={p.title ?? ""} accent={p.accent} /> : null}
      <Window x={safe.left} y={560} w={W - safe.left * 2} h={560} title="Claude" at={0.1}>
        {t >= drop ? <ChatBubble side="me" text={`📎 ${p.file ?? ""}`} at={drop} /> : null}
      </Window>
      {t < drop ? <Card x={180 + 300 * fly} y={1180 - 420 * fly} w={600} at={0.3}>🎬 {p.file}</Card> : null}
      <Cursor path={[[620, 1260, 0.4], [W / 2 + 120, 840, drop]]} clicks={[0.5, drop]} />
    </>
  );
};
export default KeoThaFile;'''


def kit_ref() -> list:
    """Chữ ký các viên gạch của motion kit, đọc thẳng từ engine/src/motion/kit.tsx (luôn khớp bản engine đang dùng)."""
    from .env import ENGINE_SRC

    src = ENGINE_SRC / "src" / "motion" / "kit.tsx"
    if not src.exists():
        return []
    txt = src.read_text(encoding="utf-8")
    lines = txt.splitlines()
    out = []
    for m in _KIT_RE.finditer(txt):
        i = txt.count("\n", 0, m.start())
        doc = lines[i - 1].strip() if i and lines[i - 1].strip().startswith("/**") else ""
        doc = doc.removeprefix("/**").removesuffix("*/").strip()
        props = m.group(2).replace("Pos & ", "Pos & ").strip()
        out.append(f"- `{m.group(1)}` {props}" + (f" — {doc}" if doc else ""))
    return out


def reference_md() -> list:
    """Mục 'Tham chiếu nhanh': đủ để viết khung motion và cảnh mới mà không đọc mã nguồn engine."""
    out = ["## Tham chiếu nhanh (đủ để viết khung motion và cảnh mới; KHÔNG cần đọc mã nguồn engine)", "",
           "Khung motion trong content.beats (`head` để trống; `pip` true = giữ ô mặt người nói ở góc khi layer full):", "",
           "```json",
           '{"start": "cụm mở", "end": "cụm đóng", "head": "", "g": {"type": "motion", "scene": "<tên>", "layer": "full", "pip": true, "params": {"say": "cụm lời"}}}',
           "```", "",
           "Khoá `say` → `d`, `xxxSay` → `xxxD` (giây từ lúc cảnh mở), kể cả trong mảng (items[].say). Cụm lời phải trùng ĐÚNG chữ trong work/loi-thoai.txt.", "",
           "### Cảnh có sẵn (ví dụ `g` dán được ngay)", ""]
    for name, (y, _prm) in BUILTIN_INFO.items():
        ex = EXAMPLES.get(name, {})
        g = {"type": "motion", "scene": name, "layer": ex.get("layer", "full"), "params": ex.get("params", {})}
        out += [f"- **{name}**: {y}. Mặc định: {DEFAULTS.get(name, '')}.", f"  `{json.dumps(g, ensure_ascii=False)}`"]
    lib = [f"- `{x['name']}` (điểm {x.get('score', 0)}, dùng {x.get('uses', 0)} lần): {x.get('y', '')}"
           + (f". Tham số: {x['params']}" if x.get("params") else "") for x in lib_items() if not x.get("off")][:20]
    out += ["", "### Cảnh trong thư viện (đã dùng ở video trước, xếp theo điểm; chép vào dự án: `video-editor motion use <dự án> <tên>`)", "",
            *(lib or ["(chưa có)"]), ""]
    out += ["### Viết cảnh mới `motion/<tên>.tsx`", "",
            "Tên: chữ thường không dấu, số, gạch nối. Chỉ import `react`, `remotion`, `./kit` (và cảnh khác trong motion/). "
            "Phải `export default`. Không mạng / eval / require / setTimeout / Math.random. ≤ 60 KB.", "",
            "Props của cảnh: `SceneProps<P>` = { p: P (params đã đổi say → d), dur (giây), W, H (1080×1920 dọc / 1920×1080 ngang), "
            "layer: \"full\" | \"overlay\", safe: { top, bottom, left, right, pip: {x, y, w, h} | null, face: {x, y, w, h} | null } }. "
            "Đặt nội dung chính trong safe.top … safe.bottom, tránh safe.pip (cảnh full) và safe.face (mặt người nói, cảnh overlay). Cảnh full tự có nền giấy (Paper). "
            "Khối chữ tự viết bằng div: thêm data-ve=\"text\" để soát bố cục đo được.", "",
            "```tsx", SCENE_TEMPLATE, "```", "",
            "Viên gạch của kit (`Pos` = { x?, y?, w?, h?, style? }; có x/y thì đặt tuyệt đối; mọi `at`, `d`, `dur` tính bằng giây từ lúc cảnh mở):", "",
            *kit_ref(), "",
            "Hàm, màu:", "", *[f"- {x}" for x in ANIM_REF], "",
            "Thêm chuyển động tự viết: `useCurrentFrame`, `interpolate`, `spring` của remotion; CSS transform/opacity; SVG `pathLength` + `strokeDashoffset` để vẽ nét.",
            "Kiểm tra nhanh (không cắt video): `video-editor check <dự án>`. Sau `preview` đọc `out/soat-bo-cuc.md` (soát bố cục tự động: chữ bị cắt, đè nhau, che mặt, mã icon, khung trống).", "",
            "### Không nên (lỗi đã gặp)", "", *[f"- {x}" for x in DONT], ""]
    return out


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
    ("so-sanh", re.compile(r"\b(so với|thay vì|khác với|hay là|hoặc là)\b|\S+ hay \S+ (không|nào|gì)\b|\b(trên|ở|dùng) \S+ hay\b", re.I), "so-sanh"),
    ("re-nhanh", re.compile(r"\b(nếu|còn không thì|không thì|trường hợp|thì để|thì nên)\b", re.I), "re-nhanh"),
    ("luu-y", re.compile(r"\b(lưu ý|nhớ là|đừng|cẩn thận|cảnh báo|mẹo|tránh)\b", re.I), "luu-y"),
    ("cau-hoi", re.compile(r"\b(cho em hỏi|cho mình hỏi|hỏi là|có nên|nên không|được không|tại sao|làm sao)\b|\?$", re.I), "hoi-dap"),
    ("nhan-manh", re.compile(r"\b(quan trọng|bí mật|đặc biệt|chú ý|newbie|người mới)\b", re.I), "chu-nghieng"),
]


def suggest(sentence: str) -> list:
    """(ý, cảnh gợi ý) cho một câu lời thoại; rỗng = câu chuyển ý / nói chuyện, nên để mặt người nói."""
    return [(k, s) for k, rx, s in INTENTS if rx.search(sentence)]


def plan_sheet(prj) -> Path:
    """work/kich-ban-hinh.md: mạch ý cả video (Hermes điền trước), rồi từng câu kèm gợi ý ý/cảnh để quyết định cảnh motion."""
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
    txt = "\n".join([
        f"# Kịch bản hình: {prj.root.name}",
        "",
        "## 1. Mạch ý (điền TRƯỚC khi chọn cảnh)",
        "",
        "Đọc cả lời thoại, viết 3–5 dòng: **câu hỏi / vấn đề** → **kết luận** → **lý do / các nhánh (nếu… thì…)** → **ví dụ**.",
        "Rồi chọn **một hệ hình chính** cho cả video, các cảnh nối tiếp nhau (ví dụ: `so-sanh` sàn / ví → `re-nhanh` có staking thì sàn, không thì ví lạnh → `luu-y` mẹo),",
        "không mỗi câu một kiểu rời rạc. Cảnh phải đúng **ý** của câu, không chỉ khớp từ khoá.",
        "",
        "- Câu hỏi / vấn đề: …",
        "- Kết luận: …",
        "- Lý do / nhánh: …",
        "- Ví dụ: …",
        "- Hệ hình chính: …",
        "",
        "## 2. Từng câu",
        "",
        "Điền cột **Quyết định**: tên cảnh (có sẵn / thư viện / `motion/<tên>.tsx` mới viết), `overlay` hay `full`, hoặc `người nói`.",
        "Gợi ý chỉ dựa vào từ khoá; đọc ý cả câu rồi tự quyết. Luật nhịp ở huong-dan/motion.md; tham số, ví dụ, motion kit ở mục Tham chiếu nhanh cuối file.",
        "",
        "| Giây (gốc) | Câu | Ý (gợi ý) | Cảnh gợi ý | Quyết định |",
        "|---|---|---|---|---|",
        *rows,
        "",
        *reference_md(),
    ])
    out = prj.work / "kich-ban-hinh.md"
    out.write_text(txt, encoding="utf-8")
    return out


ICON_CODE = re.compile(r"^(lu|si):[a-z0-9][a-z0-9-]*$")
_ICON_KEYS = {"icon", "src", "text"}
_APP_RX = re.compile(r"\b(app|ứng dụng|chatgpt|gpt|claude|gemini|copilot|chatbot|bot|ai|trợ lý|agent|hermes|zalo|messenger|telegram|gõ|nhắn)\b", re.I)


def icon_codes(beats: list) -> set:
    """Mã icon lu:/si: dùng trong params cảnh motion (build đọc hình icon cho bộ dựng)."""
    out = set()

    def walk(o, key=""):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for x in o:
                walk(x, key)
        elif isinstance(o, str) and ICON_CODE.match(o.strip()):
            out.add(o.strip())

    for b in beats or []:
        g = b.get("g") or {}
        if g.get("type") == "motion":
            walk(g.get("params") or {})
    return out


def lint(beats: list, words: list, duration: float) -> list[tuple[str, str, str]]:
    """Cảnh báo dùng cảnh chưa hợp lý (ngữ nghĩa / bố cục dễ hỏng): [(mức err|warn, chỗ, nội dung)]."""
    out = []
    italics = 0

    def said(b):
        return " ".join(w["text"] for w in words if b["start"] - 0.2 <= w["start"] <= b["end"] + 0.2)

    def walk(o, key, where):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, k, where)
        elif isinstance(o, list):
            for x in o:
                walk(x, key, where)
        elif isinstance(o, str):
            v = o.strip()
            if re.match(r"^(lu|si):", v) and key not in _ICON_KEYS:
                out.append(("err", where, f'mã icon "{v}" nằm ở khoá "{key}" sẽ hiện ra thành chữ; mã lu:/si: chỉ dùng cho khoá icon (hoặc text của nhan-dan)'))
            elif key == "icon" and v and not ICON_CODE.match(v) and not re.search(r"\.(png|jpe?g|svg|webp)$", v, re.I) and not v.isascii():
                out.append(("warn", where, f'icon "{v}" là emoji: máy chủ có thể không có font emoji → dùng mã lu:<tên Lucide> / si:<tên Simple Icons>'))

    for i, b in enumerate(beats or []):
        g = b.get("g") or {}
        if g.get("type") != "motion":
            continue
        sc, prm, layer = g.get("scene"), g.get("params") or {}, g.get("layer") or "full"
        where = f"beats[{i}] {sc}"
        walk(prm, "", where)
        if sc == "chat" and not _APP_RX.search(said(b) + " " + json.dumps(prm, ensure_ascii=False)):
            out.append(("warn", where, "cảnh chat nhưng câu không nói về app / AI / chatbot: người xem sẽ khó hiểu → dùng hoi-dap (câu hỏi) hoặc luu-y"))
        if sc == "so-do" and len(prm.get("nodes") or []) <= 2:
            out.append(("warn", where, "so-do chỉ có 2 nút: hai lựa chọn nên dùng so-sanh (A với B), rẽ nhánh nếu/thì dùng re-nhanh"))
        if sc == "chu-nghieng":
            italics += 1
            if italics == 2 and duration < 60:
                out.append(("warn", where, "chu-nghieng lần thứ 2 trong video dưới 60 s: chữ nổi lặp lại làm rối, để mặt người nói hoặc dùng cảnh khác"))
        if layer == "overlay" and sc in ("chat", "terminal", "tai-lieu", "luoi-anh", "thu-muc", "so-do", "dem-so", "dong-ho", "song-am", "dong-thoi-gian"):
            out.append(("warn", where, f"{sc} ở layer overlay có khối lớn dễ che mặt người nói → dùng layer full (ô mặt ở góc) nếu soát bố cục báo che mặt"))
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
