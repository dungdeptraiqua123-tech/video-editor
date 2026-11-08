import React from "react";
import { Easing, Img, interpolate, OffthreadVideo, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { asset } from "./assets";
import { Icon } from "./Icons";
import { DESIGN, Rect } from "./layout";
import { C, glow } from "./theme";
import { Graphic, Transition } from "./types";

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
        {g.yLabels && g.yLabels.length === 2 ? (
          <>
            <text x={w} y={14} textAnchor="end" fontSize="28" fontWeight="700" fill={C.mute} fontFamily={C.font}>{g.yLabels[1]}</text>
            <text x={w} y={h - 30} textAnchor="end" fontSize="28" fontWeight="700" fill={C.mute} fontFamily={C.font}>{g.yLabels[0]}</text>
          </>
        ) : null}
        {g.xLabels && g.xLabels.length >= 2 ? (
          <>
            <text x={0} y={h + 40} textAnchor="start" fontSize="28" fontWeight="700" fill={C.mute} fontFamily={C.font}>{g.xLabels[0]}</text>
            <text x={w} y={h + 40} textAnchor="end" fontSize="28" fontWeight="700" fill={C.mute} fontFamily={C.font}>{g.xLabels[g.xLabels.length - 1]}</text>
          </>
        ) : null}
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
      {g.source ? <div style={{ marginTop: g.xLabels ? 30 : 0, fontSize: 26, color: C.mute, fontWeight: 600 }}>{g.source}</div> : null}
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


const toneCol = (tone?: "up" | "down" | "neutral") => (tone === "up" ? C.green : tone === "down" ? C.red : C.gold);

const CompareCard: React.FC<{ g: Extract<Graphic, { type: "compare" }>; f: number }> = ({ g, f }) => {
  const { fps } = useVideoConfig();
  const sides = [g.left, g.right];
  const vs = pop(f, fps, 10);
  const win = g.winner ? (g.winner === "left" ? 0 : 1) : -1;
  const lastD = Math.max(...sides.map((s, i) => at(s.d, fps, 8 + i * 14)));
  const crown = pop(f, fps, lastD + 14);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 34 }}>
      <Kicker text={g.title} f={f} />
      <div style={{ display: "flex", alignItems: "stretch", gap: 0, position: "relative" }}>
        {sides.map((s, i) => {
          const p = pop(f, fps, at(s.d, fps, 8 + i * 14));
          const col = s.tone ? toneCol(s.tone) : i === 0 ? C.orange : C.sky;
          const isWin = win === i;
          return (
            <div
              key={i}
              style={{
                flex: 1,
                margin: i === 0 ? "0 30px 0 0" : "0 0 0 30px",
                background: C.panel,
                border: `3px solid ${isWin ? col : C.line}`,
                borderRadius: 30,
                padding: "34px 26px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 18,
                opacity: p,
                transform: `translateX(${(1 - p) * (i === 0 ? -90 : 90)}px) scale(${isWin ? 1 + 0.05 * crown : 1})`,
                boxShadow: isWin ? `0 0 ${40 * crown}px ${col}88` : "0 18px 40px rgba(0,0,0,0.35)",
              }}
            >
              {s.icon ? <Icon name={s.icon} size={110} color={col} /> : null}
              <div style={{ fontSize: 40, fontWeight: 800, color: C.mute, textTransform: "uppercase", textAlign: "center" }}>{s.label}</div>
              <div style={{ fontSize: 84, fontWeight: 900, color: col, lineHeight: 1, textAlign: "center", letterSpacing: -2 }}>{s.value}</div>
            </div>
          );
        })}
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            width: 110,
            height: 110,
            marginLeft: -55,
            marginTop: -55,
            borderRadius: "50%",
            background: C.orange,
            color: C.white,
            fontWeight: 900,
            fontSize: 46,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transform: `scale(${vs}) rotate(${(1 - vs) * 180}deg)`,
            boxShadow: `0 0 0 8px ${C.night}, 0 0 40px ${C.orange}aa`,
          }}
        >
          VS
        </div>
      </div>
    </div>
  );
};

