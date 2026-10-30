import React from "react";
import { Easing, Img, interpolate, OffthreadVideo, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { asset } from "./assets";
import { Icon } from "./Icons";
import { DESIGN, Rect } from "./layout";
import { C } from "./theme";
import { Graphic } from "./types";

const ease = Easing.bezier(0.16, 1, 0.3, 1);

const pop = (f: number, fps: number, delay = 0) =>
  spring({ frame: f - delay, fps, config: { damping: 14, stiffness: 170, mass: 0.7 } });

/** Mốc xuất hiện (khung hình) của phần tử: lấy theo lúc từ khoá được nói (d, giây), nếu không có thì dùng độ trễ mặc định. */
const at = (d: number | undefined, fps: number, fallback: number) => (d === undefined ? fallback : Math.round(d * fps));

const fmt = (n: number, dec = 0) => n.toLocaleString("vi-VN", { minimumFractionDigits: dec, maximumFractionDigits: dec });

const Kicker: React.FC<{ text: string; f: number }> = ({ text, f }) => {
  const { fps } = useVideoConfig();
  const p = pop(f, fps);
  return (
    <div
      style={{
        alignSelf: "flex-start",
        background: C.orange,
        color: C.white,
        fontWeight: 900,
        fontSize: 36,
        boxShadow: `0 0 26px ${C.orange}66`,
        padding: "10px 26px",
        borderRadius: 14,
        letterSpacing: 1,
        textTransform: "uppercase",
        transform: `translateX(${(1 - p) * -60}px)`,
        opacity: p,
      }}
    >
      {text}
    </div>
  );
};

const PriceCard: React.FC<{ g: Extract<Graphic, { type: "price" }>; f: number }> = ({ g, f }) => {
  const { fps } = useVideoConfig();
  const n0 = at(g.d, fps, 6);
  // đếm số dừng đúng lúc con số được đọc
  const count = interpolate(f, [n0 - 18, n0], [g.value * 0.9, g.value], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  const nShow = pop(f, fps, n0 - 18);
  const tone = g.up === undefined ? C.white : g.up ? C.green : C.red;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 34 }}>
      <Kicker text={g.label} f={f} />
      <div style={{ display: "flex", alignItems: "center", gap: 30, transform: `scale(${0.8 + 0.2 * nShow})`, opacity: nShow, transformOrigin: "left center" }}>
        {g.icon ? (
          <div style={{ transform: `rotate(${interpolate(f, [n0 - 18, n0 + 12], [-200, 0], { extrapolateRight: "clamp", easing: ease })}deg)` }}>
            <Icon name={g.icon} size={150} />
          </div>
        ) : null}
        <div style={{ fontSize: 150, fontWeight: 900, color: C.white, letterSpacing: -4, fontVariantNumeric: "tabular-nums" }}>
          {g.prefix ?? ""}
          {fmt(count, g.decimals ?? 0)}
          {g.suffix ?? ""}
        </div>
      </div>
      {g.change ? (
        <div style={{ display: "flex", alignItems: "center", gap: 18, opacity: pop(f, fps, at(g.changeD, fps, n0 + 8)) }}>
          <Icon name={g.up === false ? "down" : "up"} size={70} />
          <div style={{ fontSize: 64, fontWeight: 800, color: tone }}>{g.change}</div>
        </div>
      ) : null}
    </div>
  );
};

