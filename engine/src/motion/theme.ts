import "@fontsource/fraunces/500.css";
import "@fontsource/fraunces/600.css";
import "@fontsource/fraunces/500-italic.css";
import "@fontsource/fraunces/600-italic.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/600.css";
import { Brand } from "../types";
import { C } from "../theme";

/**
 * Bảng màu và font riêng cho cảnh motion (cảnh giải thích, giao diện giả lập, sơ đồ…).
 * Mặc định là "sáng": nền giấy kem, chữ mực đậm, màu nhấn lấy từ nhận diện thương hiệu.
 * "toi": dùng nền và chữ của thương hiệu (hợp với video tông tối).
 */
export type MotionStyle = {
  look?: "sang" | "toi";
  bg?: string;
  paper?: string;
  ink?: string;
  mute?: string;
  line?: string;
  accent?: string;
  accent2?: string;
  ok?: string;
  serif?: string;
  sans?: string;
  mono?: string;
};

export const M = {
  look: "sang" as "sang" | "toi",
  bg: "#f6f3ec",
  paper: "#fffdf8",
  ink: "#1f1d1a",
  mute: "#8b857a",
  line: "#e7e1d5",
  accent: "#c2410c",
  accent2: "#2563eb",
  ok: "#16a34a",
  serif: '"Fraunces", "Playfair Display", Georgia, "Times New Roman", serif',
  sans: '"Be Vietnam Pro", "Segoe UI", sans-serif',
  mono: '"JetBrains Mono", Consolas, "Courier New", monospace',
};

/** Gọi ở đầu mỗi khung (sau applyBrand): màu nhấn theo thương hiệu, phần còn lại theo kiểu sáng/tối hoặc style riêng. */
export const applyMotionStyle = (brand: Brand, s?: MotionStyle | null) => {
  const look = s?.look ?? "sang";
  const c = brand.colors;
  const base =
    look === "toi"
      ? { bg: c.bg, paper: c.panel, ink: c.text ?? "#ffffff", mute: c.mute, line: c.line }
      : { bg: "#f6f3ec", paper: "#fffdf8", ink: "#1f1d1a", mute: "#8b857a", line: "#e7e1d5" };
  Object.assign(M, base, {
    look,
    accent: c.primary,
    accent2: c.highlight,
    ok: c.up,
    sans: C.font,
  });
  if (s) {
    for (const [k, v] of Object.entries(s)) if (typeof v === "string" && v && k !== "look") (M as Record<string, string>)[k] = v;
  }
};

/** "#rrggbb" -> rgba */
export const rgba = (hex: string, a: number) => {
  const h = hex.replace("#", "");
  const n = parseInt(h.length === 3 ? h.split("").map((x) => x + x).join("") : h.slice(0, 6), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
};

export const shadow = (k = 1) =>
  M.look === "toi"
    ? `0 ${18 * k}px ${48 * k}px rgba(0,0,0,0.45)`
    : `0 ${2 * k}px ${4 * k}px rgba(40,30,10,0.05), 0 ${14 * k}px ${36 * k}px rgba(40,30,10,0.12)`;