const TimelineCard: React.FC<{ g: Extract<Graphic, { type: "timeline" }>; f: number }> = ({ g, f }) => {
  const { fps } = useVideoConfig();
  const n = g.items.length;
  const shown = g.items.map((it, i) => at(it.d, fps, 10 + i * 12));
  // đường trục mọc dần tới mốc vừa được nói
  const grow = interpolate(f, [0, ...shown.map((x) => x + 6)], [0, ...shown.map((_, i) => (i + 1) / n)], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 30 }}>
      <Kicker text={g.title} f={f} />
      <div style={{ position: "relative", paddingLeft: 70 }}>
        <div style={{ position: "absolute", left: 28, top: 20, width: 8, borderRadius: 4, height: `calc(${grow * 100}% - 40px)`, background: `linear-gradient(${C.orange}, ${C.sky})`, boxShadow: glow(C.orange, 10) }} />
        {g.items.map((it, i) => {
          const p = pop(f, fps, shown[i]);
          return (
            <div key={i} style={{ position: "relative", display: "flex", alignItems: "center", gap: 26, minHeight: Math.min(150, 640 / n), opacity: p, transform: `translateX(${(1 - p) * 60}px)` }}>
              <div style={{ position: "absolute", left: -58, width: 36, height: 36, borderRadius: "50%", background: C.night, border: `7px solid ${i === n - 1 ? C.sky : C.orange}`, transform: `scale(${p})`, boxShadow: glow(C.orange, 12 * p) }} />
              <div style={{ minWidth: 190, fontSize: 44, fontWeight: 900, color: C.gold }}>{it.when}</div>
              <div style={{ fontSize: 42, fontWeight: 700, color: C.white, lineHeight: 1.2 }}>{it.text}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const Ring: React.FC<{ v: number; p: number; size: number; col: string; label: string; suffix: string }> = ({ v, p, size, col, label, suffix }) => {
  const r = size / 2 - 22;
  const c = 2 * Math.PI * r;
  const shown = v * p;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
      <div style={{ position: "relative", width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={C.line} strokeWidth="30" />
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={col} strokeWidth="30" strokeLinecap="round" strokeDasharray={`${(c * Math.min(100, shown)) / 100} ${c}`} style={{ filter: `drop-shadow(0 0 12px ${col})` }} />
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: size * 0.24, fontWeight: 900, color: C.white }}>
          {fmt(shown, Number.isInteger(v) ? 0 : 1)}
          {suffix}
        </div>
      </div>
      <div style={{ fontSize: 42, fontWeight: 800, color: C.white, textAlign: "center", maxWidth: size + 120 }}>{label}</div>
    </div>
  );
};

const ProgressCard: React.FC<{ g: Extract<Graphic, { type: "progress" }>; f: number }> = ({ g, f }) => {
  const { fps } = useVideoConfig();
  const ring = g.ring ?? g.items.length <= 2;
  const fill = (i: number, d?: number) => interpolate(f, [at(d, fps, 8 + i * 10) - 4, at(d, fps, 8 + i * 10) + 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  if (ring) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 40 }}>
        <Kicker text={g.title} f={f} />
        <div style={{ display: "flex", justifyContent: "space-around" }}>
          {g.items.map((it, i) => (
            <Ring key={i} v={it.value} p={fill(i, it.d)} size={g.items.length === 1 ? 460 : 380} col={i % 2 ? C.sky : C.orange} label={it.label} suffix={it.suffix ?? "%"} />
          ))}
        </div>
      </div>
    );
  }
  const max = Math.max(100, ...g.items.map((x) => x.value));
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 34 }}>
      <Kicker text={g.title} f={f} />
      {g.items.map((it, i) => {
        const p = fill(i, it.d);
        return (
          <div key={i} style={{ display: "flex", flexDirection: "column", gap: 12, opacity: Math.min(1, p * 3) }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 40, fontWeight: 800, color: C.white }}>
              <span>{it.label}</span>
              <span style={{ color: C.gold }}>
                {fmt(it.value * p, Number.isInteger(it.value) ? 0 : 1)}
                {it.suffix ?? "%"}
              </span>
            </div>
            <div style={{ height: 34, borderRadius: 17, background: C.line, overflow: "hidden" }}>
              <div style={{ width: `${((it.value * p) / max) * 100}%`, height: "100%", borderRadius: 17, background: `linear-gradient(90deg, ${C.orange}, ${C.sky})`, boxShadow: glow(C.orange, 12) }} />
            </div>
          </div>
        );
      })}
    </div>
  );
};