const ChartCard: React.FC<{ g: Extract<Graphic, { type: "chart" }>; f: number }> = ({ g, f }) => {
  const { fps } = useVideoConfig();
  const w = 940;
  const h = 470;
  const min = Math.min(...g.points);
  const max = Math.max(...g.points);
  const pts = g.points.map((v, i) => [(i / (g.points.length - 1)) * w, h - 20 - ((v - min) / (max - min || 1)) * (h - 60)]);
  const d = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
  const n = g.points.length - 1;
  // đường vẽ chạm tới từng nhãn đúng lúc nhãn đó được nói
  const keys = (g.tags ?? []).filter((x) => x.d !== undefined).sort((a, b) => a.i - b.i);
  const kf = keys.length ? [8, ...keys.map((x) => at(x.d, fps, 0))] : [8, 52];
  const kv = keys.length ? [0, ...keys.map((x) => x.i / n)] : [0, 1];
  if (kv[kv.length - 1] < 1) { kf.push(kf[kf.length - 1] + 30); kv.push(1); }
  for (let k = 1; k < kf.length; k++) kf[k] = Math.max(kf[k], kf[k - 1] + 1);
  const progress = interpolate(f, kf, kv, { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const col = g.up === false ? C.red : C.green;
  const idx = progress * (pts.length - 1);
  const i0 = Math.floor(idx);
  const i1 = Math.min(pts.length - 1, i0 + 1);
  const t = idx - i0;
  const head = [pts[i0][0] + (pts[i1][0] - pts[i0][0]) * t, pts[i0][1] + (pts[i1][1] - pts[i0][1]) * t];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 30 }}>
      <Kicker text={g.title} f={f} />
      <svg width={w} height={h} style={{ overflow: "visible" }}>
        <defs>
          <linearGradient id="fill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stopColor={col} stopOpacity="0.45" />
            <stop offset="1" stopColor={col} stopOpacity="0" />
          </linearGradient>
          <clipPath id="reveal">
            <rect x="0" y="-40" width={head[0]} height={h + 80} />
          </clipPath>
        </defs>
        {[0, 1, 2, 3].map((k) => (
          <line key={k} x1="0" x2={w} y1={20 + (k * (h - 40)) / 3} y2={20 + (k * (h - 40)) / 3} stroke={C.line} strokeWidth="2" strokeDasharray="8 10" />
        ))}
        <g clipPath="url(#reveal)">
          <path d={`${d} L${w} ${h} L0 ${h} Z`} fill="url(#fill)" />
          <path d={d} fill="none" stroke={col} strokeWidth="9" strokeLinejoin="round" strokeLinecap="round" />
        </g>
        <circle cx={head[0]} cy={head[1]} r={14 + 6 * Math.sin(f / 4)} fill={col} opacity="0.35" />
        <circle cx={head[0]} cy={head[1]} r="11" fill="#fff" />
        {(g.tags ?? []).map((tag, k) => {
          const p = pts[tag.i];
          const show = pop(f, fps, at(tag.d, fps, 10 + (tag.i / (pts.length - 1)) * 44));
          return (
            <g key={k} opacity={show} transform={`translate(${Math.min(Math.max(p[0], 110), w - 110)} ${p[1] - 34 - 20 * (1 - show)})`}>
              <rect x={-110} y={-58} width={220} height={60} rx={14} fill={C.panel} stroke={C.orange} strokeWidth="3" />
              <text x="0" y="-17" textAnchor="middle" fontSize="34" fontWeight="800" fill="#fff" fontFamily={C.font}>
                {tag.text}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

const LevelsCard: React.FC<{ g: Extract<Graphic, { type: "levels" }>; f: number }> = ({ g, f }) => {
  const { fps } = useVideoConfig();
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 26 }}>
      <Kicker text={g.title} f={f} />
      {g.levels.map((l, i) => {
        const p = pop(f, fps, at(l.d, fps, 6 + i * 7));
        const col = l.kind === "res" ? C.red : l.kind === "sup" ? C.green : C.gold;
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 24, opacity: p, transform: `translateX(${(1 - p) * 80}px)` }}>
            <div style={{ width: 230, fontSize: 34, fontWeight: 800, color: col, textTransform: "uppercase" }}>{l.label}</div>
            <div style={{ flex: 1, height: 6, background: col, borderRadius: 3, transform: `scaleX(${p})`, transformOrigin: "left", opacity: l.kind === "now" ? 1 : 0.8 }} />
            <div style={{ fontSize: 58, fontWeight: 900, color: C.white, minWidth: 250, textAlign: "right" }}>{l.value}</div>
          </div>
        );
      })}
    </div>
  );
};

const ListCard: React.FC<{ g: Extract<Graphic, { type: "list" }>; f: number }> = ({ g, f }) => {
  const { fps } = useVideoConfig();
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
      <Kicker text={g.title} f={f} />
      {g.items.map((it, i) => {
        const p = pop(f, fps, at(it.d, fps, 8 + i * 9));
        return (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 28,
              background: C.panel,
              border: `2px solid ${C.line}`,
              borderRadius: 26,
              padding: "20px 28px",
              opacity: p,
              transform: `translateY(${(1 - p) * 40}px) scale(${0.92 + 0.08 * p})`,
            }}
          >
            <Icon name={it.icon} size={78} />
            <div style={{ fontSize: 46, fontWeight: 800, color: C.white, lineHeight: 1.2 }}>{it.text}</div>
          </div>
        );
      })}
    </div>
  );
};

