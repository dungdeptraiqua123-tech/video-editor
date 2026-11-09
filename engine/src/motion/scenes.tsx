/**
 * Cảnh motion có sẵn (dùng bằng tham số, không cần viết code). Tên cảnh = khoá trong registerScenes.
 * Hermes ghép cảnh mới bằng kit khi các cảnh này không hợp (xem huong-dan/motion.md).
 * Quy ước tham số: chữ trong p.*, mốc thời gian là p.d / item.d (giây từ lúc cảnh mở, do build đổi từ "say").
 */
/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import {
  Appear,
  Card,
  ChatBubble,
  Checklist,
  Clock,
  Connector,
  Counter,
  DocWriter,
  fitSize,
  Folder,
  Glyph,
  GridPop,
  Headline,
  InputBar,
  Node,
  overlaySlot,
  ProgressDots,
  Sticker,
  Terminal,
  TimelineBars,
  Waveform,
  Window,
  WordReveal,
} from "./kit";
import { prog, useSec } from "./anim";
import { registerScenes, SceneProps } from "./registry";
import { M, rgba, shadow } from "./theme";

/** Xuống dòng cân bằng cho chữ trong cảnh. */
const BAL = { textWrap: "balance" } as React.CSSProperties;
const num = (v: unknown, dflt: number) => (typeof v === "number" && isFinite(v) ? v : dflt);
const str = (v: unknown) => (typeof v === "string" ? v : "");
const arr = (v: unknown): any[] => (Array.isArray(v) ? v : []);

/** Tiêu đề chung của cảnh full (+ chấm tiến độ nếu có p.dots). Trả về chiều cao đã dùng. */
const Head: React.FC<{ p: any; safe: SceneProps["safe"]; W: number }> = ({ p, safe, W }) =>
  p.title ? (
    <>
      <Headline x={safe.left} y={safe.top + 40} w={(safe.pip ? safe.pip.x : W) - safe.left - 40} kicker={str(p.kicker)} title={str(p.title)} accent={str(p.accent)} size={num(p.size, 84)} />
      {p.dots ? <ProgressDots x={safe.pip ? safe.left : W - safe.left - 330} y={safe.top - 50} n={num(p.dots.n, 5)} i={num(p.dots.i, 1)} label={str(p.dots.label)} at={0.2} /> : null}
    </>
  ) : null;

/** Mép trên phần nội dung dưới tiêu đề: tính theo cỡ chữ / số dòng mà Headline tự co (cùng bề rộng như Head). */
const contentTop = (p: any, safe: SceneProps["safe"]) => {
  if (!p.title) return safe.top + 60;
  const W = safe.right + safe.left;
  const w = (safe.pip ? safe.pip.x : W) - safe.left - 40;
  const size = num(p.size, 84);
  const title = str(p.title), accent = str(p.accent);
  const fs = Math.min(fitSize(title, w, size, 2), accent ? fitSize(accent, w, size, 1, 0.47) : size);
  const lt = Math.min(3, Math.max(1, Math.ceil(([...title].length * fs * 0.5) / w)));
  const la = accent ? Math.min(2, Math.max(1, Math.ceil(([...accent].length * fs * 0.47) / w))) : 0;
  return safe.top + 40 + fs * (1.08 * lt + 1.12 * la) + (p.kicker ? fs * 0.44 : 0) + 70;
};

/** Tiêu đề lớn ở giữa (mở chương, ý chính). p: kicker, title, accent, sub, dots */
const TieuDe: React.FC<SceneProps> = ({ p, W, H, safe }) => (
  <>
    {p.dots ? <ProgressDots x={W - safe.left - 330} y={safe.top} n={num(p.dots.n, 5)} i={num(p.dots.i, 1)} label={str(p.dots.label)} at={0.1} /> : null}
    <Headline x={safe.left} y={H * 0.36} w={W - safe.left * 2} kicker={str(p.kicker)} title={str(p.title)} accent={str(p.accent)} size={num(p.size, 112)} at={num(p.d, 0.1)} />
    {p.sub ? <WordReveal x={safe.left} y={H * 0.36 + num(p.size, 112) * 2.9} w={W - safe.left * 2} text={str(p.sub)} size={40} serif={false} color={M.mute} at={num(p.subD, num(p.d, 0.1) + 0.6)} /> : null}
  </>
);

