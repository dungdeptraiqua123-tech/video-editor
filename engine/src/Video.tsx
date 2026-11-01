import React, { useEffect, useState } from "react";
import {
  AbsoluteFill,
  Audio,
  continueRender,
  delayRender,
  Easing,
  Img,
  interpolate,
  Loop,
  OffthreadVideo,
  Sequence,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Captions } from "./Captions";
import { GraphicPanel } from "./Graphics";
import { asset, setMediaBase } from "./assets";
import { Icon } from "./Icons";
import { faceAt, fitVideo, Layout, layoutFor } from "./layout";
import { alpha, applyBrand, C, glow } from "./theme";
import { Brand, Props, Topic } from "./types";

const RAMP = 14; // số khung hình chuyển giữa chế độ người nói và chế độ đồ hoạ

const ease = Easing.bezier(0.65, 0, 0.35, 1);
const lerp = (a: number, b: number, p: number) => a + (b - a) * p;
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** 0 = người nói toàn màn hình, 1 = đồ hoạ toàn màn hình + ô mặt người nói ở góc. */
const modeAt = (frame: number, fps: number, beats: Props["beats"]) => {
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

/** Font riêng của thương hiệu (file trong media/), chờ tải xong mới vẽ. */
const useBrandFont = (brand: Brand) => {
  const [handle] = useState(() => (brand.font.file ? delayRender("font") : null));
  useEffect(() => {
    if (!brand.font.file || handle === null) return;
    const face = new FontFace(brand.font.family, `url(${asset(brand.font.file)})`);
    face
      .load()
      .then((f) => {
        (document.fonts as unknown as { add: (x: FontFace) => void }).add(f);
        continueRender(handle);
      })
      .catch(() => continueRender(handle));
  }, [brand.font, handle]);
};

const Backdrop: React.FC<{ o: number; kind?: string }> = ({ o, kind }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ opacity: o, background: `radial-gradient(ellipse at 50% 55%, ${C.night2} 0%, ${C.night} 62%)` }}>
      {kind === "plain" ? null : (
        <AbsoluteFill
          style={{
            backgroundImage: `linear-gradient(${C.line}66 1px, transparent 1px), linear-gradient(90deg, ${C.line}66 1px, transparent 1px)`,
            backgroundSize: "72px 72px",
            backgroundPosition: `0 ${(f * 0.4) % 72}px`,
            maskImage: "radial-gradient(ellipse at 50% 50%, black 10%, transparent 70%)",
          }}
        />
      )}
    </AbsoluteFill>
  );
};

/** Video nền (b-roll sản phẩm) lặp lại, tắt tiếng, phủ lớp tối để chữ và đồ hoạ dễ đọc. */
const BRoll: React.FC<{ src: string; duration: number }> = ({ src, duration }) => {
  const { fps } = useVideoConfig();
  const isVideo = /\.(mp4|mov|webm|m4v)$/i.test(src);
  return (
    <AbsoluteFill>
      {isVideo ? (
        <Loop durationInFrames={Math.max(1, Math.floor(duration * fps))}>
          <OffthreadVideo src={asset(src)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </Loop>
      ) : (
        <Img src={asset(src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      )}
      <AbsoluteFill style={{ background: `linear-gradient(180deg, ${alpha(C.night, 0.55)} 0%, ${alpha(C.night, 0.75)} 100%)` }} />
    </AbsoluteFill>
  );
};

const BrandTag: React.FC<{ L: Layout; badge: string; title: string; o: number }> = ({ L, badge, title, o }) => (
  <div style={{ position: "absolute", left: L.head.x, top: L.head.y, width: L.head.w, fontFamily: C.font, opacity: o }}>
    <div style={{ color: C.sky, fontSize: 28 * L.u, fontWeight: 800, letterSpacing: 3, textTransform: "uppercase" }}>{badge}</div>
    <div style={{ color: C.white, fontSize: 62 * L.u, fontWeight: 900, lineHeight: 1.12, marginTop: 10 }}>{title}</div>
    <div style={{ width: 120, height: 7, borderRadius: 4, background: C.orange, marginTop: 18, boxShadow: glow(C.orange, 12) }} />
  </div>
);

const TopicCard: React.FC<{ L: Layout; topic: Topic; o: number }> = ({ L, topic, o }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const a = spring({ frame: f - Math.round(topic.start * fps), fps, config: { damping: 18, stiffness: 160 } });
  const shown = topic.items.filter((it) => t >= it.at);
  return (
    <div
      style={{
        position: "absolute",
        left: L.topic.x,
        top: L.topic.y,
        maxWidth: L.topic.maxW,
        fontFamily: C.font,
        background: alpha(C.panel, 0.86),
        border: `2px solid ${C.line}`,
        borderRadius: 26,
        padding: "22px 34px 26px",
        boxShadow: "0 18px 40px rgba(0,0,0,0.35)",
        opacity: o * a,
        transform: `translateY(${(1 - a) * -30}px)`,
      }}
    >
      <div style={{ color: C.sky, fontSize: 24 * L.u, fontWeight: 800, letterSpacing: 3, textTransform: "uppercase" }}>{topic.kicker}</div>
      <div style={{ color: C.white, fontSize: 48 * L.u, fontWeight: 800, lineHeight: 1.15, marginTop: 6 }}>{topic.title}</div>
      {shown.map((it, i) => {
        const p = spring({ frame: f - Math.round(it.at * fps), fps, config: { damping: 16, stiffness: 200 } });
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 12, opacity: p, transform: `translateX(${(1 - p) * -24}px)` }}>
            <div style={{ transform: `scale(${p})` }}>
              <Icon name="check" size={40 * L.u} color={C.orange} />
            </div>
            <div style={{ color: C.white, fontSize: 36 * L.u, fontWeight: 600 }}>{it.text}</div>
          </div>
        );
      })}
    </div>
  );
};

