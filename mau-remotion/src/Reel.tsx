import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  interpolate,
  OffthreadVideo,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Captions, CaptionStyle } from "./Captions";
import { GraphicPanel } from "./Graphics";
import { Icon } from "./Icons";
import { C, glow, H, PIP, W } from "./theme";
import { ReelData, Topic } from "./types";

const RAMP = 14; // số khung hình chuyển giữa chế độ người nói và chế độ đồ hoạ
const FACE_X = 540; // vị trí khuôn mặt trong video gốc
const FACE_Y = 760;
const PIP_SCALE = 0.3; // tỉ lệ video trong ô mặt người nói
const HOOK_SEC = 3.2;
const OUTRO_SEC = 3.6;

const ease = Easing.bezier(0.65, 0, 0.35, 1);
const lerp = (a: number, b: number, p: number) => a + (b - a) * p;
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** 0 = người nói toàn màn hình, 1 = đồ hoạ toàn màn hình + ô mặt người nói ở góc. */
const modeAt = (frame: number, fps: number, beats: ReelData["beats"]) => {
  let p = 0;
  for (const b of beats) {
    const s = b.start * fps;
    const e = b.end * fps;
    const v = Math.min(
      interpolate(frame, [s - RAMP / 2, s + RAMP / 2], [0, 1], { ...clamp, easing: ease }),
      interpolate(frame, [e - RAMP / 2, e + RAMP / 2], [1, 0], { ...clamp, easing: ease }),
    );
    p = Math.max(p, v);
  }
  return p;
};

