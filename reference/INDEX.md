# Tài liệu tham khảo

Đây là tài liệu đọc thêm, **không cần** để chạy quy trình chính (`video-editor`). Chỉ mở khi cần ý tưởng hoặc kỹ thuật mà bộ dựng mặc định chưa có.
Gồm 93 skill từ 7 bộ, chép nguyên bản (tiếng Anh). Phần lớn nhắm tới HyperFrames hoặc máy Mac: lấy nguyên tắc, còn lệnh thì điều chỉnh cho môi trường đang dùng.

`video-editor setup` cài cả 93 skill này thành skill riêng cạnh `video-editor` (xem, gỡ: `video-editor skills`). Khi đó Claude tự gọi đúng skill theo yêu cầu; danh mục dưới đây vẫn dùng để tra cứu.

Giấy phép từng bộ: xem `THIRD_PARTY.md`. Bốn bộ hyperframes, herk-edit-kit, iart-ai, motion-graphics chưa xác minh được giấy phép phân phối lại.

## Khi nào đọc gì

| Cần | Đọc |
|---|---|
| Chọn take hay nhất, phong cách Reel khác (meme, podcast, tối giản…) | `ghost-editor/ghost-editor/SKILL.md` |
| Nghiên cứu video mẫu để học nhịp, bố cục | `ghost-editor/ghost-editor/scripts/reference_study.py` |
| Cắt lặng, cắt vấp, hook, nhịp cho video người nói (cách làm trên HyperFrames) | `herk-edit-kit/edit-video`, `herk-edit-kit/short-form-edit`, `herk-edit-kit/cut-mistakes` |
| Đồ hoạ theo lời nói cho video dài, lower third, thế giới hình ảnh liền mạch | `herk-edit-kit/hyperframes-video-beats`, `herk-edit-kit/video-storytelling` |
| Ý tưởng chuyển động theo thể loại: quảng cáo, infographic, kinetic type, logo, audiogram… | `iart-ai/<kỹ thuật>/SKILL.md` (55 kỹ thuật, danh mục bên dưới) |
| Explainer sản phẩm, b-roll chuyển động, âm thanh hiệu ứng, tách nền | `motion-graphics/` |
| Dựng video bằng HTML, kho khối dựng sẵn, chuyển từ Remotion sang HyperFrames | `hyperframes/` |
| Video sản phẩm, explainer nhiều cảnh, chuyển cảnh điện ảnh | `video-shotcraft/video-shotcraft/SKILL.md` và `references/` |
| Viết chuyển động bằng GSAP (khi dựng bằng HTML/HyperFrames) | `gsap/gsap-core`, `gsap/gsap-timeline`, `gsap/gsap-plugins` |

## Danh mục 93 skill

### Ghost Editor: dựng Reel người nói trọn gói (HyperFrames, 7 phong cách) (MIT, github.com/kurbaitaev/ghost-editor)

| Skill | Đường dẫn | Mô tả gốc |
|---|---|---|
| ghost-editor | `ghost-editor/ghost-editor/SKILL.md` | AI video editor for talking-head reels: turns a raw phone recording to camera into a finished vertical 1080x1920 reel for Instagram, TikTok or Shorts with best takes, trimmed pauses, word-timed… |

### GSAP chính thức: thư viện chuyển động JavaScript (MIT)

