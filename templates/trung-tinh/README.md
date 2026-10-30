# Mẫu trung tính

Mẫu mặc định cho mọi kênh: nền than chì, màu chủ đạo xanh ngọc, vàng cho con số. Không gắn với chủ đề nào.

Đổi sang nhận diện riêng mà không cần mẫu mới: ghi đè trong `project.json`, ví dụ

```json
"brand": {
  "badge": "TÊN KÊNH",
  "logo": "/đường/dẫn/logo.png",
  "colors": { "primary": "#e63946", "highlight": "#ff8fa3" },
  "font": { "family": "Montserrat" }
}
```

- `colors`: chỉ cần ghi màu muốn đổi, còn lại giữ của mẫu.
- `font.family`: có sẵn `Be Vietnam Pro`, `Inter`, `Montserrat` (đều đủ dấu tiếng Việt). Font riêng: thêm `"file": "/đường/dẫn/font.ttf"`.
- `logo`: PNG nền trong suốt, cao tối thiểu 120px.
- `backdrop`: `grid` (lưới mờ chạy chậm) hoặc `plain`.
