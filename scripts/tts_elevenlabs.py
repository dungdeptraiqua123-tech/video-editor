"""Giọng đọc ElevenLabs cho chế độ "từ kịch bản".

  clone  : nhân bản giọng từ file mẫu, lưu voice_id vào voice.json
           python3 tts_elevenlabs.py clone --name "ivi" mau1.mp3 mau2.mp3
  speak  : đọc kịch bản, xuất voice.mp3 + transcript.json (cùng định dạng transcribe.py)
           python3 tts_elevenlabs.py speak kichban.txt
  voices : liệt kê giọng trong tài khoản

Cần biến môi trường ELEVENLABS_API_KEY và mạng mở cho api.elevenlabs.io.
Chỉ dùng thư viện chuẩn, không cần pip install.
"""
import argparse, base64, json, mimetypes, os, re, sys, uuid, urllib.request

API = "https://api.elevenlabs.io/v1"
# model hỗ trợ tiếng Việt và trả mốc thời gian; đổi bằng --model (vd. eleven_flash_v2_5, eleven_v3)
MODEL = "eleven_turbo_v2_5"


def key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k:
        sys.exit("Thiếu ELEVENLABS_API_KEY trong biến môi trường.")
    return k


def call(path, body=None, ctype="application/json", method=None):
    req = urllib.request.Request(API + path, data=body, method=method or ("POST" if body else "GET"))
    req.add_header("xi-api-key", key())
    if body is not None:
        req.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs {e.code}: {e.read().decode(errors='ignore')[:500]}")


def clone(a):
    b = uuid.uuid4().hex
    parts = []
    def field(name, val):
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{val}\r\n'.encode())
    field("name", a.name)
    field("remove_background_noise", "true")
    for f in a.files:
        mt = mimetypes.guess_type(f)[0] or "audio/mpeg"
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="files"; filename="{os.path.basename(f)}"\r\nContent-Type: {mt}\r\n\r\n'.encode())
        parts.append(open(f, "rb").read() + b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    r = call("/voices/add", b"".join(parts), f"multipart/form-data; boundary={b}")
    json.dump({"voice_id": r["voice_id"], "name": a.name}, open(a.out, "w"), ensure_ascii=False, indent=1)
    print("voice_id", r["voice_id"], "->", a.out)


def to_transcript(chars, starts, ends):
    """Mốc theo ký tự -> từ -> câu, đúng định dạng transcript.json của transcribe.py."""
    words, cur = [], None
    for c, s, e in zip(chars, starts, ends):
        if c.isspace():
            cur = None
            continue
        if cur is None:
            cur = {"w": "", "s": s, "e": e, "p": 1.0}
            words.append(cur)
        cur["w"] += c
        cur["e"] = e
    segs, seg = [], []
    for w in words:
        seg.append(w)
        if re.search(r"[.!?…]$", w["w"]):
            segs.append(seg); seg = []
    if seg:
        segs.append(seg)
    return [{"start": s[0]["s"], "end": s[-1]["e"], "text": " " + " ".join(w["w"] for w in s),
             "words": [dict(w, w=" " + w["w"]) for w in s]} for s in segs]


def speak(a):
    if not a.voice and not os.path.exists("voice.json"):
        sys.exit("Chưa có giọng: chạy clone trước hoặc truyền --voice <voice_id>.")
    vid = a.voice or json.load(open("voice.json"))["voice_id"]
    text = re.sub(r"\s+", " ", open(a.script, encoding="utf-8").read()).strip()
    body = {"text": text, "model_id": a.model, "language_code": "vi",
            "voice_settings": {"stability": a.stability, "similarity_boost": 0.85, "style": a.style, "use_speaker_boost": True, "speed": a.speed}}
    if a.model == "eleven_v3":
        body.pop("language_code")
    r = call(f"/text-to-speech/{vid}/with-timestamps?output_format=mp3_44100_192", json.dumps(body).encode())
    open(a.audio, "wb").write(base64.b64decode(r["audio_base64"]))
    al = r.get("alignment") or r["normalized_alignment"]
    t = to_transcript(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"])
    json.dump(t, open("transcript.json", "w"), ensure_ascii=False, indent=1)
    for s in t:
        print(f"[{s['start']:.2f}-{s['end']:.2f}]{s['text']}")
    print(f"{len(text)} ký tự -> {a.audio}, transcript.json ({sum(len(s['words']) for s in t)} từ)", file=sys.stderr)


def voices(a):
    for v in call("/voices")["voices"]:
        print(v["voice_id"], v["name"], v.get("category", ""))


ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
c = sub.add_parser("clone"); c.add_argument("--name", required=True); c.add_argument("--out", default="voice.json"); c.add_argument("files", nargs="+")
s = sub.add_parser("speak"); s.add_argument("script"); s.add_argument("--voice"); s.add_argument("--model", default=MODEL)
s.add_argument("--audio", default="voice.mp3"); s.add_argument("--stability", type=float, default=0.45)
s.add_argument("--style", type=float, default=0.2); s.add_argument("--speed", type=float, default=1.05)
sub.add_parser("voices")
a = ap.parse_args()
{"clone": clone, "speak": speak, "voices": voices}[a.cmd](a)