| Skill | Đường dẫn | Mô tả gốc |
|---|---|---|
| gsap-core | `gsap/gsap-core/SKILL.md` | Official GSAP skill for the core API — gsap.to(), from(), fromTo(), easing, duration, stagger, defaults, gsap.matchMedia() (responsive, prefers-reduced-motion). Use when the user asks for a… |
| gsap-frameworks | `gsap/gsap-frameworks/SKILL.md` | Official GSAP skill for Vue, Svelte, and other non-React frameworks — lifecycle, scoping selectors, cleanup on unmount. Use when the user wants animation in Vue, Nuxt, Svelte, SvelteKit, or asks… |
| gsap-performance | `gsap/gsap-performance/SKILL.md` | Official GSAP skill for performance — prefer transforms, avoid layout thrashing, will-change, batching. Use when optimizing GSAP animations, reducing jank, or when the user asks about animation… |
| gsap-plugins | `gsap/gsap-plugins/SKILL.md` | Official GSAP skill for GSAP plugins — registration, ScrollToPlugin, ScrollSmoother, Flip, Draggable, Inertia, Observer, SplitText, ScrambleText, SVG and physics plugins, CustomEase, EasePack,… |
| gsap-react | `gsap/gsap-react/SKILL.md` | Official GSAP skill for React — useGSAP hook, refs, gsap.context(), cleanup. Use when the user wants animation in React or Next.js, or asks about GSAP with React, useGSAP, or cleanup on unmount.… |
| gsap-scrolltrigger | `gsap/gsap-scrolltrigger/SKILL.md` | Official GSAP skill for ScrollTrigger — scroll-linked animations, pinning, scrub, triggers. Use when building or recommending scroll-based animation, parallax, pinned sections, or when the user asks… |
| gsap-timeline | `gsap/gsap-timeline/SKILL.md` | Official GSAP skill for timelines — gsap.timeline(), position parameter, nesting, playback. Use when sequencing animations, choreographing keyframes, or when the user asks about animation sequencing,… |
| gsap-utils | `gsap/gsap-utils/SKILL.md` | Official GSAP skill for gsap.utils — clamp, mapRange, normalize, interpolate, random, snap, toArray, wrap, pipe. Use when the user asks about gsap.utils, clamp, mapRange, random, snap, toArray, wrap,… |

### Herk Edit Kit: quy trình dựng video người nói bằng HyperFrames (chưa rõ giấy phép)

| Skill | Đường dẫn | Mô tả gốc |
|---|---|---|
| cut-mistakes | `herk-edit-kit/cut-mistakes/SKILL.md` | Agent 2 of the video editing pipeline. Finds and removes spoken mistakes — stutters, repeated words, false starts, and retakes (re-recorded lines) — from a talking-head recording. Use after… |
| cut-silences | `herk-edit-kit/cut-silences/SKILL.md` | Agent 1 of the video editing pipeline. Removes silences and dead air from a talking-head recording. Use when asked to cut silences, trim pauses, remove dead air / gaps, or tighten the pacing of a raw… |
| edit-video | `herk-edit-kit/edit-video/SKILL.md` | Edit a raw talking-head video through transcription, silence trimming, mistake review, visual storytelling, motion graphics, and verified HyperFrames rendering. Use for a complete edit; route a… |
| gsap | `herk-edit-kit/gsap/SKILL.md` | GSAP animation reference for HyperFrames. Covers gsap.to(), from(), fromTo(), easing, stagger, defaults, timelines (gsap.timeline(), position parameter, labels, nesting, playback), and performance… |
| hyperframes | `herk-edit-kit/hyperframes/SKILL.md` | Create video compositions, animations, title cards, overlays, captions, voiceovers, audio-reactive visuals, and scene transitions in HyperFrames HTML. Use when asked to build any HTML-based video… |
| hyperframes-cli | `herk-edit-kit/hyperframes-cli/SKILL.md` | HyperFrames CLI tool — hyperframes init, lint, preview, render, transcribe, tts, doctor, browser, info, upgrade, compositions, docs, benchmark. Use when scaffolding a project, linting or validating… |
| hyperframes-registry | `herk-edit-kit/hyperframes-registry/SKILL.md` | Install and wire registry blocks and components into HyperFrames compositions. Use when running hyperframes add, installing a block or component, wiring an installed item into index.html, or working… |
| hyperframes-video-beats | `herk-edit-kit/hyperframes-video-beats/SKILL.md` | Plan, write, time, style, and validate motion-graphic beats for long-form talking-head HyperFrames videos. Use when Codex is asked to add or improve visual beats, glassmorphism lower thirds,… |
| make-a-video | `herk-edit-kit/make-a-video/SKILL.md` | Beginner-friendly end-to-end video creator for HyperFrames. Use when the user says "make a video", "create a video", "new video", "build a video", "video from scratch", "I want to make a video",… |
| motion-showreel | `herk-edit-kit/motion-showreel/SKILL.md` | Design and build a 10-30 second motion-design showreel or brand reel in the style of Nate's Opus 5.5 "CLAUDE / MOTION REEL": one brand motif transformed through labeled craft chapters, a persistent… |
| short-form-edit | `herk-edit-kit/short-form-edit/SKILL.md` | Turn talking-head footage into a finished reel, YouTube Short, or short advertisement with curiosity-led openings, earned payoffs, story-driven cuts, transcript-synced motion graphics, moving B-roll,… |
| short-form-video | `herk-edit-kit/short-form-video/SKILL.md` | Maintain the existing May Shorts teaching compositions using their legacy face-mode, scene-overlay, and karaoke-caption patterns. Use only when working on those examples or explicitly requesting this… |
| style-library | `herk-edit-kit/style-library/SKILL.md` | Select, customize, or extend the project's reusable motion-graphics card library and style templates. Use for choosing a visual style, adding a card, building a new style pack, or reusing a template… |
| video-storytelling | `herk-edit-kit/video-storytelling/SKILL.md` | Design and build the visual layer of a long-form talking-head video as one persistent world the camera moves through, instead of a sequence of separate graphics. Use when asked to edit a video, add… |
| website-to-hyperframes | `herk-edit-kit/website-to-hyperframes/SKILL.md` | /   Capture a website and create a HyperFrames video from it. Use when: (1) a user provides a URL and wants a video, (2) someone says "capture this site", "turn this into a video", "make a promo from… |

