import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
export const easeOut = Easing.bezier(0.16, 1, 0.3, 1);
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);

/** Giây hiện tại tính từ lúc cảnh mở. */
export const useSec = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return f / fps;
};

/** Lò xo bắt đầu lúc `at` giây (0 → 1, có nảy nhẹ). */
export const useSpring = (at: number, cfg?: { damping?: number; stiffness?: number; mass?: number }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: f - Math.round(at * fps), fps, config: { damping: 15, stiffness: 170, mass: 1, ...cfg } });
};

/** Tiến độ tuyến tính có làm mượt từ giây a tới giây b (0 → 1). */
export const prog = (t: number, a: number, b: number, easing = easeInOut) =>
  b <= a ? (t >= a ? 1 : 0) : interpolate(t, [a, b], [0, 1], { ...clamp, easing });

/** Số ngẫu nhiên ổn định theo hạt giống (giống nhau ở mọi khung, mọi lần render). */
export const rand = (seed: number) => {
  const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
};
