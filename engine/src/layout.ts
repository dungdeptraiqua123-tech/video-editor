/**
 * Bố cục theo khổ hình. Mỗi khổ có vùng an toàn riêng (tránh nút bấm và chữ của nền tảng),
 * vị trí ô mặt người nói, vùng đồ hoạ, vị trí phụ đề. Đồ hoạ được vẽ trên khung thiết kế 940 × 880
 * rồi thu phóng vừa vùng đồ hoạ, nên cùng một nội dung chạy được trên mọi khổ.
 */
export type Rect = { x: number; y: number; w: number; h: number };

export type Layout = {
  w: number;
  h: number;
  /** Hệ số cỡ chữ chung (phụ đề, thẻ chủ đề, mở đầu). */
  u: number;
  pip: Rect & { r: number };
  panel: Rect;
  head: { x: number; y: number; w: number };
  topic: { x: number; y: number; maxW: number };
  /** Tâm phụ đề (px): khi người nói toàn màn hình, khi hiện đồ hoạ, khi không người nói và không đồ hoạ. */
  capTalk: number;
  capGfx: number;
  capCenter: number;
  capSide: number;
  hookTop: number;
  outroTop: number;
  /** Vị trí mắt người nói mong muốn trong khung (tỉ lệ chiều cao). */
  eyeLine: number;
  maxChars: number;
};

export const DESIGN = { w: 940, h: 880 };

export const layoutFor = (w: number, h: number): Layout => {
  const r = w / h;
  if (r > 1.3) {
    // 16:9 ngang (YouTube, Facebook feed)
    return {
      w, h, u: 0.95,
      pip: { x: w - 120 - 360, y: 110, w: 360, h: 440, r: 30 },
      panel: { x: 120, y: 190, w: 1200, h: 720 },
      head: { x: 120, y: 70, w: 1100 },
      topic: { x: 60, y: 60, maxW: 860 },
      capTalk: h - 170, capGfx: h - 130, capCenter: h * 0.5, capSide: 160,
      hookTop: 110, outroTop: 260, eyeLine: 0.38, maxChars: 44,
    };
  }
  if (r > 0.9) {
    // 1:1 vuông
    return {
      w, h, u: 0.85,
      pip: { x: w - 50 - 200, y: 50, w: 200, h: 250, r: 26 },
      panel: { x: 70, y: 310, w: 940, h: 530 },
      head: { x: 60, y: 60, w: 700 },
      topic: { x: 40, y: 40, maxW: 760 },
      capTalk: h - 190, capGfx: h - 150, capCenter: h * 0.5, capSide: 70,
      hookTop: 80, outroTop: 180, eyeLine: 0.4, maxChars: 30,
    };
  }
  if (r > 0.7) {
    // 4:5 (bài đăng dọc trên feed)
    return {
      w, h, u: 0.9,
      pip: { x: w - 50 - 230, y: 60, w: 230, h: 280, r: 28 },
      panel: { x: 70, y: 360, w: 940, h: 700 },
      head: { x: 60, y: 90, w: 680 },
      topic: { x: 40, y: 60, maxW: 820 },
      capTalk: h - 300, capGfx: h - 200, capCenter: h * 0.5, capSide: 80,
      hookTop: 100, outroTop: 200, eyeLine: 0.4, maxChars: 30,
    };
  }
  // 9:16 dọc (Reels, TikTok, Shorts): chừa 120px trên, 320–380px dưới, 120px cột nút bên phải
  return {
    w, h, u: 1,
    pip: { x: 790, y: 110, w: 240, h: 300, r: 30 },
    panel: { x: 70, y: 470, w: 940, h: 880 },
    head: { x: 70, y: 130, w: 680 },
    topic: { x: 50, y: 90, maxW: 860 },
    capTalk: 1420, capGfx: 1520, capCenter: 1100, capSide: 80,
    hookTop: 150, outroTop: 200, eyeLine: 0.4, maxChars: 30,
  };
};

/**
 * Đặt video nguồn vào khung. "cover": phủ kín, canh mặt người nói giữa ngang và ở đường mắt.
 * "contain": giữ trọn khung hình gốc (khi khổ gốc lệch nhiều so với khổ ra, ví dụ quay dọc mà xuất 16:9), nền thương hiệu phía sau.
 * "auto": cover nếu tỉ lệ hai khổ chênh dưới 1,35 lần, ngược lại contain.
 */
export const fitVideo = (L: Layout, srcW: number, srcH: number, fx: number, fy: number, mode: "auto" | "cover" | "contain" = "auto") => {
  const ratio = srcW / srcH / (L.w / L.h);
  const m = mode === "auto" ? (Math.max(ratio, 1 / ratio) < 1.35 ? "cover" : "contain") : mode;
  const k = m === "cover" ? Math.max(L.w / srcW, L.h / srcH) : Math.min(L.w / srcW, L.h / srcH);
  const vw = srcW * k;
  const vh = srcH * k;
  const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
  const ox = m === "cover" ? clamp(L.w / 2 - fx * vw, L.w - vw, 0) : (L.w - vw) / 2;
  const oy = m === "cover" ? clamp(L.h * L.eyeLine - fy * vh, L.h - vh, 0) : (L.h - vh) / 2;
  return { mode: m, vw, vh, ox, oy, faceX: ox + fx * vw, faceY: oy + fy * vh };
};
