"""Đọc thông tin file, kiểm tra đầu vào đặc biệt, cắt theo timeline. Dùng ffmpeg/ffprobe."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .env import VEError, run, which, warn

VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}


def need_ffmpeg() -> None:
    if not which("ffmpeg") or not which("ffprobe"):
        raise VEError("Chưa có ffmpeg.", "macOS: `brew install ffmpeg` · Windows: `winget install Gyan.FFmpeg` · Ubuntu: `sudo apt install ffmpeg`. Sau đó mở terminal mới.")


def probe(path: Path) -> dict:
    """Thông tin cơ bản. Báo lỗi dễ hiểu khi file không tồn tại, hỏng hoặc không có tiếng."""
    need_ffmpeg()
    path = Path(path)
    if not path.exists():
        raise VEError(f"Không thấy file đầu vào: {path}", "Kiểm tra lại đường dẫn (có dấu cách thì đặt trong ngoặc kép).")
    if path.stat().st_size < 1024:
        raise VEError(f"File {path.name} quá nhỏ ({path.stat().st_size} byte), có thể tải về chưa xong.")
    p = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path], quiet=True, check=False)
    if p.returncode != 0:
        raise VEError(f"File {path.name} bị hỏng hoặc không phải video/âm thanh.", "Mở thử bằng trình phát video. Nếu xem được, xuất lại bằng CapCut/QuickTime sang MP4 (H.264) rồi thử lại.")
    j = json.loads(p.stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video" and s.get("disposition", {}).get("attached_pic") != 1), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    dur = float(j["format"].get("duration") or (v or a or {}).get("duration") or 0)
    if dur <= 0:
        raise VEError(f"Không đọc được thời lượng của {path.name}.", "File có thể bị cắt dở. Xuất lại file rồi thử lại.")
    info = {"path": str(path), "duration": round(dur, 3), "has_video": v is not None, "has_audio": a is not None}
    if v:
        w, h = int(v["width"]), int(v["height"])
        rot = int((v.get("tags", {}) or {}).get("rotate", 0) or 0)
        for sd in v.get("side_data_list", []) or []:
            rot = int(sd.get("rotation", rot) or rot)
        if abs(rot) in (90, 270):
            w, h = h, w
        num, den = (v.get("avg_frame_rate") or "30/1").split("/")
        info.update(width=w, height=h, fps=round(float(num) / float(den or 1), 3) if float(den or 1) else 30)
    return info


def loudness(path: Path) -> dict:
    """Độ lớn tích hợp (LUFS) và đỉnh, dùng cho báo cáo và phát hiện file im lặng."""
    p = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], quiet=True, check=False)
    txt = p.stderr or ""
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", txt)
    pk = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", txt)
    return {"lufs": float(i[-1]) if i else None, "peak": float(pk[-1]) if pk else None}


def check_audio(info: dict) -> None:
    if not info["has_audio"]:
        raise VEError(
            "File không có tiếng nên không chép lời được.",
            "Chọn một trong hai: (1) tạo dự án từ kịch bản với giọng AI: `video-editor init <thư mục> --script kichban.txt`; "
            "(2) dùng video này làm nền và thêm giọng đọc: `video-editor init <thư mục> --script kichban.txt --background <video>`.",
        )
    p = run(["ffmpeg", "-hide_banner", "-nostats", "-t", "600", "-i", info["path"], "-vn", "-af", "volumedetect", "-f", "null", "-"], quiet=True, check=False)
    m = re.search(r"max_volume:\s*(-?[\d.]+) dB", p.stderr or "")
    if m and float(m.group(1)) < -45:
        raise VEError(f"Âm thanh gần như im lặng (đỉnh {m.group(1)} dB).", "Kiểm tra micro hoặc chọn đúng file có tiếng. Nếu video cố ý không lời, dùng chế độ kịch bản (--script).")
    if info["duration"] > 30 * 60:
        warn(f"File dài {info['duration'] / 60:.0f} phút: chép lời có thể mất lâu. Nên cắt bớt đoạn cần dùng trước (cuts.keep).")


def extract_wav(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", dst])


def cut(src: Path, segments: list, dst: Path, has_video: bool, size: tuple | None = None) -> None:
    """Giữ các đoạn segments (giây, file gốc), chuẩn hoá -14 LUFS. Video: H.264 CRF 17 (bản trung gian, chỉ nén một lần nữa khi render)."""
    sel = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in segments)
    af = f"aselect='{sel}',asetpts=N/SR/TB,loudnorm=I=-14:TP=-1.5:LRA=11"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", src]
    if has_video:
        vf = f"select='{sel}',setpts=N/FRAME_RATE/TB"
        cmd += ["-vf", vf, "-af", af, "-ar", "48000", "-c:v", "libx264", "-crf", "17", "-preset", "fast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", dst]
    else:
        cmd += ["-vn", "-af", af, "-ar", "48000", "-c:a", "aac", "-b:a", "192k", dst]
    dst.parent.mkdir(parents=True, exist_ok=True)
    run(cmd)
