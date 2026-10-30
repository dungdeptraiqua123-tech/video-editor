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
| `reference/video-shotcraft` | Apache-2.0 © Vincentwei1021 | Bản rút gọn: bỏ `demos/`, `workbench/`, `gallery/` và **toàn bộ file âm thanh** (phần lớn từ Mixkit, giấy phép không cho phân phối lại file rời; một số chưa rõ nguồn) |

## Không kèm theo

`hyperframes`, `herk-edit-kit`, `iart-ai` và `motion-graphics` (tổng cộng 83 skill) **không** được đưa vào repo, vì chưa xác minh được giấy phép phân phối lại. Danh mục và nguồn của chúng nằm ở `reference/INDEX.md`.

Lưu ý: các phiên bản đầu của repo (trước 0.2.0) từng chứa những bộ này. Nếu repo để công khai, nên xoá chúng khỏi lịch sử git, hoặc chuyển repo sang chế độ riêng tư.
