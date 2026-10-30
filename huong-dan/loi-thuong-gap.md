# Lỗi thường gặp

Mỗi lỗi của `video-editor` in hai dòng: `✗` là nguyên nhân, `→` là cách xử lý. Bảng dưới bổ sung khi dòng `→` chưa đủ.

| Thông báo | Nguyên nhân | Xử lý |
|---|---|---|
| Chưa có ffmpeg | Máy chưa cài | macOS `brew install ffmpeg` · Windows `winget install Gyan.FFmpeg` · Ubuntu `sudo apt install ffmpeg`. Mở terminal mới rồi chạy lại |
| Node.js ✗ trong doctor | Node cũ hơn 20.19 | Cài Node 22 LTS. Có nhiều bản Node thì kiểm tra `node --version` trong cùng terminal |
| Bộ dựng chưa được cài | Chưa chạy setup, hoặc vừa cập nhật skill lên phiên bản mới | `video-editor setup` (mỗi phiên bản bộ dựng cài vào thư mục riêng `engine-<phiên bản>`) |
| Không tải hoặc mở được mô hình Whisper | Mạng chặn Hugging Face, hết dung lượng | Mở `huggingface.co`, `*.hf.co`, `*.xethub.hf.co`. Trên Claude cloud: Project settings → Cloud environment → Network access → Allowed domains, rồi mở phiên mới. Thay thế: `transcribe --from-srt` với phụ đề xuất từ CapCut |
| Chép lời rất chậm | Mô hình nặng trên máy yếu | `whisper.model: "nhanh"` (large-v3-turbo, nhanh khoảng 3 lần) hoặc `"vua"` |
| File … bị hỏng | Tải về chưa xong, định dạng lạ | Xuất lại sang MP4 H.264 bằng CapCut/QuickTime |
| File không có tiếng | Video câm | Dùng chế độ kịch bản: `init --script kichban.txt --background video.mp4` |
| Âm thanh gần như im lặng | Sai file, micro tắt | Kiểm tra lại nguồn |
| Không nhận diện được lời nói | Sai ngôn ngữ, chỉ có nhạc | Đặt `whisper.language` đúng, hoặc dùng kịch bản |
| Không tìm thấy cụm "…" | Cụm neo không khớp lời (thường do đã `fix`) | Lấy đúng chữ trong `work/loi-thoai.txt` sau khi sửa. Gợi ý "Gần giống" in kèm |
| Từ khoá "…" không được nói trong lúc khung này hiện | `say` nằm ngoài khoảng `start`–`end` | Kéo dài `end`, hoặc đổi `say` sang cụm trong khoảng đó |
| Chồng lên khung trước, đã đẩy lùi | Hai khung trùng thời gian | Sửa `start`/`end` cho tách nhau |
| Chạm phần kết, đã cắt bớt | Khung kéo vào đoạn CTA cuối | Kết thúc khung sớm hơn |
| ElevenLabs từ chối key (401) | Key sai hoặc thiếu quyền | Tạo key mới có quyền Text to Speech và Voices |
| Gói ElevenLabs không nhân bản giọng được | Gói Free | Dùng giọng có sẵn (`video-editor voices`) hoặc nâng lên Starter |
| Mạng chặn api.elevenlabs.io | Môi trường giới hạn mạng | Thêm vào Allowed domains, mở phiên mới |
| Render lỗi `ENOTFOUND remotion.media` | Không tải được Chrome Headless Shell | Mở mạng tới `remotion.media`, hoặc đặt `VE_BROWSER=<đường dẫn Chrome/Chromium>` rồi chạy lại (setup tự dò Chromium của Playwright nếu có) |
| Render chậm hoặc hết RAM | Máy yếu, video dài | `render.concurrency: 2`; xem trước bằng `preview --draft` (nửa độ phân giải) |
| Bị ngắt giữa chừng | Mất mạng, tắt máy | Chạy lại đúng lệnh hoặc `video-editor run <dự án>`: bước đã xong được bỏ qua nhờ `work/state.json` |
| Muốn làm lại một bước dù đầu vào không đổi | | Thêm `--force` |
| Không thấy các skill liên quan trong Claude Code | Chưa chạy `setup`, hoặc phiên đang mở từ trước khi cài | `video-editor skills` để xem đã cài chưa, `video-editor skills install` để cài, rồi mở phiên Claude Code mới |
| "Bỏ qua … skill vì đã có skill cùng tên" | Bạn tự cài một skill trùng tên trước đó | Giữ bản của bạn, hoặc xoá thư mục đó rồi chạy lại `video-editor skills install` |
