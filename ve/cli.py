"""video-editor: công cụ điều phối dựng video ngắn.

  video-editor doctor                      kiểm tra môi trường
  video-editor setup [--model nhe|vua|nang|nhanh]   cài môi trường và các skill liên quan (một lần)
  video-editor skills [install|remove]     cài/gỡ 93 skill liên quan thành skill riêng
  video-editor init <dự án> --input video.mp4 | --script kichban.txt [--format 9:16] [--template trung-tinh]
  video-editor transcribe <dự án>          chép lời (hoặc --from-srt / --from-json)
  video-editor tts <dự án> [--placeholder] giọng đọc cho kịch bản
  video-editor build <dự án> [--check]     cắt + dò mốc đồ hoạ + kiểm tra
  video-editor preview <dự án> [--seed N]  storyboard ảnh ngẫu nhiên có tiêu đề để người dùng duyệt
  video-editor approve <dự án>             ghi nhận đã duyệt storyboard (render chỉ chạy sau bước này)
  video-editor render <dự án>              render MP4
  video-editor export <dự án>              tự kiểm tra khung hình, phụ đề SRT/VTT, ảnh bìa, bảng quy chiếu, báo cáo
  video-editor run <dự án>                 làm tiếp mọi bước còn thiếu (dừng chờ duyệt storyboard)
  video-editor rules <dự án> [--add ...]   quy tắc riêng của video này
  video-editor note "góp ý" [--project]    ghi nhớ góp ý để áp dụng cho các video sau
  video-editor shorts <dự án dài> [--so 8]  đề xuất các đoạn 25–60 giây hay nhất để cắt thành short
  video-editor shorts <dự án dài> --tao 1,3  tạo mỗi đoạn thành một dự án short (dùng lại lời thoại)
  video-editor mau <video mẫu> [--project <dự án>] [--ap-dung]  phân tích video mẫu: nhịp cắt, tốc độ nói, câu mở, ảnh kiểu phụ đề
  video-editor status <dự án>
"""
from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ve import media as M  # noqa: E402
from ve.env import SKILL_DIR, TEMPLATES, VEError, info, read_json, run, venv_python, warn, write_json  # noqa: E402
from ve import notes  # noqa: E402
from ve.notes import KINDS as NOTE_KINDS  # noqa: E402
from ve.project import FORMATS, GRAPHICS_EVERY, PACES, Project, fingerprint, init_project, rules_text  # noqa: E402


def cmd_transcribe(prj: Project, force=False, from_srt=None, from_json=None) -> None:
    from ve.build import write_transcript_text
    from ve.doctor import model_cached, resolve_model
    from ve.subs import parse_srt

    out = prj.work / "transcript.json"
    if from_srt or from_json:
        segs = parse_srt(Path(from_srt).read_text(encoding="utf-8-sig")) if from_srt else read_json(Path(from_json))
        if not any(s.get("words") for s in segs):
            raise VEError("File lời thoại không có chữ nào.")
        write_json(out, segs)
        prj.mark("transcribe", fingerprint(Path(from_srt or from_json)), source="import")
        prj.invalidate("build", "render", "export")
        info(f"✓ nhập {len(segs)} đoạn lời thoại → {write_transcript_text(prj)}")
        return
    if prj.cfg.get("script"):
        raise VEError("Dự án này đi từ kịch bản.", f"Dùng `video-editor tts {prj.root}` thay cho transcribe.")
    src = prj.path(prj.cfg["input"])
    pi = M.probe(src)
    M.check_audio(pi)
    model = resolve_model(prj.cfg["whisper"].get("model"))
    lang = prj.cfg["whisper"].get("language", "vi")
    fp = fingerprint(src, model, lang)
    if not force and prj.fresh("transcribe", fp) and out.exists():
        info("✓ lời thoại còn mới, dùng lại")
        return
    vp = venv_python()
    if not vp.exists():
        raise VEError("Chưa cài môi trường chép lời.", "Chạy `video-editor setup`.")
    if not model_cached(model):
        info(f"(lần đầu: tải mô hình {model}, có thể mất vài phút)")
    wav = prj.work / "audio.wav"
    M.extract_wav(src, wav)
    info(f"🎙 chép lời {pi['duration']:.0f}s bằng Whisper {model} …")
    t0 = time.time()
    p = run([vp, SKILL_DIR / "ve" / "whisper_worker.py", wav, out, model, lang], check=False)
    if p.returncode == 3:
        raise VEError("Không tải hoặc mở được mô hình Whisper.",
                      "Mạng có thể chặn Hugging Face: mở huggingface.co, *.hf.co, *.xethub.hf.co (Claude cloud: Project settings → Cloud environment → Network access). "
                      "Phương án thay thế: xuất phụ đề .srt từ CapCut rồi `video-editor transcribe <dự án> --from-srt file.srt`. Máy yếu: `setup --model nhe`.")
    if p.returncode != 0:
        raise VEError("Chép lời bị lỗi.", "Xem thông báo phía trên. Thử lại với mô hình nhẹ hơn: đặt whisper.model = \"nhe\" trong project.json.")
    segs = read_json(out)
    n = sum(len(s.get("words", [])) for s in segs)
    if n == 0:
        raise VEError("Không nhận diện được lời nói nào.", "Kiểm tra ngôn ngữ (whisper.language), âm lượng, hoặc file có phải chỉ có nhạc nền không.")
    wav.unlink(missing_ok=True)
    prj.mark("transcribe", fp, seconds=round(time.time() - t0), model=model)
    prj.invalidate("build", "render", "export")
    info(f"✓ {n} từ, {len(segs)} đoạn → {write_transcript_text(prj)}")


