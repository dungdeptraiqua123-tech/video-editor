import { staticFile } from "remotion";

/**
 * Đường dẫn file của dự án. Khi render qua CLI, file được phục vụ từ máy chủ cục bộ (props.mediaBase);
 * khi mở Remotion Studio thì lấy trong thư mục public/.
 */
let base: string | null = null;

export const setMediaBase = (b: string | null | undefined) => {
  base = b ?? null;
};

export const asset = (p: string) => (base ? base + p.split("/").map(encodeURIComponent).join("/") : staticFile(p));
