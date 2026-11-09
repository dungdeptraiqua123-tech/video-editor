import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { Layout } from "../layout";
import { Paper } from "./kit";
import { SCENES, Safe } from "./registry";
import { M } from "./theme";
import { Graphic } from "../types";
import "./scenes";

export type MotionGraphic = Extract<Graphic, { type: "motion" }>;

/** Khung thiết kế của cảnh theo khổ hình: dọc 1080 rộng, ngang 1920 rộng; chiều cao theo tỉ lệ khung thật. */
export const designOf = (L: Layout) => {
  const W = L.w >= L.h ? 1920 : 1080;
  return { W, H: Math.round((L.h * W) / L.w), k: L.w / W };
};

const safeOf = (L: Layout, W: number, H: number, k: number, pip: boolean): Safe => ({
  top: Math.round(L.head.y / k),
  bottom: Math.round(Math.min(H - 60, (L.capGfx - 110) / k)),
  left: Math.round(L.head.x / k),
  right: Math.round(W - L.head.x / k),
  pip: pip ? { x: L.pip.x / k, y: L.pip.y / k, w: L.pip.w / k, h: L.pip.h / k } : null,
});

class Guard extends React.Component<{ name: string; children: React.ReactNode }, { err: string | null }> {
  state = { err: null as string | null };
  static getDerivedStateFromError(e: unknown) {
    return { err: e instanceof Error ? e.message : String(e) };
  }
  render() {
    if (this.state.err) {
      // Hiện rõ lỗi trên khung để ảnh soát / storyboard bắt được (không làm hỏng cả video).
      return (
        <div style={{ position: "absolute", left: 60, right: 60, top: "40%", padding: 30, background: "#7f1d1d", color: "#fff", fontFamily: "monospace", fontSize: 30, borderRadius: 16 }}>
          ✗ Cảnh motion "{this.props.name}" lỗi: {this.state.err}
        </div>
      );
    }
    return this.props.children;
  }
}

/** Vẽ một khung motion: tra cảnh theo tên, đặt trên khung thiết kế rồi thu phóng vừa khung thật. */
export const MotionBeat: React.FC<{ g: MotionGraphic; durationFrames: number; fps: number; L: Layout }> = ({ g, durationFrames, fps, L }) => {
  const f = useCurrentFrame();
  const layer = g.layer ?? "full";
  const { W, H, k } = designOf(L);
  const Scene = SCENES[g.scene];
  const o = interpolate(f, [0, 8, durationFrames - 8, durationFrames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const safe = safeOf(L, W, H, k, layer === "full" && g.pip !== false);
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: W, height: H, transform: `scale(${k})`, transformOrigin: "0 0", opacity: o, fontFamily: M.sans, overflow: "hidden" }}>
      {layer === "full" ? <Paper /> : null}
      {Scene ? (
        <Guard name={g.scene}>
          <Scene p={g.params ?? {}} dur={durationFrames / fps} W={W} H={H} layer={layer} safe={safe} />
        </Guard>
      ) : (
        <div style={{ position: "absolute", left: 60, right: 60, top: "40%", padding: 30, background: "#7f1d1d", color: "#fff", fontFamily: "monospace", fontSize: 30, borderRadius: 16 }}>
          ✗ Không có cảnh motion "{g.scene}"
        </div>
      )}
    </div>
  );
};