const Hook: React.FC<{ L: Layout; hook: Props["hook"]; brand: Brand; sec: number }> = ({ L, hook, brand, sec }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = spring({ frame: f, fps, config: { damping: 16, stiffness: 150 } });
  const b = spring({ frame: f - 6, fps, config: { damping: 16, stiffness: 140 } });
  const out = interpolate(f, [sec * fps - 8, sec * fps], [1, 0], clamp);
  const badge = hook.kicker || brand.badge;
  return (
    <AbsoluteFill style={{ fontFamily: C.font, opacity: out }}>
      <div style={{ position: "absolute", top: L.hookTop, left: 60, right: 60, display: "flex", flexDirection: "column", alignItems: "center", gap: 20 * L.u }}>
        {badge || brand.logo || brand.hookIcon ? (
          <div style={{ display: "flex", alignItems: "center", gap: 16, background: alpha(C.night, 0.85), border: `2px solid ${C.orange}`, borderRadius: 999, padding: "8px 28px 8px 10px", transform: `scale(${a})`, boxShadow: glow(C.orange, 14) }}>
            {brand.logo ? <Img src={asset(brand.logo)} style={{ height: 60 * L.u, maxWidth: 220 }} /> : brand.hookIcon ? <Icon name={brand.hookIcon} size={60 * L.u} /> : <div style={{ width: 12 }} />}
            {badge ? <span style={{ color: C.sky, fontSize: 36 * L.u, fontWeight: 800, letterSpacing: 3 }}>{badge}</span> : null}
          </div>
        ) : null}
        <div
          style={{
            background: `linear-gradient(135deg, ${C.orange}, ${alpha(C.orange, 0.75)})`,
            color: C.white,
            fontSize: 78 * L.u,
            fontWeight: 900,
            lineHeight: 1.1,
            textAlign: "center",
            padding: "20px 36px",
            borderRadius: 26,
            maxWidth: Math.min(L.w - 120, 1300),
            transform: `scale(${b})`,
            boxShadow: `0 18px 50px rgba(0,0,0,0.4), ${glow(C.orange, 26)}`,
          }}
        >
          {hook.title}
        </div>
        {hook.sub ? (
          <div style={{ color: C.gold, fontSize: 46 * L.u, fontWeight: 800, background: alpha(C.night, 0.85), padding: "10px 26px", borderRadius: 16, opacity: spring({ frame: f - 14, fps }) }}>
            {hook.sub}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

const Outro: React.FC<{ L: Layout; cta: string; buttons: string[] }> = ({ L, cta, buttons }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = spring({ frame: f, fps, config: { damping: 16, stiffness: 150 } });
  const tap = spring({ frame: f - 30, fps, config: { damping: 8, stiffness: 200 } });
  return (
    <AbsoluteFill style={{ fontFamily: C.font }}>
      <div style={{ position: "absolute", top: L.outroTop, left: 70, right: 70, display: "flex", flexDirection: "column", alignItems: "center", gap: 26 * L.u, transform: `translateY(${(1 - a) * -80}px)`, opacity: a }}>
        <div style={{ background: alpha(C.panel, 0.92), border: `2px solid ${C.orange}`, boxShadow: glow(C.orange, 18), borderRadius: 30, padding: "26px 36px", color: C.white, fontSize: 54 * L.u, fontWeight: 800, textAlign: "center", lineHeight: 1.2, maxWidth: 1300 }}>
          {cta}
        </div>
        <div style={{ display: "flex", gap: 22 }}>
          {buttons.map((t, i) => (
            <div
              key={t}
              style={{
                background: i === 0 ? C.orange : "rgba(255,255,255,0.95)",
                color: i === 0 ? C.white : C.night,
                fontSize: 40 * L.u,
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

/** Thời điểm (giây tính từ lúc khung mở) các phần tử trong khung đồ hoạ bật ra: mọi khoá d / xxxD. */
const elementTimes = (o: unknown): number[] => {
  if (Array.isArray(o)) return o.flatMap(elementTimes);
  if (!o || typeof o !== "object") return [];
  return Object.entries(o as Record<string, unknown>).flatMap(([k, v]) =>
    typeof v === "number" ? (k === "d" || /[a-z]D$/.test(k) ? [v] : []) : elementTimes(v),
  );
};

export const Video: React.FC<Props> = (props) => {
  const { brand, media, captions, beats, topics, zooms, words, hook } = props;
  applyBrand(brand);
  setMediaBase(props.mediaBase);
  useBrandFont(brand);
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();
  const L = layoutFor(width, height);
  const t = frame / fps;
  const p = modeAt(frame, fps, beats);
  const faceless = props.mode === "faceless" || !media.hasVideo;
  const sfx = (role: "whoosh" | "impact" | "riser" | "click" | "pop" | "tick") => (props.sfx ? props.sfx.files[role] : undefined);
  const sfxVol = props.sfx ? props.sfx.volume : 0;

  // zoom cắt nhảy khi người nói toàn màn hình: luân phiên khung rộng / khung chặt
  const zi = zooms.filter((z) => z <= t).length;
  const zoom = zi % 2 ? 1.1 : 1;

  // bám mặt: tâm khung đi theo người nói (đường đi đã làm mượt, nhảy thẳng ở chỗ cắt)
  const [faceNX, faceNY] = faceAt(media.faceTrack, t, media.face?.x ?? 0.5, media.face?.y ?? 0.4);
  const fit = !faceless && media.srcW && media.srcH ? fitVideo(L, media.srcW, media.srcH, faceNX, faceNY, media.face?.fit) : null;
  // nền thương hiệu: luôn có khi không người nói hoặc khi video gốc khác khổ (contain), còn lại chỉ khi hiện đồ hoạ
  const bg = faceless || fit?.mode === "contain" ? 1 : p;
  const pipScale = media.face?.pipScale ?? (L.pip.h * 0.5) / ((fit?.vh ?? L.h) * 0.26);
  const box = { x: lerp(0, L.pip.x, p), y: lerp(0, L.pip.y, p), w: lerp(L.w, L.pip.w, p), h: lerp(L.h, L.pip.h, p), r: lerp(0, L.pip.r, p) };
  const fx = fit?.faceX ?? L.w / 2;
  const fy = fit?.faceY ?? L.h / 2;
  const s = lerp(zoom, pipScale, p);
  const tx = lerp(fx - fx * zoom, L.pip.w / 2 - fx * pipScale, p);
  const ty = lerp(fy - fy * zoom, L.pip.h / 2 - fy * pipScale, p);

  const beat = beats.find((b) => t >= b.start - 0.3 && t < b.end + 0.3);
  const topic = topics.find((x) => t >= x.start && t < x.end);
  const outroFrom = durationInFrames - Math.round(props.outroSec * fps);
  // phần kết: phụ đề dời xuống dưới để không đè khung kêu gọi
  const endP = interpolate(frame, [outroFrom - 10, outroFrom], [0, 1], { ...clamp, easing: ease });
  const capBase = faceless ? lerp(L.capCenter, L.capGfx, p) : lerp(L.capTalk, L.capGfx, p);
  const capY = captions.position != null ? captions.position * L.h : lerp(capBase, Math.max(capBase, L.capGfx), endP);

  return (
    <AbsoluteFill style={{ background: C.night }}>
      {faceless && media.background ? <BRoll src={media.background.src} duration={media.background.duration} /> : <Backdrop o={bg} kind={brand.backdrop} />}
      {faceless && media.main ? <Audio src={asset(media.main)} /> : null}
      {media.music ? <Audio src={asset(media.music.src)} volume={media.music.volume} loop /> : null}

      {fit ? (
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
          <div style={{ position: "absolute", left: 0, top: 0, width: L.w, height: L.h, transform: `translate(${tx}px, ${ty}px) scale(${s})`, transformOrigin: "0 0" }}>
            <OffthreadVideo src={asset(media.main)} style={{ position: "absolute", left: fit.ox, top: fit.oy, width: fit.vw, height: fit.vh }} />
          </div>
        </div>
      ) : null}

      {/* nền tối mờ phía dưới để phụ đề trắng luôn dễ đọc */}
      <AbsoluteFill style={{ background: `linear-gradient(to bottom, transparent 58%, ${alpha(C.night, 0.55)} 80%, ${alpha(C.night, 0.7)} 100%)`, opacity: 1 - bg }} />

      {beat && beat.head ? <BrandTag L={L} badge={brand.badge} title={beat.head} o={p} /> : null}

      {beats.map((b, i) => {
        const from = Math.round(b.start * fps);
        const dur = Math.max(1, Math.round((b.end - b.start) * fps));
        return (
          <Sequence key={i} from={from} durationInFrames={dur} layout="none">
            <GraphicPanel g={b.g} durationFrames={dur} area={L.panel} />
          </Sequence>
        );
      })}

      {sfx("whoosh")
        ? beats.map((b, i) => (
            <Sequence key={`w${i}`} from={Math.max(0, Math.round(b.start * fps) - 6)} durationInFrames={24}>
              <Audio src={asset(sfx("whoosh")!)} volume={0.17 * sfxVol} />
            </Sequence>
          ))
        : null}

      {/* pop: từng phần tử trong khung đồ hoạ bật ra (bỏ phần tử bật ngay lúc khung mở, đã có whoosh) */}
      {sfx("pop")
        ? beats.flatMap((b, i) =>
            elementTimes(b.g)
              .filter((d) => d > 0.25)
              .map((d, k) => (
                <Sequence key={`p${i}-${k}`} from={Math.round((b.start + d) * fps)} durationInFrames={15}>
                  <Audio src={asset(sfx("pop")!)} volume={0.22 * sfxVol} />
                </Sequence>
              )),
          )
        : null}
      {/* tick: ý trong thẻ chủ đề được đánh dấu (chỉ khi thẻ đang hiện) */}
      {sfx("tick") && !faceless
        ? topics.flatMap((tp, i) =>
            tp.items
              .filter((it) => it.at >= props.hookSec && it.at * fps < outroFrom)
              .map((it, k) => (
                <Sequence key={`t${i}-${k}`} from={Math.round(it.at * fps)} durationInFrames={15}>
                  <Audio src={asset(sfx("tick")!)} volume={0.5 * sfxVol} />
                </Sequence>
              )),
          )
        : null}

      {topic && t >= props.hookSec && frame < outroFrom ? <TopicCard L={L} topic={topic} o={1 - p} /> : null}

      <Sequence durationInFrames={Math.round(props.hookSec * fps)}>
        <Hook L={L} hook={hook} brand={brand} sec={props.hookSec} />
        {sfx("impact") ? (
          <Sequence durationInFrames={40}>
            <Audio src={asset(sfx("impact")!)} volume={0.19 * sfxVol} />
          </Sequence>
        ) : null}
      </Sequence>

      {captions.enabled ? <Captions words={words} y={capY} cfg={captions} side={L.capSide} u={L.u} /> : null}

      <Sequence from={outroFrom}>
        <Outro L={L} cta={props.cta} buttons={props.ctaButtons ?? ["Theo dõi", "Thích", "Chia sẻ"]} />
      </Sequence>
      {sfx("riser") ? (
        <Sequence from={Math.max(0, outroFrom - 30)} durationInFrames={40}>
          <Audio src={asset(sfx("riser")!)} volume={0.21 * sfxVol} />
        </Sequence>
      ) : null}
      {sfx("click") ? (
        <Sequence from={outroFrom + 30} durationInFrames={20}>
          <Audio src={asset(sfx("click")!)} volume={0.41 * sfxVol} />
        </Sequence>
      ) : null}

      {/* thanh tiến độ */}
      <div style={{ position: "absolute", top: 0, left: 0, height: 8, width: (L.w * frame) / durationInFrames, background: C.sky, boxShadow: glow(C.orange, 10) }} />
    </AbsoluteFill>
  );
};
