"""Đường dẫn, chạy lệnh ngoài, thông báo lỗi dễ hiểu. Chỉ dùng thư viện chuẩn."""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ENGINE_SRC = SKILL_DIR / "engine"
TEMPLATES = SKILL_DIR / "templates"
VERSION = (SKILL_DIR / "VERSION").read_text().strip() if (SKILL_DIR / "VERSION").exists() else "dev"

# Mọi thứ cài thêm (môi trường Python, node_modules, mô hình Whisper) nằm ngoài thư mục skill,
# vì thư mục skill có thể chỉ đọc và không nên phình to.
HOME = Path(os.environ.get("VE_HOME", Path.home() / ".video-editor"))
VENV = HOME / "venv"
ENGINE = HOME / f"engine-{VERSION}"
MODELS = HOME / "models"
CONFIG = HOME / "config.json"

IS_WIN = platform.system() == "Windows"


class VEError(Exception):
    """Lỗi có hướng xử lý: in ra cho người dùng, không in traceback."""

    def __init__(self, what: str, fix: str = "", code: int = 2):
        super().__init__(what)
        self.what, self.fix, self.code = what, fix, code


def _cgroup_room() -> float | None:
    """Byte còn lại trong giới hạn RAM của container (cgroup v1/v2); None nếu không giới hạn hoặc không đọc được."""
    try:
        base = Path("/sys/fs/cgroup")
        cands = []
        for ln in Path("/proc/self/cgroup").read_text().splitlines():
            _, ctrl, path = ln.split(":", 2)
            if ctrl == "":  # v2
                cands += [(base / path.lstrip("/") / "memory.max", base / path.lstrip("/") / "memory.current"), (base / "memory.max", base / "memory.current")]
            elif "memory" in ctrl.split(","):  # v1
                d = base / "memory"
                cands += [(d / path.lstrip("/") / "memory.limit_in_bytes", d / path.lstrip("/") / "memory.usage_in_bytes"), (d / "memory.limit_in_bytes", d / "memory.usage_in_bytes")]
        for lim, use in cands:
            if lim.exists() and use.exists():
                v = lim.read_text().strip()
                if v == "max" or int(v) >= 1 << 60:
                    return None
                return max(0.0, int(v) - int(use.read_text().strip()))
    except (OSError, ValueError):
        pass
    return None


def mem_available_gb() -> float:
    """RAM còn trống (GB) lúc này, tính cả giới hạn của container. 0 nếu không đọc được."""
    try:
        if sys.platform.startswith("linux"):
            avail = next((int(l.split()[1]) * 1024 for l in open("/proc/meminfo") if l.startswith("MemAvailable")), 0)
            room = _cgroup_room()
            return (min(avail, room) if room is not None else avail) / 1e9
        if sys.platform == "darwin":
            out = subprocess.check_output(["vm_stat"], text=True)
            page = int(re.search(r"page size of (\d+)", out).group(1))
            pages = sum(int(re.search(rf"{k}:\s+(\d+)", out).group(1)) for k in ("Pages free", "Pages inactive", "Pages speculative"))
            return pages * page / 1e9
        if IS_WIN:
            import ctypes

            class M(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("t", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong), ("x", ctypes.c_ulonglong * 5)]

            m = M()
            m.l = ctypes.sizeof(M)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.a / 1e9
    except Exception:
        pass
    return 0.0


def render_plan(avail_gb: float, cpus: int) -> tuple[int, int]:
    """Số luồng render và bộ đệm khung hình (byte) vừa với RAM còn trống.

    Đo trên máy 4 nhân, giới hạn 4,9 GB, video 1080×1920: 4 luồng với bộ đệm mặc định của Remotion
    (một nửa RAM) bị tràn RAM ở khoảng 50%; 4 luồng với bộ đệm 1 GB chạy hết, đỉnh 4,1 GB.
    """
    n = cpus if cpus <= 4 else min(16, cpus - 1)  # gần hết số nhân nhanh hơn ~25% so với mặc định
    if avail_gb <= 0:  # không đọc được: giữ mức an toàn vừa phải
        return min(n, 4), 1 << 30
    if avail_gb < 2.5:
        n = 1
    elif avail_gb < 3.5:
        n = min(n, 2)
    elif avail_gb < 8:
        n = min(n, 4)
    cache = int(min(2.0, max(0.5, avail_gb * 0.2)) * (1 << 30))
    return n, cache


