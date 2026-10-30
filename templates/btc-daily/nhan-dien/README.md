# BTC Daily

Bộ nhận diện cho chuỗi video ngắn cập nhật Bitcoin mỗi ngày (Facebook Reels, khổ dọc 1080 × 1920, 30 khung hình/giây). Phong cách là bản tin tài chính: nền xanh navy, một màu xanh dương chủ đạo, vàng hổ phách cho con số. Mọi đồ hoạ chỉ xuất hiện đúng lúc người nói nhắc tới.

## Tinh thần

- **Tin tức, không giật gân.** Câu ngắn, rõ, có con số. Không viết hoa toàn bộ phụ đề, không dùng màu đỏ để tạo cảm giác hoảng.
- **Nói tới đâu, hiện tới đó.** Mỗi phần tử đồ hoạ (mốc giá, dòng danh sách, con số) gắn với một từ khoá trong lời thoại và bật ra cách từ đó 0,08 giây. Không phần tử nào hiện trước lời nói.
- **Có dẫn chứng.** Ưu tiên ảnh chụp biểu đồ thật (TradingView, Glassnode, dữ liệu ETF) kèm nhãn tóm ý. Đồ hoạ vẽ tay chỉ dùng cho con số người nói đã đọc.

## Màu sắc

Tỉ lệ dùng màu trên một khung hình: **60 / 25 / 10 / 5**.

| Vai trò | Token | Mã màu | Tỉ lệ | Dùng cho |
|---|---|---|---|---|
| Nền | `night` | #050E24 | 60% | Nền mọi cảnh đồ hoạ |
| Thẻ | `panel` | #0B1B3F | trong 60% | Thẻ chủ đề, thẻ danh sách |
| Chủ đạo | `primary` | #2F7BFF | 25% | Nhãn đồ hoạ, dấu tick, nút Theo dõi, vạch dưới tiêu đề |
| Xanh sáng | `sky` | #6CC4FF | trong 25% | Từ khoá phụ đề, kicker, viền ô mặt người nói |
| Điểm nhấn | `amber` | #FFB547 | 10% | Con số, đồng Bitcoin, cảnh báo |
| Tín hiệu | `up` / `down` | #22C38E / #FF5A6A | 5% | Chỉ cho tăng / giảm, hỗ trợ / kháng cự |

Quy tắc:
- Chữ trắng trên `primary` chỉ đạt 3,9:1, nên chỉ đặt chữ đậm từ 24px trở lên (nhãn, nút).
- `amber` dành cho con số và Bitcoin. Không tô chữ thường bằng màu này.
- `up` và `down` không bao giờ dùng để trang trí.
- Không dùng dải chuyển màu tím, ngoại trừ dải `primary` sang `primary-deep` của thẻ mở đầu.

## Chữ

Một họ chữ duy nhất: **Be Vietnam Pro** (Google Fonts), đủ dấu tiếng Việt, dùng ba độ đậm 600, 800 và 900.

| Kiểu | Cỡ / đậm | Dùng cho |
|---|---|---|
| `big-number` | 150px / 900 | Con số chính của cảnh |
| `hook-title` | 78px / 900 | Thẻ mở đầu |
| `caption` | 64px / 800 | Phụ đề |
| `scene-title` | 62px / 900 | Tiêu đề cảnh đồ hoạ |
| `topic-title` | 48px / 800 | Tiêu đề thẻ chủ đề |
| `item` | 46px / 800 | Dòng danh sách |
| `body` | 36px / 600 | Ý trong thẻ chủ đề |
| `kicker` | 26px / 800, giãn chữ 3px, viết hoa | Nhãn nhỏ trên tiêu đề |

Số tiền viết theo kiểu Việt Nam (`$87.000`, `85–86K`) trong danh sách mốc giá. Con số đếm lên dùng chữ số đều nhau (`tabular-nums`).

## Phụ đề (kiểu "Phát sáng")

