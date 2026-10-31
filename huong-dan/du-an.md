# Thư mục dự án và project.json

```
du-an/<tên>/
  project.json     cài đặt + nội dung (file duy nhất cần sửa tay)
  kichban.txt      kịch bản (dự án từ kịch bản)
  media/           file đưa vào render: bản cắt, logo, ảnh sản phẩm, âm thanh hiệu ứng (công cụ tự quản)
  work/            file trung gian: transcript.json, loi-thoai.txt, bang-quy-chieu.md, timeline.json, data.json, qa.json, state.json
  out/             storyboard.jpg (+ storyboard/), file giao: <tên>.mp4, .srt, .vtt, anh-bia.jpg, bang-quy-chieu.md, kiem-tra.jpg (+ kiem-tra/), bao-cao.md
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
| `style` | `{"pace":"vua","graphics":"vua"}` | Phong cách và nhịp hỏi ở bước nhận việc, xem dưới |
| `rules` | `[]` | Quy tắc riêng của **video này**: `["Không dùng màu đỏ", "Giữ nguyên câu chào đầu"]`. Mọi lệnh dựng in lại để không quên; báo cáo có danh sách để tích. Không áp dụng cho video khác (góp ý dùng lâu dài ghi vào `GHI-NHO.md` bằng `video-editor note`) |
| `brand` | `{}` | Ghi đè thương hiệu của mẫu, xem dưới |
| `captions` | | Phụ đề, xem dưới |
| `face` | `{"x":0.5,"y":0.4}` | Vị trí mắt người nói trong video gốc (tỉ lệ 0–1). Dùng để canh khi khổ ra khác khổ gốc và để thu về ô góc. `pipScale` chỉnh độ phóng trong ô góc |
| `voice` | | Giọng AI: `provider` (`elevenlabs` / `placeholder`), `voiceId`, `model`, `speed`, `stability`, `style` |
| `whisper` | `{"model":"auto","language":"vi"}` | `model`: `auto`, `nhe` (small), `vua` (medium), `nang` (large-v3), `nhanh` (large-v3-turbo) |
| `cuts` | | Cắt, xem dưới |
| `fix` | `[]` | Sửa chữ nghe sai: `[["lon sọt", "long short"], ["bên hiểm", ""]]`. Cụm sửa rỗng = xoá. Không phân biệt hoa thường và dấu câu |
| `dropSegments` | `[]` | Bỏ hẳn một đoạn Whisper bịa ra: ghi giây bắt đầu của đoạn (xem `transcript.json`) |
| `music` | `null` | Nhạc nền: `{"file": "nhac.mp3", "volume": 0.08}`. Người dùng phải có quyền dùng bản nhạc |
| `sfx` | `{"enabled":true,"volume":1,"files":{}}` | Âm thanh hiệu ứng thu thật (Mixkit): `whoosh` khi khung đồ hoạ mở, `pop` khi từng phần tử trong khung bật ra, `tick` khi ý trong thẻ chủ đề được đánh dấu, `impact` ở mở đầu, `riser` trước phần kết, `click` ở nút theo dõi. `volume` nhân âm lượng chung. `files` thay từng âm bằng file của bạn (`{"impact": "am-thanh/trong.mp3"}`) hoặc tắt riêng một âm (`{"click": ""}`). `false` = tắt hết. Không dùng âm tạo bằng code |
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

### style

| Khoá | Mặc định | |
|---|---|---|
| `pace` | `vua` | Nhịp dựng. `nhanh`: cắt lặng trên 0,35s, chừa 0,08s, tự cắt từ đệm và nói vấp, đổi khung mỗi 2,2s. `vua`: 0,55s / 0,12s, cắt từ đệm, nói vấp chỉ gợi ý, đổi khung mỗi 3s. `cham`: 0,9s / 0,18s, từ đệm và nói vấp chỉ gợi ý, đổi khung mỗi 5s |
| `graphics` | `vua` | Mật độ đồ hoạ gợi ý khi viết `content`: `it` khoảng 1 khung mỗi 30s, `vua` mỗi 15s, `nhieu` mỗi 8s. `build` in số khung hiện có so với gợi ý |
| `reference` | `""` | Link hoặc mô tả video tham khảo về phong cách |
| `notes` | `""` | Ghi chú thêm về phong cách (màu, cảm xúc, kiểu phụ đề mong muốn) |

### cuts

Khoá nào để `null` thì lấy theo nhịp (`style.pace`); ghi số hay giá trị cụ thể thì ghi đè nhịp.

| Khoá | Mặc định | |
|---|---|---|
| `gap` | theo nhịp (`0.55` với `vua`) | Khoảng lặng dài hơn mức này thì cắt (giây) |
| `pad` | theo nhịp (`0.12` với `vua`) | Chừa trước và sau mỗi từ |
| `silence` | `true` | `false` = không cắt lặng (giữ nhịp tự nhiên) |
| `fillers` | theo nhịp | Từ đệm (ờ, ừm, ơ…): `auto` cắt, `suggest` chỉ liệt kê, `off` bỏ qua |
| `filler_words` | danh sách mặc định | Đổi danh sách từ đệm |
| `stumbles` | theo nhịp | Nói vấp (cụm 1–3 từ lặp liền nhau, trừ từ láy như "từ từ"): `auto` / `suggest` / `off` |
| `drop` | `[]` | Bỏ các khoảng `[[giây đầu, giây cuối], ...]`, theo giây gốc |
| `keep` | `[]` | Chỉ giữ các khoảng này, để dựng một đoạn ngắn từ video dài |

Sau `build`, `work/timeline.json` ghi lại các đoạn giữ, từ đã cắt theo loại, và gợi ý chưa áp dụng.
Mọi thứ hiển thị (phụ đề, đồ hoạ, zoom, SRT) đều đổi thời gian qua cùng một bảng này, nên cắt xong không bị lệch.