/** Cửa sổ chat AI: gõ câu hỏi vào ô nhập, gửi, trợ lý trả lời. p: title, accent, app, ask, askD, answer, answerD, done (dòng ✓) */
const Chat: React.FC<SceneProps> = ({ p, W, safe, layer }) => {
  const slot = layer === "overlay" ? overlaySlot(safe, num(p.h, 640), 380) : null;
  const top = slot ? slot.y : contentTop(p, safe);
  const askAt = num(p.askD, 0.4);
  const ask = str(p.ask);
  const sendAt = askAt + ask.length / 18 + 0.35;
  const ansAt = Math.max(num(p.answerD, sendAt + 0.5), sendAt + 0.3);
  const t = useSec();
  return (
    <>
      {layer === "full" ? <Head p={p} safe={safe} W={W} /> : null}
      <Window x={safe.left} y={top} w={W - safe.left * 2} h={slot ? slot.h : num(p.h, 640)} title={str(p.app) || "Claude"} at={0.1} bodyStyle={{ display: "flex", flexDirection: "column" }}>
        <div style={{ flex: 1 }}>
          {p.greet ? <ChatBubble text={str(p.greet)} side="ai" at={0.3} type={false} /> : null}
          {t >= sendAt ? <ChatBubble text={ask} side="me" at={sendAt} /> : null}
          {p.answer ? <ChatBubble text={str(p.answer)} side="ai" at={ansAt} /> : null}
          {p.done ? (
            <Appear at={num(p.doneD, ansAt + 1)} kind="rise">
              <div style={{ fontSize: 30, color: M.ok, fontWeight: 700, marginTop: 10 }}>✓ {str(p.done)}</div>
            </Appear>
          ) : null}
        </div>
        <InputBar text={ask} at={askAt} sendAt={sendAt} />
      </Window>
    </>
  );
};

/** Danh sách tự tick. p: title, accent, kicker, items[{text, d}], numbered */
const ChecklistScene: React.FC<SceneProps> = ({ p, W, safe, layer }) => {
  const items = arr(p.items).map((it, i) => ({ text: str(it.text), at: num(it.d, 0.6 + i * 0.6) }));
  const top = layer === "overlay" ? overlaySlot(safe, 140 + items.length * 70, 260).y : contentTop(p, safe);
  return (
    <>
      {layer === "full" ? <Head p={p} safe={safe} W={W} /> : null}
      {layer === "overlay" ? (
        <Appear at={0} kind="rise" x={safe.left} y={top} w={W - safe.left * 2 - (safe.pip ? 0 : 120)}>
          <div style={{ background: M.paper, borderRadius: 28, padding: "26px 36px", border: `2px solid ${M.line}` }}>
            {p.title ? <div style={{ fontFamily: M.serif, fontSize: 52, fontWeight: 600, color: M.ink }}>{str(p.title)}</div> : null}
            <Checklist items={items} size={38} numbered={!!p.numbered} />
          </div>
        </Appear>
      ) : (
        <Checklist x={safe.left + 10} y={top} items={items} size={num(p.itemSize, 46)} numbered={!!p.numbered} />
      )}
    </>
  );
};

/** Số đếm lớn (+ đồng hồ tuỳ chọn). p: title, accent, from, to, fmt(int|pct|time), dur, d, prefix, suffix, label, strike, clock */
const DemSo: React.FC<SceneProps> = ({ p, W, H, safe }) => {
  const at = num(p.d, 0.4);
  const top = contentTop(p, safe);
  return (
    <>
      <Head p={p} safe={safe} W={W} />
      {p.clock ? <Clock x={W / 2 - 170} y={top} size={340} at={0.2} dur={num(p.dur, 1.4) + at} turns={3} /> : null}
      <Counter
        x={safe.left}
        y={p.clock ? top + 400 : Math.max(top, H * 0.38)}
        from={num(p.from, 0)}
        to={num(p.to, 100)}
        at={at}
        dur={num(p.dur, 1.4)}
        fmt={(["int", "pct", "time"].includes(str(p.fmt)) ? p.fmt : "int") as "int" | "pct" | "time"}
        decimals={num(p.decimals, 0)}
        prefix={str(p.prefix)}
        suffix={str(p.suffix)}
        strike={!!p.strike}
        size={num(p.numSize, 200)}
      />
      {p.label ? <WordReveal x={safe.left} y={(p.clock ? top + 400 : Math.max(top, H * 0.38)) + num(p.numSize, 200) * 1.25} w={W - safe.left * 2} text={str(p.label)} size={42} serif={false} color={M.mute} at={at + 0.3} /> : null}
    </>
  );
};

