# Viết nội dung đồ hoạ (`content` trong project.json)

```json
"content": {
  "hook": { "kicker": "BTC DAILY · 02/10", "title": "Bitcoin chạm vùng cản 87K", "sub": "Giữ được 86K là then chốt" },
  "hookSec": 3.2,
  "cta": "Theo dõi để xem livestream tối nay",
  "ctaButtons": ["Theo dõi", "Thích", "Chia sẻ"],
  "outroSec": 3.6,
  "beats": [ ... ],
  "topics": [ ... ],
  "zooms": "auto"
}
```

## Mốc thời gian

Mọi mốc nhận một trong hai dạng:

- **Cụm từ** (nên dùng): `"start": "giá Bitcoin"`. Lấy lúc cụm được nói, tìm từ sau khung trước trở đi.
  - Khung mở trước câu nói 0,25 giây.
  - `end` dạng cụm thì đóng sau khi nói xong cụm 0,4 giây.
- **Số giây** theo lời thoại gốc (như trong `work/loi-thoai.txt`), ví dụ `"start": 39.0`. Công cụ tự đổi sang bản đã cắt.

Không có `end` thì khung hiện `dur` giây (mặc định 4).

Phần tử bên trong khung dùng `say` (hoặc `labelSay`, `changeSay`): phần tử bật ra 0,08 giây trước khi cụm được nói. Cụm phải nằm trong lúc khung đang hiện.

Số viết đúng như trong `loi-thoai.txt`: Whisper có khi ghi "85.000", có khi "85 ngàn". `"say": "85"` khớp cả "85.000"; `"say": "400"` khớp vế sau của "300-400".

Khi cụm không tìm thấy, `build` báo lỗi kèm các cụm gần giống. Thường là do chữ trong lời đã bị sửa bằng `fix`: neo theo chữ **sau khi sửa**.

## Khung đồ hoạ (`beats`)

```json
{ "start": "cụm mở", "end": "cụm đóng", "head": "Tiêu đề cảnh ≤ 30 ký tự", "g": { "type": "...", ... } }
```

Khi khung hiện, người nói thu về ô góc trên phải (video người nói), tiêu đề cảnh `head` hiện góc trên trái, đồ hoạ nằm giữa khung.

| type | Trường | Dùng cho |
|---|---|---|
| `stat` | `icon`, `big` (≤ 10 ký tự), `label` (≤ 44), `tone` (`up`/`down`/`neutral`), `say`, `labelSay` | Một con số lớn |
| `price` | `label`, `value` (số), `prefix`, `suffix`, `decimals`, `change`, `up`, `icon`, `say`, `changeSay` | Giá đếm lên, dừng đúng lúc đọc |
| `levels` | `title`, `levels: [{value, label, kind: res/sup/now, say}]` (1–5 mốc) | Kháng cự, hỗ trợ, mốc hiện tại. Mốc hiện theo thứ tự được nói |
| `list` | `title`, `items: [{icon, text ≤ 32, say}]` (1–4 dòng) | Danh sách lý do, tính năng |
| `chart` | `title`, `points: [số…]`, `up`, `tags: [{i, text, say}]` | Đường vẽ dần tới từng nhãn đúng lúc nhãn được nói. Đường minh hoạ phải nói rõ là minh hoạ |
| `title` | `kicker`, `text` | Chuyển chương |
| `media` | `src` (ảnh hoặc clip, đường dẫn tính từ dự án), `label`, `fit` (`cover`/`contain`), `kenBurns`, `say` | Ảnh/clip sản phẩm, ảnh chụp biểu đồ thật làm dẫn chứng |

Icon có sẵn: `btc`, `up`, `down`, `bank`, `warn`, `target`, `chart`, `wallet`, `clock`, `fire`, `shield`, `people`, `dollar`, `check`.

## Thẻ chủ đề (`topics`)

Chỉ hiện khi người nói toàn màn hình: thẻ góc trên trái, các ý được tick khi được nói.

```json
{ "start": "đầu tiên là", "kicker": "TÍCH LŨY", "title": "Gom được nhiều Bitcoin", "items": [{ "say": "300", "text": "Hơn 300–400 nghìn BTC" }] }
```

Thẻ kéo dài tới khi thẻ sau bắt đầu.

## Zoom

`"zooms": "auto"` đổi khung rộng/chặt (100% / 110%) ở đầu câu, cách nhau ít nhất 3 giây, tránh lúc có đồ hoạ. Muốn tự đặt thì ghi danh sách giây gốc. `[]` để tắt.

## Gợi ý theo loại video

| Loại | Nhịp đồ hoạ |
|---|---|
| Người nói (tin tức, chia sẻ) | Mỗi 10–20 giây một khung đồ hoạ dài 3–15 giây; còn lại là người nói với thẻ chủ đề |
| Explainer (không người nói) | Khung phủ gần hết thời lượng, mỗi khung 3–8 giây, khoảng trống giữa hai khung ≤ 1 giây (khi trống, phụ đề lên giữa màn hình) |
| Sản phẩm | `background` là cảnh quay sản phẩm; xen `media` (ảnh cận), `list` (tính năng), `price` (giá), kết bằng `cta` kêu gọi mua |

## Giới hạn chữ

`build` cảnh báo khi chữ vượt mức: `label` 28 (riêng `stat` 44), `title` 34, `text` 40, `big` 10, `head` 30, `hook.title` 40.
Chữ quá dài vẫn render được nhưng dễ tràn khung trên khổ 1:1. Xem `preview` trước khi render.
