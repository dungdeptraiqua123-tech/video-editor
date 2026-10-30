import React, { useMemo } from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, glow } from "./theme";
import { Word } from "./types";

type Page = { start: number; end: number; words: Word[] };

const MAX_CHARS = 30;
const MAX_WORDS = 8;

/** Gom từ thành cụm tối đa 2 dòng: ngắt khi đủ dài, gặp dấu câu, hoặc có khoảng nghỉ. */
export const buildPages = (words: Word[]): Page[] => {
  const pages: Page[] = [];
  let cur: Word[] = [];
  const flush = () => {
    if (cur.length) pages.push({ start: cur[0].start, end: cur[cur.length - 1].end, words: cur });
    cur = [];
  };
  words.forEach((w, i) => {
    const prev = words[i - 1];
    const len = cur.map((x) => x.text).join(" ").length + w.text.length + 1;
    if (cur.length && (len > MAX_CHARS || cur.length >= MAX_WORDS || (prev && w.start - prev.end > 0.35))) flush();
    cur.push(w);
    if (/[.!?]$/.test(w.text) || (/,$/.test(w.text) && cur.length >= 4)) flush();
  });
  flush();
  return pages.map((p, i) => ({ ...p, end: Math.min(pages[i + 1]?.start ?? p.end + 0.6, p.end + 0.6) }));
};

/** Chỉ tô sáng từ khoá và con số, phần còn lại để chữ trắng cho dễ đọc. */
const KEYWORDS = /^(bitcoin|btc|ethereum|eth|solana|etf|altcoin|nonfarm|payroll|volume|livestream|long|short|vĩ|mô|tích|lũy|cản|chốt|hấp|thụ)$/i;
const tone = (t: string) => {
  const w = t.replace(/[.,!?;:]/g, "");
  if (/\d/.test(w)) return C.gold;
  if (KEYWORDS.test(w)) return C.sky;
  return null;
};

/** Chia cụm thành tối đa 2 dòng dài gần bằng nhau, tránh dòng dưới chỉ còn 1 chữ. */
const balance = (ws: Word[]): number[][] => {
  const idx = ws.map((_, i) => i);
  const len = (a: number, b: number) => ws.slice(a, b).map((w) => w.text).join(" ").length;
  const total = len(0, ws.length);
  if (total <= 18 || ws.length < 3) return [idx];
  let best = 1;
  for (let k = 1; k < ws.length; k++) if (Math.abs(len(0, k) - len(k, ws.length)) < Math.abs(len(0, best) - len(best, ws.length))) best = k;
  return [idx.slice(0, best), idx.slice(best)];
};

export type CaptionStyle = "plain" | "box" | "glow" | "pop";

export const Captions: React.FC<{ words: Word[]; y: number; variant?: CaptionStyle }> = ({ words, y, variant = "glow" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const pages = useMemo(() => buildPages(words), [words]);
  const page = pages.find((p) => t >= p.start && t < p.end);
  if (!page) return null;
  const enter = spring({ frame: frame - Math.round(page.start * fps), fps, config: variant === "pop" ? { damping: 11, stiffness: 220 } : { damping: 20, stiffness: 200 } });
  const isBox = variant === "box";
  return (
    <div
      style={{
        position: "absolute",
        left: isBox ? 70 : 80,
        right: isBox ? 70 : 80,
        top: y,
        display: "flex",
        justifyContent: "center",
        fontFamily: C.font,
        transform: `translateY(calc(-50% + ${(1 - enter) * 18}px)) scale(${variant === "pop" ? 0.8 + 0.2 * enter : 1})`,
        opacity: Math.min(1, enter * 1.4),
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          rowGap: isBox ? 6 : 0,
          ...(isBox
            ? { background: "rgba(5,14,36,0.80)", border: `2px solid ${C.line}`, borderRadius: 24, padding: "16px 22px", boxShadow: "0 14px 36px rgba(0,0,0,0.35)" }
            : {}),
        }}
      >
        {balance(page.words).map((row, r) => (
        <div key={r} style={{ display: "flex", justifyContent: "center", columnGap: isBox ? 10 : variant === "pop" ? 28 : 22 }}>
        {row.map((i) => {
          const w = page.words[i];
          const col = tone(w.text);
          const said = t >= w.start;
          const active = said && t < (page.words[i + 1]?.start ?? page.end);
          const hit = spring({ frame: frame - Math.round(w.start * fps), fps, config: { damping: 13, stiffness: 240 } });
          const base: React.CSSProperties = { display: "inline-block", position: "relative" };
          if (variant === "box") {
            const bg = col === C.gold ? C.gold : C.orange;
            return (
              <span
                key={i}
                style={{
                  ...base,
                  fontSize: 58,
                  fontWeight: 800,
                  lineHeight: 1.25,
                  padding: "0 10px",
                  borderRadius: 12,
                  background: active ? bg : "transparent",
                  color: active ? (col === C.gold ? C.night : C.white) : said ? col ?? C.white : C.mute,
                  transform: `scale(${active ? 1 + 0.06 * hit : 1})`,
                  boxShadow: active ? glow(bg, 12) : undefined,
                }}
              >
                {w.text}
              </span>
            );
          }
          if (variant === "glow") {
            const ac = col ?? C.sky;
            return (
              <span
                key={i}
                style={{
                  ...base,
                  fontSize: 64,
                  fontWeight: 800,
                  lineHeight: 1.25,
                  color: active ? ac : said ? col ?? C.white : "rgba(207,224,255,0.72)",
                  textShadow: active ? `0 3px 10px rgba(0,0,0,0.8), ${glow(ac, 18)}` : "0 3px 12px rgba(0,0,0,0.85), 0 0 2px rgba(0,0,0,0.9)",
                  transform: `translateY(${active ? -5 * hit : 0}px) scale(${active ? 1 + 0.08 * hit : 1})`,
                }}
              >
                {w.text}
              </span>
            );
          }
          if (variant === "pop") {
            const fill = active ? col ?? C.sky : said ? col ?? C.white : "#dbe6ff";
            return (
              <span
                key={i}
                style={{
                  ...base,
                  fontSize: 70,
                  fontWeight: 900,
                  lineHeight: 1.2,
                  color: fill,
                  opacity: said ? 1 : 0.8,
                  WebkitTextStroke: `10px ${C.night}`,
                  paintOrder: "stroke fill",
                  textShadow: `0 7px 0 ${C.orange}`,
                  transform: `scale(${active ? 1 + 0.1 * hit : 1}) rotate(${active ? (1 - hit) * -6 : 0}deg)`,
                }}
              >
                {w.text}
              </span>
            );
          }
          const hk = col ? hit : 0;
          return (
            <span
              key={i}
              style={{
                ...base,
                fontSize: 64,
                fontWeight: 800,
                lineHeight: 1.22,
                color: col && said ? col : C.white,
                opacity: said ? 1 : 0.7,
                textShadow: col && said ? `0 3px 10px rgba(0,0,0,0.8), ${glow(col, 18)}` : "0 3px 12px rgba(0,0,0,0.85), 0 0 2px rgba(0,0,0,0.9)",
                transform: `scale(${1 + 0.06 * hk})`,
              }}
            >
              {w.text}
            </span>
          );
        })}
        </div>
        ))}
      </div>
    </div>
  );
};
