# Motion graphic: đạo diễn, dùng cảnh có sẵn, viết cảnh mới

Mục tiêu: video có **chuyển động thật** minh hoạ đúng ý từng câu (cửa sổ app tự gõ, checklist tự tick, số đếm, đồng hồ quay, sóng âm bị cắt, sơ đồ tự vẽ nét…), không chỉ thẻ chữ đứng yên. Bạn là **đạo diễn motion**: tự đọc lời, tự quyết câu nào cần cảnh, tự chọn hoặc tự viết cảnh, tự soát. Người dùng không cần mô tả gì.

## Quy trình đạo diễn (sau bước chép lời)

1. **Lập kịch bản hình:** `video-editor motion plan <dự án>` tạo `work/kich-ban-hinh.md` (mỗi câu một dòng, kèm gợi ý ý/cảnh từ từ khoá). Gợi ý chỉ là điểm xuất phát: đọc **ý cả câu** rồi điền cột Quyết định. Cuối file là **Tham chiếu nhanh**: ví dụ khung dán được + mặc định của mọi cảnh có sẵn, thư viện, chữ ký mọi viên gạch kit, khung mẫu cảnh mới (cũng in bằng `video-editor motion list --chi-tiet`). Đọc một lần là đủ; **không đọc mã nguồn engine**.
2. **Viết "Mạch ý" trước** (mục 1 của kịch bản hình): câu hỏi / vấn đề → kết luận → lý do / các nhánh → ví dụ, và chọn **một hệ hình chính** cho cả video (ví dụ `so-sanh` sàn / ví → `re-nhanh` có staking thì sàn, không thì ví lạnh → `luu-y` mẹo). Các cảnh phải nối tiếp nhau kể đúng mạch đó, không mỗi câu một kiểu rời rạc.
   **Chọn câu đáng làm motion** theo bảng "Ý → cách thể hiện" bên dưới, theo **ý** của câu chứ không theo từ khoá. Câu chuyện phiếm, chào hỏi, cảm xúc thuần → để **mặt người nói** (có thể kèm cảnh nổi `overlay` nhỏ).
3. **Tìm cảnh:** gộp mọi ý vào một lần `video-editor motion find "<ý 1>" "<ý 2>" …` → cảnh có sẵn và cảnh trong thư viện (đã dùng ở video trước, điểm càng cao càng hợp gu người dùng). Hợp thì dùng; cảnh thư viện: `video-editor motion use <dự án> <tên>` (chép vào `motion/`).
4. **Không có cảnh hợp → viết cảnh mới** `motion/<tên>.tsx` bằng motion kit (mục "Viết cảnh mới"). Đừng ép ý vào cảnh không đúng chỉ vì có sẵn.
5. **Viết khung** vào `content.beats` (cú pháp bên dưới), neo mọi mốc bằng cụm lời (`say`, `xxxSay`).
6. `video-editor check` (vài giây, không cắt video) → sửa hết lỗi neo / cảnh; rồi `video-editor build` → sửa hết lỗi (cảnh viết riêng được kiểm tra an toàn + kiểu, báo `motion/<file>:<dòng>`).
7. `video-editor preview` → đọc **`out/soat-bo-cuc.md`** (soát bố cục tự động, đo từ bộ dựng, không cần model ảnh) và sửa **hết lỗi**; rồi xem 3 ảnh mỗi cảnh trong `out/motion-soat/` theo bảng soát nếu xem được ảnh. Sửa rồi preview lại (tối đa 2 vòng; vẫn hỏng thì thay bằng cảnh có sẵn đơn giản hơn hoặc để mặt người nói).
8. Người dùng duyệt → cảnh viết riêng **tự vào thư viện** (+1 điểm). Bị góp ý về một cảnh: sửa, rồi `video-editor motion rate <tên> -1 --ly-do "<góp ý>"` để lần sau tránh.

## Ý → cách thể hiện

