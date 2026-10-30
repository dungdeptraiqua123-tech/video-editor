import "@fontsource/be-vietnam-pro/600.css";
import "@fontsource/be-vietnam-pro/800.css";
import "@fontsource/be-vietnam-pro/900.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/800.css";
import "@fontsource/inter/900.css";
import "@fontsource/montserrat/600.css";
import "@fontsource/montserrat/800.css";
import "@fontsource/montserrat/900.css";
import { Brand } from "./types";

/**
 * Bảng màu đang dùng. Các thành phần đọc C lúc vẽ, còn Video gọi applyBrand(props.brand) ở đầu mỗi khung,
 * nên đổi mẫu nhận diện chỉ cần đổi brand.json, không sửa mã.
 * Tên khoá giữ như bản đầu (orange = màu chủ đạo, sky = màu nhấn sáng, gold = màu con số) để mã cũ vẫn chạy.
 */
export const C = {
  night: "#101318",
  night2: "#1e2633",
  panel: "#181d26",
  line: "#2b3442",
  orange: "#14b8a6",
  sky: "#5eead4",
  gold: "#fbbf24",
  green: "#22c38e",
  red: "#ff5a6a",
  white: "#ffffff",
  mute: "#a3acbf",
  font: '"Be Vietnam Pro", "Segoe UI", sans-serif',
};

export const applyBrand = (b: Brand) => {
  const c = b.colors;
  Object.assign(C, {
    night: c.bg,
    night2: c.bg2 ?? c.bg,
    panel: c.panel,
    line: c.line,
    orange: c.primary,
    sky: c.highlight,
    gold: c.number,
    green: c.up,
    red: c.down,
    white: c.text ?? "#ffffff",
    mute: c.mute,
    font: `"${b.font.family}", "Be Vietnam Pro", "Segoe UI", sans-serif`,
  });
};

/** "#rrggbb" -> "rgba(r,g,b,a)" */
export const alpha = (hex: string, a: number) => {
  const n = parseInt(hex.replace("#", "").slice(0, 6), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
};

export const glow = (col: string, r = 24) => `0 0 ${r}px ${col}88, 0 0 ${r * 2}px ${col}44`;