/** Sóng âm bị cắt khoảng lặng + thời lượng giảm. p: title, accent, from, to (giây), d (lúc cắt), cuts[[a,b]] */
const SongAm: React.FC<SceneProps> = ({ p, W, safe }) => {
  const at = num(p.d, 1.2);
  const top = contentTop(p, safe);
  const cuts = (arr(p.cuts).length ? arr(p.cuts) : [[0.22, 0.3], [0.52, 0.6], [0.8, 0.86]]) as [number, number][];
  return (
    <>
      <Head p={p} safe={safe} W={W} />
      <div style={{ position: "absolute", left: safe.left, top: top - 10, fontFamily: M.sans, fontSize: 26, color: M.mute, fontWeight: 600 }}>{str(p.label) || "Độ dài video"}</div>
      <Counter x={safe.left} y={top + 30} from={num(p.from, 30)} to={num(p.to, 21)} fmt="time" at={at} dur={0.8} size={150} strike />
      <Waveform x={safe.left} y={top + 260} w={W - safe.left * 2} h={240} cuts={cuts} at={0.2} cutAt={at} play={Math.max(0.8, at - 0.3)} />
    </>
  );
};

/** Sơ đồ: nút trung tâm ở dưới, các nút phía trên nối vào. p: title, accent, center{label,icon}, nodes[{label, icon, d}] */
const SoDo: React.FC<SceneProps> = ({ p, W, H, safe }) => {
  const nodes = arr(p.nodes).slice(0, 4);
  const top = contentTop(p, safe);
  const cy = Math.min(top + 560, H * 0.7);
  const cx = W / 2;
  const n = Math.max(1, nodes.length);
  const span = W - safe.left * 2 - 240;
  return (
    <>
      <Head p={p} safe={safe} W={W} />
      {nodes.map((nd, i) => {
        const x = n === 1 ? cx : safe.left + 120 + (span * i) / (n - 1);
        const y = top + 140 + (i % 2) * 40;
        const at = num(nd.d, 0.4 + i * 0.45);
        return (
          <React.Fragment key={i}>
            <Connector from={[x, y + 90]} to={[cx, cy - 110]} at={at + 0.25} dur={0.5} bend={x < cx ? 0.2 : x > cx ? -0.2 : 0} />
            <Node x={x} y={y} label={str(nd.label)} icon={str(nd.icon) || undefined} at={at} done={nd.done ? at + 0.6 : undefined} />
          </React.Fragment>
        );
      })}
      {p.center ? <Node x={cx} y={cy} label={str(p.center.label)} icon={str(p.center.icon) || "✳"} at={num(p.center.d, 0.2)} w={260} /> : null}
    </>
  );
};

/** Tài liệu tự viết. p: title, accent, name, lines[{text, d, tag}] */
const TaiLieu: React.FC<SceneProps> = ({ p, W, safe }) => {
  const lines = arr(p.lines).map((l, i) => ({ text: str(l.text), at: num(l.d, 0.6 + i * 0.5), tag: str(l.tag) || undefined }));
  return (
    <>
      <Head p={p} safe={safe} W={W} />
      <DocWriter x={safe.left} y={contentTop(p, safe)} w={W - safe.left * 2} name={str(p.name) || "CLAUDE.md"} lines={lines} at={0.2} />
    </>
  );
};

/** Terminal. p: title, accent, app, lines[{cmd | out, d}] */
const TerminalScene: React.FC<SceneProps> = ({ p, W, safe }) => {
  const lines = arr(p.lines).map((l, i) => ({ cmd: l.cmd ? str(l.cmd) : undefined, out: l.out ? str(l.out) : undefined, at: num(l.d, 0.5 + i * 0.7) }));
  return (
    <>
      <Head p={p} safe={safe} W={W} />
      <Terminal x={safe.left} y={contentTop(p, safe)} w={W - safe.left * 2} h={num(p.h, 620)} title={str(p.app) || "Terminal"} lines={lines} at={0.15} />
    </>
  );
};

