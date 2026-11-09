/**
 * Motion kit: các "viên gạch" có sẵn chuyển động để ghép cảnh motion (xem huong-dan/motion.md).
 * Mọi thời điểm `at`, `d`… tính bằng GIÂY kể từ lúc cảnh mở. Toạ độ x, y, w, h theo khung thiết kế của cảnh
 * (dọc 1080 × 1920, ngang 1920 × 1080): có x/y thì đặt tuyệt đối, không có thì nằm theo dòng.
 */
import React from "react";
import { Img, interpolate, OffthreadVideo, useCurrentFrame, useVideoConfig } from "remotion";
import { asset } from "../assets";
import { clamp, easeInOut, easeOut, prog, rand, useSec, useSpring } from "./anim";
import { M, rgba, shadow } from "./theme";

type Pos = { x?: number; y?: number; w?: number; h?: number; style?: React.CSSProperties };

const place = ({ x, y, w, h, style }: Pos): React.CSSProperties => ({
  ...(x !== undefined || y !== undefined ? { position: "absolute", left: x ?? 0, top: y ?? 0 } : { position: "relative" }),
  ...(w !== undefined ? { width: w } : {}),
  ...(h !== undefined ? { height: h } : {}),
  ...style,
});

const src = (s: string) => (/^(https?:|data:)/.test(s) ? s : asset(s));
const isVideo = (s: string) => /\.(mp4|mov|webm|m4v)$/i.test(s);

/* ------------------------------------------------------------------ nền & xuất hiện */

/** Nền giấy (kiểu sáng) hoặc nền thương hiệu (kiểu tối), có lưới chấm mờ. */
export const Paper: React.FC<{ dots?: boolean; children?: React.ReactNode }> = ({ dots = true, children }) => (
  <div style={{ position: "absolute", inset: 0, background: M.bg, overflow: "hidden" }}>
    {dots ? (
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `radial-gradient(${rgba(M.ink, M.look === "toi" ? 0.08 : 0.06)} 1.6px, transparent 1.6px)`,
          backgroundSize: "34px 34px",
        }}
      />
    ) : null}
    {children}
  </div>
);

/** Bọc bất kỳ thứ gì để nó hiện ra lúc `at`: pop (nảy), rise (trồi lên), fade, blur (mờ → nét), left/right (trượt vào). */
export const Appear: React.FC<Pos & { at?: number; kind?: "pop" | "rise" | "fade" | "blur" | "left" | "right"; out?: number; children?: React.ReactNode }> = ({
  at = 0,
  kind = "rise",
  out,
  children,
  ...pos
}) => {
  const t = useSec();
  const s = useSpring(at, kind === "pop" ? { damping: 11, stiffness: 190 } : { damping: 18, stiffness: 150 });
  const o = Math.min(1, Math.max(0, s * 1.4)) * (out !== undefined ? 1 - prog(t, out, out + 0.3) : 1);
  const tf =
    kind === "pop" ? `scale(${0.6 + 0.4 * s})` : kind === "rise" ? `translateY(${(1 - s) * 60}px)` : kind === "left" ? `translateX(${(1 - s) * -120}px)` : kind === "right" ? `translateX(${(1 - s) * 120}px)` : kind === "blur" ? `scale(${1.04 - 0.04 * s})` : "none";
  return <div style={{ ...place(pos), opacity: o, transform: tf, filter: kind === "blur" ? `blur(${(1 - Math.min(1, s)) * 14}px)` : undefined }}>{children}</div>;
};

/* ------------------------------------------------------------------ chữ */

/** Tiêu đề kiểu biên tập: nhãn nhỏ + dòng serif + dòng nghiêng màu nhấn (có gạch chân tự vẽ). */
export const Headline: React.FC<Pos & { kicker?: string; title: string; accent?: string; at?: number; size?: number; align?: "left" | "center" }> = ({
  kicker,
  title,
  accent,
  at = 0,
  size = 86,
  align = "left",
  ...pos
}) => {
  const t = useSec();
  const line = (i: number) => {
    const p = prog(t, at + i * 0.14, at + i * 0.14 + 0.55, easeOut);
    return { opacity: p, transform: `translateY(${(1 - p) * 34}px)`, filter: `blur(${(1 - p) * 10}px)` };
  };
  const ul = prog(t, at + 0.45, at + 1.0, easeOut);
  return (
    <div style={{ ...place(pos), textAlign: align, fontFamily: M.serif, color: M.ink }}>
      {kicker ? (
        <div style={{ ...line(0), fontFamily: M.sans, fontWeight: 800, fontSize: size * 0.28, letterSpacing: 3, color: M.accent, textTransform: "uppercase", marginBottom: size * 0.16 }}>{kicker}</div>
      ) : null}
      <div style={{ ...line(kicker ? 1 : 0), fontSize: size, fontWeight: 600, lineHeight: 1.08, letterSpacing: -1 }}>{title}</div>
      {accent ? (
        <div style={{ ...line(kicker ? 2 : 1), display: "inline-block", position: "relative", fontSize: size, fontStyle: "italic", fontWeight: 500, color: M.accent, lineHeight: 1.12 }}>
          {accent}
          <svg style={{ position: "absolute", left: 0, bottom: -size * 0.1, width: "100%", height: size * 0.18, overflow: "visible" }} viewBox="0 0 100 10" preserveAspectRatio="none">
            <path d="M1 6 C 30 2, 60 9, 99 4" fill="none" stroke={M.accent} strokeWidth={2.2} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - ul} vectorEffect="non-scaling-stroke" />
          </svg>
        </div>
      ) : null}
    </div>
  );
};

