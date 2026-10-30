---
name: video-editor
description: Dựng video ngắn dọc (Facebook Reels, TikTok, Shorts) tiếng Việt, từ video người nói hoặc chỉ từ prompt/kịch bản với giọng đọc AI nhân bản (ElevenLabs). Trọn quy trình từ phiếu nhận việc, chép lời, đồ hoạ khớp lời, phụ đề, render tới giao file. Tự chứa 93 skill dựng video, mẫu Remotion, script và bộ nhận diện BTC Daily.
---

# Video editor

Một skill duy nhất cho mọi việc dựng video ngắn: Reel người nói, explainer, video quảng cáo, video sản phẩm. Hai chế độ: **A** dựng từ video người nói (quy trình 10 bước), **B** tạo video từ prompt hoặc kịch bản với giọng đọc AI nhân bản (mục "Chế độ B"). Gồm hai phần:

1. **Bộ quy trình chuẩn** (ngay dưới đây): các bước, quy tắc và lệnh đã chạy thật trên Reel "Cập nhật bitcoin 02/10" (175 giây), cộng với quy tắc chắt lọc từ các bộ skill đã cài.
2. **Thư viện 93 skill** đóng gói trong `skills/` (trong thư mục skill này), tra theo bảng "Việc gì thì mở skill nào". Danh mục đầy đủ có mô tả ở `INDEX.md`.

## Cài đặt

Skill này tự chứa mọi thứ: quy trình, 93 skill con, mẫu Remotion, script, bộ nhận diện, phiếu nhận việc. Không cần cài thêm skill nào khác.

- **Claude Code:** giải nén để có `~/.claude/skills/video-editor/SKILL.md` (hoặc `.claude/skills/video-editor/` trong dự án).
- **claude.ai:** Settings → Capabilities → Skills → Upload skill, chọn file zip.
- Mọi đường dẫn trong file này tính từ thư mục skill. Thư mục skill có thể chỉ đọc, nên luôn chép `mau-remotion/` và `scripts/` ra thư mục làm việc trước khi chạy.
- Skill con chỉ là tài liệu tham khảo: đọc `SKILL.md` của skill con khi bảng "Việc gì thì mở skill nào" trỏ tới, không cần cài riêng.

## Bộ công cụ

Thư mục skill này (đã cài ở `~/.claude/skills/video-editor/` hoặc nơi claude.ai giải nén):

| Đường dẫn | Là gì |
|---|---|
| `mau-remotion/` | Dự án Remotion 4.0.537 mẫu theo bộ nhận diện BTC Daily: `src/Reel.tsx`, `Captions.tsx` (4 kiểu phụ đề), `Graphics.tsx` (stat, price, levels, list, chart, title), `Icons.tsx`, `theme.ts`, `types.ts`, `BrandSheet.tsx`; âm thanh CC0 ở `public/sfx` |
| `nhan-dien/btc-daily/` | Bộ nhận diện BTC Daily: quy chuẩn, tokens, mẫu thành phần |
| `mau-tai-lieu/phieu-nhan-viec.md` | Phiếu nhận việc điền ở bước 1 |
| `mau-remotion/beats.mau.json` | Kịch bản đồ hoạ mẫu (hook, brand, cta, beats, topics, zooms, fix, dropSegments) |
| `scripts/transcribe.py` | faster-whisper large-v3, tiếng Việt, mốc theo từng từ |
| `scripts/tts_elevenlabs.py` | Chế độ B: nhân bản giọng, đọc kịch bản, xuất `voice.mp3` và `transcript.json` có mốc từng chữ |
| `mau-tai-lieu/kich-ban-mau.md` | Khung kịch bản cho chế độ B |
| `scripts/build.py` | Sửa lời, cắt lặng, chuẩn hoá -14 LUFS, dò từ khoá thành mốc thời gian, xuất `src/data.json` |
| `skills/` | 93 skill gốc (tiếng Anh) của 7 bộ: ghost-editor, herk-edit-kit, hyperframes, iart-ai, motion-graphics, gsap, video-shotcraft (bản gọn nhẹ) |
| `INDEX.md` | Danh mục 93 skill kèm đường dẫn và mô tả |