def cmd_tts(prj: Project, force=False, placeholder=False) -> None:
    from ve import tts
    from ve.build import write_transcript_text

    sp = prj.path(prj.cfg.get("script"))
    if not sp or not sp.exists():
        raise VEError("Dự án không có kịch bản (script).", "Dự án từ video người nói dùng `transcribe`.")
    text = tts.clean_script(sp.read_text(encoding="utf-8"))
    if len(text) < 20:
        raise VEError("Kịch bản quá ngắn.")
    voice = prj.cfg.get("voice", {})
    use_ph = placeholder or voice.get("provider") == "placeholder"
    fp = fingerprint(text, voice, use_ph)
    out = prj.work / "transcript.json"
    if not force and prj.fresh("tts", fp) and out.exists():
        info("✓ giọng đọc còn mới, dùng lại")
        return
    for old in ("voice.mp3", "voice.m4a"):
        (prj.work / old).unlink(missing_ok=True)
    if use_ph:
        segs = tts.placeholder(text, prj.work / "voice.m4a")
        info("🔇 giọng tạm (im lặng) để duyệt bố cục, chưa tốn ký tự ElevenLabs")
    else:
        if voice.get("provider") not in ("elevenlabs", None):
            raise VEError(f"Nhà cung cấp giọng \"{voice.get('provider')}\" chưa hỗ trợ.", "Dùng \"elevenlabs\" hoặc \"placeholder\".")
        info(f"🗣 ElevenLabs đọc {len(text)} ký tự …")
        segs = tts.speak(text, voice, prj.work / "voice.mp3")
    write_json(out, segs)
    prj.mark("tts", fp, chars=len(text), placeholder=use_ph)
    prj.mark("transcribe", fp)
    prj.invalidate("build", "render", "export")
    info(f"✓ {sum(len(s['words']) for s in segs)} từ → {write_transcript_text(prj)}")


def cmd_status(prj: Project) -> None:
    st = prj.state()
    first = "tts" if prj.cfg.get("script") else "transcribe"
    for s in [first, "build", "render", "export"]:
        x = st.get(s)
        info(f" {'✓' if x else '○'} {s}" + (f"  ({x['at']})" if x else ""))
    if (prj.work / "check.json").exists():
        c = read_json(prj.work / "check.json")
        info(f" kiểm tra gần nhất: {len(c['errors'])} lỗi, {len(c['warnings'])} cảnh báo")


