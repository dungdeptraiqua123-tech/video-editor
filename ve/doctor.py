"""Kiểm tra môi trường và cài đặt tự động."""
from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

from .env import (CONFIG, ENGINE, ENGINE_SRC, HOME, IS_WIN, SKILL_DIR, VENV, VEError, find_browser, has_related_skills, info, load_config, npx,
                  remotion_browser_ready, run, save_config, venv_python, warn, which)

MODELS = {"nang": "large-v3", "nhanh": "large-v3-turbo", "vua": "medium", "nhe": "small"}
MODEL_SIZE_GB = {"large-v3": 3.1, "large-v3-turbo": 1.6, "medium": 1.5, "small": 0.5}
NODE_MIN = (20, 19)


def ram_gb() -> float:
    try:
        if sys.platform.startswith("linux"):
            for l in open("/proc/meminfo"):
                if l.startswith("MemTotal"):
                    return int(l.split()[1]) / 1e6
        if sys.platform == "darwin":
            return int(subprocess.check_output(["sysctl", "-n", "hw.memsize"])) / 1e9
        if IS_WIN:
            import ctypes

            class M(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("t", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong), ("x", ctypes.c_ulonglong * 5)]

            m = M()
            m.l = ctypes.sizeof(M)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.t / 1e9
    except Exception:
        pass
    return 0.0


def auto_model() -> str:
    r = ram_gb()
    # Đo trên 4 nhân, video 176 giây: turbo 3 phút 10 giây, RAM 2,2 GB, giống large-v3 93,6%;
    # medium 4 phút 48 giây, 2,6 GB, giống 88,9%. Turbo hơn medium cả tốc độ lẫn độ đúng.
    return "large-v3" if r == 0 or r >= 12 else "large-v3-turbo" if r >= 4 else "small"


def resolve_model(name: str | None) -> str:
    n = (name or "auto").strip()
    if n == "auto":
        return load_config().get("whisper_model") or auto_model()
    return MODELS.get(n, n)


def hf_cache() -> Path:
    return Path(os.environ.get("HF_HUB_CACHE") or Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub")


def model_cached(model: str) -> bool:
    repo = {"large-v3-turbo": "mobiuslabsgmbh--faster-whisper-large-v3-turbo"}.get(model, f"Systran--faster-whisper-{model}")
    d = hf_cache() / f"models--{repo}" / "snapshots"
    return d.exists() and any(d.glob("*/model.bin"))


def node_version() -> tuple | None:
    n = which("node")
    if not n:
        return None
    try:
        v = subprocess.check_output([n, "--version"], text=True).strip().lstrip("v")
        return tuple(int(x) for x in v.split(".")[:3])
    except Exception:
        return None


def node_ok(v: tuple | None) -> bool:
    # Remotion 4.0.537 yêu cầu ^20.19 || ^22.13 || >=24
    if not v:
        return False
    return (v[0] == 20 and v[1] >= 19) or (v[0] == 22 and v[1] >= 13) or v[0] >= 24 or v[0] == 23


def online(url: str, timeout: float = 6) -> bool:
    try:
        urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=timeout)
        return True
    except urllib.error.HTTPError as e:
        return e.code < 500 and e.code != 403
    except Exception:
        return False


def install_hint(tool: str) -> str:
    sysname = platform.system()
    if tool == "ffmpeg":
        return {"Darwin": "brew install ffmpeg", "Windows": "winget install Gyan.FFmpeg"}.get(sysname, "sudo apt install ffmpeg")
    if tool == "node":
        return {"Darwin": "brew install node@22 (hoặc tải bản LTS ở nodejs.org)", "Windows": "winget install OpenJS.NodeJS.LTS"}.get(sysname, "cài Node 22 LTS từ nodejs.org hoặc nvm")
    return ""