Bộ nhận diện BTC Daily (màu, chữ, phụ đề, thành phần): https://claude.ai/artifact/A9xf3ARBKkkjjqciyYjwhv, bản sao đi kèm skill ở `nhan-dien/btc-daily/` (`README.md` là quy chuẩn, `tokens.json` là mã màu và cỡ chữ, `components/` là mẫu từng thành phần).

**Chọn công cụ dựng:**
- Mặc định dùng **Remotion** với `mau-remotion/`, vì đã chạy thật và khớp bộ nhận diện.
- Dùng **HyperFrames** (dựng video bằng HTML) khi cần các khối dựng sẵn của bộ `hyperframes` / `herk-edit-kit` / `ghost-editor` (khoảng 450 khối chuyển cảnh, kinetic type, biểu đồ). Đọc `skills/hyperframes/hyperframes/SKILL.md` trước.
- Không trộn hai công cụ trong một video.

## Nguyên tắc không được phá

1. **Không bịa.** Chữ trên màn hình chỉ là lời người nói đã nói, hoặc số liệu, tên riêng có trong lời và tài liệu người dùng đưa. Cụm nghe không rõ thì giữ nguyên, không làm đồ hoạ, và hỏi người dùng.
2. **Nói tới đâu, hiện tới đó.** Mỗi phần tử đồ hoạ gắn với một từ khoá qua khoá `say`. Có ba kiểu canh giờ:
   - Khung, trục, bố cục: hiện trước khoảng 6 khung hình.
   - Con số, giá, phần trăm: đọc được đúng lúc từ đó vang lên.
   - Câu chốt, câu trả lời: chờ tới đúng từ hé lộ.
3. **Cắt theo mốc từng từ**, không theo mốc đoạn của Whisper. Điểm vào là chữ đầu trừ 0,10 đến 0,15 giây, điểm ra là chữ cuối cộng 0,20 đến 0,30 giây. Giữ khoảng 0,14 đến 0,24 giây hơi thở giữa các câu.
4. **Đo thật, báo thật.** Thời gian render, LUFS, dung lượng, độ tương phản lấy từ log, ffprobe, ebur128. Số ước đoán phải ghi rõ là ước đoán.
5. **Soát trước khi render.** Chụp ảnh tĩnh tại mỗi mốc cắt và mỗi từ khoá, tự xem trước. Thay đổi lớn về hình thì gửi người dùng xem mẫu ngắn (10 đến 15 giây) trước khi render cả bài.
6. **Mỗi góp ý là một quy tắc.** Khi người dùng sửa ("bỏ gạch chân", "đồ hoạ hiện trước lời"), sửa video rồi ghi góp ý đó vào skill này hoặc vào bộ nhận diện, để lần sau không lặp lại.

## Bộ quy trình 10 bước

### Bước 1. Nhận việc và chuẩn bị
- Chép `mau-tai-lieu/phieu-nhan-viec.md` vào thư mục dự án và điền. Ô nào người dùng chưa trả lời thì tự suy ra, ghi "tự chọn" để báo lại ở bước 10.
- Hỏi (hoặc tự suy ra): nền tảng đăng, độ dài mong muốn, phong cách hay bộ nhận diện, có kịch bản không, có ảnh hoặc biểu đồ thật để làm dẫn chứng không.
- Mạng cần mở: `huggingface.co`, `*.hf.co`, `*.xethub.hf.co`. File model tải từ `us.aws.cdn.hf.co` và `cas-*.xethub.hf.co`. Nếu bị chặn, hướng dẫn người dùng thêm vào Allowed domains, hoặc xin file `.srt` từ CapCut. Không vòng qua mirror.
- Python: `python3 -m venv venv && ./venv/bin/pip install faster-whisper`.
- Node: chép `mau-remotion/` ra ổ cục bộ, chạy `npm ci`. Không làm việc trực tiếp trên ổ mạng hay thư mục skill (chậm, và thư mục skill có thể chỉ đọc).
- Trình duyệt: `--browser-executable=/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell`.
- Tham khảo: `skills/iart-ai/creative-brief`, `skills/iart-ai/motion-art-direction`.

