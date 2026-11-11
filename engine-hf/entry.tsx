/**
 * Lối vào của bộ dựng HyperFrames: vẽ thành phần Video của skill (engine/src/Video.tsx) theo thời gian HyperFrames đưa vào.
 *
 * - Dữ liệu dựng (work/data.json) nằm trong window.__VE_PROPS (file ve/props.js do ve/hf.py ghi).
 * - Mỗi lần HyperFrames tua tới một thời điểm (sự kiện hf-seek), vẽ lại đồng bộ đúng khung đó rồi báo chờ ảnh, phông
 *   chữ, delayRender qua e.detail.waitUntil. Không có đồng hồ riêng, nên render nào cũng ra giống nhau.
 * - window.__veSeek(t) cho phép tua khi mở trang ngoài HyperFrames (đo bố cục khi chụp storyboard: probe.mjs).
 */
import { flushSync } from "react-dom";
import { createRoot } from "react-dom/client";
import { FrameCtx, PENDING } from "remotion";
import { Video } from "./src/Video";
import { registerScenes } from "./src/motion/registry";
import { SCENES as PROJECT_SCENES } from "ve-du-an";
import type { Props } from "./src/types";

registerScenes(PROJECT_SCENES);

type Win = Window & {
  __VE_PROPS?: Props;
  __veSeek?: (t: number) => Promise<number>;
  __veReady?: Promise<void>;
};
const w = window as Win;

const props = { ...(w.__VE_PROPS as Props) };
if (new URLSearchParams(location.search).has("probe")) props.probe = true;
const fps = props.format.fps;
const total = Math.max(1, Math.round(props.duration * fps));
const config = { fps, width: props.format.w, height: props.format.h, durationInFrames: total, id: "Video" };

const host = document.getElementById("ve-stage");
if (!host) throw new Error("Thiếu #ve-stage trong index.html");
const root = createRoot(host);

let current = -1;

const draw = (t: number): Promise<number> => {
  // HyperFrames tua tới t = khung / fps; làm tròn để tránh sai số dấu phẩy động
  const frame = Math.max(0, Math.min(total - 1, Math.round(t * fps)));
  if (frame !== current || props.probe) {
    current = frame;
    flushSync(() => {
      root.render(
        <FrameCtx.Provider value={{ frame, offset: 0, config }}>
          <Video {...props} />
        </FrameCtx.Provider>,
      );
    });
  }
  const waits = PENDING.splice(0, PENDING.length);
  const fonts = (document as Document & { fonts?: { ready: Promise<unknown> } }).fonts?.ready;
  if (fonts) waits.push(fonts);
  return Promise.all(waits).then(() => frame);
};

window.addEventListener("hf-seek", (e: Event) => {
  const d = (e as CustomEvent<{ time: number; waitUntil?: (p: Promise<unknown>) => void }>).detail;
  const p = draw(d.time);
  d.waitUntil?.(p);
});

w.__veSeek = draw;
w.__veReady = draw(0).then(() => undefined);
