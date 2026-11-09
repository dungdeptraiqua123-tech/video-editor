import React from "react";

/**
 * Cảnh motion nhận:
 * - p: tham số trong project.json (khung g.params), các khoá say/xxxSay đã được đổi thành d/xxxD = giây kể từ lúc cảnh mở;
 * - dur: thời lượng cảnh (giây);
 * - W, H: khung thiết kế (dọc 1080 × 1920, ngang 1920 × 1080, vuông 1080 × 1080…);
 * - layer: "full" (cảnh toàn màn hình) hoặc "overlay" (nổi trên hình người nói);
 * - safe: vùng nên đặt nội dung (tránh ô mặt người nói, phụ đề, nút của nền tảng).
 */
export type Safe = { top: number; bottom: number; left: number; right: number; pip: { x: number; y: number; w: number; h: number } | null };
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type SceneProps<P = any> = { p: P; dur: number; W: number; H: number; layer: "full" | "overlay"; safe: Safe };
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Scene<P = any> = React.FC<SceneProps<P>>;

/** Mọi cảnh dùng được: cảnh có sẵn của skill + cảnh viết riêng cho dự án (motion/*.tsx, đăng ký khi đóng gói). */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const SCENES: Record<string, Scene<any>> = {};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const registerScenes = (m: Record<string, Scene<any>>) => {
  Object.assign(SCENES, m);
};
