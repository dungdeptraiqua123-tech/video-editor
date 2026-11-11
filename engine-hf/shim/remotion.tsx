/**
 * Lớp thay thế gói "remotion" cho bộ dựng HyperFrames.
 *
 * Mã đồ hoạ của skill (engine/src) viết bằng React với các hàm quen thuộc: useCurrentFrame, interpolate, spring,
 * Sequence, Img, OffthreadVideo… Khi đóng gói cho HyperFrames, mọi `import … from "remotion"` trỏ về file này, nên
 * đúng một bộ mã chạy được trên cả hai bộ dựng. Đây là cách HyperFrames gọi là "hosted": mã vẽ khung hình theo
 * thời gian HyperFrames đưa vào (sự kiện hf-seek), không có đồng hồ riêng.
 *
 * - Thời gian: FrameCtx giữ khung tuyệt đối và độ lệch của Sequence đang bao quanh.
 * - Video: video thật là thẻ <video class="clip"> trong index.html (HyperFrames tự lấy khung hình và tiếng).
 *   OffthreadVideo không tự vẽ video mà "mượn" thẻ đó vào đúng chỗ, đúng kích thước; hết cảnh thì trả về chỗ đỗ.
 * - Âm thanh: Audio không vẽ gì. Tiếng (nhạc nền, âm hiệu ứng, giọng) là thẻ <audio> do ve/hf.py sinh ra.
 * - Chờ tải: Img, delayRender và phông chữ ghi lời hứa vào PENDING; lối vào chờ hết rồi mới cho chụp khung.
 */
import React, { createContext, useContext, useLayoutEffect, useRef } from "react";

// ---------------------------------------------------------------- thời gian

export type VideoConfig = { fps: number; width: number; height: number; durationInFrames: number; id: string };

type FrameState = { frame: number; offset: number; config: VideoConfig };

export const FrameCtx = createContext<FrameState>({
  frame: 0,
  offset: 0,
  config: { fps: 30, width: 1080, height: 1920, durationInFrames: 1, id: "Video" },
});

/** Khung hiện tại, tính từ đầu Sequence gần nhất (như Remotion). */
export const useCurrentFrame = () => {
  const s = useContext(FrameCtx);
  return s.frame - s.offset;
};

export const useVideoConfig = () => useContext(FrameCtx).config;

// ---------------------------------------------------------------- nội suy, lò xo, đường cong

type Extrapolate = "clamp" | "extend" | "identity" | "wrap";
type InterpolateOptions = { easing?: (t: number) => number; extrapolateLeft?: Extrapolate; extrapolateRight?: Extrapolate };

export const interpolate = (input: number, inputRange: readonly number[], outputRange: readonly number[], options: InterpolateOptions = {}): number => {
  if (inputRange.length !== outputRange.length) throw new Error("interpolate: inputRange và outputRange phải cùng độ dài");
  if (inputRange.length < 2) throw new Error("interpolate: cần ít nhất 2 mốc");
  for (let i = 1; i < inputRange.length; i++) {
    if (!(inputRange[i] > inputRange[i - 1])) throw new Error(`interpolate: inputRange phải tăng dần, nhận được [${inputRange.join(",")}]`);
  }
  const easing = options.easing ?? ((t: number) => t);
  const left = options.extrapolateLeft ?? "extend";
  const right = options.extrapolateRight ?? "extend";
  let i = 1;
  while (i < inputRange.length - 1 && input > inputRange[i]) i++;
  const inMin = inputRange[i - 1];
  const inMax = inputRange[i];
  const outMin = outputRange[i - 1];
  const outMax = outputRange[i];
  let x = input;
  if (x < inMin) {
    if (left === "identity") return x;
    if (left === "clamp") x = inMin;
    else if (left === "wrap") x = inMin + ((((x - inMin) % (inMax - inMin)) + (inMax - inMin)) % (inMax - inMin));
  }
  if (x > inMax) {
    if (right === "identity") return x;
    if (right === "clamp") x = inMax;
    else if (right === "wrap") x = inMin + ((x - inMin) % (inMax - inMin));
  }
  if (outMin === outMax) return outMin;
  let p = (x - inMin) / (inMax - inMin);
  p = easing(p);
  return outMin + p * (outMax - outMin);
};