- Chữ thường theo câu, tối đa **2 dòng cân nhau**. Không để dòng dưới chỉ còn 1 chữ.
- Một cụm tối đa 30 ký tự hoặc 8 từ. Ngắt cụm khi gặp dấu chấm, dấu phẩy (từ chữ thứ 4) hoặc khoảng nghỉ trên 0,35 giây.
- **Màu theo trạng thái:** chưa đọc là `caption-pending`, đã đọc là trắng, từ khoá đã đọc là `sky`, con số đã đọc là `amber`.
- **Chữ đang đọc:** đổi sang `sky` (con số đổi sang `amber`), phát sáng (`glow-sky` / `glow-amber`), phóng to 8% và nhích lên 5px. Không có gạch chân.
- Mọi chữ có bóng `caption-shade`. Không có khung nền.
- Vị trí: tâm phụ đề ở y = 1420px khi người nói toàn màn hình, y = 1520px khi đang hiện đồ hoạ.
- Từ khoá mặc định: Bitcoin, BTC, Ethereum, ETH, Solana, ETF, altcoin, Nonfarm, Payroll, volume, livestream, long, short, tích lũy, cản, chốt, hấp thụ.

## Bố cục hai chế độ

1. **Người nói toàn màn hình.** Thẻ chủ đề ở góc trên trái (cách mép trái 50px, mép trên 90px). Các ý trong thẻ được tick bằng dấu `primary` đúng lúc được nói. Có lớp tối mờ ở 40% dưới khung để phụ đề luôn đọc được. Cứ vài giây zoom cắt luân phiên 100% / 110%.
2. **Đồ hoạ toàn màn hình.** Nền `night` có lưới `line` mờ chạy chậm. Ô mặt người nói thu về góc trên phải (240 × 300px, x = 790, y = 110, bo `radius-cam`, viền 4px `sky`, sáng `glow-primary`). Tiêu đề cảnh ở góc trên trái, khối đồ hoạ nằm trong vùng y = 470 đến 1350.

Chuyển giữa hai chế độ trong 14 khung hình (khoảng 0,47 giây), đường cong `cubic-bezier(0.65, 0, 0.35, 1)`.

## Thành phần đồ hoạ

- **Con số lớn** (`BigNumber`): biểu tượng, con số `big-number`, một dòng chú thích. Con số đếm từ 90% lên 100% trong 0,6 giây và dừng đúng lúc được đọc.
- **Mốc giá:** mỗi mốc là một vạch ngang màu theo vai trò (kháng cự `down`, hiện tại `amber`, hỗ trợ `up`). Mốc nào được nói thì mốc đó hiện, theo thứ tự lời nói, không theo thứ tự trên xuống.
- **Danh sách:** tối đa 3 dòng, mỗi dòng một biểu tượng và một ý ngắn dưới 32 ký tự.
- **Biểu đồ:** đường vẽ dần tới từng nhãn đúng lúc nhãn đó được nói. Chỉ dùng số liệu người nói đã đọc. Đường minh hoạ phải ghi rõ là minh hoạ.
- **Nhãn đồ hoạ** (`GraphicLabel`): nền `primary`, chữ trắng 36px, bo `radius-chip`.

## Chuyển động

- Phần tử vào: mờ sang rõ kèm giảm nhoè 8px trong 10 khung hình, hoặc lò xo nhẹ (damping 14, stiffness 170).
- Phần tử ra: mờ dần và nhoè 8px trong 8 khung hình.
- Không quét sọc, không rung, không xoay quá 6°.

## Âm thanh

- Giọng nói chuẩn hoá về **-14 LUFS**, đỉnh thật ≤ -1,5 dB.
- Tiếng whoosh khi đổi chế độ ở âm lượng 0,16, tiếng impact ở cảnh mở đầu 0,3, riser trước lời kêu gọi 0,18, click khi bấm Theo dõi 0,3.

## Cấu trúc video

1. **Mở đầu (3,2 giây):** huy hiệu `BTC DAILY · ngày/tháng`, thẻ tiêu đề nêu ý chính, một dòng phụ màu `amber`.
2. **Thân bài:** xen kẽ hai chế độ, mỗi cảnh đồ hoạ dài 3 đến 20 giây.
3. **Kết (3,6 giây):** khung lời kêu gọi viền `primary` cùng ba nút Theo dõi / Thích / Chia sẻ.

Thanh tiến độ 8px màu `sky` chạy dọc mép trên suốt video.

## Xuất file

MP4 H.264, CRF 20, âm thanh AAC 192 kbps, cờ `faststart`. Chỉ nén một lần khi render. Âm lượng đã chuẩn hoá ở bước cắt khoảng lặng.
