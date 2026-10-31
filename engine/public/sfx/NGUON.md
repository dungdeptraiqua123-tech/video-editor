# Nguồn âm thanh hiệu ứng

Toàn bộ là âm thanh thu thật từ thư viện Mixkit (Mixkit Sound Effects Free License: dùng miễn phí trong video, kể cả thương mại, không cần ghi công). Không file nào được tạo bằng code.

| File | Dùng khi | Tên gốc trên Mixkit | Nguồn |
|---|---|---|---|
| `whoosh.mp3` | Khung đồ hoạ mở ra | Fast small sweep transition | https://assets.mixkit.co/active_storage/sfx/166/166-preview.mp3 |
| `impact.mp3` | Thẻ mở đầu | Quick zoom impact | https://assets.mixkit.co/active_storage/sfx/772/772-preview.mp3 |
| `riser.mp3` | Trước phần kết | Air zoom vacuum | https://assets.mixkit.co/active_storage/sfx/2608/2608-preview.mp3 |
| `click.mp3` | Nút theo dõi ở phần kết | Modern technology select | https://assets.mixkit.co/active_storage/sfx/3124/3124-preview.mp3 |
| `pop.mp3` | Từng phần tử trong khung đồ hoạ bật ra | Dry pop up notification alert | https://assets.mixkit.co/active_storage/sfx/2356/2356-preview.mp3 |
| `tick.mp3` | Ý trong thẻ chủ đề được đánh dấu | Clock ticker single | https://assets.mixkit.co/active_storage/sfx/1061/1061-preview.mp3 |

`tick.mp3` đã được chỉnh từ bản gốc: cắt 0,175 giây lặng ở đầu để tiếng khớp đúng lúc ý được đánh dấu, tăng 10 dB vì bản gốc rất nhỏ (đỉnh -13,9 dB). Chỉ chỉnh âm lượng và cắt, âm vẫn là bản thu thật.

Chép từ `reference/video-shotcraft/video-shotcraft/assets/audio/sfx/` (thư viện còn khoảng 120 âm thanh Mixkit khác, danh mục và nguồn ở `ATTRIBUTION.md` cùng thư mục). Muốn đổi âm: chọn file khác trong thư viện đó hoặc dùng file của bạn qua khoá `sfx.files` trong `project.json`.
