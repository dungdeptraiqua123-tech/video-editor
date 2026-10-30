"""Giọng đọc cho dự án từ kịch bản: ElevenLabs (giọng có sẵn hoặc nhân bản), hoặc giọng tạm im lặng để xem trước bố cục.

Trả về file âm thanh + transcript.json cùng định dạng Whisper (mốc từng chữ), nên các bước sau dùng chung.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from .env import VEError, run

API = "https://api.elevenlabs.io/v1"


def key() -> str:
    k = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not k:
        raise VEError(
            "Chưa có ELEVENLABS_API_KEY.",
            "Tạo key theo huong-dan/elevenlabs.md rồi thêm vào biến môi trường (Claude cloud: Project settings → Cloud environment → Environment variables; "
            "máy cá nhân: export ELEVENLABS_API_KEY=... trong ~/.zshrc). Muốn xem trước bố cục mà chưa có key: `video-editor tts <dự án> --placeholder`.",
        )
    return k


def call(path: str, body: bytes | None = None, ctype: str = "application/json") -> dict:
    req = urllib.request.Request(API + path, data=body, method="POST" if body is not None else "GET")
    req.add_header("xi-api-key", key())
    if body is not None:
        req.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="ignore")[:400]
        if e.code == 401:
            raise VEError("ElevenLabs từ chối key (401).", "Key sai, đã xoá, hoặc thiếu quyền Text to Speech / Voices. Tạo key mới theo huong-dan/elevenlabs.md.")
        if e.code == 403 and "proxy" in msg.lower():
            raise VEError("Mạng chặn api.elevenlabs.io.", "Thêm api.elevenlabs.io vào Allowed domains của môi trường (Project settings → Cloud environment → Network access), mở phiên mới.")
        if "quota" in msg.lower() or e.code == 429:
            raise VEError("Hết ký tự hoặc vượt giới hạn gói ElevenLabs.", "Xem số ký tự còn lại trên elevenlabs.io, chờ sang tháng hoặc nâng gói. Rút gọn kịch bản cũng giúp tiết kiệm.")
        if "voice_cloning" in msg.lower() or "can_not_use_instant_voice_cloning" in msg.lower() or (e.code in (400, 403) and "/voices/add" in path):
            raise VEError("Gói ElevenLabs hiện tại không nhân bản giọng được.", "Gói Free không có Instant Voice Cloning. Dùng giọng có sẵn (`video-editor voices`, rồi đặt voice.voiceId) hoặc nâng lên Starter.")
        raise VEError(f"ElevenLabs lỗi {e.code}: {msg}")
    except urllib.error.URLError as e:
        raise VEError(f"Không kết nối được ElevenLabs: {e.reason}", "Kiểm tra mạng; trên Claude cloud cần thêm api.elevenlabs.io vào Allowed domains.")


def voices() -> list[dict]:
    return [{"id": v["voice_id"], "name": v["name"], "category": v.get("category", ""), "labels": v.get("labels", {})} for v in call("/voices")["voices"]]


def clone(name: str, files: list[Path]) -> str:
    b = uuid.uuid4().hex
    parts = []

    def field(n, v):
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{n}"\r\n\r\n{v}\r\n'.encode())

    field("name", name)
    field("remove_background_noise", "true")
    for f in files:
        mt = mimetypes.guess_type(str(f))[0] or "audio/mpeg"
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="files"; filename="{Path(f).name}"\r\nContent-Type: {mt}\r\n\r\n'.encode())
        parts.append(Path(f).read_bytes() + b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    return call("/voices/add", b"".join(parts), f"multipart/form-data; boundary={b}")["voice_id"]


def clean_script(text: str) -> str:
    """Bỏ dòng ghi chú [..], tiêu đề markdown; gộp khoảng trắng."""
    lines = []
    for l in text.splitlines():
        l = re.sub(r"\[[^\]]*\]", "", l).strip()
        if not l or l.startswith("#"):
            continue
        lines.append(l)
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def to_transcript(chars, starts, ends) -> list:
    """Mốc theo ký tự -> từ -> câu (định dạng Whisper)."""
    words, cur = [], None
    for c, s, e in zip(chars, starts, ends):
        if c.isspace():
            cur = None
            continue
        if cur is None:
            cur = {"w": "", "s": s, "e": e, "p": 1.0}
            words.append(cur)
        cur["w"] += c
        cur["e"] = e
    segs, seg = [], []
    for w in words:
        seg.append(w)
        if re.search(r"[.!?…]$", w["w"]):
            segs.append(seg)
            seg = []
    if seg:
        segs.append(seg)
    return [{"start": s[0]["s"], "end": s[-1]["e"], "text": " " + " ".join(w["w"] for w in s), "words": [dict(w, w=" " + w["w"]) for w in s]} for s in segs]


def speak(text: str, voice: dict, audio_out: Path) -> list:
    vid = voice.get("voiceId")
    if not vid:
        raise VEError("Chưa chọn giọng (voice.voiceId trong project.json).", "Gói Free: `video-editor voices` để xem giọng có sẵn. Gói Starter trở lên: `video-editor clone-voice --name <tên> mau-giong.mp3` để nhân bản.")
    model = voice.get("model", "eleven_turbo_v2_5")
    body = {
        "text": text,
        "model_id": model,
        "language_code": "vi",
        "voice_settings": {"stability": voice.get("stability", 0.45), "similarity_boost": 0.85, "style": voice.get("style", 0.2), "use_speaker_boost": True, "speed": voice.get("speed", 1.05)},
    }
    if model == "eleven_v3":
        body.pop("language_code")
    r = call(f"/text-to-speech/{vid}/with-timestamps?output_format=mp3_44100_192", json.dumps(body).encode())
    audio_out.parent.mkdir(parents=True, exist_ok=True)
    audio_out.write_bytes(base64.b64decode(r["audio_base64"]))
    al = r.get("alignment") or r["normalized_alignment"]
    return to_transcript(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"])


def placeholder(text: str, audio_out: Path, rate: float = 4.3) -> list:
    """Giọng tạm (im lặng) với nhịp ước lượng ~4,3 tiếng/giây, để duyệt bố cục trước khi tốn ký tự ElevenLabs."""
    t, words = 0.3, []
    for tok in text.split():
        d = max(0.12, 1 / rate * (0.6 + 0.08 * len(tok)))
        words.append({"w": " " + tok, "s": round(t, 3), "e": round(t + d, 3), "p": 1.0})
        t += d + (0.35 if re.search(r"[.!?…]$", tok) else 0.18 if tok.endswith(",") else 0.04)
    dur = t + 0.5
    audio_out.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", f"{dur:.2f}", "-c:a", "aac", audio_out])
    segs, seg = [], []
    for w in words:
        seg.append(w)
        if re.search(r"[.!?…]$", w["w"]):
            segs.append(seg)
            seg = []
    if seg:
        segs.append(seg)
    return [{"start": s[0]["s"], "end": s[-1]["e"], "text": " ".join(w["w"] for w in s), "words": s} for s in segs]