### HyperFrames: dựng video bằng HTML (chưa rõ giấy phép, nguồn github.com/heygen-com/hyperframes)

| Skill | Đường dẫn | Mô tả gốc |
|---|---|---|
| figma | `hyperframes/figma/SKILL.md` | Bring Figma into a HyperFrames video - rendered assets, brand tokens, components, storyboard frames as reconstructed motion (frames read as states, not slides), shaders and connector-assisted motion.… |
| hyperframes | `hyperframes/hyperframes/SKILL.md` | Read first to make, edit, animate or render any video with HyperFrames (HTML rendered to video), including launch films, explainers, music videos, charts, maps, vertical clips, title cards, captions… |
| hyperframes-cli | `hyperframes/hyperframes-cli/SKILL.md` | The HyperFrames CLI by job - scaffold, check, look at frames, edit the timeline, preview, render locally or in the cloud, publish, project history - plus reading its JSON and recovering from build or… |
| hyperframes-registry | `hyperframes/hyperframes-registry/SKILL.md` | About 450 ready-made HyperFrames blocks and components installed as editable source - transitions, overlays, titles, kinetic type, captions, charts, map overlays, 3D, camera moves. Use it before… |
| media-use | `hyperframes/media-use/SKILL.md` | Get or make any media for a HyperFrames video - music, sound effects, images, icons, logos, voiceover, avatar and generated video, transcripts, cutouts, colour grades and looks - with HeyGen or free… |
| remotion-to-hyperframes | `hyperframes/remotion-to-hyperframes/SKILL.md` | Bring existing video code or footage into HyperFrames and verify it frame by frame against the original - Remotion first, also Motion Canvas, Lottie, Three.js, p5.js, canvas or plain HTML/CSS… |
| slideshow | `hyperframes/slideshow/SKILL.md` | Build a HyperFrames slideshow to present live - slides, fragment reveals, branching hotspots and presenter mode with speaker notes, served by `hyperframes present` - or turn an existing page into… |