### Bước 2. Khảo sát nguồn và video mẫu
- `ffprobe` lấy khổ hình, fps, thời lượng. Trích bảng khung hình mỗi 10 giây để xem vị trí mặt (đặt `FACE_X`, `FACE_Y` trong `Reel.tsx`), độ sáng nền, chỗ cằm.
- Nếu có video mẫu: trích khung mỗi khoảng 2 giây (`fps=0.48,scale=300:-1,tile=6x2`) và ghi điều đáng học: bố cục, phụ đề, nhịp đồ hoạ, dẫn chứng. Chỉ học cơ chế, không chép thương hiệu.
- Tham khảo: `skills/herk-edit-kit/short-form-edit/references/reference-analysis.md`, `skills/ghost-editor/ghost-editor/scripts/reference_study.py`.

### Bước 3. Chép lời
```bash
ffmpeg -i nguon.mp4 -ar 16000 -ac 1 audio.wav
../venv/bin/python transcribe.py      # -> transcript.json (w, s, e, p cho từng từ)
```
- Script đọc wav bằng numpy, vì faster-whisper 1.2.1 lỗi `metadata_errors` với PyAV 19.
- Large-v3 trên CPU 4 nhân mất khoảng 1,4 lần thời lượng. Chạy nền và theo dõi log.
- Âm thanh ồn (gió, xe, quạt) thì khử ồn trước: `skills/ghost-editor/ghost-editor/scripts/denoise.sh`.

### Bước 4. Soát lời, chọn đoạn, cắt vấp
- Đọc toàn bộ bản chép. Sửa thuật ngữ nghe sai (ví dụ "Ninh Farm Payroll" là Nonfarm Payroll, "anh coi" là altcoin, "lon sọt" là long short, "BDC" là BTC). Soi chữ có `p < 0,4`.
- Bỏ đoạn Whisper bịa hoặc lặp: đoạn rất ngắn mà nhiều chữ, nhiều chữ cùng một mốc thời gian.
- Ghi vào `beats.json`: `"fix": [["cụm sai", "cụm đúng"]]` và `"dropSegments": [giây bắt đầu]`.
- Whisper hay gộp chỗ nói lại thành một câu trơn tru. Một quãng giọng dài mà ít chữ thường là chỗ nói lại bị giấu.
- Vấp, nói lại, bỏ dở câu: đề xuất từng chỗ cắt kèm ngữ cảnh rồi mới cắt. Lặp từ để nhấn mạnh thì giữ.
- Tham khảo: `skills/herk-edit-kit/cut-mistakes`, `skills/herk-edit-kit/cut-silences`, `skills/ghost-editor/ghost-editor/references/take-selection.md`.

### Bước 5. Thiết kế câu chuyện
- **Một video, một ý.** Gọi được tên ý chính trong một câu.
- **3 giây đầu là một bản dựng riêng.** Câu hook hiện thành chữ ngay khung đầu (85% người xem tắt tiếng). Mở một câu hỏi, và câu trả lời phải có thật trong video, đóng lại trước lời kêu gọi theo dõi. Không mở bằng màn đen hay "xin chào các bạn" kéo dài.
- **Ba chế độ hình** cho từng câu:
  - **A. Người nói:** mở đầu, ý kiến cá nhân, lời kêu gọi, câu kết.
  - **B. Chồng lớp:** người nói vẫn hiện, thêm từ khoá, con số hoặc mũi tên.
  - **C. Phủ kín:** đồ hoạ toàn màn hình, mặt người nói thu thành ô nhỏ. Dùng cho số liệu, so sánh, quy trình, từ 3 ý trở lên.
- **Nhịp:**
  - Mở và kết bằng A. Đoạn A không quá khoảng 8 giây liền.
  - Đoạn C dài 3 đến 8 giây (danh sách dài có thể tới 20 giây).
  - Có thay đổi hình (cắt, zoom, chèn, đổi chế độ) mỗi 2 đến 4 giây, khoảng cách không đều.
  - Mặt người nói xuất hiện ít nhất 65% thời lượng.
- **Không nhắc lại ba lần.** Lời và phụ đề đã mang chữ, nên đồ hoạ nên cho thấy con số, quan hệ hay hệ quả, không chép lại câu nói.
- Tham khảo: `skills/iart-ai/iart-short-form-video`, `skills/herk-edit-kit/short-form-edit`, `skills/herk-edit-kit/video-storytelling`, `skills/iart-ai/talking-head-b-roll`.