/** Chữ hiện từng ký tự như đang gõ (cps = ký tự/giây), có con trỏ nhấp nháy. */
export const TypeText: React.FC<{ text: string; at?: number; cps?: number; caret?: boolean; style?: React.CSSProperties }> = ({ text, at = 0, cps = 22, caret = true, style }) => {
  const t = useSec();
  const n = Math.max(0, Math.min(text.length, Math.floor((t - at) * cps)));
  const typing = t >= at && n < text.length;
  const blink = Math.floor(t * 2.2) % 2 === 0;
  return (
    <span style={style}>
      {text.slice(0, n)}
      {caret && t >= at - 0.3 && (typing || blink) ? <span style={{ display: "inline-block", width: "0.08em", height: "1.05em", background: M.accent, marginLeft: 2, verticalAlign: "-0.15em" }} /> : null}
    </span>
  );
};

/** Chữ hiện từng từ (mờ → nét), hợp cho câu trích hoặc dòng nhấn. */
export const WordReveal: React.FC<Pos & { text: string; at?: number; every?: number; size?: number; serif?: boolean; italic?: boolean; color?: string }> = ({
  text,
  at = 0,
  every = 0.09,
  size = 64,
  serif = true,
  italic = false,
  color,
  ...pos
}) => {
  const t = useSec();
  return (
    <div style={{ ...place(pos), fontFamily: serif ? M.serif : M.sans, fontSize: size, fontStyle: italic ? "italic" : "normal", color: color ?? M.ink, lineHeight: 1.15 }}>
      {text.split(/\s+/).map((w, i) => {
        const p = prog(t, at + i * every, at + i * every + 0.4, easeOut);
        return (
          <span key={i} style={{ display: "inline-block", marginRight: "0.26em", opacity: p, transform: `translateY(${(1 - p) * 18}px)`, filter: `blur(${(1 - p) * 8}px)` }}>
            {w}
          </span>
        );
      })}
    </div>
  );
};

/** Bút dạ quang tô dưới chữ, quét từ trái sang phải lúc `at`. */
export const Marker: React.FC<{ text: string; at?: number; color?: string; style?: React.CSSProperties }> = ({ text, at = 0, color, style }) => {
  const t = useSec();
  const p = prog(t, at, at + 0.45, easeOut);
  return (
    <span style={{ position: "relative", whiteSpace: "nowrap", ...style }}>
      <span style={{ position: "absolute", left: "-0.1em", right: "-0.1em", bottom: "0.05em", height: "0.42em", background: rgba(color ?? M.accent, 0.28), transform: `scaleX(${p})`, transformOrigin: "0 50%", borderRadius: 6 }} />
      <span style={{ position: "relative" }}>{text}</span>
    </span>
  );
};

/* ------------------------------------------------------------------ khung & giao diện giả lập */

/** Thẻ trắng bo góc, bật ra lúc `at`. */
export const Card: React.FC<Pos & { at?: number; tilt?: number; pad?: number; dark?: boolean; children?: React.ReactNode }> = ({ at = 0, tilt = 0, pad = 36, dark, children, ...pos }) => {
  const s = useSpring(at, { damping: 14, stiffness: 160 });
  return (
    <div
      style={{
        ...place(pos),
        background: dark ? "#1b1d22" : M.paper,
        color: dark ? "#f3f4f6" : M.ink,
        border: `2px solid ${dark ? "#2b2f37" : M.line}`,
        borderRadius: 28,
        padding: pad,
        boxShadow: shadow(1),
        opacity: Math.min(1, s * 1.5),
        transform: `translateY(${(1 - s) * 50}px) scale(${0.92 + 0.08 * s}) rotate(${tilt * s}deg)`,
        boxSizing: "border-box",
      }}
    >
      {children}
    </div>
  );
};

