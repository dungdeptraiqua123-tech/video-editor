"""B-roll miễn phí từ Pexels: tìm video/ảnh theo từ khoá, tải vào thư mục broll/ của dự án, ghi nguồn để ghi công.

Cần khoá API miễn phí: đăng ký tại pexels.com/api rồi đặt biến môi trường PEXELS_API_KEY.
Giấy phép Pexels: dùng miễn phí cả thương mại, không bắt buộc ghi nguồn (nên ghi), không bán lại nguyên file.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .env import VEError, info, read_json, write_json

API = "https://api.pexels.com"
UA = "video-editor/0.3 (+skill dựng video)"


def _key() -> str:
    k = os.environ.get("PEXELS_API_KEY", "").strip()
    if not k:
        raise VEError("Chưa có PEXELS_API_KEY.", "Đăng ký miễn phí tại https://www.pexels.com/api/ (mục Your API Key), rồi đặt biến môi trường PEXELS_API_KEY. Không dán key vào chat.")
    return k


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": _key(), "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise VEError(f"Pexels từ chối khoá API ({e.code}).", "Kiểm tra PEXELS_API_KEY.")
        if e.code == 429:
            raise VEError("Pexels: hết lượt gọi trong giờ này (gói miễn phí 200 lượt/giờ).", "Đợi rồi chạy lại.")
        raise VEError(f"Pexels trả lỗi {e.code}.")
    except urllib.error.URLError as e:
        raise VEError(f"Không kết nối được api.pexels.com ({e.reason}).", "Kiểm tra mạng.")


def _download(url: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    tmp = dst.with_suffix(dst.suffix + ".part")
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    tmp.replace(dst)


def _slug(q: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")
    return s[:30] or "broll"


def pick_file(files: list, want_w: int, portrait: bool) -> dict | None:
    """Chọn bản gần độ phân giải cần nhất (không nhỏ hơn nếu có), ưu tiên mp4."""
    vids = [f for f in files if f.get("file_type", "video/mp4") == "video/mp4" and f.get("width") and f.get("height")]
    if not vids:
        return None
    side = (lambda f: f["width"]) if portrait else (lambda f: f["height"])
    big = [f for f in vids if side(f) >= want_w]
    return min(big, key=side) if big else max(vids, key=side)


def search(root: Path, query: str, n: int = 3, photos: bool = False, orientation: str = "portrait", want: int = 1080) -> list[dict]:
    root = Path(root)
    q = urllib.parse.quote(query)
    out_dir = root / "broll"
    log_p = root / "work" / "broll.json"
    log = read_json(log_p) if log_p.exists() else []
    got = []
    if photos:
        d = _get(f"{API}/v1/search?query={q}&per_page={n}&orientation={orientation}")
        for ph in d.get("photos", [])[:n]:
            url = ph["src"].get("portrait" if orientation == "portrait" else "large2x") or ph["src"]["original"]
            dst = out_dir / f"{_slug(query)}-{ph['id']}.jpg"
            if not dst.exists():
                _download(url, dst)
            got.append({"file": f"broll/{dst.name}", "query": query, "author": ph.get("photographer", ""), "page": ph.get("url", ""), "kind": "photo"})
    else:
        d = _get(f"{API}/videos/search?query={q}&per_page={n}&orientation={orientation}")
        for v in d.get("videos", [])[:n]:
            f = pick_file(v.get("video_files", []), want, orientation == "portrait")
            if not f:
                continue
            dst = out_dir / f"{_slug(query)}-{v['id']}.mp4"
            if not dst.exists():
                _download(f["link"], dst)
            got.append({"file": f"broll/{dst.name}", "query": query, "author": (v.get("user") or {}).get("name", ""), "page": v.get("url", ""),
                        "kind": "video", "duration": v.get("duration"), "size": f"{f['width']}x{f['height']}"})
    if not got:
        raise VEError(f"Pexels không có kết quả cho \"{query}\".", "Thử từ khoá tiếng Anh, ngắn và cụ thể (ví dụ \"bitcoin coin\", \"stock chart\").")
    known = {x["file"] for x in log}
    log += [x for x in got if x["file"] not in known]
    write_json(log_p, log)
    for x in got:
        info(f"  ✓ {x['file']}  ({x.get('size', 'ảnh')}, {x.get('duration', '')}{'s' if x.get('duration') else ''}) · {x['author']}")
    ex = got[0]
    info("  Chèn toàn màn hình: {\"start\": \"<cụm lời>\", \"end\": \"<cụm lời>\", \"g\": {\"type\": \"media\", \"src\": \"" + ex["file"]
         + "\", \"full\": true, \"credit\": \"" + ("Video" if ex["kind"] == "video" else "Ảnh") + f": {ex['author']} / Pexels\"" + "}}")
    return got
