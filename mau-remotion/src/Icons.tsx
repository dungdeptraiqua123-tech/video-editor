import React from "react";
import { C } from "./theme";
import { IconName } from "./types";

/** Bộ icon vẽ bằng SVG (không phụ thuộc font emoji khi render). */
export const Icon: React.FC<{ name: IconName; size?: number; color?: string }> = ({
  name,
  size = 96,
  color = C.orange,
}) => {
  const s = { width: size, height: size, display: "block" } as const;
  const stroke = { fill: "none", stroke: color, strokeWidth: 6, strokeLinecap: "round", strokeLinejoin: "round" } as const;
  switch (name) {
    case "btc":
      return (
        <svg viewBox="0 0 100 100" style={s}>
          <circle cx="50" cy="50" r="46" fill={C.gold} />
          <circle cx="50" cy="50" r="46" fill="none" stroke="#ffb54a" strokeWidth="3" />
          <text x="50" y="69" textAnchor="middle" fontSize="58" fontWeight="900" fill="#fff" fontFamily="Arial" transform="rotate(14 50 50)">
            ₿
          </text>
        </svg>
      );
    case "up":
      return (
        <svg viewBox="0 0 100 100" style={s}>
          <path d="M12 74 L38 48 L54 62 L86 28" {...stroke} stroke={C.green} strokeWidth={9} />
          <path d="M64 26 H88 V50" {...stroke} stroke={C.green} strokeWidth={9} />
        </svg>
      );
    case "down":
      return (
        <svg viewBox="0 0 100 100" style={s}>
          <path d="M12 26 L38 52 L54 38 L86 72" {...stroke} stroke={C.red} strokeWidth={9} />
          <path d="M64 74 H88 V50" {...stroke} stroke={C.red} strokeWidth={9} />
        </svg>
      );
    case "bank":
      return (
        <svg viewBox="0 0 100 100" style={s}>
          <path d="M10 36 L50 14 L90 36 Z" {...stroke} />
          <path d="M22 42 V74 M40 42 V74 M60 42 V74 M78 42 V74 M12 84 H88" {...stroke} />
        </svg>
      );
    case "warn":
      return (
        <svg viewBox="0 0 100 100" style={s}>
          <path d="M50 10 L92 86 H8 Z" {...stroke} stroke={C.gold} />
          <path d="M50 38 V60" {...stroke} stroke={C.gold} strokeWidth={9} />
          <circle cx="50" cy="73" r="5" fill={C.gold} />
        </svg>
      );
    case "target":
      return (
        <svg viewBox="0 0 100 100" style={s}>
          <circle cx="50" cy="50" r="38" {...stroke} />
          <circle cx="50" cy="50" r="22" {...stroke} />
          <circle cx="50" cy="50" r="7" fill={color} />
        </svg>
      );
    case "chart":
      return (
        <svg viewBox="0 0 100 100" style={s}>
          <path d="M14 14 V86 H88" {...stroke} />
          <rect x="26" y="52" width="12" height="26" rx="2" fill={color} />
          <rect x="46" y="38" width="12" height="40" rx="2" fill={color} />
          <rect x="66" y="24" width="12" height="54" rx="2" fill={color} />
        </svg>
      );
    case "wallet":
      return (
        <svg viewBox="0 0 100 100" style={s}>
          <rect x="10" y="24" width="80" height="58" rx="10" {...stroke} />
          <path d="M66 46 H90 V62 H66 Z" {...stroke} />
          <circle cx="74" cy="54" r="3" fill={color} />
        </svg>
      );
    case "clock":
      return (
        <svg viewBox="0 0 100 100" style={s}>
          <circle cx="50" cy="50" r="38" {...stroke} />
          <path d="M50 28 V50 L66 60" {...stroke} />
        </svg>
      );
    case "fire":
      return (
        <svg viewBox="0 0 100 100" style={s}>
          <path d="M50 8 C58 30 78 38 78 62 A28 28 0 0 1 22 62 C22 46 32 40 36 28 C42 40 46 42 50 8 Z" fill={C.gold} />
          <path d="M50 52 C54 62 62 64 62 74 A12 12 0 0 1 38 74 C38 66 46 62 50 52 Z" fill={C.gold} />
        </svg>
      );
    case "shield":
      return (
        <svg viewBox="0 0 100 100" style={s}>
          <path d="M50 8 L84 22 V48 C84 70 68 84 50 92 C32 84 16 70 16 48 V22 Z" {...stroke} />
          <path d="M34 50 L46 62 L68 38" {...stroke} stroke={C.green} />
        </svg>
      );
    case "people":
      return (
        <svg viewBox="0 0 100 100" style={s}>
          <circle cx="36" cy="34" r="13" {...stroke} />
          <circle cx="68" cy="38" r="10" {...stroke} />
          <path d="M12 84 C12 62 60 62 60 84 M58 66 C70 60 90 64 90 84" {...stroke} />
        </svg>
      );
    case "dollar":
      return (
        <svg viewBox="0 0 100 100" style={s}>
          <circle cx="50" cy="50" r="44" fill={C.green} />
          <text x="50" y="70" textAnchor="middle" fontSize="58" fontWeight="900" fill="#fff" fontFamily="Arial">
            $
          </text>
        </svg>
      );
    case "check":
      return (
        <svg viewBox="0 0 100 100" style={s}>
          <circle cx="50" cy="50" r="42" fill={C.green} />
          <path d="M30 52 L44 66 L72 36" fill="none" stroke="#fff" strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
  }
};
