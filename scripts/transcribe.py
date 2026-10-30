from faster_whisper import WhisperModel
import json, wave, numpy as np
wf=wave.open("audio.wav");audio=np.frombuffer(wf.readframes(wf.getnframes()),np.int16).astype(np.float32)/32768
m=WhisperModel("large-v3",device="cpu",compute_type="int8",cpu_threads=4)
segs,info=m.transcribe(audio,language="vi",word_timestamps=True,beam_size=5,vad_filter=True)
out=[]
for s in segs:
    out.append({"start":s.start,"end":s.end,"text":s.text,"words":[{"w":w.word,"s":w.start,"e":w.end,"p":w.probability} for w in s.words]})
    print(f"[{s.start:.2f}-{s.end:.2f}] {s.text}",flush=True)
json.dump(out,open("transcript.json","w"),ensure_ascii=False,indent=1)