const StatCard: React.FC<{ g: Extract<Graphic, { type: "stat" }>; f: number }> = ({ g, f }) => {
  const { fps } = useVideoConfig();
  const p = pop(f, fps);
  const col = g.tone === "up" ? C.green : g.tone === "down" ? C.red : C.orange;
  const big = pop(f, fps, at(g.d, fps, 4));
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 18, textAlign: "center" }}>
      <div style={{ transform: `scale(${p}) rotate(${(1 - p) * -30}deg)` }}>
        <Icon name={g.icon} size={170} color={col} />
      </div>
      <div style={{ fontSize: 150, fontWeight: 900, color: col, letterSpacing: -3, lineHeight: 1, opacity: big, transform: `scale(${0.6 + 0.4 * big})` }}>{g.big}</div>
      <div style={{ fontSize: 50, fontWeight: 800, color: C.white, opacity: pop(f, fps, at(g.labelD, fps, 10)), maxWidth: 900, lineHeight: 1.25 }}>{g.label}</div>
    </div>
  );
};

const TitleCard: React.FC<{ g: Extract<Graphic, { type: "title" }>; f: number }> = ({ g, f }) => {
  const { fps } = useVideoConfig();
  const p = pop(f, fps, 4);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 26, alignItems: "flex-start" }}>
      <Kicker text={g.kicker} f={f} />
      <div style={{ fontSize: 96, fontWeight: 900, color: C.white, lineHeight: 1.12, letterSpacing: -2, opacity: p, transform: `translateY(${(1 - p) * 50}px)` }}>
        {g.text}
      </div>
      <div style={{ width: 260 * p, height: 12, borderRadius: 6, background: C.orange }} />
    </div>
  );
};

const MediaCard: React.FC<{ g: Extract<Graphic, { type: "media" }>; f: number; dur: number }> = ({ g, f, dur }) => {
  const { fps } = useVideoConfig();
  const p = pop(f, fps, at(g.d, fps, 2));
  const kb = g.kenBurns === false ? 1 : interpolate(f, [0, dur], [1, 1.08]);
  const isVideo = /\.(mp4|mov|webm|m4v)$/i.test(g.src);
  const style: React.CSSProperties = { width: "100%", height: "100%", objectFit: g.fit ?? "cover", transform: `scale(${kb})` };
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 26, alignItems: "center" }}>
      <div style={{ width: DESIGN.w, height: g.label ? 700 : 820, borderRadius: 34, overflow: "hidden", border: `3px solid ${C.line}`, boxShadow: `0 24px 60px rgba(0,0,0,0.45), 0 0 40px ${C.orange}33`, opacity: p, transform: `scale(${0.94 + 0.06 * p})`, background: C.panel }}>
        {isVideo ? <OffthreadVideo src={asset(g.src)} muted style={style} /> : <Img src={asset(g.src)} style={style} />}
      </div>
      {g.label ? <Kicker text={g.label} f={f - 6} /> : null}
    </div>
  );
};

export const GraphicView: React.FC<{ g: Graphic; f: number; dur?: number }> = ({ g, f, dur = 120 }) => {
  switch (g.type) {
    case "price":
      return <PriceCard g={g} f={f} />;
    case "chart":
      return <ChartCard g={g} f={f} />;
    case "levels":
      return <LevelsCard g={g} f={f} />;
    case "list":
      return <ListCard g={g} f={f} />;
    case "stat":
      return <StatCard g={g} f={f} />;
    case "title":
      return <TitleCard g={g} f={f} />;
    case "media":
      return <MediaCard g={g} f={f} dur={dur} />;
  }
};

/** Khung đồ hoạ: vẽ trên khung thiết kế 940 × 880 rồi thu phóng vừa vùng đồ hoạ của khổ hình, có hiệu ứng vào/ra. */
export const GraphicPanel: React.FC<{ g: Graphic; durationFrames: number; area: Rect }> = ({ g, durationFrames, area }) => {
  const f = useCurrentFrame();
  const out = interpolate(f, [durationFrames - 8, durationFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const k = Math.min(area.w / DESIGN.w, area.h / DESIGN.h);
  return (
    <div
      style={{
        position: "absolute",
        left: area.x + (area.w - DESIGN.w * k) / 2,
        top: area.y + (area.h - DESIGN.h * k) / 2,
        width: DESIGN.w,
        height: DESIGN.h,
        transform: `scale(${k})`,
        transformOrigin: "0 0",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        fontFamily: C.font,
        opacity: out * interpolate(f, [0, 10], [0, 1], { extrapolateRight: "clamp" }),
        filter: `blur(${(1 - out) * 8 + interpolate(f, [0, 10], [8, 0], { extrapolateRight: "clamp" })}px)`,
      }}
    >
      <GraphicView g={g} f={f} dur={durationFrames} />
    </div>
  );
};