| Ý của câu | Cảnh có sẵn hợp | Ghi chú |
|---|---|---|
| Con số, %, tăng/giảm | `dem-so` | số đếm tới đúng lúc đọc; `strike` để gạch số cũ |
| Thời gian trước → sau, tiết kiệm | `dong-ho` | kim quay, chữ đổi lúc nói vế sau |
| Các bước, lộ trình, danh sách | `checklist` | mỗi ý tick đúng lúc nói |
| Làm việc với AI / app chat | `chat` | gõ câu lệnh, gửi, trả lời gõ dần |
| Lệnh, cài đặt | `terminal` | |
| Ghi luật, file, ghi chú | `tai-lieu` | dòng mới kèm `tag` ("luật mới") |
| Cắt khoảng lặng, rút gọn | `song-am` | số giây giảm + sóng âm bị xoá đoạn |
| Nhiều công cụ kết nối | `so-do` | nút trên, đường nối tự vẽ về nút giữa |
| Gom tài liệu / video mẫu | `thu-muc` | thẻ rơi vào thư mục |
| Quy trình dựng (cắt, phụ đề, motion…) | `dong-thoi-gian` | |
| Nhiều ví dụ / b-roll | `luoi-anh` | ảnh/clip trong media/ |
| Mở chương, câu chốt | `tieu-de` | serif + dòng nghiêng màu nhấn |
| Từ khoá cảm xúc (newbie, storytelling) | `chu-nghieng` (overlay) | nổi trên người nói, người nói vẫn toàn màn hình |
| Nhắc sản phẩm/logo, "là em đây" | `nhan-dan` (overlay) | sticker/logo bật vào kèm chú thích; `text: "si:bitcoin"` = icon thương hiệu |
| Hai lựa chọn: A hay B, cách cũ / cách mới | `so-sanh` | hai cột có icon, `pick` sáng bên được chọn đúng lúc nói kết luận |
| Quy tắc "nếu… thì… / còn không thì…" | `re-nhanh` | điều kiện → nhánh có / không, mỗi nhánh sáng lúc nói |
| Mẹo, lưu ý, cảnh báo | `luu-y` | `kind`: meo, luu-y, canh-bao |
| Người xem / người hỏi đặt câu hỏi (không có app) | `hoi-dap` | thay cho `chat` khi không có app thật |
| Kéo thả, thao tác giao diện, so sánh trước/sau, hiệu ứng đặc biệt | **viết cảnh mới** | dùng `Window`, `Cursor`, `Card`, `Phase`… |

## Không nên (lỗi đã gặp ở video thật)

- `chat` khi câu KHÔNG nói về thao tác với app / AI / chatbot (người xem không hiểu cửa sổ chat ở đó) → `hoi-dap` hoặc `luu-y`.
- `so-do` cho hai lựa chọn → `so-sanh`; câu "nếu… thì…" → `re-nhanh`.
- `chu-nghieng` quá 1 lần trong video ngắn; chữ nổi đè lên đầu / trán người nói.
- Cảnh nổi có cửa sổ / thẻ lớn (che mặt, đè phụ đề) → dùng `layer: "full"` (ô mặt người nói ở góc).
- Chữ trên hình chép lỗi nghe nhầm của Whisper (coi → coin, stacking → staking, thủ động → thụ động). Chỉ `say` mới chép đúng chữ Whisper; chữ hiển thị phải đúng chính tả.
- Mã icon `lu:` / `si:` ở chỗ không phải ô icon (label, text) → hiện ra thành chữ. Emoji làm icon → máy chủ có thể thiếu font emoji.
- Cảnh mở ra trống (cửa sổ rỗng, chờ hơn 0,5 s mới có nội dung).

Thẻ chủ đề tự ẩn khi có cảnh motion; tiêu đề cảnh (`Headline`) tự co cỡ chữ và chừa ô mặt người nói khi không truyền `w`.

## Luật nhịp

- **Mật độ** theo `style.graphics`: `it` ≈ 1 cảnh / 15 s, `vua` ≈ 1 / 10 s, `nhieu` ≈ 1 / 6 s (cảnh `overlay` tính nửa).
- **Giữ mặt người nói** ≥ 50% thời lượng (video người nói). Cảnh `full` mặc định giữ ô mặt ở góc; `"pip": false` chỉ khi cảnh cần cả màn hình (giao diện lớn) và không quá 1/3 thời lượng.
- **Không lặp** một cảnh quá 2 lần liên tiếp; xen `full` với `overlay` và mặt người nói.
- **Nói tới đâu, hiện tới đó:** phần tử chính hiện trong 0,5 s đầu cảnh; mỗi ý / số / tick neo `say` vào đúng cụm lời. Cảnh dài 2,5–7 s; ý cuối hiện xong không đứng yên quá 3 s.
- **Chữ ngắn:** tiêu đề ≤ 26 ký tự, dòng nghiêng ≤ 22, mỗi ý checklist ≤ 28, bong bóng chat ≤ 60.
- Câu nào **không** đáng minh hoạ thì để người nói: motion nhiều mà vô nghĩa còn tệ hơn không có.

