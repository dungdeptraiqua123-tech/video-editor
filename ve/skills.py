"""Cài các skill tham khảo trong reference/ thành skill riêng của Claude Code, nằm cạnh skill video-editor.

Mỗi skill được chép sang <thư mục skills>/<tên>/ kèm file đánh dấu, nên lệnh cài lại chỉ thay bản do video-editor cài,
không đụng skill người dùng tự cài trùng tên. Chép thay vì tạo liên kết để chạy được cả trên Windows.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from .env import SKILL_DIR, VERSION, VEError, info, warn

REF = SKILL_DIR / "reference"
MARK = ".video-editor-skill"
# Khi hai bộ có skill trùng tên, bộ đứng trước giữ tên gốc; bộ sau cài với tiền tố (herk-edit-kit/hyperframes -> herk-hyperframes).
PRIORITY = ["hyperframes", "gsap", "ghost-editor", "video-shotcraft", "motion-graphics", "iart-ai", "herk-edit-kit"]


def default_dir() -> Path:
    # skill nằm trong một thư mục skills (~/.claude/skills/video-editor, <dự án>/.claude/skills/video-editor): cài cạnh nó
    return SKILL_DIR.parent if SKILL_DIR.parent.name == "skills" else Path.home() / ".claude" / "skills"


def catalog(only: list[str] | None = None) -> list[dict]:
    """[{set, src, name, renamed}] theo thứ tự ưu tiên của bộ."""
    sets = sorted((d.name for d in REF.iterdir() if d.is_dir()), key=lambda s: (PRIORITY.index(s) if s in PRIORITY else len(PRIORITY), s)) if REF.exists() else []
    if only:
        bad = [s for s in only if s not in sets]
        if bad:
            raise VEError(f"Không có bộ {', '.join(bad)}.", f"Các bộ có sẵn: {', '.join(sets)}.")
    out, taken = [], set()
    for s in sets:
        for sk in sorted(p.parent for p in (REF / s).glob("*/SKILL.md")):
            name = sk.name
            if name in taken or name == SKILL_DIR.name:
                name = f"{s.split('-')[0]}-{sk.name}"
            taken.add(name)
            if not only or s in only:
                out.append({"set": s, "src": sk, "name": name, "renamed": name != sk.name})
    return out


def _managed(d: Path) -> bool:
    return (d / MARK).exists()


def _target(target: Path | None) -> Path:
    t = Path(target).expanduser().resolve() if target else default_dir()
    if t == SKILL_DIR or SKILL_DIR in t.parents:
        raise VEError("Thư mục đích nằm trong skill video-editor.", "Chọn thư mục skills chứa video-editor, ví dụ ~/.claude/skills.")
    return t


def install(target: Path | None = None, only: list[str] | None = None) -> dict:
    t = _target(target)
    items = catalog(only)
    if not items:
        raise VEError("Không thấy skill nào trong reference/.", "Tải lại skill video-editor đầy đủ từ repo.")
    t.mkdir(parents=True, exist_ok=True)
    done, skipped = [], []
    for it in items:
        dst = t / it["name"]
        if dst.exists() or dst.is_symlink():
            if not _managed(dst):
                skipped.append(it["name"])
                continue
            shutil.rmtree(dst)
        shutil.copytree(it["src"], dst)
        if it["renamed"]:
            md = dst / "SKILL.md"
            text = md.read_text(encoding="utf-8")
            md.write_text(re.sub(r"(?m)^name:.*$", f"name: {it['name']}", text, count=1), encoding="utf-8")
        (dst / MARK).write_text(json.dumps({"set": it["set"], "source": str(it["src"]), "version": VERSION}, ensure_ascii=False), encoding="utf-8")
        done.append(it["name"])
    # bản do video-editor cài trước đây mà nay không còn trong danh mục thì gỡ
    names = {it["name"] for it in catalog()}
    stale = [d.name for d in t.iterdir() if d.is_dir() and _managed(d) and d.name not in names] if not only else []
    for n in stale:
        shutil.rmtree(t / n)
    info(f"✓ cài {len(done)} skill liên quan vào {t}" + (f" (gỡ {len(stale)} bản cũ)" if stale else ""))
    renamed = [it for it in items if it["renamed"] and it["name"] in done]
    if renamed:
        info("  trùng tên nên đổi: " + ", ".join(f"{it['set']}/{it['src'].name} → {it['name']}" for it in renamed))
    if skipped:
        warn(f"Bỏ qua {len(skipped)} skill vì đã có skill cùng tên do bạn tự cài: {', '.join(skipped)}")
    info("  Mở phiên Claude Code mới để thấy các skill này.")
    return {"dir": str(t), "installed": done, "skipped": skipped, "removed": stale}


def remove(target: Path | None = None) -> int:
    t = _target(target)
    gone = [d for d in t.iterdir() if d.is_dir() and _managed(d)] if t.exists() else []
    for d in gone:
        shutil.rmtree(d)
    info(f"✓ gỡ {len(gone)} skill do video-editor cài khỏi {t}")
    return len(gone)


def status(target: Path | None = None) -> dict:
    t = _target(target)
    items = catalog()
    ok = [it["name"] for it in items if _managed(t / it["name"])]
    clash = [it["name"] for it in items if (t / it["name"]).exists() and not _managed(t / it["name"])]
    return {"dir": str(t), "total": len(items), "installed": len(ok), "conflicts": clash}
