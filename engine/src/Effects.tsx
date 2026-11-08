import React from "react";
import { AbsoluteFill, Img, interpolate, random, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { asset } from "./assets";
import { Layout } from "./layout";
import { alpha, C, glow } from "./theme";
import { IconData, Pop, Punch, Transition } from "./types";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** Màu sáng hay tối: logo màu quá tối (Apple, X, GitHub…) đặt trên nền trắng để không chìm vào video. */
const isDark = (hex: string) => {
  const n = parseInt(hex.replace("#", "").slice(0, 6), 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return 0.299 * r + 0.587 * g + 0.114 * b < 70;
};

/** Huy hiệu tròn chứa icon: logo trắng trên màu thương hiệu, icon nét trên màu chủ đạo, hoặc ảnh logo riêng. */
export const IconBadge: React.FC<{ icon: IconData; size: number; ring?: boolean }> = ({ icon, size, ring = true }) => {
  const brand = icon.kind === "brand";
  const col = icon.color || C.orange;
  const dark = brand && isDark(col);
  const bg = icon.kind === "img" ? "#ffffff" : dark ? "#ffffff" : col;
  const fg = dark ? col : "#ffffff";
  const inner = size * (icon.kind === "line" ? 0.54 : 0.56);
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        background: bg,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxShadow: `0 ${size * 0.08}px ${size * 0.22}px rgba(0,0,0,0.45)${ring ? `, 0 0 0 ${Math.max(3, size * 0.035)}px rgba(255,255,255,0.92)` : ""}`,
        overflow: "hidden",
        flexShrink: 0,
      }}
    >
      {icon.kind === "img" && icon.src ? (
        <Img src={asset(icon.src)} style={{ width: size * 0.74, height: size * 0.74, objectFit: "contain" }} />
      ) : icon.kind === "line" ? (
        <svg
          viewBox={icon.viewBox || "0 0 24 24"}
          width={inner}
          height={inner}
          fill="none"
          stroke={fg}
          strokeWidth={2.2}
          strokeLinecap="round"
          strokeLinejoin="round"
          dangerouslySetInnerHTML={{ __html: icon.body || "" }}
        />
      ) : (
        <svg viewBox={icon.viewBox || "0 0 24 24"} width={inner} height={inner} fill={fg} dangerouslySetInnerHTML={{ __html: icon.body || "" }} />
      )}
    </div>
  );
};

const POP_SEC = 1.7;