const parseColor = (c: string): [number, number, number, number] => {
  const s = c.trim();
  if (s.startsWith("#")) {
    let h = s.slice(1);
    if (h.length === 3 || h.length === 4) h = h.split("").map((x) => x + x).join("");
    const n = parseInt(h.slice(0, 6), 16);
    const a = h.length === 8 ? parseInt(h.slice(6, 8), 16) / 255 : 1;
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255, a];
  }
  const m = s.match(/rgba?\(([^)]+)\)/);
  if (m) {
    const p = m[1].split(",").map((x) => parseFloat(x));
    return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
  }
  return [0, 0, 0, 1];
};

export const interpolateColors = (input: number, inputRange: readonly number[], outputRange: readonly string[]) => {
  const cols = outputRange.map(parseColor);
  const ch = (k: number) => interpolate(input, inputRange, cols.map((c) => c[k]), { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return `rgba(${Math.round(ch(0))}, ${Math.round(ch(1))}, ${Math.round(ch(2))}, ${ch(3)})`;
};

type SpringConfig = { damping: number; mass: number; stiffness: number; overshootClamping: boolean };
const SPRING_DEFAULT: SpringConfig = { damping: 10, mass: 1, stiffness: 100, overshootClamping: false };

/** Vị trí lò xo tắt dần (khối lượng, độ cứng, giảm chấn) sau t giây, đi từ 0 tới 1, vận tốc đầu 0. Lời giải đóng. */
const springAt = (t: number, c: SpringConfig) => {
  if (t <= 0) return 0;
  const w0 = Math.sqrt(c.stiffness / c.mass);
  const zeta = c.damping / (2 * Math.sqrt(c.stiffness * c.mass));
  let x: number; // độ lệch so với đích (đích = 1, xuất phát = -1)
  if (zeta < 1) {
    const wd = w0 * Math.sqrt(1 - zeta * zeta);
    x = Math.exp(-zeta * w0 * t) * (Math.cos(wd * t) + ((zeta * w0) / wd) * Math.sin(wd * t));
  } else if (zeta === 1) {
    x = Math.exp(-w0 * t) * (1 + w0 * t);
  } else {
    const s = w0 * Math.sqrt(zeta * zeta - 1);
    const r1 = -zeta * w0 + s;
    const r2 = -zeta * w0 - s;
    x = (r2 * Math.exp(r1 * t) - r1 * Math.exp(r2 * t)) / (r2 - r1);
  }
  return 1 - x;
};

/** Thời gian (giây) lò xo coi như đứng yên: lệch dưới 0,005 và không còn dao động đáng kể. */
const settleTime = (c: SpringConfig) => {
  for (let t = 0; t < 30; t += 1 / 120) {
    let still = true;
    for (let k = 0; k < 12 && still; k++) still = Math.abs(1 - springAt(t + k / 120, c)) < 0.005;
    if (still) return t;
  }
  return 30;
};

export const spring = ({
  frame,
  fps,
  config = {},
  from = 0,
  to = 1,
  durationInFrames,
  delay = 0,
  reverse = false,
}: {
  frame: number;
  fps: number;
  config?: Partial<SpringConfig>;
  from?: number;
  to?: number;
  durationInFrames?: number;
  durationRestThreshold?: number;
  delay?: number;
  reverse?: boolean;
}) => {
  const c = { ...SPRING_DEFAULT, ...config };
  let f = frame - delay;
  if (durationInFrames !== undefined) {
    // kéo giãn cho lò xo đứng yên đúng ở khung durationInFrames
    const natural = settleTime(c) * fps;
    f = reverse ? durationInFrames - f : f;
    f = (f / durationInFrames) * natural;
  } else if (reverse) {
    f = -f;
  }
  let v = springAt(f / fps, c);
  if (c.overshootClamping) v = Math.min(v, 1);
  if (reverse && durationInFrames === undefined) v = 1 - v;
  return from + (to - from) * v;
};

export const measureSpring = ({ fps, config = {} }: { fps: number; config?: Partial<SpringConfig> }) =>
  Math.ceil(settleTime({ ...SPRING_DEFAULT, ...config }) * fps);

const bezier = (x1: number, y1: number, x2: number, y2: number) => {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
  const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const sx = (t: number) => ((ax * t + bx) * t + cx) * t;
  const sy = (t: number) => ((ay * t + by) * t + cy) * t;
  const dx = (t: number) => (3 * ax * t + 2 * bx) * t + cx;
  return (x: number) => {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    let t = x;
    for (let i = 0; i < 8; i++) {
      const e = sx(t) - x;
      const d = dx(t);
      if (Math.abs(e) < 1e-7) return sy(t);
      if (Math.abs(d) < 1e-6) break;
      t -= e / d;
    }
    let lo = 0, hi = 1;
    t = x;
    while (hi - lo > 1e-7) {
      if (sx(t) < x) lo = t;
      else hi = t;
      t = (lo + hi) / 2;
    }
    return sy(t);
  };
};

type Fn = (t: number) => number;
export const Easing = {
  linear: (t: number) => t,
  ease: bezier(0.42, 0, 1, 1),
  quad: (t: number) => t * t,
  cubic: (t: number) => t * t * t,
  poly: (n: number) => (t: number) => Math.pow(t, n),
  sin: (t: number) => 1 - Math.cos((t * Math.PI) / 2),
  circle: (t: number) => 1 - Math.sqrt(1 - t * t),
  exp: (t: number) => Math.pow(2, 10 * (t - 1)),
  back: (s = 1.70158) => (t: number) => t * t * ((s + 1) * t - s),
  elastic: (b = 1) => {
    const p = b * Math.PI;
    return (t: number) => 1 - Math.pow(Math.cos((t * Math.PI) / 2), 3) * Math.cos(t * p);
  },
  bounce: (t: number) => {
    if (t < 1 / 2.75) return 7.5625 * t * t;
    if (t < 2 / 2.75) { const u = t - 1.5 / 2.75; return 7.5625 * u * u + 0.75; }
    if (t < 2.5 / 2.75) { const u = t - 2.25 / 2.75; return 7.5625 * u * u + 0.9375; }
    const u = t - 2.625 / 2.75;
    return 7.5625 * u * u + 0.984375;
  },
  bezier,
  in: (e: Fn) => e,
  out: (e: Fn) => (t: number) => 1 - e(1 - t),
  inOut: (e: Fn) => (t: number) => (t < 0.5 ? e(t * 2) / 2 : 1 - e((1 - t) * 2) / 2),
};

/** Số ngẫu nhiên cố định theo hạt giống (0 ≤ x < 1): cùng hạt giống luôn ra cùng số, ở mọi khung. */
export const random = (seed: number | string | null): number => {
  if (seed === null) throw new Error("random(null) không xác định được: hãy truyền hạt giống");
  const s = String(seed);
  let h = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  // mulberry32
  let a = (h + 0x6d2b79f5) >>> 0;
  a = Math.imul(a ^ (a >>> 15), a | 1);
  a ^= a + Math.imul(a ^ (a >>> 7), a | 61);
  return ((a ^ (a >>> 14)) >>> 0) / 4294967296;
};

// ---------------------------------------------------------------- chờ tải

/** Lời hứa phải xong trước khi chụp khung (ảnh, phông chữ, delayRender). Lối vào đọc rồi xoá sau mỗi lần vẽ. */
export const PENDING: Promise<unknown>[] = [];
const handles = new Map<number, () => void>();
let nextHandle = 1;

export const delayRender = (_label?: string): number => {
  const id = nextHandle++;
  PENDING.push(new Promise<void>((res) => handles.set(id, res)));
  return id;
};

export const continueRender = (id: number) => {
  const r = handles.get(id);
  handles.delete(id);
  r?.();
};

export const cancelRender = (e: unknown) => {
  console.error("cancelRender", e);
};

// ---------------------------------------------------------------- tệp

let staticBase = "assets/";
export const setStaticBase = (b: string) => {
  staticBase = b;
};
export const staticFile = (p: string) => staticBase + p.replace(/^\/+/, "").split("/").map(encodeURIComponent).join("/");

// ---------------------------------------------------------------- khung, đoạn

const FILL: React.CSSProperties = {
  position: "absolute",
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
};

export const AbsoluteFill = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ style, ...rest }, ref) => (
  <div ref={ref} {...rest} style={{ ...FILL, ...style }} />
));
AbsoluteFill.displayName = "AbsoluteFill";

