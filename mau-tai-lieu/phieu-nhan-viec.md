# Phiếu nhận việc dựng video

Điền trước khi dựng. Hỏi người dùng gọn trong một lượt; ô nào họ không trả lời thì tự suy ra và ghi "tự chọn" để báo lại khi giao file. Mỗi ô ghi kèm khoá tương ứng trong `project.json`.

## 1. Nguồn

| Câu hỏi | Lựa chọn | Khoá |
|---|---|---|
| Đi từ đâu? | Video người nói / file thu âm / kịch bản (giọng AI) | `init --input` hoặc `init --script` |
| Loại video | Người nói / giải thích bằng đồ hoạ / giới thiệu sản phẩm | `type` |
| Có cảnh quay hoặc ảnh làm nền không (video không người nói)? | đường dẫn | `background` |
| Có phụ đề `.srt` sẵn không (thay cho chép lời)? | có / không | `transcribe --from-srt` |
| Giọng AI: đã có key ElevenLabs? Gói gì? Đã có giọng nhân bản (voiceId)? | Free / Starter+ | `voice` |
| Ảnh, biểu đồ, số liệu thật để làm dẫn chứng | đường dẫn | đồ hoạ `media` |

## 2. Đầu ra

| Câu hỏi | Mặc định | Khoá |
|---|---|---|
| Nền tảng đăng | Facebook Reels | quyết định khổ |
| Khổ hình | 9:16 (Reels, TikTok, Shorts); 16:9 cho YouTube; 1:1 hoặc 4:5 cho bài đăng feed | `format` |
| Độ dài | giữ nguyên ý, cắt lặng | `cuts` |
| Đoạn cần bỏ / chỉ lấy một đoạn | | `cuts.drop`, `cuts.keep` |

## 3. Nhận diện

| Câu hỏi | Mặc định | Khoá |
|---|---|---|
| Mẫu | `trung-tinh`; kênh Bitcoin dùng `btc-daily` | `template` |
| Tên kênh, logo, màu chủ đạo, font | của mẫu | `brand` |
| Kiểu phụ đề | glow | `captions.style` |
| Từ khoá cần tô màu trong phụ đề | của mẫu | `captions.keywords` |
| Nhạc nền (người dùng có quyền dùng) | không | `music` |
| Câu kêu gọi cuối video | "Theo dõi để xem video tiếp theo" | `content.cta` |

## 4. Nội dung

- Ý chính một câu, dùng cho thẻ mở đầu: `content.hook.title`.
- Những con số, mốc, danh sách cần thành đồ hoạ: `content.beats`.
- Tên riêng, thuật ngữ dễ nghe sai: `fix`.

## 5. Trước khi render

- [ ] `build` không còn lỗi; đã xem các cảnh báo và chỗ nghi nói vấp.
- [ ] Đã gửi người dùng các cụm lời "nghe chưa chắc" nếu không tự đoán chắc được.
- [ ] Đã xem `out/xem-truoc.jpg`: chữ không tràn, đồ hoạ không che mặt, màu đúng nhận diện.
- [ ] Video từ kịch bản: đã thay giọng tạm bằng giọng thật (`tts` không có `--placeholder`).