### iArt AI: 55 kỹ thuật motion design (chưa rõ giấy phép)

| Skill | Đường dẫn | Mô tả gốc |
|---|---|---|
| 60fps-animation | `iart-ai/60fps-animation/SKILL.md` | This skill should be used when the user asks to "fix janky CSS animation", "make animation 60fps", "stop layout thrashing", "animate width/height/top/left smoothly", "convert animation to transform",… |
| accessible-animation | `iart-ai/accessible-animation/SKILL.md` | This skill should be used when the user asks to "respect prefers-reduced-motion", "honor reduced motion", "make my animations accessible", "fix vestibular / motion-sickness issues", "add a… |
| ad-creative-video | `iart-ai/ad-creative-video/SKILL.md` | This skill should be used when the user asks to "make a video ad", "create an animated ad", "build a performance/UGC-style ad", "batch-produce ad creative variations", "generate ad variants for A/B… |
| after-effects | `iart-ai/after-effects/SKILL.md` | This skill should be used when the user asks anything about Adobe After Effects — to "write an After Effects expression", "make a wiggle / loopOut / inertial bounce", "rig a control with a slider /… |
| animated-infographic | `iart-ai/animated-infographic/SKILL.md` | This skill should be used when the user asks to "make an animated infographic", "create an infographic video", "build an infographic animation", "animate an explainer infographic", "do a sequenced… |
| animation-principles | `iart-ai/animation-principles/SKILL.md` | This skill should be used when the user asks to "make this animation feel natural", "fix motion that feels stiff/floaty/cheap", "my animation looks robotic", "choose an easing curve", "how do I use… |
| ascii-animation | `iart-ai/ascii-animation/SKILL.md` | This skill should be used when the user asks to "make an ASCII animation", "build a terminal/CLI intro or loader", "convert an image or video to ASCII art", "add an ASCII shader/post-effect to a… |
| audiogram | `iart-ai/audiogram/SKILL.md` | This skill should be used when the user asks to "make an audiogram", "turn a podcast into a video", "create a waveform video", "make a podcast clip video", "convert audio to video", "animate a… |
| beat-sync-editing | `iart-ai/beat-sync-editing/SKILL.md` | This skill should be used when the user asks to "cut to the beat", "fix the pacing", "edit this sequence", "sync cuts to music/BPM", "add a match cut / J-cut / L-cut", "build a speed ramp", or "plan… |
| brand-motion-guidelines | `iart-ai/brand-motion-guidelines/SKILL.md` | This skill should be used when the user asks to "write motion guidelines", "create a brand motion system", "define easing and timing tokens", "document our animation principles", "build a motion… |
| caption-animation | `iart-ai/caption-animation/SKILL.md` | This skill should be used when the user asks to "add animated captions", "make TikTok captions", "karaoke captions", "word-by-word subtitles", "auto subtitles", "highlight the active word", "burn in… |
| chart-animation | `iart-ai/chart-animation/SKILL.md` | This skill should be used when the user asks to "make a bar chart race", "turn a CSV into a video", "build an animated data visualization", "create an animated statistics video", "animate a… |
| client-revisions | `iart-ai/client-revisions/SKILL.md` | This skill should be used when the user asks to "stop scope creep", "limit revision rounds", "write SOW revision language", "the client keeps asking for changes", "how do I say this is out of scope",… |
| color-motion | `iart-ai/color-motion/SKILL.md` | This skill should be used when the user asks to "build a color palette for a motion piece", "make a gradient background", "animate a color transition", "interpolate colors smoothly", "fix muddy/gray… |
| countdown-video | `iart-ai/countdown-video/SKILL.md` | This skill should be used when the user asks to "make a countdown timer video", "create a countdown animation", "build a stream starting soon countdown", "do an event/launch/sale countdown", "animate… |
| creative-brief | `iart-ai/creative-brief/SKILL.md` | This skill should be used when the user asks to "write a creative brief", "build a motion brief", "the client doesn't know what they want", "turn this vague client request into a brief", "what… |
| diagram-animation | `iart-ai/diagram-animation/SKILL.md` | This skill should be used when the user asks to "animate this diagram", "build a flowchart that reveals step by step", "animate an architecture/sequence diagram", "make a chart animate in", "grow the… |
| explainer-video | `iart-ai/explainer-video/SKILL.md` | This skill should be used when the user asks to "make an explainer video", "turn this into a short explainer", "write a script and storyboard for a product video", "produce a how-it-works/onboarding… |
| generative-illustration | `iart-ai/generative-illustration/SKILL.md` | This skill should be used when the user asks to "make an animated illustration", "animate an illustration", "make a generative motion piece" / "动态平面", "turn AI-generated art into something that… |
| glassmorphism | `iart-ai/glassmorphism/SKILL.md` | This skill should be used when the user asks to "add a glassmorphism effect", "frosted glass UI", "Apple liquid glass style", "frosted blur card", "translucent glass panel animation", "make a frosted… |
| gsap-web | `iart-ai/gsap-web/SKILL.md` | This skill should be used when the user asks to "build a scroll animation", "add ScrollTrigger", "pin a section while scrolling", "scrub an animation to scroll", "create a hero timeline", "do a… |
| iart-short-form-video | `iart-ai/iart-short-form-video/SKILL.md` | This skill should be used when the user asks to "make a Reels/TikTok/YouTube Shorts video", "build a short-form video template", "write a hook for a short", "edit for retention", "add pattern… |
| isometric-animation | `iart-ai/isometric-animation/SKILL.md` | This skill should be used when the user asks to "make an isometric animation", "build a 2.5D isometric scene", "create an isometric infographic", "animate an exploded diagram", "do an isometric… |
| javascript-animation | `iart-ai/javascript-animation/SKILL.md` | This skill should be used when the user asks to "draw every frame in JavaScript", "make an animation with no image assets", "animate this in code / on a canvas", "make a hand-drawn style animated… |
| kinetic-typography | `iart-ai/kinetic-typography/SKILL.md` | This skill should be used when the user asks to "animate a headline", "make a kinetic typography video", "do a split-text reveal", "stagger text by character/word/line", "make a lyric or caption… |
| launch-video | `iart-ai/launch-video/SKILL.md` | This skill should be used when the user asks to "make a launch video", "create a product hype/sizzle film", "build a teaser/trailer for a drop", "do a reveal montage with an end-card CTA", "cut a… |
| logo-animation | `iart-ai/logo-animation/SKILL.md` | This skill should be used when the user asks to "animate our logo", "make a logo intro/stinger", "build a brand reveal", "create an app splash animation", "loop a loader logo", "draw on our SVG… |
| lottie-animation | `iart-ai/lottie-animation/SKILL.md` | This skill should be used when the user asks to "add a Lottie animation", "play a .lottie or .json animation", "integrate a Bodymovin/After Effects animation on web or mobile", "control Lottie… |
| lower-thirds | `iart-ai/lower-thirds/SKILL.md` | Make animated lower thirds and other broadcast overlays (name straps, corner bugs, subscribe reminders, scripture or song titles) as transparent video files, drawn frame by frame in JavaScript on a… |
| manim | `iart-ai/manim/SKILL.md` | This skill should be used when the user asks to "make a math animation", "animate an equation", "use Manim", "make a 3Blue1Brown-style video", "plot or animate a graph/function", "visualize a… |
| map-animation | `iart-ai/map-animation/SKILL.md` | This skill should be used when the user asks to "make a Vox-style map animation", "animate a map zoom", "draw a route on a map", "highlight a country/region", "use Google Earth Studio", "drop pins on… |
| micro-interaction | `iart-ai/micro-interaction/SKILL.md` | This skill should be used when the user asks to "add a hover/press effect", "animate a toggle or switch", "build an animated like button", "make a toast/snackbar slide in", "animate a drawer or… |
| motion-art-direction | `iart-ai/motion-art-direction/SKILL.md` | This skill should be used when the user asks to "direct a motion graphics video", "do creative/art direction for a video", "define a motion language", "set the tone and pacing", "make the animation… |
| motion-background | `iart-ai/motion-background/SKILL.md` | This skill should be used when the user asks to "add an animated background", "build a mesh/gradient background", "make an aurora/shader background", "add constellation/particle background",… |
| motion-pricing | `iart-ai/motion-pricing/SKILL.md` | This skill should be used when the user asks to "quote a motion project", "estimate this animation job", "how much should I charge for this video", "what's my day rate", "build a quote", "price a… |
| page-transition-animation | `iart-ai/page-transition-animation/SKILL.md` | This skill should be used when the user asks to "animate page or route transitions", "add a page transition or crossfade between views", "animate route changes in Next.js App Router", "use the View… |
| particle-system | `iart-ai/particle-system/SKILL.md` | This skill should be used when the user asks to "build a particle system", "make confetti/snow/smoke/sparks", "create a connected-dot/constellation network background", "add a flow-field or… |
| photo-slideshow | `iart-ai/photo-slideshow/SKILL.md` | This skill should be used when the user asks to "make a photo slideshow", "turn photos into a video", "create a photo montage video", "make a picture slideshow with music", "build a memories/recap… |
| presentation-video | `iart-ai/presentation-video/SKILL.md` | This skill should be used when the user asks to "make an animated presentation", "turn a pitch deck into a video", "convert slides/a deck to video", "make a presentation video", "build a deck video",… |
| product-demo-video | `iart-ai/product-demo-video/SKILL.md` | This skill should be used when the user asks to "make a product demo video", "create an app demo video", "build a feature announcement video", "do a SaaS demo", "make a UI walkthrough video",… |
| promo-video | `iart-ai/promo-video/SKILL.md` | This skill should be used when the user asks to "make a sale video", "create a promo video", "build a discount/percentage-off reveal", "animate a was→now price with a strike-through", "do a Black… |
| remotion-video | `iart-ai/remotion-video/SKILL.md` | This skill should be used when the user asks to "make a video with Remotion", "create a programmatic/data-driven video in React", "render an MP4/GIF from code", "animate with… |
| shader-glsl | `iart-ai/shader-glsl/SKILL.md` | This skill should be used when the user asks to "write a fragment shader", "make a GLSL gradient/noise/plasma background", "create an image transition (dissolve, displacement, glitch)", "add… |
| shot-composition | `iart-ai/shot-composition/SKILL.md` | This skill should be used when the user asks to "compose a frame", "set up a grid", "plan shot composition", "place the focal point", "decide where elements enter and exit", "add a parallax/camera… |
| soundtrack | `iart-ai/soundtrack/SKILL.md` | This skill should be used when the user asks to "add music to the animation", "make the music in code", "synthesize a soundtrack", "compose background music that fits the cuts", "sync the music to… |
| svg-animation | `iart-ai/svg-animation/SKILL.md` | This skill should be used when the user asks to "animate an SVG", "make a line draw itself on", "do a stroke draw-on / signature animation", "morph one shape into another", "move an element along a… |
| talking-head-b-roll | `iart-ai/talking-head-b-roll/SKILL.md` | Add b-roll motion graphics to a talking-head video. Transcribes the recording with word timings, decides line by line when the speaker is shown, when a graphic is laid over them and when a full-frame… |
| testimonial-video | `iart-ai/testimonial-video/SKILL.md` | This skill should be used when the user asks to "make an animated testimonial", "create a quote video", "build a review video", "turn a customer testimonial into a graphic", "animate a customer… |
| text-message-animation | `iart-ai/text-message-animation/SKILL.md` | This skill should be used when the user asks to "make a fake text message video", "animate an iMessage conversation", "create a text story video", "do a chat reply animation", "WhatsApp/SMS… |
| threejs-animation | `iart-ai/threejs-animation/SKILL.md` | This skill should be used when the user asks to "build a 3D hero section or WebGL background", "animate a Three.js scene", "play or crossfade GLTF animation clips", "move/lerp the camera or link it… |
| tiktok-lower-thirds | `iart-ai/tiktok-lower-thirds/SKILL.md` | This skill should be used when the user asks to "make an animated lower third", "add lower thirds", "create a name tag/name lower third", "build broadcast titles", "animate a title/name/role… |
| video-delivery-specs | `iart-ai/video-delivery-specs/SKILL.md` | This skill should be used when the user asks "what are the specs for Instagram Reels / TikTok / YouTube / broadcast", "export settings for social", "what aspect ratio and bitrate", "how do I… |
| whiteboard-animation | `iart-ai/whiteboard-animation/SKILL.md` | This skill should be used when the user asks to "make a whiteboard animation", "draw-on explainer", "VideoScribe style", "hand-drawn explainer video", "animate a sketch being drawn", "do a… |
| wrapped-video | `iart-ai/wrapped-video/SKILL.md` | This skill should be used when the user asks to "make a Spotify Wrapped style video", "build a year in review / year-in-review video", "create a personalized data video", "generate a recap video",… |
| youtube-intro-outro | `iart-ai/youtube-intro-outro/SKILL.md` | This skill should be used when the user asks to "make a YouTube intro", "create a channel intro", "build a logo sting/bumper", "design an outro / end screen / end card", "add subscribe and next-video… |