type SequenceProps = {
  from?: number;
  durationInFrames?: number;
  layout?: "absolute-fill" | "none";
  name?: string;
  style?: React.CSSProperties;
  premountFor?: number;
  children?: React.ReactNode;
};

export const Sequence: React.FC<SequenceProps> = ({ from = 0, durationInFrames = Infinity, layout = "absolute-fill", style, children }) => {
  const s = useContext(FrameCtx);
  const rel = s.frame - s.offset;
  if (rel < from || rel >= from + durationInFrames) return null;
  // như Remotion: trong một Sequence, useVideoConfig().durationInFrames là độ dài của Sequence đó
  const config = Number.isFinite(durationInFrames) ? { ...s.config, durationInFrames } : s.config;
  const inner = <FrameCtx.Provider value={{ ...s, offset: s.offset + from, config }}>{children}</FrameCtx.Provider>;
  return layout === "none" ? inner : <AbsoluteFill style={style}>{inner}</AbsoluteFill>;
};

export const Loop: React.FC<{ durationInFrames: number; times?: number; layout?: "absolute-fill" | "none"; style?: React.CSSProperties; children?: React.ReactNode }> = ({
  durationInFrames,
  times = Infinity,
  layout = "absolute-fill",
  style,
  children,
}) => {
  const s = useContext(FrameCtx);
  const rel = s.frame - s.offset;
  const k = Math.floor(rel / durationInFrames);
  if (rel < 0 || k >= times) return null;
  const inner = <FrameCtx.Provider value={{ ...s, offset: s.offset + k * durationInFrames }}>{children}</FrameCtx.Provider>;
  return layout === "none" ? inner : <AbsoluteFill style={style}>{inner}</AbsoluteFill>;
};