## Cú pháp khung motion

```json
{ "start": "cụm mở", "end": "cụm đóng", "head": "",
  "g": { "type": "motion", "scene": "checklist", "layer": "full", "pip": true,
         "params": { "kicker": "Lộ trình", "title": "Học edit video", "accent": "trong 7 ngày",
                     "items": [ { "text": "Cài Claude Code", "say": "cài Claude" },
                                { "text": "Tạo CLAUDE.md", "say": "tạo file" } ] } } }
```

- `scene`: tên cảnh có sẵn (`video-editor motion list`) hoặc tên file `motion/<tên>.tsx`.
- `layer`: `full` (cảnh toàn màn hình, nền giấy sáng, người nói vào ô góc) hoặc `overlay` (nổi trên hình người nói, nền trong suốt).
- `params`: tham số của cảnh. Khoá `say` → `d`, `xxxSay` → `xxxD` (giây tính từ lúc cảnh mở) do build tự đổi.
- Ảnh/clip trong params (`src`) là đường dẫn trong `media/` của dự án.
- `head` để trống: cảnh motion tự có tiêu đề (`title`/`accent`).
- Màu, font: mặc định nền giấy kem, chữ serif Fraunces, màu nhấn = `brand.primary`. Đổi qua `project.json` → `"motion": {"style": {"look": "toi"}}` (nền tối theo thương hiệu) hoặc từng khoá `bg, paper, ink, mute, line, accent, accent2, ok, serif, sans, mono`.
- Khi cảnh nền sáng hiện toàn màn hình, phụ đề tự đổi sang chữ mực đậm.

## Viết cảnh mới (`motion/<tên>.tsx`)

Tên file: chữ thường không dấu, số, gạch nối; không trùng cảnh có sẵn. Chỉ import `react`, `remotion`, `./kit` (và cảnh khác trong `motion/`). Không gọi mạng, không `eval`/`require`. Phải `export default`.

```tsx
import React from "react";
import { Headline, Window, Card, Cursor, ChatBubble, Appear, prog, useSec, M, SceneProps } from "./kit";

type P = { title?: string; accent?: string; file?: string; dropD?: number; reply?: string };

/** Kéo file video vào khung chat rồi trợ lý nhận file. */
const KeoThaFile: React.FC<SceneProps<P>> = ({ p, W, safe }) => {
  const t = useSec();                       // giây từ lúc cảnh mở
  const drop = p.dropD ?? 1.6;              // "dropSay" trong project.json → dropD
  const fly = prog(t, drop - 0.9, drop);    // 0 → 1 trong khoảng thời gian, có làm mượt
  return (
    <>
      <Headline x={safe.left} y={safe.top + 40} title={p.title ?? "Bước 2"} accent={p.accent ?? "Đưa video gốc"} />
      <Window x={safe.left} y={560} w={W - safe.left * 2} h={560} title="Claude" at={0.1}>
        {t >= drop ? <ChatBubble side="me" text={`📎 ${p.file}`} at={drop} /> : null}
        {p.reply ? <ChatBubble side="ai" text={p.reply} at={drop + 0.8} /> : null}
      </Window>
      {t < drop ? <Card x={180 + 300 * fly} y={1180 - 420 * fly} w={600} at={0.3}>🎬 {p.file}</Card> : null}
      <Cursor path={[[620, 1260, 0.4], [W / 2 + 120, 840, drop]]} clicks={[0.5, drop]} />
    </>
  );
};
export default KeoThaFile;
```

**Khung thiết kế:** dọc 1080 × 1920 (ngang 1920 × 1080). `safe` = vùng an toàn: `top`, `bottom` (trên phụ đề), `left`, `right`, `pip` (ô mặt người nói, null nếu không có). Đặt nội dung chính trong `safe.top … safe.bottom`, tránh `safe.pip`.

**Motion kit** (mọi `at`, `d` tính bằng giây từ lúc cảnh mở; có `x`/`y` thì đặt tuyệt đối):