/** Cửa sổ ứng dụng (thanh tiêu đề 3 chấm). dark = kiểu terminal / trình dựng. */
export const Window: React.FC<Pos & { title?: string; at?: number; dark?: boolean; children?: React.ReactNode; bodyStyle?: React.CSSProperties }> = ({
  title,
  at = 0,
  dark,
  children,
  bodyStyle,
  ...pos
}) => {
  const s = useSpring(at, { damping: 15, stiffness: 150 });
  const bar = dark ? "#23262d" : "#f1ede4";
  return (
    <div
      style={{
        ...place(pos),
        borderRadius: 26,
        overflow: "hidden",
        background: dark ? "#16181d" : M.paper,
        border: `2px solid ${dark ? "#2b2f37" : M.line}`,
        boxShadow: shadow(1.2),
        opacity: Math.min(1, s * 1.5),
        transform: `translateY(${(1 - s) * 60}px) scale(${0.9 + 0.1 * s})`,
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
      }}
    >
      <div style={{ height: 64, background: bar, display: "flex", alignItems: "center", gap: 12, padding: "0 24px", flexShrink: 0 }}>
        {["#ff5f57", "#febc2e", "#28c840"].map((c) => (
          <div key={c} style={{ width: 18, height: 18, borderRadius: 9, background: c }} />
        ))}
        {title ? <div style={{ marginLeft: 14, fontFamily: M.sans, fontWeight: 700, fontSize: 26, color: dark ? "#9aa1ad" : M.mute }}>{title}</div> : null}
      </div>
      <div style={{ flex: 1, position: "relative", padding: 32, fontFamily: M.sans, color: dark ? "#e5e7eb" : M.ink, ...bodyStyle }}>{children}</div>
    </div>
  );
};

/** Bong bóng chat. side "me" = người dùng (bên phải), "ai" = trợ lý (bên trái, có thể gõ dần). */
export const ChatBubble: React.FC<{ text: string; side?: "me" | "ai"; at?: number; type?: boolean; size?: number }> = ({ text, side = "ai", at = 0, type = side === "ai", size = 34 }) => {
  const s = useSpring(at, { damping: 13, stiffness: 190 });
  const me = side === "me";
  return (
    <div style={{ display: "flex", justifyContent: me ? "flex-end" : "flex-start", margin: "14px 0", opacity: Math.min(1, s * 1.6), transform: `translateY(${(1 - s) * 24}px) scale(${0.85 + 0.15 * s})`, transformOrigin: me ? "100% 100%" : "0 100%" }}>
      {!me ? <div style={{ width: 22, height: 22, marginTop: 14, marginRight: 14, borderRadius: 11, background: M.accent, flexShrink: 0 }} /> : null}
      <div
        style={{
          maxWidth: "82%",
          fontSize: size,
          lineHeight: 1.35,
          padding: me ? "16px 24px" : "4px 0",
          borderRadius: 22,
          background: me ? rgba(M.ink, 0.07) : "transparent",
          color: M.ink,
        }}
      >
        {type ? <TypeText text={text} at={at} cps={30} caret={false} /> : text}
      </div>
    </div>
  );
};

/** Ô nhập lệnh: gõ chữ từ `at`, tới `sendAt` thì chữ biến mất (đã gửi). */
export const InputBar: React.FC<{ text: string; at?: number; sendAt?: number; placeholder?: string; cps?: number }> = ({ text, at = 0, sendAt, placeholder = "Type / for commands", cps = 18 }) => {
  const t = useSec();
  const sent = sendAt !== undefined && t >= sendAt;
  const typing = t >= at && !sent;
  return (
    <div style={{ border: `2px solid ${M.line}`, borderRadius: 20, padding: "22px 26px", fontSize: 30, background: M.paper, color: typing ? M.ink : M.mute, minHeight: 40 }}>
      {typing ? <TypeText text={text} at={at} cps={cps} /> : placeholder}
    </div>
  );
};

/** Tài liệu (vd. CLAUDE.md) tự viết từng dòng; mỗi dòng có thời điểm riêng. */
export const DocWriter: React.FC<Pos & { name?: string; lines: { text: string; at: number; tag?: string }[]; at?: number; size?: number }> = ({ name = "CLAUDE.md", lines, at = 0, size = 30, ...pos }) => {
  const t = useSec();
  const cur = [...lines].reverse().find((l) => t >= l.at);
  return (
    <Card at={at} pad={34} {...pos}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, fontFamily: M.mono, fontSize: size * 0.85, color: M.mute, marginBottom: 18 }}>
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={M.mute} strokeWidth={2}>
          <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
          <path d="M14 3v6h6" />
        </svg>
        {name}
      </div>
      {lines.map((l, i) => {
        const shown = t >= l.at;
        return (
          <div key={i} style={{ fontFamily: M.mono, fontSize: size, lineHeight: 1.7, color: i === 0 ? M.accent : M.ink, minHeight: size * 1.7, display: "flex", gap: 12, alignItems: "center" }}>
            {shown ? <TypeText text={l.text} at={l.at} cps={34} caret={cur === l} /> : <span style={{ color: rgba(M.ink, 0.15) }}>—</span>}
            {l.tag && shown ? (
              <span style={{ marginLeft: "auto", fontSize: size * 0.7, color: M.accent, border: `2px solid ${M.accent}`, borderRadius: 999, padding: "2px 14px", opacity: prog(t, l.at + 0.4, l.at + 0.7) }}>{l.tag}</span>
            ) : null}
          </div>
        );
      })}
    </Card>
  );
};

