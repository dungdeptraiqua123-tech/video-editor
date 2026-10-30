Phụ đề kiểu Phát sáng: chữ thường, tối đa 2 dòng cân nhau, chữ đang đọc đổi màu, phát sáng và phóng to nhẹ.

- Cỡ `caption` (64px / 800), khoảng cách chữ `space-word`, bóng `caption-shade`, không khung nền, không gạch chân.
- Chưa đọc: `caption-pending`. Đã đọc: `ink`. Từ khoá đã đọc: `sky`. Con số đã đọc: `amber`.
- Đang đọc: `sky` kèm `glow-sky` (con số: `amber` kèm `glow-amber`), phóng to 8%, nhích lên 5px, lò xo damping 13 / stiffness 240.
- Cụm tối đa 30 ký tự hoặc 8 từ; chia 2 dòng sao cho độ dài hai dòng gần nhau nhất.
- Đặt tâm ở y = 1420px (người nói toàn màn hình) hoặc y = 1520px (đang hiện đồ hoạ).
- Mốc thời gian từng chữ lấy từ bản chép lời Whisper large-v3 theo từ.