export const Freeze: React.FC<{ frame: number; children?: React.ReactNode }> = ({ frame, children }) => {
  const s = useContext(FrameCtx);
  return <FrameCtx.Provider value={{ ...s, frame: s.offset + frame }}>{children}</FrameCtx.Provider>;
};

// ---------------------------------------------------------------- ảnh

const loaded = new Set<string>();

export const Img = React.forwardRef<HTMLImageElement, React.ImgHTMLAttributes<HTMLImageElement>>(({ src, onLoad, onError, ...rest }, ref) => {
  const own = useRef<HTMLImageElement | null>(null);
  useLayoutEffect(() => {
    const el = own.current;
    if (!el || !src || loaded.has(src)) return;
    if (el.complete && el.naturalWidth > 0) {
      loaded.add(src);
      return;
    }
    PENDING.push(
      el.decode().then(
        () => void loaded.add(src),
        () => void loaded.add(src),
      ),
    );
  }, [src]);
  return (
    <img
      ref={(el) => {
        own.current = el;
        if (typeof ref === "function") ref(el);
        else if (ref) ref.current = el;
      }}
      src={src}
      decoding="sync"
      onLoad={onLoad}
      onError={onError}
      {...rest}
    />
  );
});
Img.displayName = "Img";

// ---------------------------------------------------------------- video: mượn thẻ <video class="clip"> của HyperFrames