| Nhóm | Viên gạch |
|---|---|
| Nền, xuất hiện | `Paper` (nền giấy, tự có ở cảnh full), `Appear` (`kind`: pop, rise, fade, blur, left, right; `out` = lúc ẩn), `Phase` (hiện trong khoảng from–to, cho cảnh nhiều pha) |
| Chữ | `Headline` (kicker, title, accent nghiêng gạch chân tự vẽ), `TypeText` (gõ dần, cps), `WordReveal` (từng từ mờ → nét), `Marker` (bút dạ quang) |
| Giao diện giả lập | `Card`, `Window` (3 chấm, `dark`), `ChatBubble` (me/ai), `InputBar` (gõ rồi gửi), `DocWriter` (file tự viết dòng), `Terminal`, `PhoneFrame`, `Cursor` (đi theo [x, y, giây], `clicks`) |
| Danh sách, đồ vật | `Checklist` (tick theo `at`), `Folder` (thẻ rơi vào), `GridPop` (lưới ảnh bật từng ô), `Sticker` (ảnh/chữ bật + lắc) |
| Số liệu | `Counter` (from → to, fmt int/pct/time, strike), `Clock` (kim quay), `Waveform` (cuts, cutAt), `TimelineBars` (rãnh dựng) |
| Sơ đồ | `Node` (thẻ nút, `done` = tick), `Connector` (đường nối tự vẽ, bend) |
| Hàm | `useSec()`, `useSpring(at)`, `prog(t, a, b)`, `rand(seed)`, `M` (màu/font hiện tại), `rgba()`, `shadow()` |

Hoạt hình tự viết thêm: dùng `useCurrentFrame`, `interpolate`, `spring` của `remotion`, CSS transform/opacity/filter, SVG (`pathLength` + `strokeDashoffset` để vẽ nét). Mọi chuyển động phải **tính từ thời gian** (không `setTimeout`, không `Math.random()` — dùng `rand(seed)`).

**Để soát bố cục tự động đo được:** dùng viên gạch của kit (đã gắn sẵn nhãn đo). Khối chữ tự viết bằng thẻ `div` thì thêm `data-ve="text"`, khung / thẻ thêm `data-ve="box"`. Icon: `<Glyph name="lu:wallet" />` (không emoji). Khối lớn ở layer overlay đặt bằng `overlaySlot(safe, cao)` để tránh mặt người nói (`safe.face`).

**Hiệu năng (VPS 4 vCPU):** tránh `filter: blur` lớn trên vùng rộng, bóng đổ chồng nhiều lớp, hàng trăm phần tử; 3D chỉ bằng CSS transform đơn giản. Mỗi cảnh ≤ 60 KB mã.

## Bảng tự soát (mỗi ảnh trong `out/motion-soat/`)

1. Đúng ý câu đang nói? (đọc lời ghi dưới ảnh storyboard)
2. Phần tử chính đã hiện ở ảnh 1 (vừa mở)? Ảnh 3 đủ nội dung?
3. Chữ không tràn, không bị cắt mép, không đè ô mặt người nói, không đè vùng phụ đề.
4. Màu đúng nhận diện; chữ đọc được trên nền.
5. Không có khung đỏ "Cảnh motion … lỗi" / "Không có cảnh motion".
6. Không lặp cảnh, nhịp xen kẽ với mặt người nói.

## Thư viện cảnh

- `video-editor motion list` — cảnh có sẵn + thư viện (điểm, số lần dùng); `--chi-tiet` in Tham chiếu nhanh đầy đủ.
- `video-editor motion find "<ý>"` — tìm cảnh hợp ý.
- `video-editor motion use <dự án> <tên> [--as <tên mới>]` — chép cảnh thư viện vào dự án.
- `video-editor motion save <dự án> <cảnh> --y "<ý dùng>" --tags a,b --mo-ta "<chuyển động>"` — lưu tay (duyệt thì tự lưu).
- `video-editor motion rate <tên> +1|-1 --ly-do "…"` — chấm điểm; `motion off <tên>` — không gợi ý nữa.
- Cảnh tốt dùng nhiều lần nên được đưa vào skill làm cảnh có sẵn (sửa `engine/src/motion/scenes.tsx` + `ve/motion.py`).
