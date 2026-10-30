# video-editor

Skill dựng video ngắn dọc (Facebook Reels, TikTok, Shorts) tiếng Việt cho Claude. Cài một skill là đủ: quy trình từ phiếu nhận việc tới giao file, 93 skill con, mẫu Remotion, script và bộ nhận diện BTC Daily.

## Làm được gì

**Chế độ A: dựng từ video người nói**

Đưa vào một video người nói, nhận về một Reel hoàn chỉnh:

1. **Nhận việc** bằng phiếu: nền tảng, độ dài, phong cách, dẫn chứng.
2. **Chép lời tiếng Việt** có mốc từng chữ (faster-whisper large-v3), sửa chữ nghe sai, bỏ đoạn thừa.
3. **Cắt khoảng lặng và chỗ vấp**, chuẩn hoá âm thanh về -14 LUFS.
4. **Đồ hoạ nói tới đâu hiện tới đó:** thẻ giá, mốc hỗ trợ/kháng cự, danh sách, biểu đồ, con số lớn, thẻ chủ đề. Mỗi phần tử bật ra 0,08 giây sau từ khoá.
5. **Phụ đề 4 kiểu** (mặc định là kiểu phát sáng): chữ đang đọc đổi màu, con số màu vàng, tối đa 2 dòng cân nhau.
6. **Hai bố cục:** người nói toàn màn hình, hoặc đồ hoạ toàn màn hình với ô mặt ở góc. Có zoom, chuyển cảnh và hiệu ứng âm thanh.
7. **Render và giao file:** MP4, phụ đề `.srt`, ảnh xem trước, mã nguồn, cùng báo cáo.

Số đo thật trên video 175 giây: ra Reel 173 giây, render khoảng 10 phút trên máy 4 nhân, file khoảng 90 MB.

**Chế độ B: tạo video từ prompt hoặc kịch bản**

- Viết kịch bản từ một câu chủ đề.
- Đọc bằng giọng ElevenLabs: giọng có sẵn với gói Free, hoặc giọng nhân bản của chủ kênh với gói Starter trở lên.
- Video là đồ hoạ toàn màn hình; phụ đề và đồ hoạ bám từng chữ của giọng đọc.
- Thiết lập theo `huong-dan/elevenlabs.md`.

**Kèm 93 skill con** để tra cứu: video quảng cáo, explainer, kinetic typography, khoảng 450 khối chuyển cảnh HyperFrames, soát lỗi khung hình.

**Chưa làm được:** quay cảnh mới hoặc tạo người thật.

## Cài đặt

**Claude Code (máy cá nhân):**

```bash
git clone https://github.com/dungdeptraiqua123-tech/video-editor.git ~/.claude/skills/video-editor
```

**claude.ai:**
1. Nén thư mục này thành zip, có thể bỏ `.git` và các thư mục `demos`, `workbench`, `gallery` của video-shotcraft cho nhẹ.
2. Vào Settings → Capabilities → Skills → Upload skill.

## Môi trường cần có

| Thứ cần | Dùng cho |
|---|---|
| Python 3 và `faster-whisper` | Chép lời (chế độ A) |
| Node 18 trở lên, Remotion 4.0.537 (`npm ci` trong bản chép của `mau-remotion/`) | Dựng video |
| ffmpeg | Cắt, ghép |
| Chromium headless | Render |
| Mạng mở cho `huggingface.co`, `*.hf.co`, `*.xethub.hf.co` | Tải mô hình Whisper |
| `ELEVENLABS_API_KEY` và mạng mở cho `api.elevenlabs.io` | Chế độ B |

## Cấu trúc

| Đường dẫn | Nội dung |
|---|---|
| `SKILL.md` | Quy trình đầy đủ, bắt đầu đọc từ đây |
| `mau-remotion/` | Dự án Remotion mẫu |
| `scripts/` | `transcribe.py`, `build.py`, `tts_elevenlabs.py` |
| `nhan-dien/btc-daily/` | Bộ nhận diện |
| `mau-tai-lieu/` | Phiếu nhận việc, khung kịch bản |
| `huong-dan/` | Hướng dẫn thiết lập ElevenLabs |
| `skills/`, `INDEX.md` | 93 skill con và danh mục |
