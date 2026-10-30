"""Kiểm thử trọn quy trình bằng lệnh thật (cần đã chạy `video-editor setup`). Mất khoảng 3–5 phút.

  python3 tests/e2e.py            chạy cả hai video và các tình huống lỗi
  python3 tests/e2e.py --keep     giữ thư mục tạm để xem kết quả

Không dùng mạng, không cần Whisper hay ElevenLabs: lời thoại nạp từ dữ liệu giả, giọng đọc dùng giọng tạm.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = [sys.executable, str(ROOT / "ve" / "cli.py")]
FAILS = []


def ve(*args, ok=True):
    p = subprocess.run(CLI + [str(a) for a in args], capture_output=True, text=True, encoding="utf-8")
    if ok and p.returncode != 0:
        print(p.stdout[-2000:], p.stderr[-2000:])
        raise SystemExit(f"lệnh lỗi: video-editor {' '.join(map(str, args))}")
    return p


def check(name, cond, detail=""):
    print(f"  {'✓' if cond else '✗'} {name}" + (f" ({detail})" if detail else ""))
    if not cond:
        FAILS.append(name)


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)], check=True)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


def srt_end(p):
    t = re.findall(r"--> (\d+):(\d+):(\d+),(\d+)", Path(p).read_text(encoding="utf-8"))
    h, m, s, ms = map(int, t[-1])
    return h * 3600 + m * 60 + s + ms / 1000


def edit(prj, fn):
    f = prj / "project.json"
    c = json.loads(f.read_text(encoding="utf-8"))
    fn(c)
    f.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")


def talking(tmp):
    print("▶ A. video người nói 9:16, có khoảng lặng và từ đệm cần cắt")
    src = tmp / "nguoi-noi.mp4"
    # 12 giây: nói 0–5s, im 5–8s, nói 8–12s
    ff("-f", "lavfi", "-i", "testsrc2=s=1080x1920:r=30:d=12", "-f", "lavfi", "-i", "sine=f=220:d=12", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", src)
    text = "xin chào các bạn ờ hôm nay giá Bitcoin tăng lên 87 ngàn đô".split()
    text2 = "mốc hỗ trợ gần nhất là 85 ngàn đô cảm ơn các bạn đã xem".split()
    ws, t = [], 0.2
    for x in text:
        ws.append({"w": " " + x, "s": round(t, 2), "e": round(t + 0.3, 2), "p": 0.9})
        t += 0.35
    t = 8.1
    for x in text2:
        ws.append({"w": " " + x, "s": round(t, 2), "e": round(t + 0.25, 2), "p": 0.9})
        t += 0.28
    tr = tmp / "tr.json"
    tr.write_text(json.dumps([{"start": ws[0]["s"], "end": ws[-1]["e"], "text": " ".join(w["w"] for w in ws), "words": ws}], ensure_ascii=False), encoding="utf-8")

    prj = tmp / "a"
    ve("init", prj, "--input", src, "--template", "btc-daily")
    ve("transcribe", prj, "--from-json", tr)
    edit(prj, lambda c: c.update(content={
        "hook": {"title": "Bitcoin lên 87K"}, "hookSec": 1.5, "outroSec": 2.0, "cta": "Theo dõi",
        "beats": [{"start": "giá Bitcoin", "end": "85 ngàn đô", "head": "Mốc giá", "g": {"type": "levels", "title": "Các mốc", "levels": [
            {"value": "87K", "label": "Cản", "kind": "res", "say": "87 ngàn"}, {"value": "85K", "label": "Hỗ trợ", "kind": "sup", "say": "85 ngàn"}]}}],
        "topics": [], "zooms": "auto"}))
    p = ve("build", prj)
    tl = json.loads((prj / "work/timeline.json").read_text(encoding="utf-8"))
    d = json.loads((prj / "work/data.json").read_text(encoding="utf-8"))
    check("cắt khoảng lặng 3 giây", tl["sourceDuration"] - tl["duration"] > 2.5, f"{tl['sourceDuration']:.1f}s → {tl['duration']:.1f}s")
    check("bỏ từ đệm \"ờ\"", "ờ" not in [w["text"] for w in d["words"]] and len(tl["removed"]["filler"]) == 1)
    lv = d["beats"][0]["g"]["levels"]
    w87 = next(w for w in d["words"] if w["text"] == "87")
    w85 = next(w for w in d["words"] if w["text"] == "85")
    check("mốc 87K bật đúng lúc nói (theo bản đã cắt)", abs(d["beats"][0]["start"] + lv[0]["d"] - (w87["start"] - 0.08)) < 0.02)
    check("mốc 85K bật đúng lúc nói sau đoạn cắt", abs(d["beats"][0]["start"] + lv[1]["d"] - (w85["start"] - 0.08)) < 0.02)

    # chạy lại build không cắt lại (dùng bản cắt cũ)
    p = ve("build", prj)
    check("build lần hai dùng lại bản cắt", "dùng lại" in p.stdout)

    t0 = time.time()
    ve("render", prj)
    took = time.time() - t0
    ve("export", prj)
    mp4 = prj / "out" / "a.mp4"
    check("có MP4", mp4.exists(), f"render {took:.0f}s")
    check("thời lượng video khớp dữ liệu", abs(dur(mp4) - d["duration"]) < 0.1, f"{dur(mp4):.2f}s / {d['duration']:.2f}s")
    check("phụ đề không vượt video", srt_end(prj / "out/a.srt") <= dur(mp4) + 0.05)
    check("có VTT, ảnh bìa, báo cáo", all((prj / "out" / f).exists() for f in ("a.vtt", "anh-bia.jpg", "bao-cao.md")))
    check("báo cáo xác nhận đồng bộ", "✓ khớp" in (prj / "out/bao-cao.md").read_text(encoding="utf-8"))
    p = ve("render", prj)
    check("render lại khi không đổi gì thì bỏ qua", "bỏ qua" in p.stdout)


def script(tmp):
    print("▶ B. video từ kịch bản 16:9, giọng tạm, ảnh nền và ảnh sản phẩm")
    sc = tmp / "kichban.txt"
    sc.write_text("# tiêu đề bị bỏ qua\nSản phẩm mới giúp bạn tiết kiệm 30 phần trăm thời gian. [ghi chú đồ hoạ]\nPin dùng được 12 giờ liên tục. Đặt hàng hôm nay để nhận ưu đãi.\n", encoding="utf-8")
    bg = tmp / "nen.jpg"
    ff("-f", "lavfi", "-i", "gradients=s=1920x1080:d=1", "-frames:v", "1", bg)
    sp = tmp / "san-pham.png"
    ff("-f", "lavfi", "-i", "testsrc=s=800x800:d=1", "-frames:v", "1", sp)
    prj = tmp / "b"
    ve("init", prj, "--script", sc, "--format", "16:9", "--type", "product", "--background", bg, "--voice", "placeholder")
    ve("tts", prj)
    edit(prj, lambda c: c.update(content={
        "hook": {"title": "Ra mắt sản phẩm mới"}, "hookSec": 1.5, "outroSec": 2.0, "cta": "Đặt hàng hôm nay",
        "beats": [
            {"start": "tiết kiệm", "end": "thời gian.", "head": "Nhanh hơn", "g": {"type": "stat", "icon": "clock", "big": "-30%", "label": "thời gian", "tone": "up", "say": "30"}},
            {"start": "Pin", "end": "liên tục.", "head": "Pin bền", "g": {"type": "media", "src": str(sp), "label": "12 giờ"}},
        ], "topics": [], "zooms": []}))
    ve("build", prj)
    d = json.loads((prj / "work/data.json").read_text(encoding="utf-8"))
    check("khổ 16:9", d["format"]["w"] == 1920 and d["format"]["h"] == 1080)
    check("không người nói, có nền", d["mode"] == "faceless" and d["media"].get("background"))
    check("ảnh sản phẩm được đưa vào media/", (prj / "media" / d["beats"][1]["g"]["src"]).exists())
    check("ghi chú [..] và tiêu đề # không bị đọc", not any("ghi" in w["text"] or "tiêu" in w["text"] for w in d["words"]))
    ve("preview", prj)
    check("có ảnh xem trước", (prj / "out/xem-truoc.jpg").exists())
    ve("render", prj)
    ve("export", prj)
    mp4 = prj / "out" / "b.mp4"
    check("có MP4 16:9", mp4.exists() and abs(dur(mp4) - d["duration"]) < 0.1)
    check("báo cáo ghi rõ đang dùng giọng tạm", "giọng tạm" in (prj / "out/bao-cao.md").read_text(encoding="utf-8"))


def errors(tmp):
    print("▶ C. đầu vào lỗi phải báo đúng nguyên nhân")
    bad = tmp / "hong.mp4"
    bad.write_bytes(b"\x00" * 4096)
    p = ve("init", tmp / "c1", "--input", bad, ok=False)
    check("file hỏng", p.returncode == 2 and "hỏng" in p.stderr, p.stderr.strip().splitlines()[0] if p.stderr else "")
    mute = tmp / "khong-tieng.mp4"
    ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=30:d=2", "-c:v", "libx264", "-pix_fmt", "yuv420p", mute)
    p = ve("init", tmp / "c2", "--input", mute, ok=False)
    check("video không có tiếng", p.returncode == 2 and "không có tiếng" in p.stderr)
    quiet = tmp / "im-lang.mp4"
    ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=30:d=2", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", quiet)
    p = ve("init", tmp / "c3", "--input", quiet, ok=False)
    check("âm thanh im lặng", p.returncode == 2 and "im lặng" in p.stderr)
    p = ve("build", tmp / "khong-co", ok=False)
    check("thư mục không phải dự án", p.returncode == 2 and "project.json" in p.stderr)
    # cụm từ neo sai chính tả: lỗi có gợi ý
    edit(tmp / "a", lambda c: c["content"]["beats"][0].update(start="gia Bitcoin"))
    p = ve("build", tmp / "a", ok=False)
    check("cụm neo không có trong lời: báo lỗi kèm gợi ý", p.returncode == 2 and "giá Bitcoin" in p.stderr)


if __name__ == "__main__":
    tmp = Path(tempfile.mkdtemp(prefix="ve-e2e-"))
    t0 = time.time()
    try:
        talking(tmp)
        script(tmp)
        errors(tmp)
    finally:
        print(f"\n{'✓ tất cả đạt' if not FAILS else '✗ lỗi: ' + ', '.join(FAILS)} sau {time.time() - t0:.0f}s · {tmp}")
        if "--keep" not in sys.argv and not FAILS:
            shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if FAILS else 0)