def checks(online_checks: bool = True) -> list[dict]:
    out = []

    def add(name, ok, detail, fix="", need=True):
        out.append({"name": name, "ok": bool(ok), "detail": detail, "fix": fix, "required": need})

    add("Python", sys.version_info >= (3, 9), platform.python_version(), "Cài Python 3.10 trở lên từ python.org")
    add("ffmpeg", which("ffmpeg") and which("ffprobe"), which("ffmpeg") or "không thấy", install_hint("ffmpeg"))
    nv = node_version()
    add("Node.js", node_ok(nv), ".".join(map(str, nv)) if nv else "không thấy", f"Cần 20.19+, 22.13+ hoặc 24+: {install_hint('node')}")
    free = shutil.disk_usage(HOME if HOME.exists() else Path.home()).free / 1e9
    add("Dung lượng trống", free >= 4, f"{free:.0f} GB", "Cần ít nhất 4 GB (mô hình Whisper ~3 GB, bộ dựng ~0,3 GB, mỗi video vài trăm MB)")
    r = ram_gb()
    add("RAM", r == 0 or r >= 4, f"{r:.0f} GB → mô hình gợi ý: {auto_model()}" if r else "không đọc được", "Máy dưới 4 GB RAM nên dùng mô hình nhẹ: `video-editor setup --model nhe`. Render tự giảm số luồng theo RAM còn trống", need=False)
    vp = venv_python()
    fw = vp.exists() and subprocess.run([str(vp), "-c", "import faster_whisper"], capture_output=True).returncode == 0
    add("Môi trường chép lời", fw, str(VENV) if fw else "chưa cài", "Chạy `video-editor setup`")
    cv = fw and subprocess.run([str(vp), "-c", "import cv2"], capture_output=True).returncode == 0
    add("Bám mặt (OpenCV)", cv, "có" if cv else "chưa cài", "Chạy lại `video-editor setup`. Thiếu thì khi đổi khổ 16:9 → 9:16 khung giữ cố định", need=False)
    eng = (ENGINE / "node_modules" / "remotion").exists()
    add("Bộ dựng Remotion", eng, str(ENGINE) if eng else "chưa cài", "Chạy `video-editor setup`")
    br = remotion_browser_ready() or find_browser()
    add("Trình duyệt render", br, "Chrome Headless Shell của Remotion" if remotion_browser_ready() else (find_browser() or "chưa có"), "Chạy `video-editor setup`; nếu mạng chặn tải, đặt biến VE_BROWSER trỏ tới Chrome có sẵn")
    m = resolve_model("auto")
    mc = model_cached(m)
    hf = mc or not online_checks or online("https://huggingface.co")
    add(f"Mô hình Whisper ({m})", mc, "đã tải" if mc else ("chưa tải, mạng tới Hugging Face OK" if hf else "chưa tải, KHÔNG kết nối được huggingface.co"),
        "Chạy `video-editor setup`. Nếu mạng chặn: mở huggingface.co, *.hf.co, *.xethub.hf.co; hoặc nhập phụ đề có sẵn: `video-editor transcribe <dự án> --from-srt file.srt`", need=False)
    key = bool(os.environ.get("ELEVENLABS_API_KEY", "").strip())
    el = "có key" if key else "chưa có key (chỉ cần cho video từ kịch bản)"
    if key and online_checks:
        el += ", kết nối OK" if online("https://api.elevenlabs.io/v1/models") else ", KHÔNG kết nối được api.elevenlabs.io"
    add("Giọng đọc ElevenLabs", key, el, "Xem huong-dan/elevenlabs.md", need=False)
    if not has_related_skills():
        return out  # bản gọn: không kèm skill liên quan
    from .skills import status

    try:
        st = status()
        sk = f"{st['installed']}/{st['total']} skill trong {st['dir']}" + (f", {len(st['conflicts'])} trùng tên skill có sẵn" if st["conflicts"] else "")
        add("Skill liên quan", st["installed"] + len(st["conflicts"]) >= st["total"], sk, "Chạy `video-editor skills install`", need=False)
    except VEError as e:
        add("Skill liên quan", False, e.what, e.fix, need=False)
    return out


def doctor(as_json: bool = False, online_checks: bool = True) -> int:
    res = checks(online_checks)
    if as_json:
        import json

        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        info(f"video-editor · skill: {SKILL_DIR} · cài đặt: {HOME}")
        for c in res:
            mark = "✓" if c["ok"] else ("✗" if c["required"] else "–")
            info(f" {mark} {c['name']}: {c['detail']}")
            if not c["ok"] and c["fix"]:
                info(f"     → {c['fix']}")
    bad = [c for c in res if c["required"] and not c["ok"]]
    if not as_json:
        info("Sẵn sàng dựng video." if not bad else f"Còn {len(bad)} mục bắt buộc chưa đạt.")
    return 1 if bad else 0


