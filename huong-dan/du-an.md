# Thư mục dự án và project.json

```
du-an/<tên>/
  project.json     cài đặt + nội dung (file duy nhất cần sửa tay)
  kichban.txt      kịch bản (dự án từ kịch bản)
  media/           file đưa vào render: bản cắt, logo, ảnh sản phẩm, âm thanh hiệu ứng (công cụ tự quản)
  work/            file trung gian: transcript.json, loi-thoai.txt, timeline.json, data.json, state.json
  out/             file giao: <tên>.mp4, .srt, .vtt, anh-bia.jpg, xem-truoc.jpg, bao-cao.md
```

Môi trường cài đặt dùng chung cho mọi dự án nằm ở `~/.video-editor/` (đổi bằng biến `VE_HOME`): `venv/`, `engine-<phiên bản>/`, `config.json`.
Mô hình Whisper lưu ở bộ nhớ đệm Hugging Face (`~/.cache/huggingface`), tải một lần và dùng lại.

## Các khoá

| Khoá | Mặc định | Ý nghĩa |
|---|---|---|
| `name` | tên thư mục | Tên video, dùng đặt tên file ra |
| `type` | `talking-head` | `talking-head` (người nói), `explainer` (đồ hoạ + giọng), `product` (giới thiệu sản phẩm, thường kèm `background`) |
| `input` | | Video/âm thanh người nói. File âm thanh → tự thành `explainer` |
| `script` | | `kichban.txt`, nếu dự án đi từ kịch bản |
| `background` | | Video hoặc ảnh nền cho video không người nói (cảnh quay sản phẩm). Tự lặp, tắt tiếng, phủ lớp tối |
| `format` | `9:16` | `9:16`, `16:9`, `1:1`, `4:5`. Bố cục, vùng an toàn, cỡ chữ đổi theo khổ |
| `fps` | `30` | |
| `template` | `trung-tinh` | Thư mục trong `templates/` |
| `brand` | `{}` | Ghi đè thương hiệu của mẫu, xem dưới |
| `captions` | | Phụ đề, xem dưới |
| `face` | `{"x":0.5,"y":0.4}` | Vị trí mắt người nói trong video gốc (tỉ lệ 0–1). Dùng để canh khi khổ ra khác khổ gốc và để thu về ô góc. `pipScale` chỉnh độ phóng trong ô góc |
| `voice` | | Giọng AI: `provider` (`elevenlabs` / `placeholder`), `voiceId`, `model`, `speed`, `stability`, `style` |
| `whisper` | `{"model":"auto","language":"vi"}` | `model`: `auto`, `nhe` (small), `vua` (medium), `nang` (large-v3), `nhanh` (large-v3-turbo) |
| `cuts` | | Cắt, xem dưới |
| `fix` | `[]` | Sửa chữ nghe sai: `[["lon sọt", "long short"], ["bên hiểm", ""]]`. Cụm sửa rỗng = xoá. Không phân biệt hoa thường và dấu câu |
| `dropSegments` | `[]` | Bỏ hẳn một đoạn Whisper bịa ra: ghi giây bắt đầu của đoạn (xem `transcript.json`) |
| `music` | `null` | Nhạc nền: `{"file": "nhac.mp3", "volume": 0.08}`. Người dùng phải có quyền dùng bản nhạc |
| `sfx` | `true` | Âm thanh hiệu ứng (whoosh khi đổi cảnh, impact mở đầu, riser và click ở kết) |
| `render` | `{"crf":20}` | `concurrency`: số luồng render (mặc định để Remotion chọn) |
| `content` | | Nội dung đồ hoạ, xem `do-hoa.md` |

### brand

```json
"brand": {
  "badge": "TÊN KÊNH",
  "logo": "/đường/dẫn/logo.png",
  "hookIcon": null,
  "colors": { "primary": "#e63946", "highlight": "#ff8fa3", "number": "#ffd166" },
  "font": { "family": "Montserrat" },
  "backdrop": "grid"
}
```

- **`colors`**: chỉ ghi màu muốn đổi.
  - `bg`, `bg2`: nền và vùng sáng giữa nền.
  - `panel`, `line`: thẻ và viền.
  - `primary`: màu chủ đạo (nhãn, nút, viền).
  - `highlight`: từ khoá trong phụ đề, chữ nhỏ.
  - `number`: con số.
  - `up`, `down`: tăng, giảm.
  - `text`, `mute`: chữ chính, chữ phụ.
- **`font.family`**: có sẵn `Be Vietnam Pro`, `Inter`, `Montserrat`, đều đủ dấu tiếng Việt. Font riêng: thêm `"file": "đường/dẫn/font.ttf"`.
- **`logo`** (PNG nền trong suốt) hoặc **`hookIcon`** (tên icon có sẵn): hiện ở huy hiệu mở đầu.

### captions

| Khoá | Mặc định | |
|---|---|---|
| `enabled` | `true` | Tắt nếu nền tảng tự làm phụ đề |
| `style` | `glow` | `glow` (chữ đang đọc phát sáng), `box` (ô màu sau chữ đang đọc), `pop` (chữ viền dày, nảy), `plain` |
| `position` | theo khổ | Tâm phụ đề theo tỉ lệ chiều cao, ví dụ `0.72` |
| `keywords` | của mẫu | Từ được tô màu `highlight`. Con số luôn tô màu `number` |
| `maxChars` / `maxWords` | 30 (44 với 16:9) / 8 | Độ dài tối đa một cụm phụ đề |
| `size` | `1` | Hệ số cỡ chữ |

### cuts

| Khoá | Mặc định | |
|---|---|---|
| `gap` | `0.55` | Khoảng lặng dài hơn mức này thì cắt (giây) |
| `pad` | `0.12` | Chừa trước và sau mỗi từ |
| `silence` | `true` | `false` = không cắt lặng (giữ nhịp tự nhiên) |
| `fillers` | `auto` | Từ đệm (ờ, ừm, ơ…): `auto` cắt, `suggest` chỉ liệt kê, `off` bỏ qua |
| `filler_words` | danh sách mặc định | Đổi danh sách từ đệm |
| `stumbles` | `suggest` | Nói vấp (cụm 1–3 từ lặp liền nhau, trừ từ láy như "từ từ"): `auto` / `suggest` / `off` |
| `drop` | `[]` | Bỏ các khoảng `[[giây đầu, giây cuối], ...]`, theo giây gốc |
| `keep` | `[]` | Chỉ giữ các khoảng này, để dựng một đoạn ngắn từ video dài |

Sau `build`, `work/timeline.json` ghi lại các đoạn giữ, từ đã cắt theo loại, và gợi ý chưa áp dụng.
Mọi thứ hiển thị (phụ đề, đồ hoạ, zoom, SRT) đều đổi thời gian qua cùng một bảng này, nên cắt xong không bị lệch.