const QuoteCard: React.FC<{ g: Extract<Graphic, { type: "quote" }>; f: number }> = ({ g, f }) => {
  const { fps } = useVideoConfig();
  const start = at(g.d, fps, 6);
  const mark = pop(f, fps, start - 6);
  // chữ hiện dần như đang gõ, xong trong khoảng 1,2 giây
  const chars = Math.round(interpolate(f, [start, start + Math.max(18, Math.min(42, g.text.length * 0.6))], [0, g.text.length], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24, position: "relative", padding: "20px 10px" }}>
      <div style={{ fontSize: 260, lineHeight: 0.7, color: C.orange, fontWeight: 900, fontFamily: "Georgia, serif", transform: `scale(${mark}) rotate(${(1 - mark) * -40}deg)`, transformOrigin: "left top", textShadow: glow(C.orange, 20), height: 150 }}>“</div>
      <div style={{ fontSize: 64, fontWeight: 800, color: C.white, lineHeight: 1.28, minHeight: 300 }}>
        {g.text.slice(0, chars)}
        <span style={{ opacity: chars < g.text.length && Math.floor(f / 8) % 2 === 0 ? 1 : 0, color: C.sky }}>▍</span>
      </div>
      {g.author ? (
        <div style={{ display: "flex", alignItems: "center", gap: 18, opacity: pop(f, fps, start + 30) }}>
          <div style={{ width: 70, height: 6, borderRadius: 3, background: C.orange }} />
          <div style={{ fontSize: 42, fontWeight: 800, color: C.sky }}>{g.author}</div>
        </div>
      ) : null}
    </div>
  );
};

