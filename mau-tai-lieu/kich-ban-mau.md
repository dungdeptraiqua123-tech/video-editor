# Khung kịch bản chế độ B (45 đến 60 giây)

Viết đúng như sẽ đọc. Mỗi dòng một câu, mỗi câu một ý. Phần trong ngoặc vuông là ghi chú đồ hoạ, **không** đưa vào `kichban.txt`.

## Mở (3 đến 5 giây): một câu nêu ý chính, có con số
Bitcoin vừa vượt 87 nghìn đô sau ba ngày tích lũy.
[hook: "BTC vượt 87K", dòng phụ màu amber]

## Thân (35 đến 45 giây): 3 ý, mỗi ý 2 đến 4 câu
Ý 1. Điều gì vừa xảy ra.
Giá đã phá mốc 85 nghìn 5 trong phiên Mỹ.
[stat: 85.500, say "85 nghìn 5"]

Ý 2. Vì sao.
Dòng tiền ETF quay lại, ba ngày liên tiếp mua ròng.
[list: 3 dòng, say theo từng ý]

Ý 3. Mốc cần theo dõi.
Hỗ trợ gần nhất là 85 nghìn, kháng cự tiếp theo là 90 nghìn.
[levels: say "85 nghìn", "90 nghìn"]

## Kết (4 giây): một câu kêu gọi
Theo dõi BTC Daily để cập nhật mỗi ngày nhé.
[cta]

## Quy tắc viết
- 120 đến 180 chữ. Đọc thử thành tiếng, quá 60 giây thì cắt.
- Số viết theo cách đọc: "87 nghìn đô", "85 nghìn 5", "3 phần trăm".
- Tên tiếng Anh dễ đọc sai thì viết phiên âm hoặc thử trước một câu ngắn.
- Không dùng ký hiệu $, %, K, ->, dấu ngoặc trong `kichban.txt`.
- Neo `say` trong beats.json phải trùng chữ trong kịch bản.
