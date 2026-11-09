import React from "react";
import { IconData } from "../types";
import { Safe } from "./registry";

/** Vùng an toàn của cảnh đang vẽ: viên gạch (Headline…) tự tránh ô mặt người nói / ô PIP mà cảnh không phải truyền tay. */
export const SafeCtx = React.createContext<Safe | null>(null);
export const useSafe = () => React.useContext(SafeCtx);

let ICONS: Record<string, IconData> = {};
/** Bảng icon của video (lu:… / si:… / file:…) do build đọc sẵn; Video gọi trước khi vẽ. */
export const setMotionIcons = (t: Record<string, IconData> | undefined | null) => {
  ICONS = t || {};
};
export const motionIcon = (id: string): IconData | undefined => ICONS[id];

/** Chữ khoá icon (lu:wallet, si:bitcoin, file:…): là mã để tra hình, không bao giờ in ra màn hình. */
export const ICON_CODE = /^(lu|si|file):[\w.\/-]+$/i;