### Motion Graphics: explainer, b-roll chuyển động, âm thanh hiệu ứng (chưa rõ giấy phép)

| Skill | Đường dẫn | Mô tả gốc |
|---|---|---|
| explainer-default | `motion-graphics/explainer-default/SKILL.md` | Make a clean 45–90 second product demo video for any software product, rendered from code to MP4 with music. Airy light canvas, short centred lines the camera pushes into, the product's own UI… |
| explainer-engaging | `motion-graphics/explainer-engaging/SKILL.md` | Make a 10–30 second continuous-shot explainer for any product, rendered from code to MP4 with sound. One hero element (a ball, a cursor, a file, a message) travels through the product's workflow laid… |
| explainer-high-energy | `motion-graphics/explainer-high-energy/SKILL.md` | Make a 12–20 second high-energy motion-graphics promo for any product, rendered from code to MP4 with synthesised music. Fast beat-locked scene changes, kinetic typography, a shape that carries… |
| motion-broll | `motion-graphics/motion-broll/SKILL.md` | Turn a talking-head video and its transcript into motion-graphic B-roll timed to the speaker's words, in a continuous one-shape style (one element that morphs and never cuts, driven by a cursor,… |
| object-separation | `motion-graphics/object-separation/SKILL.md` | Separate a person, product or hand from the background in a video, on the user's own computer with SAM 2. Scans the machine first to pick the right model size, then outputs the same video with the… |
| sound-effects | `motion-graphics/sound-effects/SKILL.md` | Add a measured sound pass to a motion-graphics video made with Claude Code (HyperFrames, Remotion, GSAP, Claude Motion or the motion-broll skill). Builds a cue list, checks the music's beat grid… |

### Video Shotcraft: video sản phẩm điện ảnh (Apache-2.0, github.com/Vincentwei1021/video-shotcraft)

| Skill | Đường dẫn | Mô tả gốc |
|---|---|---|
| video-shotcraft | `video-shotcraft/video-shotcraft/SKILL.md` | Create cinematic product videos from shot recipe cards, a validated template, and code/audio assets (Remotion + real page screenshots + 2.5D camera moves + beat-synced cuts + sound design). Use when… |
