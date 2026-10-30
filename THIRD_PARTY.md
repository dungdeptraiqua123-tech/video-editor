# Giấy phép và thành phần bên thứ ba

Rà soát ngày 30/10/2026. Đây là ghi chú để tra cứu, không phải tư vấn pháp lý.

## Mã và thư viện dùng khi chạy

| Thành phần | Giấy phép | Ghi chú |
|---|---|---|
| Remotion 4.0.537 (`remotion`, `@remotion/cli`) | Remotion License | **Miễn phí** cho cá nhân, tổ chức phi lợi nhuận và công ty **tối đa 3 người**. Công ty lớn hơn cần mua Company License ở remotion.pro trước khi dùng thương mại |
| React 19 | MIT | |
| faster-whisper 1.2.1, CTranslate2 | MIT | |
| Mô hình Whisper (Systran/faster-whisper-*, mobiuslabsgmbh/faster-whisper-large-v3-turbo) | MIT (OpenAI Whisper) | Tải lúc cài, không kèm trong repo |
| Chrome Headless Shell | BSD-3 (Chromium) | Remotion tải lúc cài |
| ffmpeg | LGPL/GPL | Người dùng tự cài, không kèm theo |
| ElevenLabs | Điều khoản dịch vụ ElevenLabs | Gói Free không cho dùng thương mại. Chỉ nhân bản giọng khi có sự đồng ý của chủ giọng |

## Tài nguyên kèm trong repo

| Thành phần | Giấy phép | Ghi chú |
|---|---|---|
| Be Vietnam Pro, Inter, Montserrat (qua @fontsource) | SIL Open Font License 1.1 | Cài qua npm, không chép file font vào repo |
| `engine/public/sfx/*.wav` | Tự tạo bằng ffmpeg (sóng sin, nhiễu) | Không vướng bản quyền |
| `templates/btc-daily/logo.png`, `icon.png` | Của chủ kênh BTC Daily | Chỉ dùng cho kênh đó |
| `reference/ghost-editor` | MIT © kurbaitaev | Kèm font OFL có file LICENSE riêng |
| `reference/gsap` | MIT (ghi trong từng SKILL.md) | Tài liệu; thư viện GSAP có giấy phép riêng của GreenSock |
| `reference/video-shotcraft` | Apache-2.0 © Vincentwei1021 | Bản đầy đủ như nguồn, gồm `demos/`, `workbench/`, `gallery/` và file âm thanh. Phần lớn âm thanh lấy từ Mixkit: giấy phép Mixkit cho dùng trong video nhưng không cho phân phối lại file rời; một số file chưa rõ nguồn |
| `reference/hyperframes` (7 skill) | **Chưa xác minh** | Nguồn: github.com/heygen-com/hyperframes |
| `reference/herk-edit-kit` (15 skill) | **Chưa xác minh** | Nguồn: người cung cấp bộ skill |
| `reference/iart-ai` (55 skill) | **Chưa xác minh** | Nguồn: người cung cấp bộ skill |
| `reference/motion-graphics` (6 skill) | **Chưa xác minh** | Nguồn: người cung cấp bộ skill |

## Lưu ý về các bộ chưa xác minh giấy phép

Bốn bộ hyperframes, herk-edit-kit, iart-ai, motion-graphics (83 skill) và các file âm thanh Mixkit trong video-shotcraft được kèm theo theo yêu cầu của chủ dự án, để cài một lần là đủ toàn bộ thư viện tham khảo. Chúng không kèm file LICENSE, nên chưa rõ tác giả có cho phép phân phối lại hay không.

- Nên để repo ở chế độ riêng tư và không chia sẻ gói cài cho người ngoài.
- Muốn công khai repo hoặc phát hành gói cho người khác: xác minh giấy phép với tác giả trước, hoặc bỏ các bộ này khỏi `reference/` (bộ dựng `video-editor` không cần chúng).