### Bước 6. Viết kịch bản đồ hoạ `beats.json`
Chép `beats.mau.json` thành `beats.json` rồi sửa. Mốc thời gian tính theo giây của video gốc.
- `hook` (kicker, title, sub), `brand` (`"BTC DAILY · dd/mm"`), `cta`.
- `beats[]`: `start`, `end`, `head` và `g`:
  - `stat`: `say` cho con số lớn, `labelSay` cho dòng chú thích.
  - `price`: `say` là lúc số đếm xong, `changeSay` cho dòng thay đổi.
  - `levels` và `list`: mỗi dòng có `say`, tối đa 3 dòng.
  - `chart`: mỗi nhãn có `say`.
  - `title`.
- `topics[]`: thẻ chủ đề cho đoạn A. Ý trong thẻ có `say`.
- `zooms[]`: zoom cắt 100% / 110% mỗi 4 đến 9 giây ở đoạn A, tối đa vài lần zoom mạnh trong cả video.
- `start` cảnh đặt trước từ khoá đầu 0,5 đến 2 giây. `end` đặt sau từ khoá cuối ít nhất 1 giây.
- Từ khoá `say` khớp nguyên văn (không phân biệt hoa thường, bỏ dấu câu) trong khoảng `[start - 1, end + 0,5]`. Không thấy thì script dừng và báo lỗi.
- Dẫn chứng: ưu tiên ảnh chụp biểu đồ thật của người dùng, đặt trong khung kèm nhãn tóm ý. Ảnh, video stock chỉ dùng sau cùng và luôn đặt trong khung, không toàn màn hình. Tối đa 3 lần chèn mỗi phút. Một cảnh cho một ý.
- Tham khảo đồ hoạ: `skills/iart-ai/chart-animation`, `animated-infographic`, `kinetic-typography`, `lower-thirds`, `tiktok-lower-thirds`, `diagram-animation`, `map-animation`, `skills/motion-graphics/motion-broll`.

### Bước 7. Cắt lặng và dựng dữ liệu
```bash
python3 build.py nguon.mp4              # cắt lặng > 0,55 s (đệm 0,12 s), chuẩn hoá -14 LUFS -> public/cut.mp4, src/data.json
SKIP_CUT=1 python3 build.py nguon.mp4   # chỉ đổi kịch bản đồ hoạ (vài giây)
```
- Mọi mốc thời gian sau khi cắt đều suy ra từ cùng một bản đồ cắt. Đổi cắt thì chạy lại để phụ đề, đồ hoạ và âm thanh cùng cập nhật.
- `doan-giu-lai.json` ghi các đoạn giữ lại và chữ đã soát theo giờ gốc, dùng khi dựng song song trong CapCut.

### Bước 8. Âm thanh
- Thứ tự ưu tiên: giọng nói, rồi hiệu ứng, rồi nhạc. Âm lượng giọng chuẩn hoá ở bước cắt. Không tăng âm lượng bản trộn cuối.
- Chỉ dùng tiếng thu thật (CC0 hoặc Mixkit), không tự tổng hợp tiếng beep bằng code.
- Bộ `public/sfx`: whoosh 0,16 khi đổi chế độ (đặt sớm 2 khung hình), impact 0,3 ở cảnh mở đầu, riser 0,18 kết thúc đúng cú chốt, click 0,3, pop khi phần tử hiện.
- Mật độ khoảng 0,4 đến 0,9 tiếng hiệu ứng mỗi 10 giây. Không đặt tiếng hiệu ứng đè lên chữ đang nói.
- Nhạc nền (nếu có) thấp hơn hiệu ứng khoảng 12 dB và giảm thêm 8 đến 12 dB khi có lời. Ghi rõ nguồn và giấy phép nhạc.
- Mục tiêu Reels: **-14 LUFS**, đỉnh thật ≤ -1,5 dB. Đo trên file MP4 cuối bằng `ffmpeg -af ebur128=peak=true`.
- Không nghe được thì không nói "nghe ổn". Đưa người dùng 5 mốc thời gian rủi ro nhất để nghe bằng tai nghe.
- Tham khảo: `skills/motion-graphics/sound-effects`, `skills/iart-ai/soundtrack`, `skills/iart-ai/beat-sync-editing`.

