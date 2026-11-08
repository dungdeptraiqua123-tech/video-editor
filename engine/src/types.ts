export type Word = { text: string; start: number; end: number; /** icon nhỏ gắn cạnh chữ trong phụ đề (khoá trong Props.icons) */ ic?: string };

/** Hình icon nhúng sẵn trong dữ liệu render: logo thương hiệu (brand), icon nét (line) hoặc ảnh riêng (img). */
export type IconData = { kind: "brand" | "line" | "img"; body?: string; viewBox?: string; color?: string | null; src?: string; label?: string };

/** Icon bật lên lúc người nói nhắc tới (t: giây trong video đã cắt). */
export type Pop = { t: number; id: string; word: string };

/** Chữ lớn đập vào màn hình đúng lúc nói một con số, một ý mạnh. */
export type Punch = { t: number; text: string; sub?: string; tone?: "up" | "down" | "neutral" };

export type Transition = "mem" | "vuot" | "zoom" | "flash" | "glitch";

export type IconName =
  | "btc" | "up" | "down" | "bank" | "warn" | "target" | "chart" | "wallet"
  | "clock" | "fire" | "shield" | "people" | "dollar" | "check";

export type Graphic =
  | { type: "price"; label: string; value: number; d?: number; changeD?: number; prefix?: string; suffix?: string; change?: string; up?: boolean; icon?: IconName; decimals?: number }
  | { type: "chart"; title: string; points: number[]; up?: boolean; tags?: { i: number; text: string; d?: number }[]; xLabels?: string[]; yLabels?: string[]; source?: string }
  | { type: "levels"; title: string; levels: { value: string; label: string; kind: "res" | "sup" | "now"; d?: number }[] }
  | { type: "list"; title: string; items: { icon: IconName; text: string; d?: number }[] }
  | { type: "stat"; icon: IconName; big: string; label: string; tone?: "up" | "down" | "neutral"; d?: number; labelD?: number }
  | { type: "title"; kicker: string; text: string }
  | { type: "media"; src: string; label?: string; fit?: "cover" | "contain"; kenBurns?: boolean; d?: number; full?: boolean; credit?: string }
  | { type: "compare"; title: string; left: Side; right: Side; winner?: "left" | "right"; d?: number }
  | { type: "timeline"; title: string; items: { when: string; text: string; d?: number }[] }
  | { type: "progress"; title: string; items: { label: string; value: number; suffix?: string; d?: number }[]; ring?: boolean }
  | { type: "quote"; text: string; author?: string; d?: number }
  | { type: "table"; title: string; cols: string[]; rows: { cells: string[]; tone?: "up" | "down" | "neutral"; d?: number }[] }
  | { type: "countdown"; title: string; items: { text: string; d?: number }[] };

export type Side = { label: string; value: string; icon?: IconName; tone?: "up" | "down" | "neutral"; d?: number };

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

export type CaptionStyle = "plain" | "box" | "glow" | "pop" | "karaoke";

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
  /** Hiện icon nhỏ cạnh từ được nhắc tới (logo, khái niệm). */
  icons?: boolean;
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
    /** Đường đi của mặt người nói theo thời gian bản cắt: [giây, x, y] tỉ lệ 0–1 của khung gốc (bám mặt khi đổi khổ). */
    faceTrack?: number[][];
    background?: { src: string; duration: number } | null;
    /** Nhạc nền: duck = hệ số âm lượng khi có người nói (0–1), fade = giây tăng/giảm dần ở đầu/cuối. */
    music?: { src: string; volume: number; duck?: number; fade?: number; start?: number } | null;
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
  /** Icon tự hiện theo lời. */
  icons?: Record<string, IconData>;
  pops?: Pop[];
  punches?: Punch[];
  /** Phụ đề dòng hai (song ngữ), thời gian theo video đã cắt. */
  second?: { start: number; end: number; text: string }[];
  /** Hiệu ứng động: kiểu chuyển cảnh, rung khung khi chữ đập, hạt bay nền, nhịp nhạc (giây). */
  fx?: { transition: Transition; shake: boolean; particles: boolean; musicBeats?: number[] };
};