def has_related_skills() -> bool:
    """Bản đầy đủ (clone từ repo) kèm reference/ và bộ cài skill liên quan. Bản gọn để tải lên làm skill cá nhân thì không."""
    return (SKILL_DIR / "reference").is_dir() and (SKILL_DIR / "ve" / "skills.py").exists()


def info(msg: str) -> None:
    print(msg, flush=True)


def warn(msg: str) -> None:
    print(f"⚠ {msg}", file=sys.stderr, flush=True)


def which(name: str) -> str | None:
    return shutil.which(name)


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if IS_WIN else "bin/python")


def npx() -> str:
    exe = which("npx.cmd" if IS_WIN else "npx") or which("npx")
    if not exe:
        raise VEError("Không tìm thấy Node.js (npx).", "Cài Node.js 22 LTS từ nodejs.org, rồi chạy lại `video-editor setup`.")
    return exe


def run(cmd: list, cwd: Path | None = None, quiet: bool = False, check: bool = True, env: dict | None = None) -> subprocess.CompletedProcess:
    """Chạy lệnh; lỗi thì nêu lệnh và 20 dòng cuối để dễ chẩn đoán."""
    cmd = [str(c) for c in cmd]
    e = dict(os.environ, **(env or {}))
    if quiet:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=e)
    else:
        p = subprocess.run(cmd, cwd=cwd, text=True, env=e)
    if check and p.returncode != 0:
        tail = "\n".join(((p.stderr or "") + (p.stdout or "")).strip().splitlines()[-20:]) if quiet else ""
        raise VEError(f"Lệnh lỗi ({p.returncode}): {' '.join(cmd[:4])} …\n{tail}".rstrip())
    return p


def load_config() -> dict:
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_config(cfg: dict) -> None:
    HOME.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")


def read_json(p: Path) -> dict:
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise VEError(f"Không có file {p}.")
    except ValueError as e:
        raise VEError(f"File {p} không phải JSON hợp lệ: {e}", "Sửa lỗi cú pháp (dấu phẩy, ngoặc) rồi chạy lại.")


def write_json(p: Path, data, indent: int | None = 1) -> None:
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=indent), encoding="utf-8")


def find_browser() -> str | None:
    """Trình duyệt render: biến VE_BROWSER, cấu hình, rồi các chỗ cài phổ biến. None = để Remotion tự lo."""
    for c in (os.environ.get("VE_BROWSER"), load_config().get("browser")):
        if c and Path(c).exists():
            return c
    pats = [
        "/opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell",
        str(Path.home() / ".cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell"),
    ]
    import glob

    for pat in pats:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return None


def browser_exe() -> str | None:
    """Đường dẫn trình duyệt chạy được (Chrome Headless Shell của Remotion, hoặc trình duyệt tìm thấy) để chụp trang HTML."""
    d = ENGINE / "node_modules" / ".remotion" / "chrome-headless-shell"
    name = "chrome-headless-shell.exe" if IS_WIN else "chrome-headless-shell"
    if d.exists():
        hits = [p for p in d.rglob(name) if p.is_file()]
        if hits:
            return str(hits[0])
    return find_browser()


def remotion_browser_ready() -> bool:
    """Remotion tự tải Chrome Headless Shell vào node_modules/.remotion khi chạy `browser ensure`. Chỉ tính khi có file chạy được."""
    d = ENGINE / "node_modules" / ".remotion" / "chrome-headless-shell"
    if not d.exists():
        return False
    names = ("chrome-headless-shell.exe",) if IS_WIN else ("chrome-headless-shell",)
    return any(p.is_file() for n in names for p in d.rglob(n))
