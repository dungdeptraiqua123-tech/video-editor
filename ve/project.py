"""Thư mục dự án: project.json (cài đặt + nội dung), media/ (file đưa vào render), work/ (file trung gian), out/ (file giao).

Trạng thái từng bước lưu ở work/state.json kèm dấu vân tay đầu vào: chạy lại chỉ làm bước nào có đầu vào đổi.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path

from .env import TEMPLATES, VEError, read_json, write_json

FORMATS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}
TYPES = {"talking-head", "explainer", "product"}
STEPS = ["transcribe", "build", "preview", "render", "export"]

DEFAULT = {
    "version": 1,
    "name": "",
    "type": "talking-head",
    "input": None,
    "script": None,
    "background": None,
    "format": "9:16",
    "fps": 30,
    "template": "trung-tinh",
    "brand": {},
    "captions": {"enabled": True, "style": "glow", "position": None, "keywords": [], "maxChars": None, "maxWords": 8},
    "face": {"x": 0.5, "y": 0.4},
    "voice": {"provider": "recorded", "voiceId": None, "model": "eleven_turbo_v2_5", "speed": 1.05, "stability": 0.45, "style": 0.2},
    "whisper": {"model": "auto", "language": "vi"},
    "cuts": {"gap": 0.55, "pad": 0.12, "fillers": "auto", "stumbles": "suggest", "drop": [], "keep": []},
    "fix": [],
    "dropSegments": [],
    "music": None,
    "sfx": True,
    "render": {"crf": 20, "concurrency": None},
    "content": {"hook": {"kicker": "", "title": "", "sub": ""}, "cta": "Theo dõi để xem video tiếp theo", "beats": [], "topics": [], "zooms": "auto"},
}


def _merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


class Project:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.file = self.root / "project.json"
        if not self.file.exists():
            raise VEError(f"{self.root} chưa phải thư mục dự án (thiếu project.json).", f"Tạo dự án: `video-editor init {self.root} --input <video>` hoặc `--script <kịch bản>`.")
        self.cfg = _merge(DEFAULT, read_json(self.file))
        self.media = self.root / "media"
        self.work = self.root / "work"
        self.out = self.root / "out"
        for d in (self.media, self.work, self.out):
            d.mkdir(exist_ok=True)

    # ---- đường dẫn tiện dụng
    def path(self, p: str | None) -> Path | None:
        if not p:
            return None
        q = Path(p).expanduser()
        return q if q.is_absolute() else (self.root / q).resolve()

    @property
    def faceless(self) -> bool:
        return self.cfg["type"] != "talking-head" or not self.cfg.get("input") or bool(self.cfg.get("script"))

    @property
    def size(self) -> tuple[int, int]:
        f = self.cfg["format"]
        if f not in FORMATS:
            raise VEError(f"Khổ hình \"{f}\" chưa hỗ trợ.", f"Chọn một trong: {', '.join(FORMATS)}")
        return FORMATS[f]

    @property
    def slug(self) -> str:
        import re
        import unicodedata

        s = unicodedata.normalize("NFKD", self.cfg.get("name") or self.root.name).replace("đ", "d").replace("Đ", "D")
        s = "".join(c for c in s if not unicodedata.combining(c))
        return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower() or "video"

    def save(self) -> None:
        write_json(self.file, self.cfg)

    # ---- trạng thái bước
    @property
    def state_file(self) -> Path:
        return self.work / "state.json"

    def state(self) -> dict:
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def mark(self, step: str, fp: str, **extra) -> None:
        st = self.state()
        st[step] = {"fp": fp, "at": time.strftime("%Y-%m-%d %H:%M:%S"), **extra}
        write_json(self.state_file, st)

    def fresh(self, step: str, fp: str) -> bool:
        return self.state().get(step, {}).get("fp") == fp

    def invalidate(self, *steps: str) -> None:
        st = self.state()
        for s in steps:
            st.pop(s, None)
        write_json(self.state_file, st)


def fingerprint(*parts) -> str:
    h = hashlib.sha1()
    for p in parts:
        if isinstance(p, Path):
            if p.is_dir():
                for f in sorted(p.rglob("*")):
                    if f.is_file():
                        st = f.stat()
                        h.update(f"{f.relative_to(p)}:{st.st_size}:{int(st.st_mtime)}".encode())
            elif p.exists():
                st = p.stat()
                h.update(f"{p.name}:{st.st_size}:{int(st.st_mtime)}".encode())
            else:
                h.update(b"missing")
        else:
            h.update(json.dumps(p, sort_keys=True, ensure_ascii=False).encode())
    return h.hexdigest()[:16]


def init_project(root: Path, input: str | None, script: str | None, fmt: str, template: str, typ: str | None, background: str | None, name: str | None, voice: str | None) -> Project:
    root = Path(root).resolve()
    if (root / "project.json").exists():
        raise VEError(f"{root} đã có project.json.", "Dùng thư mục khác, hoặc sửa project.json hiện có.")
    if not input and not script:
        raise VEError("Cần --input (video/âm thanh người nói) hoặc --script (kịch bản để đọc bằng giọng AI).")
    if fmt not in FORMATS:
        raise VEError(f"Khổ hình \"{fmt}\" chưa hỗ trợ.", f"Chọn: {', '.join(FORMATS)}")
    if not (TEMPLATES / template / "brand.json").exists():
        have = ", ".join(sorted(p.name for p in TEMPLATES.iterdir() if (p / "brand.json").exists()))
        raise VEError(f"Không có mẫu \"{template}\".", f"Các mẫu có sẵn: {have}")
    root.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(json.dumps(DEFAULT))
    cfg["name"] = name or root.name
    cfg["format"] = fmt
    cfg["template"] = template
    if script:
        sp = Path(script).expanduser().resolve()
        if not sp.exists():
            raise VEError(f"Không thấy kịch bản {sp}.")
        shutil.copy2(sp, root / "kichban.txt")
        cfg["script"] = "kichban.txt"
        cfg["type"] = typ or "explainer"
        cfg["voice"]["provider"] = voice or "elevenlabs"
        if input:
            cfg["background"] = str(Path(input).expanduser().resolve())
    else:
        ip = Path(input).expanduser().resolve()
        cfg["input"] = str(ip)
        from .media import AUDIO_EXT

        cfg["type"] = typ or ("explainer" if ip.suffix.lower() in AUDIO_EXT else "talking-head")
    if background:
        cfg["background"] = str(Path(background).expanduser().resolve())
    if cfg["type"] not in TYPES:
        raise VEError(f"Loại video \"{cfg['type']}\" chưa hỗ trợ.", f"Chọn: {', '.join(sorted(TYPES))}")
    write_json(root / "project.json", cfg)
    return Project(root)
