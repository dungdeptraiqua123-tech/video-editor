"""Chạy trong môi trường Python riêng (~/.video-editor/venv): dò khuôn mặt trong video bằng OpenCV (bộ dò Haar có sẵn trong gói,
không tải mô hình từ mạng), xuất vị trí mặt theo thời gian.

  python face_worker.py <video> <face-raw.json> [số khung mỗi giây, mặc định 4]

ffmpeg giải mã và thu nhỏ sẵn thành ảnh xám 480 px, đưa qua ống dẫn; worker chỉ dò mặt nên chạy nhanh và ít RAM.
Kết quả: {"fps", "w", "h", "samples": [[t, [[x, y, w, h], ...]], ...]} với toạ độ tỉ lệ 0–1 của khung gốc.
"""
import json
import subprocess
import sys
import time


def main():
    src, out = sys.argv[1], sys.argv[2]
    fps = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0
    import cv2
    import numpy as np

    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", src],
                        capture_output=True, text=True, check=True)
    sw, sh = (int(x) for x in pr.stdout.strip().split(",")[:2])
    W = 480 if sw >= sh else 320
    H = int(round(sh * W / sw / 2) * 2)
    front = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    side = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
    if front.empty():
        print("CASCADE_ERROR", file=sys.stderr)
        sys.exit(3)
    min_side = max(24, int(min(W, H) * 0.08))
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-an", "-sn", "-vf", f"fps={fps},scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                          stdout=subprocess.PIPE)
    size = W * H
    samples, i, t0 = [], 0, time.time()
    while True:
        buf = ff.stdout.read(size)
        if len(buf) < size:
            break
        img = cv2.equalizeHist(np.frombuffer(buf, np.uint8).reshape(H, W))
        boxes = list(front.detectMultiScale(img, scaleFactor=1.1, minNeighbors=6, minSize=(min_side, min_side)))
        if not boxes:
            boxes = list(side.detectMultiScale(img, scaleFactor=1.1, minNeighbors=6, minSize=(min_side, min_side)))
            if not boxes:
                # mặt nghiêng sang phía kia: lật ảnh rồi dò lại
                fl = side.detectMultiScale(cv2.flip(img, 1), scaleFactor=1.1, minNeighbors=6, minSize=(min_side, min_side))
                boxes = [(W - x - w, y, w, h) for x, y, w, h in fl]
        samples.append([round(i / fps, 3), [[round(x / W, 4), round(y / H, 4), round(w / W, 4), round(h / H, 4)] for x, y, w, h in boxes]])
        i += 1
    ff.wait()
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"fps": fps, "w": sw, "h": sh, "samples": samples}, f)
    hit = sum(1 for _, b in samples if b)
    print(f"dò mặt {len(samples)} khung trong {time.time() - t0:.1f}s, thấy mặt ở {hit} khung", flush=True)


if __name__ == "__main__":
    main()