/** Lưới ảnh / b-roll. p: title, accent, items[{src, label, d}], cols */
const LuoiAnh: React.FC<SceneProps> = ({ p, W, safe }) => (
  <>
    <Head p={p} safe={safe} W={W} />
    <GridPop x={safe.left} y={contentTop(p, safe)} w={W - safe.left * 2} cols={num(p.cols, 3)} at={num(p.d, 0.3)} items={arr(p.items).map((it) => ({ src: str(it.src) || undefined, label: str(it.label) || undefined, at: typeof it.d === "number" ? it.d : undefined }))} />
  </>
);

/** Đồng hồ + "trước → sau" (vd 3–4 tiếng → 20–30 phút). p: kicker, before, after, d (lúc đổi), dur */
const DongHo: React.FC<SceneProps> = ({ p, W, H }) => {
  const t = useSec();
  const at = num(p.d, 1.4);
  const sw = prog(t, at, at + 0.35);
  return (
    <>
      {p.kicker ? (
        <Appear at={0.1} kind="pop" x={W / 2 - 200} y={H * 0.24} w={400}>
          <div style={{ textAlign: "center", fontFamily: M.sans, fontWeight: 800, fontSize: 40, color: M.accent }}>{str(p.kicker)}</div>
        </Appear>
      ) : null}
      <Clock x={W / 2 - 190} y={H * 0.3} size={380} at={0.15} dur={num(p.dur, at + 0.4)} turns={4} />
      <div style={{ position: "absolute", left: 0, right: 0, top: H * 0.3 + 440, textAlign: "center", fontFamily: M.serif, fontStyle: "italic", fontSize: 110, color: M.ink }}>
        <span style={{ opacity: 1 - sw, filter: `blur(${sw * 10}px)`, position: "absolute", left: 0, right: 0 }}>{str(p.before)}</span>
        <span style={{ opacity: sw, color: M.accent, position: "absolute", left: 0, right: 0, transform: `translateY(${(1 - sw) * 30}px)` }}>{str(p.after)}</span>
      </div>
    </>
  );
};

/** Thư mục + thẻ rơi vào. p: title, accent, label, cards[{label, d}] */
const ThuMuc: React.FC<SceneProps> = ({ p, W, safe }) => (
  <>
    <Head p={p} safe={safe} W={W} />
    <Folder x={W / 2 - 290} y={contentTop(p, safe) - 80} w={580} label={str(p.label) || "tham-khao/"} at={0.2} cards={arr(p.cards).map((c, i) => ({ label: str(c.label), at: num(c.d, 0.6 + i * 0.5) }))} />
  </>
);

/** Rãnh dòng thời gian (cắt / phụ đề / motion / âm thanh). p: title, accent, tracks[{label, segs[[a,b]]}], d, dur */
const DongThoiGian: React.FC<SceneProps> = ({ p, W, safe }) => (
  <>
    <Head p={p} safe={safe} W={W} />
    <TimelineBars x={safe.left} y={contentTop(p, safe)} w={W - safe.left * 2} at={num(p.d, 0.4)} dur={num(p.dur, 1.6)} tracks={arr(p.tracks).map((tr) => ({ label: str(tr.label), segs: arr(tr.segs) as [number, number][], color: str(tr.color) || undefined }))} />
  </>
);

/** (overlay) Chữ serif nghiêng lớn nổi trên người nói, kiểu "dành cho / newbie". p: small, big, d, y (0–1) */
const ChuNghieng: React.FC<SceneProps> = ({ p, W, H, safe }) => {
  const at = num(p.d, 0.1);
  const y = num(p.y, 0.16) * H;
  return (
    <>
      {p.small ? <WordReveal x={safe.left} y={y} w={W - safe.left * 2} text={str(p.small)} size={46} serif={false} color="#ffffff" at={at} style={{ textAlign: "center", fontWeight: 700, textShadow: "0 3px 14px rgba(0,0,0,.55)" }} /> : null}
      <WordReveal x={safe.left} y={y + (p.small ? 62 : 0)} w={W - safe.left * 2} text={str(p.big)} size={num(p.size, 104)} italic color={str(p.color) || "#ffffff"} at={at + 0.15} every={0.12} style={{ textAlign: "center", textShadow: "0 4px 22px rgba(0,0,0,.5)" }} />
    </>
  );
};

