# Tài liệu tham khảo

Đây là tài liệu đọc thêm, **không cần** để chạy quy trình chính (`video-editor`). Chỉ mở khi cần ý tưởng hoặc kỹ thuật mà bộ dựng mặc định chưa có.
Các skill gốc viết bằng tiếng Anh, nhắm tới HyperFrames hoặc máy Mac: lấy nguyên tắc, còn lệnh thì điều chỉnh cho môi trường đang dùng.

## Khi nào đọc gì

| Cần | Đọc |
|---|---|
| Chọn take hay nhất, phong cách Reel khác (meme, podcast, tối giản…) | `ghost-editor/ghost-editor/SKILL.md` |
| Nghiên cứu video mẫu để học nhịp, bố cục | `ghost-editor/ghost-editor/scripts/reference_study.py` |
| Video sản phẩm, explainer nhiều cảnh, chuyển cảnh điện ảnh | `video-shotcraft/video-shotcraft/SKILL.md` và `references/` |
| Viết chuyển động bằng GSAP (khi dựng bằng HTML/HyperFrames) | `gsap/gsap-core`, `gsap/gsap-timeline`, `gsap/gsap-plugins` |

## Danh mục kèm theo

### Ghost Editor (MIT, github.com/kurbaitaev/ghost-editor): dựng Reel người nói bằng HyperFrames, 7 phong cách

| Skill | Đường dẫn | Mô tả gốc |
|---|---|---|
| ghost-editor | `ghost-editor/ghost-editor/SKILL.md` | AI video editor for talking-head reels: turns a raw phone recording to camera into a finished vertical 1080x1920 reel for Instagram, TikTok or Shorts with best takes, tri… |

### GSAP (MIT): thư viện chuyển động JavaScript

| Skill | Đường dẫn | Mô tả gốc |
|---|---|---|
| gsap-core | `gsap/gsap-core/SKILL.md` | Official GSAP skill for the core API — gsap.to(), from(), fromTo(), easing, duration, stagger, defaults, gsap.matchMedia() (responsive, prefers-reduced-motion). Use when … |
| gsap-frameworks | `gsap/gsap-frameworks/SKILL.md` | Official GSAP skill for Vue, Svelte, and other non-React frameworks — lifecycle, scoping selectors, cleanup on unmount. Use when the user wants animation in Vue, Nuxt, Sv… |
| gsap-performance | `gsap/gsap-performance/SKILL.md` | Official GSAP skill for performance — prefer transforms, avoid layout thrashing, will-change, batching. Use when optimizing GSAP animations, reducing jank, or when the us… |
| gsap-plugins | `gsap/gsap-plugins/SKILL.md` | Official GSAP skill for GSAP plugins — registration, ScrollToPlugin, ScrollSmoother, Flip, Draggable, Inertia, Observer, SplitText, ScrambleText, SVG and physics plugins,… |
| gsap-react | `gsap/gsap-react/SKILL.md` | Official GSAP skill for React — useGSAP hook, refs, gsap.context(), cleanup. Use when the user wants animation in React or Next.js, or asks about GSAP with React, useGSAP… |
| gsap-scrolltrigger | `gsap/gsap-scrolltrigger/SKILL.md` | Official GSAP skill for ScrollTrigger — scroll-linked animations, pinning, scrub, triggers. Use when building or recommending scroll-based animation, parallax, pinned sec… |
| gsap-timeline | `gsap/gsap-timeline/SKILL.md` | Official GSAP skill for timelines — gsap.timeline(), position parameter, nesting, playback. Use when sequencing animations, choreographing keyframes, or when the user ask… |
| gsap-utils | `gsap/gsap-utils/SKILL.md` | Official GSAP skill for gsap.utils — clamp, mapRange, normalize, interpolate, random, snap, toArray, wrap, pipe. Use when the user asks about gsap.utils, clamp, mapRange,… |

### Video Shotcraft (Apache-2.0, github.com/Vincentwei1021/video-shotcraft): video sản phẩm, explainer; bản gọn, đã bỏ demos/workbench/gallery

| Skill | Đường dẫn | Mô tả gốc |
|---|---|---|
| video-shotcraft | `video-shotcraft/video-shotcraft/SKILL.md` | Create cinematic product videos from shot recipe cards, a validated template, and code/audio assets (Remotion + real page screenshots + 2.5D camera moves + beat-synced cu… |

## Bộ chưa kèm

Bốn bộ dưới đây có trong bản cài riêng của chủ dự án nhưng **không** đưa vào repo vì chưa xác minh được giấy phép phân phối lại. Muốn dùng thì cài từ nguồn gốc:

| Bộ | Số skill | Nội dung | Nguồn |
|---|---|---|---|
| hyperframes | 7 | Dựng video bằng HTML, CLI, kho khối dựng sẵn | github.com/heygen-com/hyperframes |
| herk-edit-kit | 15 | Quy trình người nói trên HyperFrames: cắt lặng, cắt vấp, hook, nhịp | nguồn của người cung cấp bộ skill |
| iart-ai | 55 | Hướng dẫn chuyển động theo thể loại: quảng cáo, infographic, kinetic type, logo, audiogram… | nguồn của người cung cấp bộ skill |
| motion-graphics | 6 | Explainer, b-roll chuyển động, âm thanh hiệu ứng, tách nền | nguồn của người cung cấp bộ skill |
