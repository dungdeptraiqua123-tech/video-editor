import "@fontsource/be-vietnam-pro/600.css";
import "@fontsource/be-vietnam-pro/800.css";
import "@fontsource/be-vietnam-pro/900.css";

/**
 * Bộ nhận diện "BTC DAILY": xanh dương chủ đạo, vàng hổ phách làm điểm nhấn
 * (Bitcoin, con số), xanh lá / đỏ chỉ dùng cho tăng / giảm.
 */
export const C = {
  night: "#050e24", // nền chính (navy đậm)
  panel: "#0b1b3f", // thẻ, khung
  line: "#1d3566", // đường kẻ, viền mảnh
  orange: "#2f7bff", // màu chủ đạo: xanh dương (giữ tên khoá cũ cho tương thích)
  sky: "#6cc4ff", // xanh sáng: từ khoá, ánh sáng viền
  gold: "#ffb547", // vàng hổ phách: con số, Bitcoin, cảnh báo
  green: "#22c38e",
  red: "#ff5a6a",
  white: "#ffffff",
  mute: "#9fb3d9",
  font: '"Be Vietnam Pro", "Segoe UI", sans-serif',
};

export const glow = (col: string, r = 24) => `0 0 ${r}px ${col}88, 0 0 ${r * 2}px ${col}44`;

export const FPS = 30;
export const W = 1080;
export const H = 1920;
/** Ô mặt người nói khi đồ hoạ chiếm toàn màn hình. */
export const PIP = { x: 790, y: 110, w: 240, h: 300, r: 30 };