/** (overlay) Sticker / logo bật vào kèm chữ chú thích. p: src, text, note, x, y (0–1), d */
const NhanDan: React.FC<SceneProps> = ({ p, W, H }) => {
  const at = num(p.d, 0.1);
  const x = num(p.x, 0.12) * W;
  const y = num(p.y, 0.2) * H;
  return (
    <>
      <Sticker x={x} y={y} src={str(p.src) || undefined} text={str(p.text) || undefined} size={num(p.size, 240)} at={at} />
      {p.note ? <WordReveal x={x + num(p.size, 240) + 20} y={y + 30} w={W - x - num(p.size, 240) - 60} text={str(p.note)} size={48} italic color="#ffffff" at={at + 0.3} style={{ textShadow: "0 3px 14px rgba(0,0,0,.55)" }} /> : null}
    </>
  );
};

/* ---------------------------------------------------------------- cảnh cho video lời khuyên / giải thích nói chuyện */

/** Icon nét vẽ sẵn (không phụ thuộc font emoji trên máy chủ). */
const MiniIcon: React.FC<{ kind: "meo" | "canh-bao" | "luu-y" | "hoi"; size: number; color: string }> = ({ kind, size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" style={{ display: "block", flexShrink: 0 }}>
    {kind === "canh-bao" ? (
      <>
        <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
        <path d="M12 9v4M12 17h.01" />
      </>
    ) : kind === "meo" ? (
      <>
        <path d="M9 18h6M10 22h4" />
        <path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.2 1 2V17h6v-.3c0-.8.4-1.5 1-2A7 7 0 0 0 12 2z" />
      </>
    ) : kind === "hoi" ? (
      <>
        <circle cx="12" cy="12" r="10" />
        <path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01" />
      </>
    ) : (
      <>
        <path d="M12 17v5" />
        <path d="M9 10.8a2 2 0 0 1-1.1 1.8l-1.8.9A2 2 0 0 0 5 15.2V17h14v-1.8a2 2 0 0 0-1.1-1.8l-1.8-.9a2 2 0 0 1-1.1-1.8V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z" />
      </>
    )}
  </svg>
);

/** Một cột của cảnh so sánh: icon, nhãn, các ý hiện dần; được chọn thì nổi viền màu nhấn, cột kia mờ đi. */
const SideCard: React.FC<{ s: any; x: number; y: number; w: number; at: number; picked: number; other: number; size: number }> = ({ s, x, y, w, at, picked, other, size }) => {
  const t = useSec();
  const items = arr(s.items).map((it, i) => (typeof it === "string" ? { text: it, at: at + 0.5 + i * 0.5 } : { text: str(it.text), at: num(it.d, at + 0.5 + i * 0.5) }));
  return (
    <Appear at={at} kind="rise" x={x} y={y} w={w}>
      <div
        data-ve="box"
        data-ve-name="cot"
        style={{
          background: M.paper,
          border: `${picked > 0 ? 6 : 2}px solid ${picked > 0 ? M.accent : M.line}`,
          borderRadius: 30,
          padding: "30px 26px 32px",
          boxShadow: `0 18px 40px rgba(0,0,0,${0.12 + 0.12 * picked})`,
          opacity: 1 - 0.55 * other,
          transform: `scale(${1 + 0.04 * picked})`,
          textAlign: "center",
          boxSizing: "border-box",
        }}
      >
        <div style={{ display: "flex", justifyContent: "center", minHeight: size * 1.6 }}>
          <Glyph name={str(s.icon)} size={size * 1.6} color={M.accent} />
        </div>
        <div data-ve="text" data-ve-name="nhan" style={{ ...BAL, fontFamily: M.serif, fontWeight: 600, fontSize: size * Math.min(1.15, 9 / Math.max(6, [...str(s.label)].length) * 1.05), color: M.ink, lineHeight: 1.1, marginTop: 10 }}>
          {str(s.label)}
        </div>
        {items.map((it, i) => (
          <div
            key={i}
            data-ve="text"
            data-ve-name="y"
            style={{ fontSize: size * 0.72, color: M.ink, marginTop: 14, opacity: prog(t, it.at, it.at + 0.35), lineHeight: 1.25 }}
          >
            {it.text}
          </div>
        ))}
        {picked > 0 ? (
          <div style={{ marginTop: 18, display: "inline-block", background: M.accent, color: "#fff", fontWeight: 800, fontSize: size * 0.7, padding: "6px 22px", borderRadius: 999, transform: `scale(${picked})` }}>
            ✓ {str(s.badge) || "Nên chọn"}
          </div>
        ) : null}
      </div>
    </Appear>
  );
};

/** So sánh A với B (sàn hay ví, cách cũ hay cách mới…). p: kicker, title, accent, a{label, icon, items[], badge}, b{…}, d (lúc hai cột hiện), pick ("a"|"b"), pickD (lúc chọn), verdict, verdictD */
const SoSanh: React.FC<SceneProps> = ({ p, W, H, safe, layer }) => {
  const t = useSec();
  const at = num(p.d, 0.2);
  const pickAt = num(p.pickD, 1e9);
  const pk = prog(t, pickAt, pickAt + 0.45);
  const gap = 36;
  const colW = (W - safe.left * 2 - gap) / 2;
  const slot = layer === "overlay" ? overlaySlot(safe, 620, 420) : null;
  const size = W > H ? 40 : 54;
  const estH = size * 7.2 + arr((p.a || {}).items).length * size;
  const ct = contentTop(p, safe);
  const top = slot ? slot.y : Math.max(ct, ct + (safe.bottom - 160 - ct - estH) / 2);
  const pick = str(p.pick);
  return (
    <>
      {layer === "full" ? <Head p={p} safe={safe} W={W} /> : null}
      <SideCard s={p.a || {}} x={safe.left} y={top} w={colW} at={at} picked={pick === "a" ? pk : 0} other={pick === "b" ? pk : 0} size={size} />
      <SideCard s={p.b || {}} x={safe.left + colW + gap} y={top} w={colW} at={at + 0.25} picked={pick === "b" ? pk : 0} other={pick === "a" ? pk : 0} size={size} />
      <Appear at={at + 0.15} kind="pop" x={W / 2 - 46} y={top + 60} w={92}>
        <div style={{ width: 92, height: 92, borderRadius: 46, background: M.ink, color: M.bg, fontFamily: M.sans, fontWeight: 900, fontSize: 32, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 10px 26px rgba(0,0,0,.3)" }}>
          {str(p.vs) || "VS"}
        </div>
      </Appear>
      {p.verdict ? (
        <WordReveal x={safe.left} y={Math.min(safe.bottom - 140, top + 640)} w={W - safe.left * 2} text={str(p.verdict)} size={size * 1.1} italic color={M.accent} at={num(p.verdictD, pickAt + 0.3)} style={{ textAlign: "center" }} />
      ) : null}
    </>
  );
};

/** Rẽ nhánh "nếu… thì… / còn không thì…". p: title, accent, cond, condD, yes{label, text, icon, d}, no{…} (nhánh sáng lên đúng lúc nói), yesLabel, noLabel */
const ReNhanh: React.FC<SceneProps> = ({ p, W, H, safe, layer }) => {
  const t = useSec();
  const slot = layer === "overlay" ? overlaySlot(safe, 700, 520) : null;
  const top = slot ? slot.y : Math.max(contentTop(p, safe), H * 0.24);
  const condAt = num(p.condD, 0.2);
  const yes = p.yes || {};
  const no = p.no || {};
  const yAt = num(yes.d, condAt + 0.9);
  const nAt = num(no.d, yAt + 1.2);
  const gap = 36;
  const colW = (W - safe.left * 2 - gap) / 2;
  const size = W > H ? 36 : 48;
  const condH = size * 4.2;
  const by = top + condH + 150;
  // nhánh đang nói sáng lên, nhánh kia mờ đi (sau khi cả hai đã hiện thì giữ cả hai rõ)
  const lit = (mine: number, other: number) => (t >= mine && (t < other || other < mine) ? 1 : t >= mine ? 0.85 : 0);
  const branch = (b: any, x: number, at: number, label: string, other: number, ok: boolean) => (
    <Appear at={at} kind="rise" x={x} y={by} w={colW}>
      <div
        data-ve="box"
        data-ve-name="nhanh"
        style={{
          background: M.paper,
          border: `${lit(at, other) >= 1 ? 5 : 2}px solid ${lit(at, other) >= 1 ? (ok ? M.ok : M.accent) : M.line}`,
          borderRadius: 28,
          padding: "26px 24px 28px",
          boxShadow: shadow(0.9),
          textAlign: "center",
          boxSizing: "border-box",
        }}
      >
        <div style={{ display: "inline-block", fontFamily: M.sans, fontWeight: 900, fontSize: size * 0.7, color: "#fff", background: ok ? M.ok : M.accent, borderRadius: 999, padding: "4px 20px" }}>
          {label}
        </div>
        <div style={{ display: "flex", justifyContent: "center", marginTop: 16, minHeight: b.icon ? size * 1.5 : 0 }}>
          <Glyph name={str(b.icon)} size={size * 1.5} color={ok ? M.ok : M.accent} />
        </div>
        <div data-ve="text" data-ve-name="nhan" style={{ ...BAL, fontFamily: M.serif, fontWeight: 600, fontSize: size * 1.1, color: M.ink, lineHeight: 1.12, marginTop: 10 }}>
          {str(b.label)}
        </div>
        {b.text ? (
          <div data-ve="text" data-ve-name="y" style={{ ...BAL, fontSize: size * 0.7, color: M.mute, marginTop: 10, lineHeight: 1.25 }}>
            {str(b.text)}
          </div>
        ) : null}
      </div>
    </Appear>
  );
  return (
    <>
      {layer === "full" ? <Head p={p} safe={safe} W={W} /> : null}
      <Card at={condAt} x={safe.left + 40} y={top} w={W - safe.left * 2 - 80} pad={30}>
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <MiniIcon kind="hoi" size={size * 1.3} color={M.accent} />
          <div data-ve="text" data-ve-name="dieu-kien" style={{ ...BAL, fontFamily: M.serif, fontWeight: 600, fontSize: size * 1.05, lineHeight: 1.15 }}>
            {str(p.cond)}
          </div>
        </div>
      </Card>
      <Connector from={[W / 2 - 40, top + condH]} to={[safe.left + colW / 2, by - 10]} at={yAt - 0.35} dur={0.4} bend={0.25} color={M.ok} />
      <Connector from={[W / 2 + 40, top + condH]} to={[safe.left + colW + gap + colW / 2, by - 10]} at={nAt - 0.35} dur={0.4} bend={-0.25} color={M.accent} />
      {branch(yes, safe.left, yAt, str(p.yesLabel) || "Có", nAt, true)}
      {branch(no, safe.left + colW + gap, nAt, str(p.noLabel) || "Không", yAt, false)}
    </>
  );
};

/** Thẻ lưu ý / mẹo / cảnh báo có icon. p: kind ("luu-y" | "meo" | "canh-bao"), title, text, icon (lu:/si: thay icon mặc định), d */
const LuuY: React.FC<SceneProps> = ({ p, W, H, safe, layer }) => {
  const at = num(p.d, 0.15);
  const kind = (["meo", "canh-bao", "luu-y"].includes(str(p.kind)) ? str(p.kind) : "luu-y") as "meo" | "canh-bao" | "luu-y";
  const col = kind === "canh-bao" ? "#dc2626" : kind === "meo" ? M.ok : M.accent;
  const slot = layer === "overlay" ? overlaySlot(safe, 420, 300) : null;
  const top = slot ? slot.y : Math.max(contentTop(p, safe), (safe.top + safe.bottom) / 2 - 260);
  const label = str(p.label) || (kind === "canh-bao" ? "Cảnh báo" : kind === "meo" ? "Mẹo" : "Lưu ý");
  return (
    <>
      {layer === "full" && p.headline ? <Head p={{ title: p.headline, accent: p.accent }} safe={safe} W={W} /> : null}
      <Card at={at} x={safe.left} y={top} w={W - safe.left * 2} pad={40}>
        <div style={{ display: "flex", gap: 30, alignItems: "flex-start" }}>
          <div style={{ width: 120, height: 120, borderRadius: 30, background: rgba(col, 0.12), display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            {p.icon ? <Glyph name={str(p.icon)} size={70} color={col} /> : <MiniIcon kind={kind} size={70} color={col} />}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: M.sans, fontWeight: 900, fontSize: 30, letterSpacing: 3, textTransform: "uppercase", color: col }}>{label}</div>
            <div data-ve="text" data-ve-name="tieu-de" style={{ ...BAL, fontFamily: M.serif, fontWeight: 600, fontSize: W > H ? 56 : 72, lineHeight: 1.1, marginTop: 8, color: M.ink }}>
              {str(p.title)}
            </div>
            {p.text ? <WordReveal text={str(p.text)} size={W > H ? 34 : 44} serif={false} color={M.mute} at={num(p.textD, at + 0.5)} style={{ marginTop: 16 }} /> : null}
          </div>
        </div>
      </Card>
    </>
  );
};

/** Hỏi – đáp: bong bóng câu hỏi (người xem / người hỏi) rồi câu trả lời hiện ra. Dùng khi KHÔNG có app chat thật. p: who, q, qD, a, aD, title, accent */
const HoiDap: React.FC<SceneProps> = ({ p, W, H, safe, layer }) => {
  const t = useSec();
  const qAt = num(p.qD, 0.2);
  const aAt = Math.max(num(p.aD, qAt + 1.2), qAt + 0.5);
  const slot = layer === "overlay" ? overlaySlot(safe, 640, 420) : null;
  const top = slot ? slot.y : Math.max(contentTop(p, safe), H * 0.3);
  const size = W > H ? 40 : 46;
  const w = W - safe.left * 2;
  return (
    <>
      {layer === "full" ? <Head p={p} safe={safe} W={W} /> : null}
      <Appear at={qAt} kind="left" x={safe.left} y={top} w={w * 0.86}>
        <div data-ve="box" data-ve-name="hoi" style={{ background: M.paper, border: `2px solid ${M.line}`, borderRadius: "34px 34px 34px 8px", padding: "26px 32px", boxShadow: shadow(0.8) }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, fontFamily: M.sans, fontWeight: 800, fontSize: size * 0.55, color: M.mute, letterSpacing: 2, textTransform: "uppercase" }}>
            <MiniIcon kind="hoi" size={size * 0.7} color={M.mute} />
            {str(p.who) || "Câu hỏi"}
          </div>
          <div data-ve="text" data-ve-name="cau-hoi" style={{ ...BAL, fontFamily: M.serif, fontWeight: 600, fontSize: size, lineHeight: 1.15, marginTop: 10, color: M.ink }}>
            {str(p.q)}
          </div>
        </div>
      </Appear>
      <Appear at={aAt} kind="right" x={safe.left + w * 0.14} y={top + size * 4.4} w={w * 0.86}>
        <div data-ve="box" data-ve-name="dap" style={{ background: M.accent, borderRadius: "34px 34px 8px 34px", padding: "26px 32px", boxShadow: shadow(1), color: "#fff" }}>
          <div style={{ fontFamily: M.sans, fontWeight: 800, fontSize: size * 0.55, letterSpacing: 2, textTransform: "uppercase", opacity: 0.85 }}>{str(p.answerLabel) || "Trả lời"}</div>
          <div data-ve="text" data-ve-name="tra-loi" style={{ ...BAL, fontFamily: M.serif, fontWeight: 600, fontSize: size, lineHeight: 1.15, marginTop: 10, opacity: prog(t, aAt + 0.1, aAt + 0.5) }}>
            {str(p.a)}
          </div>
        </div>
      </Appear>
    </>
  );
};

registerScenes({
  "tieu-de": TieuDe,
  chat: Chat,
  checklist: ChecklistScene,
  "dem-so": DemSo,
  "song-am": SongAm,
  "so-do": SoDo,
  "tai-lieu": TaiLieu,
  terminal: TerminalScene,
  "luoi-anh": LuoiAnh,
  "dong-ho": DongHo,
  "thu-muc": ThuMuc,
  "dong-thoi-gian": DongThoiGian,
  "chu-nghieng": ChuNghieng,
  "nhan-dan": NhanDan,
  "so-sanh": SoSanh,
  "re-nhanh": ReNhanh,
  "luu-y": LuuY,
  "hoi-dap": HoiDap,
});
