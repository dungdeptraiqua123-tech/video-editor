// Dự án không có cảnh motion viết riêng: không đăng ký thêm cảnh nào. ve/hf.py thay file này bằng danh sách cảnh của dự án.
import type { Scene } from "../src/motion/registry";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const SCENES: Record<string, Scene<any>> = {};