def setup(model: str | None = None, skip_model: bool = False, install_system: bool = False, skills: bool = True, skills_dir: str | None = None) -> int:
    HOME.mkdir(parents=True, exist_ok=True)
    # 0. skill liên quan (chỉ chép file, không cần mạng): làm trước để có ngay cả khi các bước sau còn thiếu công cụ
    if skills and has_related_skills():
        from .skills import install

        info("▶ cài các skill liên quan")
        install(skills_dir)
    # 1. công cụ hệ thống
    missing = [t for t in ("ffmpeg", "node") if (t == "ffmpeg" and not which("ffmpeg")) or (t == "node" and not node_ok(node_version()))]
    if missing:
        cmds = [install_hint(t) for t in missing]
        if install_system and all(c.split()[0] in ("brew", "winget") and which(c.split()[0]) for c in cmds):
            for c in cmds:
                info(f"▶ {c}")
                run(c.split(" (")[0].split())
        else:
            raise VEError(f"Thiếu {', '.join(missing)}.", "Cài bằng: " + " ; ".join(cmds) + ". Sau đó mở terminal mới và chạy lại `video-editor setup`."
                          + (" (Hoặc `video-editor setup --install-system` để tự cài bằng brew/winget.)" if platform.system() in ("Darwin", "Windows") else ""))

    # 2. môi trường Python riêng cho chép lời
    vp = venv_python()
    if not vp.exists():
        info(f"▶ tạo môi trường Python riêng: {VENV}")
        run([sys.executable, "-m", "venv", VENV])
    info("▶ cài thư viện chép lời và dò mặt (faster-whisper, OpenCV; đúng phiên bản trong requirements.txt)")
    run([vp, "-m", "pip", "install", "-q", "--upgrade", "pip"], quiet=True)
    run([vp, "-m", "pip", "install", "-q", "-r", SKILL_DIR / "requirements.txt"], quiet=True)

    # 3. bộ dựng
    info(f"▶ cài bộ dựng Remotion: {ENGINE}")
    ENGINE.mkdir(parents=True, exist_ok=True)
    for name in ("package.json", "package-lock.json", "remotion.config.ts", "tsconfig.json"):
        shutil.copy2(ENGINE_SRC / name, ENGINE / name)
    for name in ("src", "public"):
        shutil.rmtree(ENGINE / name, ignore_errors=True)
        shutil.copytree(ENGINE_SRC / name, ENGINE / name)
    npm = which("npm.cmd" if IS_WIN else "npm") or which("npm")
    run([npm, "ci", "--no-audit", "--no-fund", "--loglevel=error"], cwd=ENGINE, quiet=True)

    # 4. trình duyệt render
    info("▶ chuẩn bị trình duyệt render")
    p = run([npx(), "remotion", "browser", "ensure"], cwd=ENGINE, quiet=True, check=False)
    if p.returncode != 0 and not remotion_browser_ready():
        b = find_browser()
        if b:
            cfg = load_config()
            cfg["browser"] = b
            save_config(cfg)
            info(f"  không tải được Chrome Headless Shell, dùng trình duyệt có sẵn: {b}")
        else:
            warn("Không tải được trình duyệt render. Kiểm tra mạng, hoặc đặt biến VE_BROWSER trỏ tới Chrome/Chromium có sẵn.")

    # 5. mô hình Whisper
    m = resolve_model(model) if model else resolve_model("auto")
    cfg = load_config()
    cfg["whisper_model"] = m
    save_config(cfg)
    if not skip_model:
        if model_cached(m):
            info(f"▶ mô hình Whisper {m} đã có, dùng lại")
        else:
            info(f"▶ tải mô hình Whisper {m} (~{MODEL_SIZE_GB.get(m, 1.5)} GB, chỉ một lần)")
            p = run([vp, SKILL_DIR / "ve" / "whisper_worker.py", "-", "-", m, "vi", "--download-only"], check=False)
            if p.returncode != 0:
                warn("Chưa tải được mô hình. Nếu mạng chặn Hugging Face: mở huggingface.co, *.hf.co, *.xethub.hf.co; "
                     "hoặc dùng phụ đề có sẵn (`transcribe --from-srt`). Video từ kịch bản (ElevenLabs) không cần mô hình này.")
    info(f"Cấu hình lưu ở {CONFIG}")
    return doctor()
