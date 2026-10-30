# Thiết lập ElevenLabs cho chế độ B

## 1. Chọn gói

Số liệu dưới đây lấy từ các trang tổng hợp giá năm 2026, không phải từ ElevenLabs. Trước khi mua, xem lại trang Pricing chính thức.

| | Free | Starter (khoảng 5 đến 6 USD/tháng) |
|---|---|---|
| Ký tự mỗi tháng | khoảng 10.000 | khoảng 30.000 |
| Số video 45 đến 60 giây | khoảng 8 đến 10 | khoảng 25 đến 30 |
| Gọi API | có | có |
| Nhân bản giọng (Instant Voice Cloning) | **không** | có |
| Dùng thương mại | **không** | có |

- **Gói Free:** chỉ dùng giọng có sẵn trong thư viện, để làm thử quy trình. Không đăng lên kênh có kiếm tiền hoặc bán hàng.
- **Gói Starter:** là gói thấp nhất nhân bản được giọng chủ kênh và đăng thương mại được.

Mỗi video 45 đến 60 giây tốn khoảng 800 đến 1.200 ký tự. Lần tạo lại giọng nào cũng tốn ký tự, nên phải duyệt kịch bản trước khi tạo.

## 2. Tạo API key

1. Đăng nhập elevenlabs.io.
2. Mở trang API Keys: bấm tên hoặc avatar ở góc dưới trái, chọn **API Keys** (hoặc vào elevenlabs.io/app/settings/api-keys).
3. Bấm **Create API Key** và đặt tên, ví dụ `video-editor`.
4. Phân quyền:
   - bật **Text to Speech** và **Voices** (đọc, xem và nhân bản giọng);
   - tắt các mục khác.
5. Bấm **Create** và copy key ngay, vì key chỉ hiện một lần.

Không bao giờ dán key vào khung chat, kịch bản hay commit.

## 3. Đưa key vào môi trường làm việc

**Claude cloud** (claude.ai/code, dự án):

1. Mở Project settings, vào menu **Cloud environment**, bấm bánh răng cạnh môi trường đang chọn.
2. Mục **Environment variables**: thêm `ELEVENLABS_API_KEY=<key>`.
3. Mục **Network access**, phần **Allowed domains**: thêm `api.elevenlabs.io`, giữ ô Allow package managers.
4. Cài đặt chỉ có hiệu lực ở **phiên làm việc mới**, nên mở thread hoặc phiên mới để chạy.

Môi trường thuộc tổ chức thì chỉ đọc được: nhờ admin tổ chức sửa.

**Máy cá nhân (Claude Code):** thêm `export ELEVENLABS_API_KEY=...` vào `~/.zshrc` hoặc `~/.bashrc`, hoặc dùng file `.env` không commit.

## 4. Kiểm tra

```bash
video-editor doctor          # dòng "Giọng đọc ElevenLabs": có key, kết nối OK
video-editor voices          # liệt kê giọng trong tài khoản
```

| Kết quả | Ý nghĩa |
|---|---|
| In ra danh sách giọng | Thành công |
| `Chưa có ELEVENLABS_API_KEY` | Biến môi trường chưa vào phiên này. Mở phiên hoặc terminal mới |
| `ElevenLabs từ chối key (401)` | Key sai hoặc thiếu quyền Voices hay Text to Speech |
| `Mạng chặn api.elevenlabs.io` | Chưa mở domain |
| `Gói … không nhân bản giọng được` khi `clone-voice` | Gói Free không có nhân bản giọng |

## 5. Dùng trong dự án

**Gói Free (giọng có sẵn):**

1. Chạy `video-editor voices` và chọn một giọng đọc tiếng Việt tự nhiên.
2. Ghi `voice.voiceId` vào `project.json`.
3. Chạy `video-editor tts <dự án>`.

Video làm bằng gói Free không được đăng cho kênh kiếm tiền hoặc bán hàng.

**Gói Starter trở lên (giọng nhân bản):**

```bash
ffmpeg -i video-cu.mp4 -ss 10 -t 150 -vn -ac 1 -ar 44100 mau-giong.mp3
video-editor clone-voice --name "Tên kênh" mau-giong.mp3 --project du-an/<tên>
video-editor tts du-an/<tên>
```

- Mẫu giọng nên dài 1 đến 3 phút, nói rõ, không có nhạc nền, không có người khác chen vào.
- `voiceId` được ghi vào dự án. Với video sau, chép `voice.voiceId` sang `project.json` mới, không cần nhân bản lại.
- Chỉ nhân bản giọng của chính mình hoặc của người đã đồng ý.

**Tiết kiệm ký tự:**
- Duyệt bố cục bằng `video-editor tts <dự án> --placeholder` trước (giọng tạm im lặng, không tốn ký tự).
- Chỉ tạo giọng thật khi kịch bản đã chốt.
- `tts` chỉ gọi lại ElevenLabs khi kịch bản hoặc cài đặt giọng thay đổi.

**Chỉnh giọng trong `voice`:**
- `speed`: 0,7 đến 1,2, mặc định 1,05.
- `stability`: thấp hơn thì cảm xúc hơn, mặc định 0,45.
- `style`: 0 đến 1.
- `model`: `eleven_turbo_v2_5` (mặc định, hỗ trợ tiếng Việt), `eleven_flash_v2_5` (rẻ, nhanh), `eleven_v3` (biểu cảm hơn).
