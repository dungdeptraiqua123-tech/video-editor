"""Ghi nhớ góp ý của người dùng qua từng video (GHI-NHO.md trong thư mục skill), để video sau làm tốt hơn.

Khác với quy tắc riêng trong project.json (chỉ áp dụng cho một video), ghi nhớ áp dụng cho mọi video về sau.
Thư mục skill chỉ đọc thì ghi vào ~/.video-editor/GHI-NHO.md. Biến VE_NOTES chỉ định file khác.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

from .env import HOME, SKILL_DIR, VEError, info

KINDS = ["nhip", "cat", "phu-de", "do-hoa", "am-thanh", "mau-sac", "bo-cuc", "noi-dung", "khac"]
HEAD = """# Ghi nhớ góp ý của người dùng

Claude đọc file này ở bước 1 của mỗi video và áp dụng mọi dòng bên dưới, trừ khi người dùng dặn khác cho video đó.
Thêm dòng bằng `video-editor note "nội dung" --project <dự án> --loai <loại>`. Sửa hoặc xoá dòng cũ thì sửa thẳng file này.

Loại: nhip, cat, phu-de, do-hoa, am-thanh, mau-sac, bo-cuc, noi-dung, khac.

## Góp ý
"""


def path() -> Path:
    if os.environ.get("VE_NOTES"):
        return Path(os.environ["VE_NOTES"]).expanduser()
    p = SKILL_DIR / "GHI-NHO.md"
    if os.access(SKILL_DIR, os.W_OK) and (not p.exists() or os.access(p, os.W_OK)):
        return p
    return HOME / "GHI-NHO.md"


def entries(p: Path | None = None) -> list[str]:
    p = p or path()
    if not p.exists():
        return []
    return [ln[2:].strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.startswith("- ")]


def add(text: str, project: str = "", kind: str = "khac", p: Path | None = None) -> str:
    text = " ".join(text.split())
    if not text:
        raise VEError("Góp ý rỗng.", 'Ví dụ: video-editor note "Phụ đề to hơn, ít chữ mỗi dòng" --loai phu-de')
    if kind not in KINDS:
        raise VEError(f"Loại \"{kind}\" không có.", f"Chọn: {', '.join(KINDS)}")
    p = p or path()
    p.parent.mkdir(parents=True, exist_ok=True)
    body = p.read_text(encoding="utf-8") if p.exists() else HEAD
    line = f"- [{time.strftime('%Y-%m-%d')} · {kind}" + (f" · {project}" if project else "") + f"] {text}"
    if re.search(rf"\] {re.escape(text)}$", body, re.M):
        info("Góp ý này đã có trong ghi nhớ, không thêm lại.")
        return line
    p.write_text(body.rstrip("\n") + "\n" + line + "\n", encoding="utf-8")
    info(f"✓ đã ghi nhớ ({len(entries(p))} góp ý) → {p}")
    return line


def show(limit: int = 30) -> None:
    es = entries()
    if not es:
        return
    info(f"📒 Ghi nhớ góp ý từ các video trước ({len(es)}), áp dụng cho video này ({path()}):")
    for e in es[-limit:]:
        info(f"   - {e}")
    if len(es) > limit:
        info(f"   … và {len(es) - limit} dòng cũ hơn trong file")
