# video-editor

Skill dựng video ngắn tiếng Việt cho Claude Code (và Codex): đưa vào **video người nói** hoặc **kịch bản**, nhận về MP4 có phụ đề, đồ hoạ bật đúng lúc nói, kèm phụ đề rời SRT/VTT, ảnh bìa và báo cáo.

```
nhận việc → doctor/setup → init → transcribe | tts → build → preview → render → export
```

## Làm được gì

**Đầu vào**
- Video người nói, file thu âm, hoặc kịch bản đọc bằng giọng ElevenLabs (giọng có sẵn hoặc giọng nhân bản).
- Video sản phẩm: cảnh quay làm nền, giọng AI, ảnh hoặc clip sản phẩm trong khung.

**Cắt**
- Khoảng lặng, từ đệm (ờ, ừm…), nói vấp (gợi ý hoặc tự cắt), khoảng giữ hoặc bỏ tuỳ chọn.
- Một hệ thời gian chung, nên phụ đề, đồ hoạ và SRT không lệch sau khi cắt.

**Đồ hoạ**
- Con số lớn, giá đếm lên, mốc kháng cự/hỗ trợ, danh sách, biểu đồ vẽ dần, tiêu đề chương, ảnh/clip sản phẩm, thẻ chủ đề có tick.
- Neo bằng cụm từ trong lời: phần tử bật 0,08 giây trước khi được nói.

**Khổ hình:** 9:16, 16:9, 1:1, 4:5. Mỗi khổ có bố cục và vùng an toàn riêng.

**Nhận diện**
- Mẫu `trung-tinh` (mặc định) và `btc-daily` (ví dụ).
- Đổi màu, font, logo, kiểu phụ đề trong `project.json`, không cần sửa mã.

**Đầu ra**
- MP4 H.264, -14 LUFS, chỉ nén một lần.
- Phụ đề SRT/VTT, ảnh bìa, ảnh xem trước các khoảnh khắc chính.
- Báo cáo đồng bộ và chất lượng.

**Tự cài và tự kiểm tra:** `doctor` chỉ ra thiếu gì và cách sửa; `setup` cài môi trường riêng; chạy lại thì làm tiếp từ bước dở.

**Chưa làm được:** quay cảnh mới, tạo người thật, đăng video.

## Cài đặt (Claude Code)

```bash
git clone https://github.com/dungdeptraiqua123-tech/video-editor.git ~/.claude/skills/video-editor
~/.claude/skills/video-editor/bin/video-editor setup
```

| Cần có | Ghi chú |
|---|---|
| Python 3.9+ | macOS/Linux thường có sẵn; Windows: python.org |
| Node.js 20.19+, 22.13+ hoặc 24+ | nodejs.org (bản LTS) |
| ffmpeg | `brew install ffmpeg` · `winget install Gyan.FFmpeg` · `sudo apt install ffmpeg` |
| 4 GB trống, 8 GB RAM | Máy yếu hơn: `setup --model nhe` |
| Mạng lúc cài | npm, huggingface.co (mô hình chép lời), remotion.media (trình duyệt render) |
| `ELEVENLABS_API_KEY` | Chỉ khi làm video từ kịch bản, xem `huong-dan/elevenlabs.md` |

`setup` làm hai việc:

- **Cài 93 skill liên quan** (từ `reference/`) thành skill riêng, nằm cạnh `video-editor` trong `~/.claude/skills/`. Ba skill trùng tên với bộ hyperframes chính thức được cài với tiền tố `herk-` (`herk-hyperframes`, `herk-hyperframes-cli`, `herk-hyperframes-registry`). Skill bạn tự cài trùng tên thì giữ nguyên, không ghi đè. Mở phiên Claude Code mới để thấy chúng.
- **Cài công cụ** vào `~/.video-editor/` (đổi bằng biến `VE_HOME`), không ghi vào thư mục skill.

Quản lý skill liên quan: `video-editor skills` (xem), `skills install --only gsap,hyperframes` (chỉ cài vài bộ), `skills remove` (gỡ hết bản do video-editor cài). Không muốn cài: `setup --no-skills`.
Sau khi cài, chỉ cần nói với Claude: *"dựng Reel từ video này"* hoặc *"làm video 45 giây từ kịch bản này"*.

Đã kiểm thử trên Linux (Claude Code cloud). macOS và Windows được hỗ trợ theo thiết kế (đường dẫn, lệnh khởi chạy `.cmd`, gợi ý cài đặt) nhưng chưa chạy thử trên máy thật.

## Dùng thủ công

```bash
video-editor init du-an/bitcoin --input video.mp4 --template btc-daily
video-editor transcribe du-an/bitcoin
# sửa du-an/bitcoin/project.json: fix, content (xem huong-dan/do-hoa.md)
video-editor build du-an/bitcoin
video-editor preview du-an/bitcoin
video-editor render du-an/bitcoin
video-editor export du-an/bitcoin
```

## Cấu trúc

| Đường dẫn | Nội dung |
|---|---|
| `SKILL.md` | Quy trình cho Claude |
| `AGENTS.md` | Hướng dẫn cho Codex và công cụ khác |
| `bin/` | Lệnh `video-editor` (macOS/Linux) và `video-editor.cmd` (Windows) |
| `ve/` | Công cụ điều phối (Python, chỉ thư viện chuẩn) |
| `engine/` | Bộ dựng Remotion |
| `templates/` | Mẫu nhận diện |
| `examples/` | Dự án mẫu |
| `huong-dan/` | Hướng dẫn: dự án, đồ hoạ, lỗi thường gặp, ElevenLabs |
| `mau-tai-lieu/` | Phiếu nhận việc, khung kịch bản |
| `tests/` | Kiểm thử đơn vị và trọn quy trình |
| `reference/` | Thư viện tham khảo: 93 skill từ 7 bộ (không cần cho quy trình chính). Danh mục ở `reference/INDEX.md` |
| `THIRD_PARTY.md` | Giấy phép thành phần bên thứ ba (Remotion miễn phí tới 3 người, công ty lớn hơn cần mua giấy phép) |

## Kiểm thử

```bash
python3 -m unittest discover -s tests -t .   # 26 kiểm thử đơn vị, dưới 1 giây
python3 tests/e2e.py                          # 2 video trọn quy trình + 5 tình huống lỗi
```
