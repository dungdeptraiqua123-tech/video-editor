# video-editor

Skill dựng video ngắn tiếng Việt cho Claude Code (và Codex): đưa vào **video người nói** hoặc **kịch bản**, nhận về MP4 có phụ đề, đồ hoạ bật đúng lúc nói, kèm phụ đề rời SRT/VTT, ảnh bìa và báo cáo.

```
nhận việc (phong cách, nhịp, quy tắc riêng) → doctor/setup → init → transcribe | tts → build
  → storyboard → người dùng duyệt (approve) → render → tự kiểm tra khung hình → export
```

**Quy trình có kiểm soát**
- Bước nhận việc hỏi phong cách và nhịp (`nhanh`/`vua`/`cham`), mật độ đồ hoạ, và quy tắc riêng chỉ áp dụng cho video đang làm.
- Bảng quy chiếu `bang-quy-chieu.md`: từng chữ kèm thời gian trong video, lịch xuất hiện mọi phần tử.
- Storyboard ảnh ngẫu nhiên có tiêu đề để duyệt; chưa duyệt thì không render.
- Tự kiểm tra khung hình lấy từ chính file MP4, dò khung đen, hình đứng yên, khoảng câm trước khi giao.
- `GHI-NHO.md` ghi góp ý của người dùng qua từng video, áp dụng cho video sau.
- Âm thanh hiệu ứng là âm thu thật (Mixkit), không tạo bằng code.

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

**Tốc độ đo thật** trên máy 4 vCPU, giới hạn RAM 4,9 GB (ngày 31/10/2026):

| Việc | Thời gian | RAM cao nhất |
|---|---|---|
| Chép lời video 176 giây, `large-v3-turbo` (mặc định cho máy 4–12 GB) | 3 phút 10 giây | 2,2 GB |
| Chép lời video 176 giây, `medium` | 4 phút 48 giây | 2,6 GB |
| Storyboard 7 ảnh | 16 giây | |
| Bản nháp 540×960, video 33 giây | 2 phút 16 giây | |
| Bản chính 1080×1920, video 33 giây | 2 phút 54 giây | 4,4 GB |

Bản chính mất khoảng 5,3 lần độ dài video: video 1 phút cần khoảng 5 phút render. Máy ít RAM nên thêm swap.
| `ELEVENLABS_API_KEY` | Chỉ khi làm video từ kịch bản, xem `huong-dan/elevenlabs.md` |

`setup` làm hai việc:

- **Cài 93 skill liên quan** (từ `reference/`) thành skill riêng, nằm cạnh `video-editor` trong `~/.claude/skills/`. Ba skill trùng tên với bộ hyperframes chính thức được cài với tiền tố `herk-` (`herk-hyperframes`, `herk-hyperframes-cli`, `herk-hyperframes-registry`). Skill bạn tự cài trùng tên thì giữ nguyên, không ghi đè. Mở phiên Claude Code mới để thấy chúng.
- **Cài công cụ** vào `~/.video-editor/` (đổi bằng biến `VE_HOME`), không ghi vào thư mục skill.

Quản lý skill liên quan: `video-editor skills` (xem), `skills install --only gsap,hyperframes` (chỉ cài vài bộ), `skills remove` (gỡ hết bản do video-editor cài). Không muốn cài: `setup --no-skills`.

## Tải lên làm skill cá nhân (bản gọn)

Nền tảng cho tải skill lên (skill cá nhân trên claude.ai và các nền tảng tương tự) thường quét an toàn trước khi nhận. Đừng tải cả repo: thư mục `reference/` chứa 93 skill của bên thứ ba, có mã gọi dịch vụ ngoài, và bộ cài chép skill vào thư mục skills của trợ lý, nên dễ bị chặn. Tạo bản gọn chỉ gồm phần lõi:

```bash
python3 tools/dong-goi.py        # → dist/video-editor-skill.zip (khoảng 0,5 MB)
```

Bản gọn vẫn dựng video đầy đủ. Nó chỉ không kèm thư viện tham khảo và lệnh `video-editor skills`. Skill ghi file ở đâu, gọi mạng tới đâu: `AN-TOAN.md`.
Môi trường chạy skill tải lên thường chặn mạng tới huggingface.co và nơi tải trình duyệt render; khi đó `doctor` báo thiếu mô hình chép lời hoặc trình duyệt. Chép lời có thể thay bằng phụ đề có sẵn (`transcribe --from-srt`).
Sau khi cài, chỉ cần nói với Claude: *"dựng Reel từ video này"* hoặc *"làm video 45 giây từ kịch bản này"*.

Đã kiểm thử trên Linux (Claude Code cloud). macOS và Windows được hỗ trợ theo thiết kế (đường dẫn, lệnh khởi chạy `.cmd`, gợi ý cài đặt) nhưng chưa chạy thử trên máy thật.

## Dùng thủ công

```bash
video-editor init du-an/bitcoin --input video.mp4 --template btc-daily --pace nhanh --rule "Không dùng màu đỏ cho số tăng"
video-editor transcribe du-an/bitcoin
# sửa du-an/bitcoin/project.json: fix, content (xem huong-dan/do-hoa.md); soát work/bang-quy-chieu.md
video-editor build du-an/bitcoin
video-editor preview du-an/bitcoin        # out/storyboard.jpg → gửi người dùng duyệt
video-editor approve du-an/bitcoin        # khi người dùng đồng ý
video-editor render du-an/bitcoin
video-editor export du-an/bitcoin         # tự kiểm tra (out/kiem-tra.jpg), phụ đề, báo cáo
video-editor note "Phụ đề to hơn" --project du-an/bitcoin --loai phu-de   # ghi nhớ góp ý cho video sau
```

## Cấu trúc

| Đường dẫn | Nội dung |
|---|---|
| `SKILL.md` | Quy trình cho Claude |
| `GHI-NHO.md` | Góp ý của người dùng qua các video, Claude đọc ở đầu mỗi video |
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
