export type Word = { text: string; start: number; end: number };

export type IconName =
  | "btc" | "up" | "down" | "bank" | "warn" | "target" | "chart" | "wallet"
  | "clock" | "fire" | "shield" | "people" | "dollar" | "check";

export type Graphic =
  | { type: "price"; label: string; value: number; d?: number; changeD?: number; prefix?: string; suffix?: string; change?: string; up?: boolean; icon?: IconName; decimals?: number }
  | { type: "chart"; title: string; points: number[]; up?: boolean; tags?: { i: number; text: string; d?: number }[] }
  | { type: "levels"; title: string; levels: { value: string; label: string; kind: "res" | "sup" | "now"; d?: number }[] }
  | { type: "list"; title: string; items: { icon: IconName; text: string; d?: number }[] }
  | { type: "stat"; icon: IconName; big: string; label: string; tone?: "up" | "down" | "neutral"; d?: number; labelD?: number }
  | { type: "title"; kicker: string; text: string }
  | { type: "media"; src: string; label?: string; fit?: "cover" | "contain"; kenBurns?: boolean; d?: number };

export type Beat = { start: number; end: number; head: string; g: Graphic };

/** Thẻ chủ đề ở góc trên khi chỉ có người nói; các ý được tick dần theo lời nói. */
export type Topic = { start: number; end: number; kicker: string; title: string; items: { at: number; text: string }[] };

export type Brand = {
  name: string;
  /** Chữ trên huy hiệu mở đầu và nhãn nhỏ trên tiêu đề cảnh. */
  badge: string;
  colors: {
    bg: string; bg2?: string; panel: string; line: string; primary: string; highlight: string;
    number: string; up: string; down: string; text?: string; mute: string;
  };
  font: { family: string; file?: string };
  /** Ảnh logo trong media/ (vd. "brand/logo.png"), hiện ở huy hiệu mở đầu. */
  logo?: string | null;
  /** Hoặc dùng một icon có sẵn thay cho logo. */
  hookIcon?: IconName | null;
  backdrop?: "grid" | "plain";
};

export type CaptionStyle = "plain" | "box" | "glow" | "pop";

export type CaptionCfg = {
  enabled: boolean;
  style: CaptionStyle;
  /** Vị trí tâm phụ đề theo tỉ lệ chiều cao (0–1). null = theo bố cục mặc định của khổ hình. */
  position: number | null;
  keywords: string[];
  maxChars: number;
  maxWords: number;
  /** Hệ số cỡ chữ, 1 = 64px trên khổ 1080. */
  size: number;
};

export type Props = {
  /** Địa chỉ máy chủ file của dự án khi render (do CLI đặt). */
  mediaBase?: string | null;
  format: { w: number; h: number; fps: number };
  duration: number;
  mode: "talking" | "faceless";
  brand: Brand;
  captions: CaptionCfg;
  media: {
    main: string;
    hasVideo: boolean;
    srcW?: number;
    srcH?: number;
    face?: { x: number; y: number; pipScale?: number; fit?: "auto" | "cover" | "contain" };
    background?: { src: string; duration: number } | null;
    music?: { src: string; volume: number } | null;
  };
  /** Âm thanh hiệu ứng (file thu thật trong media/): false = tắt. */
  sfx: false | { files: Partial<Record<"whoosh" | "impact" | "riser" | "click" | "pop" | "tick", string>>; volume: number };
  hook: { kicker?: string; title: string; sub?: string };
  hookSec: number;
  outroSec: number;
  cta: string;
  ctaButtons?: string[];
  words: Word[];
  beats: Beat[];
  topics: Topic[];
  zooms: number[];
};