/** Bảng thẻ video thật trong index.html: src → các đoạn [bắt đầu, kết thúc] (giây), do ve/hf.py ghi vào window.__VE_CLIPS. */
type ClipRef = { id: string; src: string; start: number; end: number };
const clipList = (): ClipRef[] => (window as unknown as { __VE_CLIPS?: ClipRef[] }).__VE_CLIPS ?? [];
const park = () => document.getElementById("ve-park");
const borrowed = new Map<string, HTMLElement>(); // id thẻ video → ô đang mượn

const normSrc = (s: string) => {
  try {
    return decodeURIComponent(new URL(s, document.baseURI).pathname).replace(/^\/+/, "");
  } catch {
    return s;
  }
};

const findClip = (src: string, t: number): ClipRef | null => {
  const want = normSrc(src);
  let best: ClipRef | null = null;
  for (const c of clipList()) {
    if (normSrc(c.src) !== want) continue;
    if (t >= c.start - 1e-6 && t < c.end - 1e-6) {
      if (!best || c.start > best.start) best = c;
    }
  }
  return best;
};

/** Trả thẻ video (và ảnh khung HyperFrames chèn ngay sau nó) về chỗ đỗ. */
const giveBack = (id: string) => {
  const p = park();
  const v = document.getElementById(id);
  borrowed.delete(id);
  if (!p || !v) return;
  const next = v.nextElementSibling;
  p.appendChild(v);
  if (next && next.classList.contains("__render_frame__")) p.appendChild(next);
  v.style.cssText = "position:absolute;left:0;top:0;width:16px;height:16px;";
};

type VideoProps = { src: string; style?: React.CSSProperties; className?: string; muted?: boolean; volume?: unknown; startFrom?: number; endAt?: number; playbackRate?: number; loop?: boolean };

export const OffthreadVideo: React.FC<VideoProps> = ({ src, style }) => {
  const s = useContext(FrameCtx);
  const slot = useRef<HTMLDivElement | null>(null);
  const t = s.frame / s.config.fps;
  const clip = findClip(src, t);
  const id = clip?.id ?? null;
  useLayoutEffect(() => {
    const el = slot.current;
    if (!el || !id) return;
    const v = document.getElementById(id);
    if (!v) return;
    if (v.parentElement !== el) {
      const next = v.nextElementSibling;
      el.appendChild(v);
      if (next && next.classList.contains("__render_frame__")) el.appendChild(next);
    }
    borrowed.set(id, el);
    // kích thước, vị trí, cách lấp đầy của thẻ video theo style của thành phần (như Remotion vẽ <video>)
    const st = v.style;
    st.cssText = "";
    Object.assign(st, { display: "block", width: "100%", height: "100%", objectFit: "cover" });
    for (const [k, val] of Object.entries(style ?? {})) {
      const key = k as keyof CSSStyleDeclaration;
      (st as unknown as Record<string, string>)[key as string] = typeof val === "number" && !/^(opacity|zIndex|flex|fontWeight|lineHeight)$/.test(k) ? `${val}px` : String(val);
    }
    return () => {
      if (borrowed.get(id) === el) giveBack(id);
    };
  });
  // ô giữ chỗ: chiếm đúng chỗ thẻ <video> của Remotion; thẻ video thật được gắn vào trong
  return <div ref={slot} data-ve-video={src} style={{ display: "contents" }} />;
};

export const Video = OffthreadVideo;

/** Âm thanh không vẽ gì: tiếng trong video HyperFrames là các thẻ <audio> do ve/hf.py sinh ra. */
type AudioProps = { src: string; volume?: number | ((frame: number) => number); loop?: boolean; startFrom?: number; endAt?: number; playbackRate?: number; muted?: boolean };
export const Audio: React.FC<AudioProps> = () => null;

// ---------------------------------------------------------------- phần không dùng khi chạy trong HyperFrames

export const registerRoot = (_: unknown) => {};
export const Composition: React.FC<Record<string, unknown>> = () => null;
export type CalculateMetadataFunction<P> = (o: { props: P }) => Partial<VideoConfig>;
export const getInputProps = () => (window as unknown as { __VE_PROPS?: unknown }).__VE_PROPS ?? {};