const TableCard: React.FC<{ g: Extract<Graphic, { type: "table" }>; f: number }> = ({ g, f }) => {
  const { fps } = useVideoConfig();
  const n = g.cols.length;
  const fs = n >= 4 ? 34 : 40;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 26 }}>
      <Kicker text={g.title} f={f} />
      <div style={{ borderRadius: 26, overflow: "hidden", border: `2px solid ${C.line}`, background: C.panel, opacity: pop(f, fps, 4) }}>
        <div style={{ display: "flex", background: C.orange }}>
          {g.cols.map((c, i) => (
            <div key={i} style={{ flex: i === 0 ? 1.4 : 1, padding: "18px 22px", fontSize: fs, fontWeight: 900, color: C.white, textAlign: i === 0 ? "left" : "right", textTransform: "uppercase" }}>
              {c}
            </div>
          ))}
        </div>
        {g.rows.map((r, k) => {
          const p = pop(f, fps, at(r.d, fps, 10 + k * 8));
          return (
            <div key={k} style={{ display: "flex", borderTop: `2px solid ${C.line}`, background: k % 2 ? "rgba(255,255,255,0.03)" : "transparent", opacity: p, transform: `translateY(${(1 - p) * 20}px)` }}>
              {r.cells.map((c, i) => (
                <div key={i} style={{ flex: i === 0 ? 1.4 : 1, padding: "20px 22px", fontSize: fs + 2, fontWeight: i === 0 ? 700 : 900, color: i === 0 ? C.white : r.tone ? toneCol(r.tone) : C.white, textAlign: i === 0 ? "left" : "right" }}>
                  {c}
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const CountdownCard: React.FC<{ g: Extract<Graphic, { type: "countdown" }>; f: number }> = ({ g, f }) => {
  const { fps } = useVideoConfig();
  const n = g.items.length;
  const times = g.items.map((it, i) => at(it.d, fps, 8 + i * 30));
  let cur = -1;
  times.forEach((x, i) => {
    if (f >= x - 4) cur = i;
  });
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 30 }}>
      <Kicker text={g.title} f={f} />
      <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
        {g.items.map((it, i) => {
          const p = pop(f, fps, times[i] - 4);
          const active = i === cur;
          const num = n - i;
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 26, opacity: f >= times[i] - 4 ? (active ? 1 : 0.55) : 0, transform: `translateX(${(1 - p) * -80}px) scale(${active ? 1 : 0.94})`, transformOrigin: "left center" }}>
              <div
                style={{
                  width: 120,
                  height: 120,
                  borderRadius: 26,
                  background: active ? C.orange : C.panel,
                  border: `3px solid ${active ? C.orange : C.line}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 78,
                  fontWeight: 900,
                  color: C.white,
                  transform: `rotateX(${(1 - p) * 90}deg)`,
                  boxShadow: active ? glow(C.orange, 20) : undefined,
                  flexShrink: 0,
                }}
              >
                {num}
              </div>
              <div style={{ fontSize: active ? 52 : 44, fontWeight: 800, color: C.white, lineHeight: 1.18 }}>{it.text}</div>
            </div>
          );
        })}
      </div>
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
    case "compare":
      return <CompareCard g={g} f={f} />;
    case "timeline":
      return <TimelineCard g={g} f={f} />;
    case "progress":
      return <ProgressCard g={g} f={f} />;
    case "quote":
      return <QuoteCard g={g} f={f} />;
    case "table":
      return <TableCard g={g} f={f} />;
    case "countdown":
      return <CountdownCard g={g} f={f} />;
  }
};

/** Khung đồ hoạ: vẽ trên khung thiết kế 940 × 880 rồi thu phóng vừa vùng đồ hoạ của khổ hình, có hiệu ứng vào/ra. */
/** Khung ít mục thì phóng to chữ và icon cho đầy khung (tránh 1–2 dòng chữ nhỏ giữa khoảng trống lớn). */
export const fillZoom = (g: Graphic): number => {
  const n = (g as { items?: unknown[] }).items?.length ?? (g as { levels?: unknown[] }).levels?.length ?? (g as { rows?: unknown[] }).rows?.length ?? 0;
  switch (g.type) {
    case "list":
      return n <= 1 ? 1.45 : n === 2 ? 1.35 : n === 3 ? 1.15 : 1;
    case "levels":
      return n <= 2 ? 1.25 : n === 3 ? 1.1 : 1;
    case "countdown":
      return n <= 3 ? 1.15 : 1;
    case "timeline":
      return n <= 2 ? 1.2 : n === 3 ? 1.1 : 1;
    case "progress":
      return n <= 1 ? 1.3 : n === 2 ? 1.15 : 1;
    case "table":
      return n <= 2 ? 1.15 : 1;
    case "compare":
      return 1.1;
    default:
      return 1;
  }
};

export const GraphicPanel: React.FC<{ g: Graphic; durationFrames: number; area: Rect; tr?: Transition }> = ({ g, durationFrames, area, tr = "mem" }) => {
  const f = useCurrentFrame();
  const inP = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp", easing: ease });
  const enter = tr === "vuot" ? `translateX(${(1 - inP) * 260}px)` : tr === "zoom" ? `scale(${1 + (1 - inP) * 0.25})` : tr === "glitch" ? `translateX(${f < 8 ? Math.sin(f * 7) * 18 : 0}px)` : "";
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
        transform: `scale(${k}) ${enter}`,
        transformOrigin: "0 0",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        fontFamily: C.font,
        opacity: out * interpolate(f, [0, 10], [0, 1], { extrapolateRight: "clamp" }),
        filter: `blur(${(1 - out) * 8 + interpolate(f, [0, 10], [8, 0], { extrapolateRight: "clamp" })}px)`,
      }}
    >
      <div style={{ zoom: fillZoom(g), width: DESIGN.w / fillZoom(g) }}>
        <GraphicView g={g} f={f} dur={durationFrames} />
      </div>
    </div>
  );
};
