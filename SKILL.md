---
name: video-editor
description: Dựng video ngắn tiếng Việt (Reels, TikTok, Shorts, YouTube) từ video người nói hoặc từ kịch bản với giọng đọc AI. Tự cài môi trường, chép lời, cắt lặng và từ đệm, đồ hoạ bật đúng lúc nói, phụ đề, render MP4, xuất SRT/VTT và báo cáo. Khổ 9:16, 16:9, 1:1, 4:5; mẫu nhận diện đổi được.
---

# video-editor

Mọi bước chạy qua một lệnh: `<skill>/bin/video-editor` (Windows: `bin\video-editor.cmd`). `<skill>` là thư mục chứa file này.
Công cụ tự quản lý đường dẫn, file trung gian và trạng thái; chạy lại một lệnh chỉ làm phần có đầu vào thay đổi. Việc của bạn là **nội dung**: đọc lời thoại, viết `content` trong `project.json`, duyệt ảnh xem trước, báo cáo cho người dùng.

## Môi trường hỗ trợ

| Môi trường | Mức hỗ trợ |
|---|---|
| Claude Code trên macOS, Linux, Windows; Claude Code trên web (cloud) | Đầy đủ. Đã chạy thật trên Linux; macOS/Windows theo thiết kế, chưa kiểm thử trên máy thật |
| Codex và công cụ khác đọc `AGENTS.md` | Dùng được, cùng lệnh |
| Chat không có terminal, hoặc sandbox không có mạng | Không đủ: cần Node, ffmpeg, tải mô hình |

## Quy trình

**1. Nhận việc.** Hỏi hoặc tự suy ra theo `mau-tai-lieu/phieu-nhan-viec.md`:
- nguồn (video người nói hay kịch bản);
- nền tảng → khổ hình;
- mẫu nhận diện, độ dài;
- dẫn chứng (ảnh, số liệu).

Ô nào tự chọn thì ghi lại để báo ở bước 8.

**2. Kiểm tra môi trường.**

```bash
<skill>/bin/video-editor doctor
```

- Còn dấu ✗ thì chạy `<skill>/bin/video-editor setup` (một lần, 1–10 phút).
- Lệnh này tự cài môi trường Python riêng, thư viện đúng phiên bản, bộ dựng Remotion và trình duyệt render, rồi tải mô hình Whisper.
- Máy yếu (dưới 8 GB RAM): `setup --model nhe`.
- Thiếu ffmpeg hoặc Node: làm theo dòng `→` mà doctor in ra, hoặc `setup --install-system` (macOS/Windows).

**3. Tạo dự án** trong thư mục làm việc của người dùng. Không tạo trong thư mục skill.

```bash
video-editor init du-an/<tên> --input video.mp4 [--format 9:16] [--template trung-tinh]
video-editor init du-an/<tên> --script kichban.txt [--type explainer|product] [--background canh-quay.mp4]
```

- Khổ: `9:16` (Reels/TikTok/Shorts), `16:9` (YouTube), `1:1`, `4:5`.
- Mẫu: `trung-tinh` (mặc định) hoặc `btc-daily` (ví dụ kênh Bitcoin). Thương hiệu riêng: ghi đè `brand` trong `project.json` (xem `huong-dan/du-an.md`).

**4. Lấy lời thoại.**
- **Video người nói:** `video-editor transcribe <dự án>`.
  - Mạng chặn Hugging Face: dùng `--from-srt phu-de.srt` (xuất từ CapCut).
- **Kịch bản:** `video-editor tts <dự án>`, cần `ELEVENLABS_API_KEY`, xem `huong-dan/elevenlabs.md`.
  - Chưa có key, hoặc muốn duyệt bố cục trước khi tốn ký tự: `tts --placeholder` (giọng tạm im lặng).

**5. Soát lời, viết nội dung.** Đọc `work/loi-thoai.txt`.
- **Sửa chữ nghe sai:** thêm vào `fix`. Dòng có `⟵ nghe chưa chắc` cần hỏi người dùng nếu không đoán chắc được.
- **Viết `content`:** `hook`, `beats` (khung đồ hoạ), `topics` (thẻ chủ đề), `cta`. Cú pháp và các loại đồ hoạ ở `huong-dan/do-hoa.md`.
- **Neo đồ hoạ bằng cụm từ trong lời** (`"start": "giá Bitcoin"`, `"say": "87 ngàn"`), không đoán giây. Nhờ vậy đồ hoạ bật đúng lúc nói và không lệch khi cắt lại.

**6. Dựng và kiểm tra.**

```bash
video-editor build <dự án>
```

