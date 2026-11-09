/**
 * Cảnh motion có sẵn (dùng bằng tham số, không cần viết code). Tên cảnh = khoá trong registerScenes.
 * Hermes ghép cảnh mới bằng kit khi các cảnh này không hợp (xem huong-dan/motion.md).
 * Quy ước tham số: chữ trong p.*, mốc thời gian là p.d / item.d (giây từ lúc cảnh mở, do build đổi từ "say").
 */
/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import {
  Appear,
  ChatBubble,
  Checklist,
  Clock,
  Connector,
  Counter,
  DocWriter,
  Folder,
  GridPop,
  Headline,
  InputBar,
  Node,
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
import { M } from "./theme";

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

const contentTop = (p: any, safe: SceneProps["safe"]) => (p.title ? safe.top + 40 + num(p.size, 84) * (p.accent ? 2.6 : 1.6) + (p.kicker ? 50 : 0) + 60 : safe.top + 60);

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
  const top = layer === "overlay" ? safe.top + 40 : contentTop(p, safe);
  const askAt = num(p.askD, 0.4);
  const ask = str(p.ask);
  const sendAt = askAt + ask.length / 18 + 0.35;
  const ansAt = Math.max(num(p.answerD, sendAt + 0.5), sendAt + 0.3);
  const t = useSec();
  return (
    <>
      {layer === "full" ? <Head p={p} safe={safe} W={W} /> : null}
      <Window x={safe.left} y={top} w={W - safe.left * 2} h={num(p.h, 640)} title={str(p.app) || "Claude"} at={0.1} bodyStyle={{ display: "flex", flexDirection: "column" }}>
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
  const top = layer === "overlay" ? safe.top + 40 : contentTop(p, safe);
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
});