/** Icon bật lên phía trên phụ đề lúc người nói nhắc tới: nảy vào, vòng sóng lan ra, tia lấp lánh, bay nhẹ rồi thu lại. */
export const IconPops: React.FC<{ pops: Pop[]; icons: Record<string, IconData>; L: Layout; y: number; hide: number; edge?: boolean }> = ({ pops, icons, L, y, hide, edge }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const live = pops.map((p, i) => ({ p, i })).filter(({ p }) => t >= p.t && t < p.t + POP_SEC);
  if (!live.length || hide > 0.98) return null;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: 1 - hide }}>
      {live.map(({ p, i }) => {
        const icon = icons[p.id];
        if (!icon) return null;
        const f = frame - Math.round(p.t * fps);
        const life = POP_SEC * fps;
        const a = spring({ frame: f, fps, config: { damping: 9, stiffness: 190, mass: 0.6 } });
        const out = interpolate(f, [life - 8, life], [1, 0], clamp);
        const size = 168 * L.u;
        // vị trí: có người nói thì nép sát mép trái/phải (không che mặt), không người nói thì quanh giữa; luôn phía trên phụ đề
        const side = edge ? (i % 2 === 0 ? 1 : -1) : i % 3 === 0 ? 0 : i % 3 === 1 ? -1 : 1;
        const cx = edge ? L.w / 2 + side * (L.w / 2 - size * 0.62 - 24 * L.u) : L.w / 2 + side * Math.min(220, L.w * 0.2) + (random(`x${i}`) - 0.5) * 60;
        const cy = y - 230 * L.u - interpolate(f, [0, life], [0, 34 * L.u]);
        const wave = interpolate(f, [0, 18], [0, 1], clamp);
        const label = icon.label;
        return (
          <div key={i} style={{ position: "absolute", left: cx - size / 2, top: cy - size / 2, width: size, display: "flex", flexDirection: "column", alignItems: "center" }}>
            {/* vòng sóng lan ra */}
            <div
              style={{
                position: "absolute",
                left: size / 2 - size * (0.5 + wave * 0.6),
                top: size / 2 - size * (0.5 + wave * 0.6),
                width: size * (1 + wave * 1.2),
                height: size * (1 + wave * 1.2),
                borderRadius: "50%",
                border: `${6 * L.u}px solid ${icon.color || C.orange}`,
                opacity: (1 - wave) * 0.8,
              }}
            />
            {/* tia lấp lánh */}
            {Array.from({ length: 8 }).map((_, k) => {
              const ang = (k / 8) * Math.PI * 2 + random(`a${i}`) * 0.6;
              const dist = size * (0.55 + wave * 0.55);
              return (
                <div
                  key={k}
                  style={{
                    position: "absolute",
                    left: size / 2 + Math.cos(ang) * dist - 7,
                    top: size / 2 + Math.sin(ang) * dist - 7,
                    width: 14 * L.u,
                    height: 14 * L.u,
                    borderRadius: 4,
                    background: k % 2 ? C.gold : C.sky,
                    transform: `rotate(45deg) scale(${(1 - wave) * 1.2})`,
                    opacity: 1 - wave,
                  }}
                />
              );
            })}
            <div style={{ transform: `scale(${a * out}) rotate(${(1 - a) * -18}deg)` }}>
              <IconBadge icon={icon} size={size} />
            </div>
            {label ? (
              <div
                style={{
                  marginTop: 14 * L.u,
                  whiteSpace: "nowrap",
                  fontFamily: C.font,
                  fontWeight: 900,
                  fontSize: 36 * L.u,
                  color: C.white,
                  background: alpha(C.night, 0.88),
                  border: `2px solid ${icon.color || C.orange}`,
                  padding: `${6 * L.u}px ${20 * L.u}px`,
                  borderRadius: 999,
                  opacity: spring({ frame: f - 5, fps }) * out,
                  transform: `translateY(${(1 - spring({ frame: f - 5, fps })) * 16}px)`,
                }}
              >
                {label}
              </div>
            ) : null}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const PUNCH_SEC = 1.5;

/** Độ rung khung (px) tại lúc t: tắt dần trong 0,35 giây sau mỗi chữ đập. */
export const shakeAt = (punches: Punch[] | undefined, t: number, on: boolean): [number, number] => {
  if (!on || !punches) return [0, 0];
  const p = punches.find((x) => t >= x.t && t < x.t + 0.35);
  if (!p) return [0, 0];
  const k = 1 - (t - p.t) / 0.35;
  const s = 16 * k * k;
  return [Math.sin(t * 95) * s, Math.cos(t * 77) * s * 0.7];
};

/** Chữ lớn đập vào giữa khung: phóng từ to xuống, có vệt sáng chạy qua, lắc nhẹ rồi bay ra. */
export const Punches: React.FC<{ punches: Punch[]; L: Layout; y: number; hide: number }> = ({ punches, L, y, hide }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const p = punches.find((x) => t >= x.t && t < x.t + PUNCH_SEC);
  if (!p || hide > 0.98) return null;
  const f = frame - Math.round(p.t * fps);
  const life = PUNCH_SEC * fps;
  const a = spring({ frame: f, fps, config: { damping: 12, stiffness: 260, mass: 0.7 } });
  const out = interpolate(f, [life - 7, life], [1, 0], clamp);
  const col = p.tone === "up" ? C.green : p.tone === "down" ? C.red : C.gold;
  const sweep = interpolate(f, [4, 20], [-30, 130], clamp);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: (1 - hide) * out, alignItems: "center" }}>
      <div style={{ position: "absolute", top: y, transform: `translateY(-50%) scale(${2.2 - 1.2 * a}) rotate(${(1 - a) * 8 - 3}deg)`, display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div style={{ position: "relative" }}>
          <div
            style={{
              fontFamily: C.font,
              fontWeight: 900,
              fontSize: 150 * L.u,
              lineHeight: 1,
              letterSpacing: -4,
              color: col,
              WebkitTextStroke: `${12 * L.u}px ${C.night}`,
              paintOrder: "stroke fill",
              textShadow: `0 ${10 * L.u}px 0 ${alpha(C.night, 0.9)}, ${glow(col, 30)}`,
              whiteSpace: "nowrap",
            }}
          >
            {p.text}
          </div>
          {/* vệt sáng chạy qua chữ */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              fontFamily: C.font,
              fontWeight: 900,
              fontSize: 150 * L.u,
              lineHeight: 1,
              letterSpacing: -4,
              whiteSpace: "nowrap",
              color: "transparent",
              backgroundImage: `linear-gradient(110deg, transparent ${sweep - 12}%, rgba(255,255,255,0.9) ${sweep}%, transparent ${sweep + 12}%)`,
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
            }}
          >
            {p.text}
          </div>
        </div>
        {p.sub ? (
          <div style={{ marginTop: 16 * L.u, fontFamily: C.font, fontWeight: 800, fontSize: 44 * L.u, color: C.white, background: alpha(C.night, 0.85), padding: `${8 * L.u}px ${24 * L.u}px`, borderRadius: 16, opacity: spring({ frame: f - 6, fps }) }}>
            {p.sub}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

/** Hạt sáng trôi chậm trên nền thương hiệu (khi hiện đồ hoạ); nảy nhẹ theo nhịp nhạc nếu có. */
export const Particles: React.FC<{ o: number; beats?: number[] }> = ({ o, beats }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  if (o < 0.02) return null;
  const t = frame / fps;
  const last = beats && beats.length ? beats.filter((b) => b <= t).pop() : undefined;
  const pulse = last !== undefined ? Math.max(0, 1 - (t - last) / 0.25) : 0;
  return (
    <AbsoluteFill style={{ opacity: o, pointerEvents: "none" }}>
      {Array.from({ length: 26 }).map((_, i) => {
        const x = random(`px${i}`) * width;
        const sp = 18 + random(`ps${i}`) * 40;
        const yy = (random(`py${i}`) * height - t * sp + height * 10) % height;
        const r = 3 + random(`pr${i}`) * 7;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x + Math.sin(t * 0.7 + i) * 18,
              top: yy,
              width: r * (1 + pulse * 0.8),
              height: r * (1 + pulse * 0.8),
              borderRadius: "50%",
              background: i % 3 ? C.sky : C.orange,
              opacity: 0.18 + random(`po${i}`) * 0.3 + pulse * 0.2,
              boxShadow: glow(i % 3 ? C.sky : C.orange, r * 1.5),
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

const TR_FRAMES = 14;

/** Lớp chuyển cảnh phủ lên đúng lúc đổi giữa người nói và đồ hoạ (mỗi mốc trong `at`, giây). */
export const TransitionFx: React.FC<{ kind: Transition; at: number[] }> = ({ kind, at }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  if (kind === "mem" || kind === "zoom") return null;
  const hit = at.map((s) => frame - Math.round(s * fps) + TR_FRAMES / 2).find((f) => f >= 0 && f < TR_FRAMES);
  if (hit === undefined) return null;
  const k = hit / TR_FRAMES;
  if (kind === "flash") {
    const o = interpolate(k, [0, 0.45, 1], [0, 0.85, 0]);
    return <AbsoluteFill style={{ background: "#ffffff", opacity: o, pointerEvents: "none" }} />;
  }
  if (kind === "vuot") {
    const x = interpolate(k, [0, 1], [-1.3 * width, 1.3 * width]);
    return (
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div style={{ position: "absolute", top: -height * 0.3, left: x, width: width * 0.35, height: height * 1.6, background: C.orange, transform: "rotate(14deg)", boxShadow: glow(C.orange, 60) }} />
        <div style={{ position: "absolute", top: -height * 0.3, left: x - width * 0.16, width: width * 0.06, height: height * 1.6, background: C.sky, transform: "rotate(14deg)", opacity: 0.8 }} />
      </AbsoluteFill>
    );
  }
  // glitch: các dải ngang lệch màu, nhấp nháy trong vài khung
  const n = 9;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen" }}>
      {Array.from({ length: n }).map((_, i) => {
        const r = random(`g${hit}-${i}`);
        if (r < 0.35) return null;
        const h = height * (0.02 + random(`gh${hit}-${i}`) * 0.07);
        const top = random(`gy${hit}-${i}`) * height;
        const off = (random(`gx${hit}-${i}`) - 0.5) * width * 0.25;
        return <div key={i} style={{ position: "absolute", left: off, top, width, height: h, background: i % 2 ? alpha(C.sky, 0.55) : alpha(C.red, 0.5) }} />;
      })}
    </AbsoluteFill>
  );
};

/** Hệ số phóng toàn khung cho chuyển cảnh "zoom" (đập nhẹ vào lúc đổi cảnh). */
export const zoomBump = (kind: Transition | undefined, at: number[], t: number) => {
  if (kind !== "zoom") return 1;
  const d = Math.min(...at.map((s) => Math.abs(t - s)));
  return d < 0.25 ? 1 + 0.12 * (1 - d / 0.25) ** 2 : 1;
};