### Bước 9. Soát và render
```bash
npx tsc --noEmit -p .
npx remotion still BitcoinReel out/k.png --frame=<giây × 30> --browser-executable=...
npx remotion render BitcoinReel out/raw.mp4 --concurrency=4 --crf=20 --audio-bitrate=192k --browser-executable=...
ffmpeg -i out/raw.mp4 -c copy -movflags +faststart out/final.mp4
```
- **Danh sách soát ảnh tĩnh:**
  - Phần tử không hiện trước từ khoá.
  - Phụ đề không đè mặt hay miệng.
  - Chữ không tràn mép, không có dòng chỉ một chữ.
  - Ô mặt người nói thấy rõ mặt.
  - Không có khung đen ở 0,4 giây cuối (Reels lặp lại từ đầu).
- **Vùng an toàn 9:16:**
  - Chữ quan trọng nằm trong khung giữa 900 × 1400.
  - Chừa 120px trên, 320 đến 380px dưới, 120px bên phải (cột nút bấm).
- Chỉ nén một lần. Muốn thử mẫu nhanh thì render một đoạn: `--frames=1080-1499 --props='{"captionStyle":"glow"}'`.
- Đo được trên máy đám mây 4 nhân: render khoảng 10 đến 11 phút cho 173 giây. Bỏ nén lần hai tiết kiệm khoảng 4,5 phút.
- Tham khảo: `skills/iart-ai/video-delivery-specs`, `skills/ghost-editor/ghost-editor` (mục render report và QA).

### Bước 10. Giao file và báo cáo
- Lưu vào thư mục dự án người dùng chỉ định (mặc định `/mnt/project-files/<du-an>/` nếu có thư mục chung, không thì `./xuat/<du-an>/`):
  - `reel-<chu-de>.mp4` (H.264 8-bit, faststart)
  - `phu-de-<chu-de>.srt` (tối đa 8 chữ mỗi dòng)
  - Ảnh xem trước
  - Mã nguồn (không gồm `node_modules`, `cut.mp4`, `audio.wav`)
- Báo cáo: thời lượng, thời gian render đo được, dung lượng, LUFS, những gì đã sửa trong lời, những cụm còn chưa rõ, và 5 mốc nên nghe kiểm tra.

## Chế độ B: từ prompt hoặc kịch bản, giọng đọc AI (ElevenLabs)

Dùng khi không có video người nói. Đầu vào là một câu chủ đề hoặc một kịch bản. Đầu ra là Reel đồ hoạ toàn màn hình, giọng nhân bản của chủ kênh, phụ đề và đồ hoạ bám từng chữ như chế độ thường.

**Chuẩn bị một lần:**
- Người dùng tạo API key ở ElevenLabs (cần gói có Instant Voice Cloning) và thêm `ELEVENLABS_API_KEY` vào biến môi trường của môi trường làm việc.
- Mở mạng cho `api.elevenlabs.io`. Nếu bị chặn, hướng dẫn người dùng thêm vào Allowed domains, không vòng qua đường khác.
- Chỉ nhân bản giọng của chính người dùng hoặc người đã đồng ý bằng lời.

**Các bước:**
1. **Nhận việc:** điền `mau-tai-lieu/phieu-nhan-viec.md`, chọn chế độ B.
2. **Kịch bản:** nếu chỉ có prompt, viết theo `mau-tai-lieu/kich-ban-mau.md`.
   - Dài 120 đến 180 chữ cho video 45 đến 60 giây.
   - Câu ngắn, mỗi câu một ý, có con số.
   - Viết số theo cách đọc khi dễ đọc sai (`87 nghìn đô` thay cho `$87.000`).
   - Gửi kịch bản cho người dùng duyệt trước khi tạo giọng, vì mỗi lần tạo giọng đều tốn ký tự.
3. **Nhân bản giọng (lần đầu):**
   - Lấy 1 đến 3 phút nói sạch từ video cũ: `ffmpeg -i video-cu.mp4 -ss 10 -t 150 -vn -ac 1 -ar 44100 mau-giong.mp3`.
   - Chạy `python3 scripts/tts_elevenlabs.py clone --name "<tên kênh>" mau-giong.mp3`. Lệnh ghi `voice.json`; giữ file này cho các video sau.
4. **Tạo giọng:** `python3 scripts/tts_elevenlabs.py speak kichban.txt`.
   - Ra `voice.mp3` và `transcript.json` (mốc từng chữ, cùng định dạng Whisper), nên **bỏ qua bước 3 chép lời**.
   - Chỉnh giọng: `--speed 1.05`; `--stability 0.45` (thấp hơn thì cảm xúc hơn); `--model eleven_v3` nếu muốn biểu cảm hơn.
