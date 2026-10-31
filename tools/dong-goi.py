#!/usr/bin/env python3
"""Đóng gói bản gọn của skill video-editor để tải lên làm skill cá nhân (claude.ai và các nền tảng có bước quét an toàn).

Bản gọn chỉ gồm phần lõi để dựng video. Không kèm:
- reference/: 93 skill tham khảo của bên thứ ba, có mã gọi dịch vụ ngoài (HeyGen, KIE, Upload-Post…);
- ve/skills.py: bộ chép skill liên quan vào thư mục skills của trợ lý AI;
- tests/, tools/, README.md, AGENTS.md: chỉ dùng khi phát triển hoặc đọc trên repo.

  python3 tools/dong-goi.py                       → dist/video-editor-skill.zip
  python3 tools/dong-goi.py --out /duong/dan.zip
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "video-editor"
SKIP_DIRS = ("reference/", "tests/", "tools/", "dist/", ".git/", ".github/")
SKIP_FILES = {"ve/skills.py", ".gitignore", "README.md", "AGENTS.md"}  # README, AGENTS: hướng dẫn cho repo, skill tải lên chỉ cần SKILL.md


def files() -> list[str]:
    try:
        out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        names = [n for n in out.splitlines() if (ROOT / n).is_file()]
    except (OSError, subprocess.CalledProcessError):
        names = [str(p.relative_to(ROOT)).replace("\\", "/") for p in ROOT.rglob("*") if p.is_file()]
    keep = [n for n in names if not n.startswith(SKIP_DIRS) and n not in SKIP_FILES
            and "__pycache__/" not in n and "node_modules/" not in n and not n.endswith(".pyc")]
    return sorted(keep)


def third_party_core(text: str) -> str:
    """THIRD_PARTY.md cho bản gọn: bỏ các dòng về reference/ vì bản gọn không kèm."""
    text = text.split("\n## Lưu ý về các bộ chưa xác minh giấy phép")[0].rstrip() + "\n"
    lines = [ln for ln in text.splitlines() if not ln.startswith("| `reference/")]
    return "\n".join(lines) + "\n\nBản gọn này không kèm thư mục `reference/` (93 skill tham khảo của bên thứ ba). Bản đầy đủ ở repo gốc.\n"


def an_toan_core(text: str) -> str:
    """AN-TOAN.md cho bản gọn: bỏ phần chỉ nói về bản đầy đủ."""
    head, sep, rest = text.partition("\n## Chỉ có ở bản đầy đủ")
    if not sep:
        return text
    _, sep2, tail = rest.partition("\n## Bản gọn để tải lên")
    return head.rstrip() + "\n" + (sep2 + tail if sep2 else "")


def pack(out: Path) -> dict:
    names = files()
    if "SKILL.md" not in names:
        sys.exit("✗ không thấy SKILL.md ở gốc skill")
    out.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for n in names:
            data = (ROOT / n).read_bytes()
            if n == "THIRD_PARTY.md":
                data = third_party_core(data.decode("utf-8")).encode("utf-8")
            elif n == "AN-TOAN.md":
                data = an_toan_core(data.decode("utf-8")).encode("utf-8")
            info = zipfile.ZipInfo(f"{NAME}/{n}", date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if n.startswith("bin/") and not n.endswith(".cmd") else 0o644) << 16
            z.writestr(info, data)
            size += len(data)
    hosts = set()
    with zipfile.ZipFile(out) as z:
        for i in z.infolist():
            if i.filename.endswith((".py", ".ts", ".tsx", ".mjs", ".js", ".json", ".md", ".cmd")) or i.filename.endswith("/bin/video-editor"):
                hosts |= set(re.findall(r"https?://([a-zA-Z0-9.-]+)", z.read(i).decode("utf-8", "replace")))
    return {"out": out, "files": len(names), "bytes": size, "zip_bytes": out.stat().st_size, "hosts": sorted(hosts)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "dist" / f"{NAME}-skill.zip"))
    a = ap.parse_args()
    r = pack(Path(a.out).expanduser().resolve())
    print(f"✓ bản gọn: {r['files']} file, {r['bytes'] / 1e6:.1f} MB (nén {r['zip_bytes'] / 1e6:.1f} MB) → {r['out']}")
    print("  Tên miền nhắc tới trong mã và tài liệu: " + ", ".join(r["hosts"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
