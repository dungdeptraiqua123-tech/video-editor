"""Chạy trong môi trường Python riêng (~/.video-editor/venv): chép lời bằng faster-whisper, xuất transcript.json.

  python whisper_worker.py <audio.wav 16k mono> <transcript.json> <model> <ngôn ngữ> [--download-only]
"""
import json
import os
import sys
import time
import wave


def main():
    wav, out, model, lang = sys.argv[1:5]
    from faster_whisper import WhisperModel

    threads = max(1, min(8, os.cpu_count() or 4))
    t0 = time.time()
    try:
        m = WhisperModel(model, device="cpu", compute_type="int8", cpu_threads=threads)
    except Exception as e:  # thường là mạng chặn Hugging Face hoặc hết chỗ
        print(f"MODEL_ERROR {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(3)
    print(f"mô hình {model} sẵn sàng sau {time.time() - t0:.0f}s", flush=True)
    if "--download-only" in sys.argv:
        return
    import numpy as np

    # đọc wav bằng numpy thay vì để faster-whisper gọi PyAV (PyAV 19 lỗi metadata_errors)
    wf = wave.open(wav)
    audio = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
    total = len(audio) / 16000
    segs, _ = m.transcribe(audio, language=lang, word_timestamps=True, beam_size=5, vad_filter=True)
    res = []
    for s in segs:
        res.append({"start": s.start, "end": s.end, "text": s.text, "words": [{"w": w.word, "s": w.start, "e": w.end, "p": w.probability} for w in (s.words or [])]})
        print(f"[{100 * s.end / total:5.1f}%] {s.start:7.2f}s {s.text.strip()}", flush=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(f"xong {len(res)} đoạn trong {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