5. **Tạo video nền từ giọng:**
   - `ffmpeg -f lavfi -i color=c=0x050e24:s=1080x1920:r=30 -i voice.mp3 -shortest -c:v libx264 -tune stillimage -c:a aac voice.mp4`
   - Sau đó `python3 scripts/build.py voice.mp4`, như bước 7.
6. **Đồ hoạ:** vì không có người nói, beats phải **phủ gần hết thời lượng**.
   - Nối các cảnh: stat, list, levels, chart, title.
   - Mỗi cảnh 3 đến 8 giây.
   - Giữa hai cảnh không để trống quá 1 giây.
   - Vẫn neo `say` vào từ khoá như cũ.
7. **Render** với `--props='{"faceless":true}'`. Chế độ này ẩn khung video và bật nền đồ hoạ suốt video. Tiếng lấy từ `cut.mp4`, và render nhanh hơn vì không phải giải mã hình.
8. **Giao file** như bước 10, thêm `kichban.txt`, `voice.mp3` và số ký tự đã dùng.

**Lưu ý:**
- Giọng AI đọc sai tên riêng hoặc từ tiếng Anh. Sửa bằng cách viết lại theo cách đọc trong kịch bản (`ê tê ép` cho ETF nếu cần), không sửa trong `fix`.
- Giọng AI đều nhịp nên build.py gần như không cắt gì. Đó là bình thường.
- Không có mạng hoặc API key thì dừng lại, báo người dùng. Không thay bằng giọng khác khi chưa được đồng ý.

## Phong cách mặc định: BTC Daily

- **Màu:**
  - Nền `#050E24`, thẻ `#0B1B3F`, viền `#1D3566`.
  - Chủ đạo `#2F7BFF`, xanh sáng `#6CC4FF`, vàng hổ phách `#FFB547` cho con số.
  - `#22C38E` và `#FF5A6A` chỉ dùng cho tăng / giảm.
  - Tỉ lệ 60/25/10/5.
- **Chữ:** Be Vietnam Pro 600/800/900. Con số lớn 150px, tiêu đề cảnh 62px, phụ đề 64px.
- **Phụ đề Phát sáng** (mặc định `glow`):
  - Chữ thường, tối đa 2 dòng cân nhau, cụm tối đa 30 ký tự hoặc 8 từ.
  - Chưa đọc là xanh nhạt 72%, đã đọc là trắng, từ khoá là xanh sáng, con số là vàng.
  - Chữ đang đọc phát sáng, phóng to 8%, nhích lên 5px. Không gạch chân, không khung.
  - Tâm phụ đề ở y = 1420 (người nói toàn màn hình) hoặc 1520 (đang có đồ hoạ).
  - Phụ đề cao tối thiểu 48px, tương phản tối thiểu 3:1.
- **Bố cục:** chế độ C có đồ hoạ toàn màn hình và ô mặt 240 × 300 ở góc trên phải. Chế độ A có thẻ chủ đề góc trên trái. Chuyển chế độ trong 14 khung hình. Chuyển cảnh mờ dần kèm nhoè 8px, không quét sọc.
- **Đổi phong cách:** sửa `theme.ts`, danh sách `KEYWORDS` trong `Captions.tsx`, rồi cập nhật trang bộ nhận diện. Tham khảo `skills/iart-ai/brand-motion-guidelines` và `color-motion`.

## Việc gì thì mở skill nào

Đường dẫn tính từ `skills/` trong thư mục skill này. Các skill gốc viết cho máy Mac hoặc HyperFrames. Lấy nguyên tắc và công thức của chúng, còn lệnh thì điều chỉnh cho môi trường này.

