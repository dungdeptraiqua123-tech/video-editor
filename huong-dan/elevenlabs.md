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
python3 scripts/tts_elevenlabs.py voices
```

| Kết quả | Ý nghĩa |
|---|---|
| In ra danh sách giọng | Thành công |
| `Thiếu ELEVENLABS_API_KEY` | Biến môi trường chưa vào phiên này. Mở phiên mới. |
| `ElevenLabs 401` | Key sai hoặc thiếu quyền Voices hay Text to Speech |
| `403` từ proxy, hoặc không kết nối được | Chưa mở `api.elevenlabs.io` |
| Lỗi khi `clone` | Gói Free không có nhân bản giọng |

## 5. Dùng theo gói

**Gói Free (giọng có sẵn):**

```bash
python3 scripts/tts_elevenlabs.py voices
python3 scripts/tts_elevenlabs.py speak kichban.txt --voice <voice_id>
```

Chạy lệnh đầu để xem danh sách giọng, rồi chọn một giọng đọc tiếng Việt tự nhiên cho lệnh thứ hai. Đọc thử một câu ngắn trước để tiết kiệm ký tự.

**Gói Starter trở lên (giọng nhân bản):**

```bash
ffmpeg -i video-cu.mp4 -ss 10 -t 150 -vn -ac 1 -ar 44100 mau-giong.mp3
python3 scripts/tts_elevenlabs.py clone --name "BTC Daily" mau-giong.mp3
python3 scripts/tts_elevenlabs.py speak kichban.txt
```

- Lệnh `clone` ghi `voice.json`. Giữ file này cho các video sau.
- Mẫu giọng nên là 1 đến 3 phút nói rõ, không nhạc nền, không người khác chen vào.
- Chỉ nhân bản giọng của chính mình hoặc người đã đồng ý.
