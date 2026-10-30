export type Word = { text: string; start: number; end: number };

export type IconName =
  | "btc" | "up" | "down" | "bank" | "warn" | "target" | "chart" | "wallet"
  | "clock" | "fire" | "shield" | "people" | "dollar" | "check";

export type Graphic =
  | { type: "price"; label: string; value: number; d?: number; changeD?: number; prefix?: string; suffix?: string; change?: string; up?: boolean }
  | { type: "chart"; title: string; points: number[]; up?: boolean; tags?: { i: number; text: string; d?: number }[] }
  | { type: "levels"; title: string; levels: { value: string; label: string; kind: "res" | "sup" | "now"; d?: number }[] }
  | { type: "list"; title: string; items: { icon: IconName; text: string; d?: number }[] }
  | { type: "stat"; icon: IconName; big: string; label: string; tone?: "up" | "down" | "neutral"; d?: number; labelD?: number }
  | { type: "title"; kicker: string; text: string };

export type Beat = { start: number; end: number; head: string; g: Graphic };

/** Thẻ chủ đề ở góc trên khi chỉ có người nói; các ý được tick dần theo lời nói. */
export type Topic = { start: number; end: number; kicker: string; title: string; items: { at: number; text: string }[] };

export type ReelData = {
  hook: { kicker: string; title: string; sub?: string };
  duration: number;
  words: Word[];
  beats: Beat[];
  topics: Topic[];
  brand: string;
  /** Mốc thời gian đổi khung (zoom cắt) khi đang ở chế độ toàn màn hình. */
  zooms: number[];
  cta: string;
};