def cmd_run(prj: Project, force=False, until: str | None = None, placeholder=False) -> None:
    from ve.build import build
    from ve.render import export, render

    steps = [("tts" if prj.cfg.get("script") else "transcribe"), "build", "preview", "render", "export"]
    for s in steps:
        info(f"── {s}")
        if s == "preview":
            from ve.storyboard import data_fp, preview

            fp = data_fp(prj.work / "data.json")
            if prj.fresh("approve", fp):
                info("✓ storyboard đã được duyệt")
                continue
            if not prj.fresh("preview", fp):
                preview(prj)
            info(f"⏸ Dừng chờ duyệt storyboard (out/storyboard.jpg). Người dùng đồng ý thì `video-editor approve {prj.root}` rồi chạy lại `video-editor run {prj.root}`.")
            return
        if s == "transcribe":
            cmd_transcribe(prj, force)
        elif s == "tts":
            cmd_tts(prj, force, placeholder)
        elif s == "build":
            build(prj, force)
        elif s == "render":
            render(prj, force)
        elif s == "export":
            export(prj)
        if until and s == until:
            info(f"dừng sau bước {s} theo yêu cầu")
            return


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="video-editor", description="Dựng video ngắn từ video người nói hoặc kịch bản.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("doctor", help="kiểm tra môi trường")
    d.add_argument("--json", action="store_true")
    d.add_argument("--offline", action="store_true", help="không thử kết nối mạng")
    s = sub.add_parser("setup", help="cài môi trường (một lần)")
    s.add_argument("--model", help="mô hình Whisper: nhe (small), vua (medium), nang (large-v3), nhanh (large-v3-turbo)")
    s.add_argument("--skip-model", action="store_true")
    s.add_argument("--install-system", action="store_true", help="tự cài ffmpeg/Node bằng brew hoặc winget nếu thiếu")
    s.add_argument("--no-skills", action="store_true", help="không cài các skill liên quan trong reference/")
    s.add_argument("--skills-dir", help="thư mục skills đích (mặc định: thư mục đang chứa video-editor, hoặc ~/.claude/skills)")
    k = sub.add_parser("skills", help="cài, gỡ, xem các skill liên quan (93 skill trong reference/)")
    k.add_argument("action", nargs="?", default="status", choices=["status", "install", "remove"])
    k.add_argument("--dir", help="thư mục skills đích (mặc định: thư mục đang chứa video-editor, hoặc ~/.claude/skills)")
    k.add_argument("--only", help="chỉ cài các bộ này, cách nhau dấu phẩy, ví dụ gsap,hyperframes")
    i = sub.add_parser("init", help="tạo thư mục dự án")
    i.add_argument("dir")
    i.add_argument("--input", help="video hoặc âm thanh người nói")
    i.add_argument("--script", help="kịch bản (.txt) để đọc bằng giọng AI")
    i.add_argument("--background", help="video/ảnh nền cho video không người nói (vd. cảnh quay sản phẩm)")
    i.add_argument("--format", default="9:16", choices=list(FORMATS))
    i.add_argument("--template", default="trung-tinh")
    i.add_argument("--type", choices=["talking-head", "explainer", "product"])
    i.add_argument("--voice", choices=["elevenlabs", "placeholder"])
    i.add_argument("--name")
    i.add_argument("--pace", choices=list(PACES), help="nhịp dựng: nhanh, vua (mặc định), cham")
    i.add_argument("--graphics", choices=list(GRAPHICS_EVERY), help="mật độ đồ hoạ: it, vua (mặc định), nhieu")
    i.add_argument("--rule", action="append", default=[], help="quy tắc riêng cho video này (lặp lại được), không áp dụng cho video khác")
    sub.add_parser("templates", help="liệt kê mẫu nhận diện")
    r = sub.add_parser("rules", help="xem/thêm quy tắc riêng của một video")
    r.add_argument("dir")
    r.add_argument("--add", action="append", default=[], help="thêm quy tắc (lặp lại được)")
    r.add_argument("--remove", type=int, action="append", default=[], help="xoá quy tắc số N")
    n = sub.add_parser("note", help="ghi nhớ góp ý của người dùng để áp dụng cho các video sau")
    n.add_argument("text")
    n.add_argument("--project", help="dự án nhận góp ý (ghi tên kèm theo)")
    n.add_argument("--loai", default="khac", choices=NOTE_KINDS)
    sub.add_parser("notes", help="xem ghi nhớ góp ý")
    ap_ = sub.add_parser("approve", help="ghi nhận người dùng đã duyệt storyboard (sau đó mới render được)")
    ap_.add_argument("dir")
    ap_.add_argument("--note", default="", help="ghi chú của người duyệt")
    q = sub.add_parser("qa", help="tự kiểm tra khung hình video đã render")
    q.add_argument("dir")
    sh = sub.add_parser("shorts", help="cắt video dài thành nhiều short: đề xuất đoạn hay, tạo dự án cho từng đoạn")
    sh.add_argument("dir", help="dự án của video dài (đã chép lời)")
    sh.add_argument("--so", type=int, default=8, help="số đoạn đề xuất (mặc định 8)")
    sh.add_argument("--min", type=float, default=25, help="độ dài ngắn nhất, giây (mặc định 25)")
    sh.add_argument("--max", type=float, default=60, help="độ dài dài nhất, giây (mặc định 60)")
    sh.add_argument("--tao", help="tạo dự án cho các đoạn: số thứ tự trong đề xuất (1,3) hoặc mốc giây gốc (35.4-69)")
    sh.add_argument("--vao", help="thư mục chứa các dự án short (mặc định <dự án dài>/shorts)")
    mp = sub.add_parser("mau", aliases=["ref"], help="phân tích video mẫu (file trên máy): nhịp đổi cảnh, tốc độ nói, quãng nghỉ, câu mở đầu → gợi ý nhịp")
    mp.add_argument("video", help="đường dẫn video mẫu trên máy")
    mp.add_argument("--project", help="dự án sẽ dựng theo mẫu: lưu phân tích vào work/mau/ và ghi style.reference")
    mp.add_argument("--ap-dung", action="store_true", help="ghi luôn nhịp, mật độ đồ hoạ, mức cắt lặng gợi ý vào dự án (cần --project)")
    mp.add_argument("--ra", help="thư mục ghi kết quả khi không có --project (mặc định ./phan-tich-mau/<tên video>)")
    mp.add_argument("--khong-loi", action="store_true", help="bỏ phần chép lời (nhanh hơn, không có số đo tốc độ nói)")
    mp.add_argument("--ngon-ngu", default="vi", help="ngôn ngữ lời nói trong video mẫu (mặc định vi)")
    mp.add_argument("--toi-da", type=float, default=180, help="chỉ chép lời bấy nhiêu giây đầu (mặc định 180)")

    for name, hlp in [("transcribe", "chép lời"), ("tts", "giọng đọc cho kịch bản"), ("build", "cắt, dò mốc, kiểm tra"), ("check", "chỉ kiểm tra nội dung"),
                      ("preview", "storyboard để người dùng duyệt"), ("render", "render video"), ("export", "tự kiểm tra, phụ đề, ảnh bìa, báo cáo"), ("run", "làm tiếp mọi bước"), ("status", "trạng thái")]:
        p = sub.add_parser(name, help=hlp)
        p.add_argument("dir")
        if name in ("transcribe", "tts", "build", "render", "run"):
            p.add_argument("--force", action="store_true", help="làm lại kể cả khi đầu vào không đổi")
        if name == "transcribe":
            p.add_argument("--from-srt")
            p.add_argument("--from-json")
        if name in ("tts", "run"):
            p.add_argument("--placeholder", action="store_true", help="giọng tạm im lặng để duyệt bố cục")
        if name == "preview":
            p.add_argument("--draft", action="store_true", help="kèm bản nháp nửa độ phân giải")
            p.add_argument("--seed", type=int, help="đổi bộ ảnh ngẫu nhiên")
        if name == "run":
            p.add_argument("--until", choices=["transcribe", "tts", "build", "preview", "render", "export"])
    v = sub.add_parser("voices", help="liệt kê giọng ElevenLabs trong tài khoản")
    v.add_argument("--json", action="store_true")
    c = sub.add_parser("clone-voice", help="nhân bản giọng (ElevenLabs Starter trở lên)")
    c.add_argument("files", nargs="+")
    c.add_argument("--name", required=True)
    c.add_argument("--project", help="ghi voiceId vào project.json của dự án này")

    a = ap.parse_args(argv)
    try:
        if a.cmd == "doctor":
            from ve.doctor import doctor

            return doctor(a.json, not a.offline)
        if a.cmd == "setup":
            from ve.doctor import setup

            return setup(a.model, a.skip_model, a.install_system, not a.no_skills, a.skills_dir)
        if a.cmd == "skills":
            from ve.env import has_related_skills

            if not has_related_skills():
                raise VEError("Bản này là bản gọn, không kèm các skill liên quan.", "Muốn cài 93 skill liên quan: clone bản đầy đủ từ repo rồi chạy `video-editor skills install`.")
            from ve import skills as SK

            if a.action == "install":
                SK.install(a.dir, [x.strip() for x in a.only.split(",") if x.strip()] if a.only else None)
            elif a.action == "remove":
                SK.remove(a.dir)
            else:
                st = SK.status(a.dir)
                info(f"{st['installed']}/{st['total']} skill liên quan đã cài trong {st['dir']}")
                if st["conflicts"]:
                    info(f"  trùng tên skill có sẵn (không ghi đè): {', '.join(st['conflicts'])}")
                if st["installed"] < st["total"] - len(st["conflicts"]):
                    info("  → video-editor skills install")
            return 0
        if a.cmd == "templates":
            for t in sorted(TEMPLATES.iterdir()):
                if (t / "brand.json").exists():
                    info(f" {t.name}: {read_json(t / 'brand.json').get('name', '')}")
            return 0
        if a.cmd == "init":
            prj = init_project(Path(a.dir), a.input, a.script, a.format, a.template, a.type, a.background, a.name, a.voice, a.pace, a.graphics, a.rule)
            if a.input and not a.script:
                pi = M.probe(prj.path(prj.cfg["input"]))
                info(f"nguồn: {pi['duration']:.1f}s" + (f", {pi['width']}×{pi['height']}" if pi.get("has_video") else ", chỉ âm thanh"))
                M.check_audio(pi)
            st = prj.cfg["style"]
            info(f"✓ tạo dự án {prj.root} ({prj.cfg['type']}, {prj.cfg['format']}, mẫu {prj.cfg['template']}, nhịp {st['pace']}, đồ hoạ {st['graphics']})")
            if rules_text(prj.cfg):
                info(rules_text(prj.cfg))
            notes.show()
            info(f"  bước tiếp: video-editor {'tts' if a.script else 'transcribe'} {prj.root}")
            return 0
        if a.cmd == "note":
            notes.add(a.text, Project(Path(a.project)).cfg.get("name", "") if a.project else "", a.loai)
            return 0
        if a.cmd == "notes":
            if not notes.entries():
                info(f"Chưa có góp ý nào ({notes.path()}).")
            notes.show(limit=1000)
            return 0
        if a.cmd == "voices":
            from ve import tts

            vs = tts.voices()
            if a.json:
                print(__import__("json").dumps(vs, ensure_ascii=False, indent=1))
            else:
                for x in vs:
                    lab = ", ".join(f"{k}: {v}" for k, v in (x["labels"] or {}).items())
                    info(f" {x['id']}  {x['name']}  [{x['category']}] {lab}")
            return 0
        if a.cmd == "clone-voice":
            from ve import tts

            vid = tts.clone(a.name, [Path(f) for f in a.files])
            info(f"✓ voiceId {vid}")
            if a.project:
                prj = Project(Path(a.project))
                prj.cfg["voice"]["voiceId"] = vid
                prj.cfg["voice"]["provider"] = "elevenlabs"
                prj.save()
                info(f"  đã ghi vào {prj.file}")
            return 0

        if a.cmd in ("mau", "ref"):
            from ve import mau as MAU

            if a.ap_dung and not a.project:
                raise VEError("--ap-dung cần --project.", "Ví dụ: `video-editor mau mau.mp4 --project du-an --ap-dung`.")
            name = MAU._slug(Path(a.video).stem)
            prj = Project(Path(a.project)) if a.project else None
            work = prj.work / "mau" / name if prj else (Path(a.ra) if a.ra else Path.cwd() / "phan-tich-mau" / name).resolve()
            r = MAU.analyze(a.video, work, a.ngon_ngu, not a.khong_loi, a.toi_da)
            sg = r["suggest"]
            info(f"✓ phân tích xong → {work / 'phan-tich.md'}")
            info(f"  gợi ý: nhịp {MAU.PACE_LABEL[sg['pace']]}, đồ hoạ {MAU.GRAPHICS_LABEL[sg['graphics']]}" + (f", cắt lặng từ {sg['gap']:.2f}s" if sg["gap"] else ""))
            for w_ in sg["why"]:
                info(f"   · {w_}")
            info(f"  ảnh: {r['images']['toan-canh']} · {r['images']['mo-dau']}")
            if prj:
                rel = str((work / "phan-tich.md").relative_to(prj.root))
                for c in MAU.apply(prj, r, rel, a.ap_dung):
                    info(f"  ghi {c}")
                if not a.ap_dung:
                    info(f"  Hỏi người dùng có theo gợi ý không, đồng ý thì chạy lại với --ap-dung (hoặc sửa project.json).")
            return 0

        prj = Project(Path(a.dir))
        if a.cmd in ("build", "preview", "render", "export", "run", "qa") and rules_text(prj.cfg):
            info(rules_text(prj.cfg))
        if a.cmd == "rules":
            rs = [x for x in prj.cfg.get("rules") or []]
            for k in sorted(set(a.remove), reverse=True):
                if not 1 <= k <= len(rs):
                    raise VEError(f"Không có quy tắc số {k}.", f"Đang có {len(rs)} quy tắc.")
                rs.pop(k - 1)
            rs += [x.strip() for x in a.add if x.strip()]
            if a.add or a.remove:
                prj.cfg["rules"] = rs
                prj.save()
            info(rules_text(prj.cfg) or "Video này chưa có quy tắc riêng.")
            return 0
        if a.cmd == "shorts":
            from ve import shorts as SH
            from ve.bang import clock

            if a.tao:
                SH.make(prj, a.tao, Path(a.vao).resolve() if a.vao else None)
                return 0
            res = SH.suggest(prj, a.so, a.min, a.max)
            info(f"✂ {len(res)} đoạn đề xuất (điểm 0–100) → {prj.work / 'de-xuat-short.md'}")
            for r in res:
                info(f"  {r['i']:>2}. {clock(r['start'])}–{clock(r['end'])} {r['duration']:>3.0f}s  {r['score']:>3.0f} điểm  {r['title']}")
            info(f"  Đọc lại từng đoạn trong de-xuat-short.md, bỏ đoạn lạc đề, gửi người dùng chọn. Tạo dự án: `video-editor shorts {prj.root} --tao 1,3`.")
            return 0
        if a.cmd == "approve":
            from ve.storyboard import approve

            approve(prj, a.note)
            return 0
        if a.cmd == "qa":
            from ve.storyboard import qa

            final = prj.out / f"{prj.slug}.mp4"
            if not final.exists():
                raise VEError("Chưa có video.", f"Chạy `video-editor render {prj.root}` trước.")
            qa(prj, final)
            return 0
        if a.cmd == "transcribe":
            cmd_transcribe(prj, a.force, a.from_srt, a.from_json)
        elif a.cmd == "tts":
            cmd_tts(prj, a.force, a.placeholder)
        elif a.cmd in ("build", "check"):
            from ve.build import build

            build(prj, getattr(a, "force", False), check_only=a.cmd == "check")
        elif a.cmd == "preview":
            from ve.storyboard import preview

            preview(prj, a.draft, a.seed)
        elif a.cmd == "render":
            from ve.render import render

            render(prj, a.force)
        elif a.cmd == "export":
            from ve.render import export

            export(prj)
        elif a.cmd == "run":
            cmd_run(prj, a.force, a.until, a.placeholder)
        elif a.cmd == "status":
            cmd_status(prj)
        return 0
    except VEError as e:
        print(f"\n✗ {e.what}", file=sys.stderr)
        if e.fix:
            print(f"  → {e.fix}", file=sys.stderr)
        return e.code
    except KeyboardInterrupt:
        print("\nĐã dừng. Chạy lại cùng lệnh để làm tiếp từ bước còn dở.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