| Việc | Skill |
|---|---|
| Reel người nói trọn gói, 7 phong cách, chọn take, meme | `ghost-editor/ghost-editor` |
| Quy trình dựng video người nói dài | `herk-edit-kit/edit-video`, `herk-edit-kit/hyperframes-video-beats` |
| Hook, vòng tò mò, nhịp giữ chân người xem | `herk-edit-kit/short-form-edit`, `iart-ai/iart-short-form-video`, `herk-edit-kit/video-storytelling` |
| Cắt lặng, cắt vấp và nói lại | `herk-edit-kit/cut-silences`, `herk-edit-kit/cut-mistakes` |
| Phụ đề theo từng từ | `iart-ai/caption-animation` |
| Đồ hoạ minh hoạ theo lời (b-roll) | `iart-ai/talking-head-b-roll`, `motion-graphics/motion-broll` |
| Biểu đồ, infographic, sơ đồ, bản đồ | `iart-ai/chart-animation`, `iart-ai/animated-infographic`, `iart-ai/diagram-animation`, `iart-ai/map-animation` |
| Chữ chuyển động, tiêu đề, thanh tên | `iart-ai/kinetic-typography`, `iart-ai/lower-thirds`, `iart-ai/tiktok-lower-thirds` |
| Âm thanh hiệu ứng, nhạc, cắt theo nhịp | `motion-graphics/sound-effects`, `iart-ai/soundtrack`, `iart-ai/beat-sync-editing` |
| Nguyên lý chuyển động, bố cục khung hình, màu | `iart-ai/animation-principles`, `iart-ai/shot-composition`, `iart-ai/color-motion`, `iart-ai/motion-art-direction` |
| Nền chuyển động, hạt, shader | `iart-ai/motion-background`, `iart-ai/particle-system`, `iart-ai/shader-glsl` |
| Video quảng cáo, khuyến mãi, ra mắt, cảm nhận khách hàng | `iart-ai/ad-creative-video`, `iart-ai/promo-video`, `iart-ai/launch-video`, `iart-ai/testimonial-video` |
| Video sản phẩm, demo phần mềm, explainer | `iart-ai/product-demo-video`, `iart-ai/explainer-video`, `motion-graphics/explainer-default`, `motion-graphics/explainer-engaging`, `motion-graphics/explainer-high-energy`, `video-shotcraft/video-shotcraft` |
| Slide thành video, ảnh thành video, podcast thành video | `iart-ai/presentation-video`, `iart-ai/photo-slideshow`, `iart-ai/audiogram` |
| Video đếm ngược, tin nhắn, tổng kết năm, intro/outro YouTube | `iart-ai/countdown-video`, `iart-ai/text-message-animation`, `iart-ai/wrapped-video`, `iart-ai/youtube-intro-outro` |
| Logo động, bộ quy tắc chuyển động thương hiệu | `iart-ai/logo-animation`, `iart-ai/brand-motion-guidelines` |
| Tách người khỏi nền | `motion-graphics/object-separation` |
| Remotion | `iart-ai/remotion-video` và plugin `remotion:*` |
| HyperFrames | `hyperframes/hyperframes`, `hyperframes/hyperframes-cli`, `hyperframes/hyperframes-registry`, `hyperframes/media-use`, `hyperframes/remotion-to-hyperframes` |
| GSAP | `gsap/gsap-core`, `gsap/gsap-timeline`, `gsap/gsap-plugins`, `iart-ai/gsap-web` |
| Thông số xuất, vùng an toàn từng nền tảng | `iart-ai/video-delivery-specs` |
| Làm dịch vụ: brief, báo giá, giới hạn sửa | `iart-ai/creative-brief`, `iart-ai/motion-pricing`, `iart-ai/client-revisions` |

Các skill còn lại (hoạt hình web, Three.js, Lottie, After Effects, Manim, ASCII...) xem trong `INDEX.md`.

## Lỗi đã gặp

- Tải model bị chặn dù huggingface.co mở: file nằm trên CDN `*.hf.co` và `*.xethub.hf.co`.
- `TypeError: open() got an unexpected keyword argument 'metadata_errors'`: truyền mảng numpy thay vì đường dẫn file.
- Whisper bịa một câu lặp dài 0,76 giây với 15 chữ cùng mốc thời gian: bỏ bằng `dropSegments`.
- Ba mốc giá hiện cùng lúc trước khi được nói: do dùng độ trễ cố định. Đã chuyển sang gắn `say`.
- Phụ đề viết hoa, từ nào cũng nhảy thì trông "gào". Chữ phóng to đè lên chữ bên cạnh: tăng khoảng cách chữ lên 22px.
- Dòng dưới chỉ còn 1 chữ: chia 2 dòng cân độ dài.
- Ô mặt người nói chỉ thấy mắt: giảm `PIP_SCALE` xuống 0,3.
