# Hướng dẫn cho tác tử AI (Codex, Cursor và các công cụ đọc AGENTS.md)

Repo này là skill `video-editor`: dựng video ngắn tiếng Việt từ video người nói hoặc kịch bản.

- **Dùng skill để dựng video:** làm theo `SKILL.md`. Mọi bước chạy qua `bin/video-editor` (Windows: `bin\video-editor.cmd`). Bắt đầu bằng `bin/video-editor doctor`.
- **Cài skill:** clone repo vào thư mục skills của công cụ (Claude Code: `~/.claude/skills/video-editor`) rồi chạy `bin/video-editor setup`. Lệnh này cài luôn 93 skill liên quan trong `reference/` thành skill riêng cạnh nó (thư mục khác: `--skills-dir`).
- **Tải lên làm skill cá nhân** (nền tảng có bước quét an toàn): `python3 tools/dong-goi.py` tạo bản gọn `dist/video-editor-skill.zip`, chỉ gồm phần lõi. Phạm vi hoạt động: `AN-TOAN.md`.
- **Sửa chính skill:**
  - mã điều phối Python (chỉ dùng thư viện chuẩn): `ve/`;
  - bộ dựng Remotion: `engine/src`;
  - mẫu nhận diện: `templates/`.
- **Kiểm thử sau khi sửa:**
  - `python3 -m unittest discover -s tests -t .` (nhanh, không cần cài gì);
  - `python3 tests/e2e.py` (trọn quy trình, cần đã chạy `bin/video-editor setup`, khoảng 3–5 phút).
- **Kiểm tra kiểu cho bộ dựng:** `npx tsc` trong `~/.video-editor/engine-<VERSION>` sau khi `setup` (thư mục này có node_modules).
- **Đổi phụ thuộc trong `engine/package.json`:** tăng `VERSION` để bộ dựng cài vào thư mục mới.