/** Terminal: dòng lệnh gõ dần (cmd) và dòng kết quả hiện ra (out). */
export const Terminal: React.FC<Pos & { title?: string; lines: { cmd?: string; out?: string; at: number }[]; at?: number; size?: number }> = ({ title = "Terminal", lines, at = 0, size = 30, ...pos }) => {
  const t = useSec();
  return (
    <Window dark title={title} at={at} {...pos} bodyStyle={{ fontFamily: M.mono, fontSize: size, lineHeight: 1.6 }}>
      {lines.map((l, i) =>
        t >= l.at ? (
          <div key={i} style={{ color: l.cmd ? "#e5e7eb" : "#8b93a1" }}>
            {l.cmd ? (
              <>
                <span style={{ color: M.accent }}>❯ </span>
                <TypeText text={l.cmd} at={l.at} cps={26} caret={i === lines.length - 1 || t < (lines[i + 1]?.at ?? 1e9)} />
              </>
            ) : (
              <span style={{ opacity: prog(t, l.at, l.at + 0.25) }}>{l.out}</span>
            )}
          </div>
        ) : null,
      )}
    </Window>
  );
};

/* ------------------------------------------------------------------ danh sách & đồ vật */

/** Danh sách tự tick: mỗi ý hiện lúc `at` của nó, dấu tick bật ngay sau. */
export const Checklist: React.FC<Pos & { items: { text: string; at: number; done?: number }[]; size?: number; numbered?: boolean }> = ({ items, size = 40, numbered, ...pos }) => {
  const t = useSec();
  return (
    <div style={{ ...place(pos), fontFamily: M.sans }}>
      {items.map((it, i) => {
        const p = prog(t, it.at, it.at + 0.4, easeOut);
        const doneAt = it.done ?? it.at + 0.35;
        const c = prog(t, doneAt, doneAt + 0.3, easeOut);
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: size * 0.5, margin: `${size * 0.32}px 0`, opacity: p, transform: `translateX(${(1 - p) * -40}px)` }}>
            <div style={{ width: size * 1.05, height: size * 1.05, borderRadius: size, border: `3px solid ${c > 0 ? M.accent : M.line}`, background: rgba(M.accent, c), display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <svg width={size * 0.62} height={size * 0.62} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={3.4} strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 12.5l5 5L20 6.5" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - c} />
              </svg>
            </div>
            {numbered ? <span style={{ fontFamily: M.serif, fontStyle: "italic", color: M.accent, fontSize: size * 0.9 }}>{String(i + 1).padStart(2, "0")}</span> : null}
            <span style={{ fontSize: size, fontWeight: 600, color: M.ink }}>{it.text}</span>
          </div>
        );
      })}
    </div>
  );
};

/** Thư mục: các thẻ (cards) rơi vào lần lượt rồi nằm sau mép trước của thư mục. */
export const Folder: React.FC<Pos & { label: string; cards?: { label: string; at: number; color?: string }[]; at?: number }> = ({ label, cards = [], at = 0, w = 520, ...pos }) => {
  const t = useSec();
  const s = useSpring(at);
  const h = w * 0.62;
  return (
    <div style={{ ...place({ ...pos, w }), height: h + 160, opacity: Math.min(1, s * 1.5), transform: `translateY(${(1 - s) * 50}px)` }}>
      <div style={{ position: "absolute", left: 0, top: 160, width: w * 0.42, height: 60, background: M.accent, borderRadius: "18px 18px 0 0", filter: "brightness(0.85)" }} />
      <div style={{ position: "absolute", left: 0, top: 190, width: w, height: h, background: M.accent, borderRadius: 18, filter: "brightness(0.85)" }} />
      {cards.map((c, i) => {
        const p = prog(t, c.at, c.at + 0.55, easeOut);
        const y = interpolate(p, [0, 1], [-260, 120 + i * 6]);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: w * 0.12 + i * 26,
              top: y,
              width: w * 0.62,
              height: w * 0.5,
              background: c.color ?? M.paper,
              border: `2px solid ${M.line}`,
              borderRadius: 16,
              boxShadow: shadow(0.6),
              transform: `rotate(${(i % 2 ? 4 : -5) * (1 - p * 0.6)}deg)`,
              opacity: t >= c.at ? 1 : 0,
              fontFamily: M.sans,
              fontWeight: 700,
              fontSize: 28,
              color: M.ink,
              padding: 22,
              boxSizing: "border-box",
            }}
          >
            {c.label}
          </div>
        );
      })}
      <div style={{ position: "absolute", left: 0, top: 260, width: w, height: h - 70, background: M.accent, borderRadius: 18, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: shadow(0.8) }}>
        <span style={{ fontFamily: M.mono, fontSize: 34, color: "#fff", fontWeight: 600 }}>{label}</span>
      </div>
    </div>
  );
};