- Lệnh này cắt khoảng lặng và từ đệm, đổi cụm neo thành mốc thời gian theo bản đã cắt, rồi kiểm tra nội dung.
- Lỗi nào cũng chỉ rõ chỗ và cách sửa. Cụm neo sai thì kèm gợi ý cụm gần giống.
- Lặp bước 5–6 tới khi không còn lỗi.
- Chỗ nghi nói vấp được liệt kê. Xem và quyết: `cuts.stumbles: "auto"`, hoặc thêm khoảng vào `cuts.drop`.

**7. Xem trước, rồi render.**

```bash
video-editor preview <dự án>
video-editor render <dự án>
```

- **preview:** tạo `out/xem-truoc.jpg`, ảnh mọi khoảnh khắc chính, khoảng 1 phút. Mở xem từng ảnh: chữ có tràn không, đồ hoạ có che mặt không, màu có đúng không. Gửi người dùng duyệt nếu là lần đầu với kênh này.
- **render:** khoảng 3–4 lần thời lượng video trên máy 4 nhân.

**8. Xuất và báo cáo.**

```bash
video-editor export <dự án>
```

- File ra: `out/<tên>.mp4`, `.srt`, `.vtt`, `anh-bia.jpg`, `bao-cao.md`.
- Gửi người dùng video và báo cáo. Báo cáo gồm thời lượng, phần đã cắt, LUFS, đồng bộ, chỗ nghi nói vấp, cảnh báo.
- Nêu rõ những ô ở bước 1 đã tự chọn, và các cụm lời chưa chắc.

`video-editor run <dự án>` chạy liền các bước còn thiếu (lấy lời → build → render → export). Bị ngắt giữa chừng thì chạy lại đúng lệnh đó: bước đã xong được bỏ qua.

## Nguyên tắc

1. **Nói tới đâu, hiện tới đó.** Phần tử đồ hoạ nào cũng phải có `say` neo vào lời. Không bịa số người nói không đọc.
2. **Không sửa mã bộ dựng cho từng dự án.** Mọi khác biệt nằm trong `project.json` (`brand`, `captions`, `face`, `cuts`, `content`). Nếu thật sự cần tính năng mới, sửa trong `engine/src` của skill và kiểm thử lại (`python3 tests/e2e.py`).
3. **Một hệ thời gian.** Giây ghi bằng số trong `project.json` là giây của lời thoại gốc (như `loi-thoai.txt`); công cụ tự đổi sang bản đã cắt. Không tự cộng trừ.
4. **Chỉ nén một lần.** Render xuất thẳng H.264 CRF 20, không nén lại bằng ffmpeg.
5. **Báo đúng nguyên nhân.** Lệnh lỗi in `✗` kèm `→ cách xử lý`. Chuyển nguyên văn cho người dùng khi cần họ làm gì (cấp mạng, thêm key). Không đoán vòng.
6. **Không lan ra ngoài.** Không đăng video, không gửi file ra dịch vụ khác ngoài ElevenLabs khi người dùng đã chọn giọng AI.

## Có sẵn và cần dịch vụ ngoài

| Tính năng | Cần gì |
|---|---|
| Cắt lặng, từ đệm, nói vấp, đoạn giữ/bỏ | Có sẵn |
| Đồ hoạ, phụ đề, 4 khổ hình, mẫu nhận diện, âm thanh hiệu ứng | Có sẵn (âm thanh tự tạo, không vướng bản quyền) |
| Chép lời tiếng Việt | Tải mô hình Whisper một lần từ huggingface.co (0,5–3 GB) |
| Giọng đọc từ kịch bản | ElevenLabs: key + mạng tới api.elevenlabs.io. Gói Free không nhân bản giọng, không dùng thương mại |
| Render | Node 20.19+; trình duyệt Chrome Headless Shell do Remotion tải |

## Tài liệu

| File | Khi nào đọc |
|---|---|
| `huong-dan/du-an.md` | Mọi khoá trong `project.json`: thương hiệu, phụ đề, mặt người nói, cắt, nhạc nền |
| `huong-dan/do-hoa.md` | Viết `content`: các loại đồ hoạ, neo cụm từ, độ dài chữ, mẫu cho từng loại video |
| `huong-dan/loi-thuong-gap.md` | Khi một lệnh báo lỗi mà dòng `→` chưa đủ |
| `huong-dan/elevenlabs.md` | Thiết lập giọng đọc AI (chọn gói, key, nhân bản giọng) |
| `mau-tai-lieu/` | Phiếu nhận việc, khung kịch bản 45–60 giây |
| `templates/<mẫu>/README.md` | Quy chuẩn nhận diện của mẫu |
| `examples/btc-daily/project.json` | Ví dụ thật: Reel 175 giây, 11 khung đồ hoạ, 11 thẻ chủ đề |
| `reference/INDEX.md` | Kỹ thuật nâng cao ngoài bộ dựng mặc định (đọc khi cần) |
