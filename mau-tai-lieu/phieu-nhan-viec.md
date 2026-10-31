# Phiếu nhận việc dựng video

Điền trước khi dựng. **Đọc `GHI-NHO.md` trước** (góp ý từ các video trước) để không hỏi lại điều người dùng đã dặn. Hỏi người dùng gọn trong một lượt; ô nào họ không trả lời thì tự suy ra và ghi "tự chọn" để báo lại khi giao file. Mỗi ô ghi kèm khoá tương ứng trong `project.json`.

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

## 3. Phong cách và nhịp

| Câu hỏi | Lựa chọn | Khoá |
|---|---|---|
| Muốn video dựng theo nhịp nào? | `nhanh`: dồn dập, cắt sát, hợp Reels/TikTok · `vua` (mặc định) · `cham`: giữ hơi thở, hợp kể chuyện, phân tích | `style.pace` (`init --pace`) |
| Bao nhiêu đồ hoạ? | `it` (~1 khung/30s) · `vua` (~1/15s) · `nhieu` (~1/8s) | `style.graphics` (`init --graphics`) |
| Có video mẫu muốn giống không? Cảm giác mong muốn (nghiêm túc, năng động, sang trọng…)? | link, mô tả | `style.reference`, `style.notes` |
| Kiểu phụ đề | glow · box · pop · plain | `captions.style` |
| Âm thanh hiệu ứng | bật (âm thu thật) · tắt · dùng file riêng | `sfx` |

**Quy tắc riêng cho video này.** Hỏi: "Video này có điều gì bắt buộc phải làm hoặc tránh không?" Ví dụ: không dùng màu đỏ, giữ nguyên đoạn chào đầu, không hiện logo đối thủ, không cắt đoạn 1:20–1:35. Ghi vào `rules` (`init --rule "…"`, hoặc `video-editor rules <dự án> --add "…"`).

- Quy tắc này **chỉ áp dụng cho video đang làm**. Không chép sang dự án khác, không ghi vào `GHI-NHO.md`.
- Người dùng muốn giữ quy tắc cho mọi video về sau thì ghi thêm bằng `video-editor note`.

## 4. Nhận diện

| Câu hỏi | Mặc định | Khoá |
|---|---|---|
| Mẫu | `trung-tinh`; kênh Bitcoin dùng `btc-daily` | `template` |
| Tên kênh, logo, màu chủ đạo, font | của mẫu | `brand` |
| Kiểu phụ đề | glow | `captions.style` |
| Từ khoá cần tô màu trong phụ đề | của mẫu | `captions.keywords` |
| Nhạc nền (người dùng có quyền dùng) | không | `music` |
| Câu kêu gọi cuối video | "Theo dõi để xem video tiếp theo" | `content.cta` |

## 5. Nội dung

- Ý chính một câu, dùng cho thẻ mở đầu: `content.hook.title`.
- Những con số, mốc, danh sách cần thành đồ hoạ: `content.beats`.
- Tên riêng, thuật ngữ dễ nghe sai: `fix`.

## 6. Trước khi gửi storyboard

- [ ] `build` không còn lỗi; đã xem các cảnh báo và chỗ nghi nói vấp.
- [ ] Đã soát `work/bang-quy-chieu.md`: phần tử nào cũng hiện đúng lúc lời được nói.
- [ ] Đã gửi người dùng các cụm lời "nghe chưa chắc" nếu không tự đoán chắc được.
- [ ] Đã tự xem từng ảnh trong `out/storyboard/`: chữ không tràn, đồ hoạ không che mặt, màu đúng nhận diện, đúng từng quy tắc riêng và góp ý trong `GHI-NHO.md`.
- [ ] Video từ kịch bản: đã thay giọng tạm bằng giọng thật (`tts` không có `--placeholder`).

## 7. Trước khi giao video

- [ ] Người dùng đã đồng ý storyboard, đã chạy `video-editor approve`.
- [ ] Đã xem từng khung trong `out/kiem-tra.jpg` (lấy từ chính file MP4) và đối chiếu với storyboard đã duyệt.
- [ ] Phần "Tự kiểm tra" trong `bao-cao.md` không còn cảnh báo, hoặc đã giải thích được.
- [ ] Đã tích từng quy tắc riêng trong báo cáo.
- [ ] Góp ý mới của người dùng (nếu có) đã ghi bằng `video-editor note`.