/** Lưới ảnh/video (b-roll) bật từng ô. */
export const GridPop: React.FC<Pos & { items: { src?: string; label?: string; at?: number }[]; cols?: number; gap?: number; at?: number; every?: number; ratio?: number }> = ({
  items,
  cols = 3,
  gap = 22,
  at = 0,
  every = 0.14,
  ratio = 1.25,
  w = 940,
  ...pos
}) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const cw = (w - gap * (cols - 1)) / cols;
  return (
    <div style={{ ...place({ ...pos, w }), display: "flex", flexWrap: "wrap", gap }}>
      {items.map((it, i) => {
        const a = it.at ?? at + i * every;
        const s = Math.max(0, Math.min(1.2, interpolate(f - a * fps, [0, 9, 14], [0, 1.08, 1], clamp)));
        return (
          <div key={i} style={{ width: cw, height: cw * ratio, borderRadius: 18, overflow: "hidden", background: rgba(M.ink, 0.06), boxShadow: shadow(0.6), transform: `scale(${s})`, opacity: s > 0 ? 1 : 0, position: "relative" }}>
            {it.src ? (
              isVideo(it.src) ? (
                <OffthreadVideo src={src(it.src)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              ) : (
                <Img src={src(it.src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              )
            ) : null}
            {it.label ? <div style={{ position: "absolute", left: 12, bottom: 12, right: 12, fontFamily: M.sans, fontWeight: 700, fontSize: 24, color: it.src ? "#fff" : M.ink, textShadow: it.src ? "0 2px 8px rgba(0,0,0,.6)" : undefined }}>{it.label}</div> : null}
          </div>
        );
      })}
    </div>
  );
};

/** Khung điện thoại chứa ảnh hoặc video. */
export const PhoneFrame: React.FC<Pos & { src?: string; at?: number; label?: string; children?: React.ReactNode }> = ({ src: s, at = 0, label, w = 420, children, ...pos }) => {
  const sp = useSpring(at, { damping: 14, stiffness: 140 });
  const h = w * 2.05;
  return (
    <div style={{ ...place({ ...pos, w }), height: h, borderRadius: w * 0.12, background: "#111", padding: w * 0.035, boxSizing: "border-box", boxShadow: shadow(1.4), opacity: Math.min(1, sp * 1.5), transform: `translateY(${(1 - sp) * 80}px) rotate(${(1 - sp) * -6}deg)` }}>
      <div style={{ width: "100%", height: "100%", borderRadius: w * 0.09, overflow: "hidden", position: "relative", background: "#222" }}>
        {s ? isVideo(s) ? <OffthreadVideo src={src(s)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : <Img src={src(s)} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : null}
        {children}
        {label ? <div style={{ position: "absolute", top: 18, left: 18, right: 18, textAlign: "center", fontFamily: M.sans, fontWeight: 800, fontSize: w * 0.065, color: M.ink, background: "#ffe066", borderRadius: 10, padding: "6px 10px" }}>{label}</div> : null}
      </div>
    </div>
  );
};

/** Sticker / logo / ảnh nhỏ bật vào và lắc nhẹ (hoặc chữ nếu không có ảnh). */
export const Sticker: React.FC<Pos & { src?: string; text?: string; at?: number; size?: number; rot?: number }> = ({ src: s, text, at = 0, size = 220, rot = -8, ...pos }) => {
  const t = useSec();
  const sp = useSpring(at, { damping: 9, stiffness: 200 });
  const wob = Math.sin((t - at) * 5) * 3 * Math.min(1, Math.max(0, t - at));
  return (
    <div style={{ ...place(pos), transform: `scale(${sp}) rotate(${rot + wob}deg)`, opacity: sp > 0.01 ? 1 : 0 }}>
      {s ? (
        <Img src={src(s)} style={{ width: size, height: size, objectFit: "contain", filter: "drop-shadow(0 10px 18px rgba(0,0,0,.25))" }} />
      ) : (
        <div style={{ fontFamily: M.sans, fontWeight: 900, fontSize: size * 0.3, color: "#fff", background: M.accent, padding: "10px 26px", borderRadius: 18, boxShadow: shadow(0.8), border: "5px solid #fff" }}>{text}</div>
      )}
    </div>
  );
};

/* ------------------------------------------------------------------ số liệu */

const fmtNum = (v: number, fmt: string, dec: number) => {
  if (fmt === "time") {
    const s = Math.max(0, Math.round(v));
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  }
  const n = v.toLocaleString("vi-VN", { minimumFractionDigits: dec, maximumFractionDigits: dec });
  return fmt === "pct" ? `${n}%` : n;
};

/** Bộ đếm số chạy từ `from` tới `to` trong `dur` giây (fmt: int, pct, time = m:ss). strike: hiện số cũ bị gạch bên cạnh. */
export const Counter: React.FC<Pos & { from: number; to: number; at?: number; dur?: number; fmt?: "int" | "pct" | "time"; decimals?: number; size?: number; prefix?: string; suffix?: string; strike?: boolean; color?: string }> = ({
  from,
  to,
  at = 0,
  dur = 1.2,
  fmt = "int",
  decimals = 0,
  size = 180,
  prefix = "",
  suffix = "",
  strike = false,
  color,
  ...pos
}) => {
  const t = useSec();
  const p = prog(t, at, at + dur, easeOut);
  const v = from + (to - from) * p;
  const done = p >= 1;
  return (
    <div style={{ ...place(pos), display: "flex", alignItems: "baseline", gap: size * 0.18, fontFamily: M.serif, color: color ?? (done && strike ? M.accent : M.ink) }}>
      <span style={{ fontSize: size, fontWeight: 600, fontStyle: done && strike ? "italic" : "normal", letterSpacing: -2, fontVariantNumeric: "tabular-nums" }}>
        {prefix}
        {fmtNum(v, fmt, decimals)}
        {suffix}
      </span>
      {strike ? (
        <span style={{ position: "relative", fontSize: size * 0.32, color: M.mute, opacity: prog(t, at + dur * 0.6, at + dur) }}>
          {prefix}
          {fmtNum(from, fmt, decimals)}
          {suffix}
          <span style={{ position: "absolute", left: 0, top: "52%", height: 4, background: M.accent, width: `${prog(t, at + dur, at + dur + 0.3) * 100}%` }} />
        </span>
      ) : null}
    </div>
  );
};

/** Đồng hồ kim quay (turns = số vòng kim phút trong dur giây). */
export const Clock: React.FC<Pos & { at?: number; dur?: number; turns?: number; size?: number; color?: string }> = ({ at = 0, dur = 2, turns = 3, size = 300, color, ...pos }) => {
  const t = useSec();
  const s = useSpring(at, { damping: 12, stiffness: 160 });
  const p = prog(t, at, at + dur, easeInOut);
  const col = color ?? M.accent;
  const min = p * turns * 360;
  const hr = 60 + p * turns * 30;
  return (
    <div style={{ ...place(pos), width: size, height: size, transform: `scale(${s})` }}>
      <svg viewBox="0 0 100 100" width={size} height={size}>
        <circle cx={50} cy={50} r={44} fill={M.paper} stroke={col} strokeWidth={4.5} />
        {Array.from({ length: 12 }, (_, i) => {
          const a = (i * 30 * Math.PI) / 180;
          return <line key={i} x1={50 + Math.sin(a) * 36} y1={50 - Math.cos(a) * 36} x2={50 + Math.sin(a) * 40} y2={50 - Math.cos(a) * 40} stroke={M.ink} strokeWidth={i % 3 ? 1.2 : 2.4} strokeLinecap="round" />;
        })}
        <line x1={50} y1={50} x2={50} y2={28} stroke={M.ink} strokeWidth={3.6} strokeLinecap="round" transform={`rotate(${hr} 50 50)`} />
        <line x1={50} y1={50} x2={50} y2={18} stroke={col} strokeWidth={2.4} strokeLinecap="round" transform={`rotate(${min} 50 50)`} />
        <circle cx={50} cy={50} r={3.2} fill={M.ink} />
      </svg>
    </div>
  );
};

/** Sóng âm: các đoạn `cuts` (tỉ lệ 0–1 theo chiều ngang) bị tô đỏ rồi xoá đi lúc `cutAt`; vạch chạy quét từ `at`. */
export const Waveform: React.FC<Pos & { bars?: number; seed?: number; cuts?: [number, number][]; at?: number; cutAt?: number; play?: number; color?: string }> = ({
  bars = 64,
  seed = 7,
  cuts = [],
  at = 0,
  cutAt,
  play = 1.6,
  color,
  w = 900,
  h = 220,
  ...pos
}) => {
  const t = useSec();
  const col = color ?? M.accent;
  const shown = prog(t, at, at + 0.5, easeOut);
  const head = prog(t, at + 0.2, at + 0.2 + play, easeInOut);
  const cut = cutAt !== undefined ? prog(t, cutAt, cutAt + 0.6, easeInOut) : 0;
  const inCut = (x: number) => cuts.some(([a, b]) => x >= a && x <= b);
  const bw = w / bars;
  return (
    <div style={{ ...place({ ...pos, w, h }), opacity: shown }}>
      <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center" }}>
        {Array.from({ length: bars }, (_, i) => {
          const x = (i + 0.5) / bars;
          const c = inCut(x);
          const amp = c ? 0.12 + rand(seed + i) * 0.18 : 0.25 + Math.abs(Math.sin(i * 0.7 + seed)) * 0.45 + rand(seed + i) * 0.3;
          const hh = h * Math.min(0.95, amp) * (c ? 1 - cut : 1);
          return (
            <div key={i} style={{ width: c ? bw * (1 - cut) : bw, display: "flex", justifyContent: "center", flexShrink: 0 }}>
              <div style={{ width: Math.max(2, bw * 0.55), height: Math.max(2, hh * shown), borderRadius: 4, background: c ? rgba("#ef4444", 0.5 + 0.3 * (1 - cut)) : x <= head ? col : rgba(col, 0.35) }} />
            </div>
          );
        })}
      </div>
      {cutAt !== undefined
        ? cuts.map(([a, b], i) => (
            <div key={i} style={{ position: "absolute", left: `${a * 100}%`, width: `${(b - a) * 100 * (1 - cut)}%`, top: 0, bottom: 0, background: rgba("#ef4444", 0.1 * (1 - cut)), borderRadius: 8 }} />
          ))
        : null}
      <div style={{ position: "absolute", top: -12, bottom: -12, left: `${head * 100}%`, width: 4, background: M.ink, borderRadius: 2, opacity: head > 0 && head < 1 ? 1 : 0 }} />
    </div>
  );
};

/** Dòng thời gian nhiều rãnh (cắt, phụ đề, motion, âm thanh…), các đoạn mọc dần từ trái sang. */
export const TimelineBars: React.FC<Pos & { tracks: { label: string; color?: string; segs: [number, number][] }[]; at?: number; dur?: number; size?: number }> = ({ tracks, at = 0, dur = 1.6, size = 28, w = 940, ...pos }) => {
  const t = useSec();
  const p = prog(t, at, at + dur, easeInOut);
  return (
    <div style={{ ...place({ ...pos, w }), fontFamily: M.sans }}>
      {tracks.map((tr, i) => {
        const rp = prog(t, at + i * 0.15, at + i * 0.15 + 0.4, easeOut);
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 20, margin: "16px 0", opacity: rp }}>
            <div style={{ width: 170, fontSize: size, fontWeight: 700, color: M.ink }}>{tr.label}</div>
            <div style={{ flex: 1, height: size * 1.6, position: "relative", background: rgba(M.ink, 0.05), borderRadius: 10 }}>
              {tr.segs.map(([a, b], k) => (
                <div key={k} style={{ position: "absolute", top: 6, bottom: 6, left: `${a * 100}%`, width: `${Math.max(0, Math.min(b, p) - a) * 100}%`, background: tr.color ?? M.accent, borderRadius: 7 }} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};

/* ------------------------------------------------------------------ sơ đồ */

/** Nút sơ đồ: thẻ nhỏ có biểu tượng (chữ/emoji/ảnh) và nhãn; `done` = lúc hiện dấu tick ở góc. */
export const Node: React.FC<{ x: number; y: number; label: string; icon?: string; at?: number; done?: number; w?: number; color?: string }> = ({ x, y, label, icon, at = 0, done, w = 230, color }) => {
  const t = useSec();
  const s = useSpring(at, { damping: 12, stiffness: 190 });
  const c = done !== undefined ? prog(t, done, done + 0.3, easeOut) : 0;
  const isImg = icon && /\.(png|jpe?g|svg|webp)$/i.test(icon);
  return (
    <div style={{ position: "absolute", left: x - w / 2, top: y - w * 0.45, width: w, transform: `scale(${s})`, opacity: s > 0.01 ? 1 : 0 }}>
      <div style={{ background: M.paper, border: `2px solid ${M.line}`, borderRadius: 24, boxShadow: shadow(0.8), padding: "22px 14px 18px", textAlign: "center", fontFamily: M.sans, position: "relative" }}>
        {icon ? (
          isImg ? (
            <Img src={src(icon)} style={{ width: w * 0.32, height: w * 0.32, objectFit: "contain" }} />
          ) : (
            <div style={{ fontSize: w * 0.26, lineHeight: 1, color: color ?? M.accent, fontWeight: 900 }}>{icon}</div>
          )
        ) : null}
        <div style={{ fontSize: 26, fontWeight: 700, color: M.ink, marginTop: icon ? 10 : 0 }}>{label}</div>
        <div style={{ height: 5, width: "46%", margin: "10px auto 0", borderRadius: 3, background: color ?? M.accent, opacity: 0.85 }} />
        {done !== undefined ? (
          <div style={{ position: "absolute", top: -14, right: -14, width: 42, height: 42, borderRadius: 21, background: M.accent, transform: `scale(${c})`, display: "flex", alignItems: "center", justifyContent: "center", border: "4px solid #fff" }}>
            <svg width={22} height={22} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={3.6} strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 12.5l5 5L20 6.5" />
            </svg>
          </div>
        ) : null}
      </div>
    </div>
  );
};

/** Đường nối tự vẽ giữa hai điểm (cong theo bend), có chấm ở đầu mút. */
export const Connector: React.FC<{ from: [number, number]; to: [number, number]; at?: number; dur?: number; bend?: number; color?: string; width?: number; dashed?: boolean }> = ({
  from,
  to,
  at = 0,
  dur = 0.6,
  bend = 0.25,
  color,
  width = 5,
  dashed,
}) => {
  const t = useSec();
  const p = prog(t, at, at + dur, easeInOut);
  const [x1, y1] = from;
  const [x2, y2] = to;
  const mx = (x1 + x2) / 2 - (y2 - y1) * bend;
  const my = (y1 + y2) / 2 + (x2 - x1) * bend;
  const col = color ?? M.accent;
  return (
    <svg style={{ position: "absolute", left: 0, top: 0, width: "100%", height: "100%", overflow: "visible", pointerEvents: "none" }}>
      <path d={`M${x1} ${y1} Q${mx} ${my} ${x2} ${y2}`} fill="none" stroke={col} strokeWidth={width} strokeLinecap="round" pathLength={1} strokeDasharray={dashed ? "0.02 0.02" : 1} strokeDashoffset={dashed ? 0 : 1 - p} opacity={dashed ? p : 1} />
      <circle cx={x1} cy={y1} r={width * 1.4} fill={col} opacity={p > 0 ? 1 : 0} />
      <circle cx={x2} cy={y2} r={width * 1.4 * (p >= 1 ? 1 : 0)} fill={col} />
    </svg>
  );
};

/** Con trỏ chuột đi theo các điểm [x, y, giây]; clicks = các giây bấm (gợn tròn). */
export const Cursor: React.FC<{ path: [number, number, number][]; clicks?: number[]; size?: number }> = ({ path, clicks = [], size = 54 }) => {
  const t = useSec();
  if (!path.length) return null;
  let x = path[0][0];
  let y = path[0][1];
  for (let i = 0; i < path.length - 1; i++) {
    const [ax, ay, at] = path[i];
    const [bx, by, bt] = path[i + 1];
    if (t >= at) {
      const p = prog(t, at, bt, easeInOut);
      x = ax + (bx - ax) * p;
      y = ay + (by - ay) * p;
    }
  }
  if (t >= path[path.length - 1][2]) [x, y] = path[path.length - 1];
  const click = clicks.find((c) => t >= c && t < c + 0.45);
  const cp = click !== undefined ? prog(t, click, click + 0.45, easeOut) : 0;
  const press = click !== undefined && t < click + 0.12 ? 0.85 : 1;
  return (
    <div style={{ position: "absolute", left: x, top: y, pointerEvents: "none", opacity: t >= path[0][2] - 0.2 ? 1 : 0 }}>
      {click !== undefined ? <div style={{ position: "absolute", left: -40 * cp, top: -40 * cp, width: 80 * cp, height: 80 * cp, borderRadius: "50%", border: `4px solid ${M.accent}`, opacity: 1 - cp }} /> : null}
      <svg width={size} height={size} viewBox="0 0 24 24" style={{ transform: `scale(${press})`, transformOrigin: "0 0", filter: "drop-shadow(0 3px 4px rgba(0,0,0,.35))" }}>
        <path d="M3 2l7.5 19 2.6-7.6L21 10.8z" fill="#111" stroke="#fff" strokeWidth={1.6} strokeLinejoin="round" />
      </svg>
    </div>
  );
};

/** Thanh tiến độ dạng chấm ("Ngày 2 ●●○○○") ở góc trên. */
export const ProgressDots: React.FC<Pos & { n: number; i: number; label?: string; at?: number }> = ({ n, i, label, at = 0, ...pos }) => {
  const t = useSec();
  const s = useSpring(at);
  return (
    <div style={{ ...place(pos), display: "flex", alignItems: "center", gap: 12, background: M.paper, border: `2px solid ${M.line}`, borderRadius: 999, padding: "10px 20px", fontFamily: M.sans, fontSize: 24, fontWeight: 700, color: M.mute, opacity: s, transform: `translateY(${(1 - s) * -20}px)` }}>
      {label ? <span style={{ marginRight: 6 }}>{label}</span> : null}
      {Array.from({ length: n }, (_, k) => {
        const on = k < i;
        const cur = k === i - 1;
        const g = cur ? prog(t, at + 0.2, at + 0.6, easeOut) : 1;
        return <div key={k} style={{ width: cur ? 16 + 22 * g : 14, height: 14, borderRadius: 7, background: on ? M.accent : M.line }} />;
      })}
    </div>
  );
};

/** Đẩy mọi thứ bên trong ra/vào theo thời gian (dùng cho các cảnh có nhiều pha). */
export const Phase: React.FC<{ from: number; to?: number; children?: React.ReactNode; fade?: number }> = ({ from, to, children, fade = 0.25 }) => {
  const t = useSec();
  if (t < from - 0.01 || (to !== undefined && t > to + fade)) return null;
  const o = prog(t, from, from + fade) * (to !== undefined ? 1 - prog(t, to, to + fade) : 1);
  return <div style={{ position: "absolute", inset: 0, opacity: o }}>{children}</div>;
};

export { easeInOut, easeOut, prog, rand, useSec, useSpring };