const Backdrop: React.FC<{ o: number }> = ({ o }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ opacity: o, background: `radial-gradient(ellipse at 50% 55%, #10306e 0%, ${C.night} 62%)` }}>
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${C.line}66 1px, transparent 1px), linear-gradient(90deg, ${C.line}66 1px, transparent 1px)`,
          backgroundSize: "72px 72px",
          backgroundPosition: `0 ${(f * 0.4) % 72}px`,
          maskImage: "radial-gradient(ellipse at 50% 50%, black 10%, transparent 70%)",
        }}
      />
    </AbsoluteFill>
  );
};

const BrandTag: React.FC<{ brand: string; title: string; o: number }> = ({ brand, title, o }) => (
  <div style={{ position: "absolute", left: 70, top: 130, width: 680, fontFamily: C.font, opacity: o }}>
    <div style={{ color: C.sky, fontSize: 28, fontWeight: 800, letterSpacing: 3, textTransform: "uppercase" }}>{brand}</div>
    <div style={{ color: C.white, fontSize: 62, fontWeight: 900, lineHeight: 1.12, marginTop: 10 }}>{title}</div>
    <div style={{ width: 120, height: 7, borderRadius: 4, background: C.orange, marginTop: 18, boxShadow: glow(C.orange, 12) }} />
  </div>
);

const TopicCard: React.FC<{ topic: Topic; o: number }> = ({ topic, o }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const a = spring({ frame: f - Math.round(topic.start * fps), fps, config: { damping: 18, stiffness: 160 } });
  const shown = topic.items.filter((it) => t >= it.at);
  return (
    <div
      style={{
        position: "absolute",
        left: 50,
        top: 90,
        maxWidth: 860,
        fontFamily: C.font,
        background: "rgba(11,27,63,0.86)",
        border: `2px solid ${C.line}`,
        borderRadius: 26,
        padding: "22px 34px 26px",
        boxShadow: "0 18px 40px rgba(0,0,0,0.35)",
        opacity: o * a,
        transform: `translateY(${(1 - a) * -30}px)`,
      }}
    >
      <div style={{ color: C.sky, fontSize: 24, fontWeight: 800, letterSpacing: 3, textTransform: "uppercase" }}>{topic.kicker}</div>
      <div style={{ color: C.white, fontSize: 48, fontWeight: 800, lineHeight: 1.15, marginTop: 6 }}>{topic.title}</div>
      {shown.map((it, i) => {
        const p = spring({ frame: f - Math.round(it.at * fps), fps, config: { damping: 16, stiffness: 200 } });
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 12, opacity: p, transform: `translateX(${(1 - p) * -24}px)` }}>
            <div style={{ transform: `scale(${p})` }}>
              <Icon name="check" size={40} color={C.orange} />
            </div>
            <div style={{ color: C.white, fontSize: 36, fontWeight: 600 }}>{it.text}</div>
          </div>
        );
      })}
    </div>
  );
};

const Hook: React.FC<{ hook: ReelData["hook"]; brand: string }> = ({ hook, brand }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = spring({ frame: f, fps, config: { damping: 16, stiffness: 150 } });
  const b = spring({ frame: f - 6, fps, config: { damping: 16, stiffness: 140 } });
  const out = interpolate(f, [HOOK_SEC * fps - 8, HOOK_SEC * fps], [1, 0], clamp);
  return (
    <AbsoluteFill style={{ fontFamily: C.font, opacity: out }}>
      <div style={{ position: "absolute", top: 150, left: 60, right: 60, display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, background: "rgba(5,14,36,0.85)", border: `2px solid ${C.orange}`, borderRadius: 999, padding: "8px 28px 8px 10px", transform: `scale(${a})`, boxShadow: glow(C.orange, 14) }}>
          <Icon name="btc" size={60} />
          <span style={{ color: C.sky, fontSize: 36, fontWeight: 800, letterSpacing: 3 }}>{brand}</span>
        </div>
        <div
          style={{
            background: `linear-gradient(135deg, ${C.orange}, #1a4fd6)`,
            color: C.white,
            fontSize: 78,
            fontWeight: 900,
            lineHeight: 1.1,
            textAlign: "center",
            padding: "20px 36px",
            borderRadius: 26,
            transform: `scale(${b})`,
            boxShadow: `0 18px 50px rgba(0,0,0,0.4), ${glow(C.orange, 26)}`,
          }}
        >
          {hook.title}
        </div>
        {hook.sub ? (
          <div style={{ color: C.gold, fontSize: 46, fontWeight: 800, background: "rgba(5,14,36,0.85)", padding: "10px 26px", borderRadius: 16, opacity: spring({ frame: f - 14, fps }) }}>
            {hook.sub}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

const Outro: React.FC<{ cta: string }> = ({ cta }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = spring({ frame: f, fps, config: { damping: 16, stiffness: 150 } });
  const tap = spring({ frame: f - 30, fps, config: { damping: 8, stiffness: 200 } });
  return (
    <AbsoluteFill style={{ fontFamily: C.font }}>
      <div style={{ position: "absolute", top: 200, left: 70, right: 70, display: "flex", flexDirection: "column", alignItems: "center", gap: 26, transform: `translateY(${(1 - a) * -80}px)`, opacity: a }}>
        <div style={{ background: "rgba(11,27,63,0.9)", border: `2px solid ${C.orange}`, boxShadow: glow(C.orange, 18), borderRadius: 30, padding: "26px 36px", color: C.white, fontSize: 54, fontWeight: 800, textAlign: "center", lineHeight: 1.2 }}>
          {cta}
        </div>
        <div style={{ display: "flex", gap: 22 }}>
          {["Theo dõi", "Thích", "Chia sẻ"].map((t, i) => (
            <div
              key={t}
              style={{
                background: i === 0 ? C.orange : "rgba(255,255,255,0.95)",
                color: i === 0 ? C.white : C.night,
                fontSize: 40,
                fontWeight: 800,
                padding: "16px 30px",
                borderRadius: 999,
                transform: `scale(${spring({ frame: f - 8 - i * 5, fps }) * (i === 0 ? 1 + 0.1 * Math.sin(tap * Math.PI) : 1)})`,
              }}
            >
              {i === 0 ? "+ " : ""}
              {t}
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const BitcoinReel: React.FC<{ data: ReelData; video: string; captionStyle?: CaptionStyle }> = ({ data, video, captionStyle }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;
  const p = modeAt(frame, fps, data.beats);

  // zoom cắt nhảy khi người nói toàn màn hình: luân phiên khung rộng / khung chặt
  const zi = data.zooms.filter((z) => z <= t).length;
  const zoom = zi % 2 ? 1.1 : 1;

  // khung chứa video: từ toàn màn hình thu về ô góc phải
  const box = { x: lerp(0, PIP.x, p), y: lerp(0, PIP.y, p), w: lerp(W, PIP.w, p), h: lerp(H, PIP.h, p), r: lerp(0, PIP.r, p) };
  const s = lerp(zoom, PIP_SCALE, p);
  const tx = lerp(FACE_X - FACE_X * zoom, PIP.w / 2 - FACE_X * PIP_SCALE, p);
  const ty = lerp(FACE_Y - FACE_Y * zoom, PIP.h / 2 - FACE_Y * PIP_SCALE, p);

  const beat = data.beats.find((b) => t >= b.start - 0.3 && t < b.end + 0.3);
  const topic = data.topics.find((x) => t >= x.start && t < x.end);
  const captionY = lerp(1420, 1520, p);
  const outroFrom = durationInFrames - Math.round(OUTRO_SEC * fps);

  return (
    <AbsoluteFill style={{ background: C.night }}>
      <Backdrop o={p} />
      <div
        style={{
          position: "absolute",
          left: box.x,
          top: box.y,
          width: box.w,
          height: box.h,
          borderRadius: box.r,
          overflow: "hidden",
          border: p > 0.01 ? `${4 * p}px solid ${C.sky}` : undefined,
          boxShadow: p > 0.01 ? glow(C.orange, 22 * p) : undefined,
        }}
      >
        <div style={{ position: "absolute", left: 0, top: 0, width: W, height: H, transform: `translate(${tx}px, ${ty}px) scale(${s})`, transformOrigin: "0 0" }}>
          <OffthreadVideo src={staticFile(video)} style={{ width: W, height: H }} />
        </div>
      </div>

      {/* nền tối mờ phía dưới để phụ đề trắng luôn dễ đọc */}
      <AbsoluteFill style={{ background: "linear-gradient(to bottom, transparent 58%, rgba(5,14,36,0.55) 80%, rgba(5,14,36,0.7) 100%)", opacity: 1 - p }} />

      {beat ? <BrandTag brand={data.brand} title={beat.head} o={p} /> : null}

      {data.beats.map((b, i) => {
        const from = Math.round(b.start * fps);
        const dur = Math.max(1, Math.round((b.end - b.start) * fps));
        return (
          <Sequence key={i} from={from} durationInFrames={dur} layout="none">
            <GraphicPanel g={b.g} durationFrames={dur} />
          </Sequence>
        );
      })}

      {data.beats.map((b, i) => (
        <Sequence key={`w${i}`} from={Math.round(b.start * fps) - 6} durationInFrames={20}>
          <Audio src={staticFile("sfx/whoosh.ogg")} volume={0.16} />
        </Sequence>
      ))}

      {topic && t >= HOOK_SEC && frame < outroFrom ? <TopicCard topic={topic} o={1 - p} /> : null}

      <Sequence durationInFrames={Math.round(HOOK_SEC * fps)}>
        <Hook hook={data.hook} brand={data.brand} />
        <Audio src={staticFile("sfx/impact.ogg")} volume={0.3} />
      </Sequence>

      <Captions words={data.words} y={captionY} variant={captionStyle} />

      <Sequence from={outroFrom}>
        <Outro cta={data.cta} />
      </Sequence>
      <Sequence from={outroFrom - 20} durationInFrames={50}>
        <Audio src={staticFile("sfx/riser.ogg")} volume={0.18} />
      </Sequence>
      <Sequence from={outroFrom + 30} durationInFrames={20}>
        <Audio src={staticFile("sfx/click.ogg")} volume={0.3} />
      </Sequence>

      {/* thanh tiến độ */}
      <div style={{ position: "absolute", top: 0, left: 0, height: 8, width: (W * frame) / durationInFrames, background: C.sky, boxShadow: glow(C.orange, 10) }} />
    </AbsoluteFill>
  );
};
