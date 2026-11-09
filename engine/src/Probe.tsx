/**
 * Đo bố cục khi chụp ảnh soát (props.probe = true): vị trí từng phần tử có data-ve, chữ bị cắt / tràn / ra ngoài khung,
 * số dòng và chữ lẻ cuối dòng, khung trống, chữ khoá icon in ra màn hình. Ghi một dòng "VE_PROBE {json}" ra console;
 * stills.mjs thu lại, ve/layout.py đối chiếu luật và viết out/soat-bo-cuc.md. Không vẽ gì nên ảnh chụp không đổi.
 */
import React, { useEffect, useRef, useState } from "react";
import { continueRender, delayRender, useCurrentFrame } from "remotion";

type Box = { x: number; y: number; w: number; h: number };

const visibleOpacity = (el: Element, root: Element) => {
  let o = 1;
  for (let e: Element | null = el; e && e !== root.parentElement; e = e.parentElement) {
    const cs = getComputedStyle(e);
    if (cs.display === "none" || cs.visibility === "hidden") return 0;
    o *= parseFloat(cs.opacity || "1");
  }
  return o;
};

const measure = (root: HTMLElement, frame: number, W: number, H: number, face: Box | null) => {
  const rr = root.getBoundingClientRect();
  const k = rr.width / W || 1;
  const box = (r: DOMRect): Box => ({ x: (r.left - rr.left) / k, y: (r.top - rr.top) / k, w: r.width / k, h: r.height / k });
  const nodes = Array.from(root.querySelectorAll<HTMLElement>("[data-ve]")).filter((el) => el.dataset.ve !== "scene");
  const index = new Map(nodes.map((el, i) => [el, i]));
  const leafText = (el: HTMLElement) =>
    Array.from(el.querySelectorAll<HTMLElement>("*"))
      .concat([el])
      .filter((c) => c.childElementCount === 0 && (c.textContent || "").trim() && visibleOpacity(c, root) > 0.35);
  const items = nodes.map((el) => {
    const kind = el.dataset.ve || "";
    let r = box(el.getBoundingClientRect());
    if (el.dataset.veTight !== undefined) {
      // khối rộng hơn phần chữ thật (phụ đề): lấy hợp các mẩu chữ đang hiện
      const rs = leafText(el).map((c) => box(c.getBoundingClientRect()));
      if (rs.length) {
        const x0 = Math.min(...rs.map((b) => b.x)), y0 = Math.min(...rs.map((b) => b.y));
        const x1 = Math.max(...rs.map((b) => b.x + b.w)), y1 = Math.max(...rs.map((b) => b.y + b.h));
        r = { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
      }
    }
    const scene = el.closest<HTMLElement>('[data-ve="scene"]');
    const anc: number[] = [];
    for (let p = el.parentElement; p && p !== root; p = p.parentElement) {
      const i = index.get(p as HTMLElement);
      if (i !== undefined) anc.push(i);
    }
    // phần nhìn thấy sau khi bị khung cha (overflow ẩn) và mép khung hình cắt
    let vis = { ...r };
    for (let p = el.parentElement; p && p !== root.parentElement; p = p.parentElement) {
      const cs = getComputedStyle(p);
      if (cs.overflow !== "visible" || p === root) {
        const pb = box(p.getBoundingClientRect());
        const x0 = Math.max(vis.x, pb.x), y0 = Math.max(vis.y, pb.y);
        const x1 = Math.min(vis.x + vis.w, pb.x + pb.w), y1 = Math.min(vis.y + vis.h, pb.y + pb.h);
        vis = { x: x0, y: y0, w: Math.max(0, x1 - x0), h: Math.max(0, y1 - y0) };
      }
    }
    const area = r.w * r.h;
    const out: Record<string, unknown> = {
      kind,
      name: el.dataset.veName || "",
      scene: scene?.dataset.veName || "",
      layer: scene?.dataset.veLayer || "",
      r: [Math.round(r.x), Math.round(r.y), Math.round(r.w), Math.round(r.h)],
      o: Math.round(visibleOpacity(el, root) * 100) / 100,
      shown: area > 0 ? Math.round(((vis.w * vis.h) / area) * 100) / 100 : 1,
      anc,
    };
    if (kind === "text" || kind === "cta" || kind === "hook" || kind === "topic") {
      // ghép theo từng mẩu chữ (WordReveal tách từ thành ô riêng nên innerText dính liền)
      const parts: string[] = [];
      const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      for (let n = tw.nextNode(); n; n = tw.nextNode()) if ((n.textContent || "").trim()) parts.push((n.textContent || "").trim());
      out.text = parts.join(" ").replace(/\s+/g, " ").slice(0, 90);
      out.over = el.scrollWidth > el.clientWidth + 3 && getComputedStyle(el).overflow !== "visible";
      // dòng chữ: gom từng từ theo toạ độ dọc
      const tops: { top: number; word: string }[] = [];
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      for (let n = walker.nextNode(); n; n = walker.nextNode()) {
        const s = n.textContent || "";
        for (const m of s.matchAll(/\S+/g)) {
          const rg = document.createRange();
          rg.setStart(n, m.index ?? 0);
          rg.setEnd(n, (m.index ?? 0) + m[0].length);
          const b = rg.getBoundingClientRect();
          if (b.width > 0) tops.push({ top: Math.round(b.top / k), word: m[0] });
        }
      }
      const lines: string[][] = [];
      let last = -1e9;
      for (const t of tops.sort((a, b) => a.top - b.top)) {
        if (Math.abs(t.top - last) > 6) {
          lines.push([]);
          last = t.top;
        }
        lines[lines.length - 1].push(t.word);
      }
      out.lines = lines.length;
      if (lines.length >= 2) out.lastLine = lines[lines.length - 1].join(" ");
    }
    if (kind === "box") {
      // khung có nội dung thấy được (chữ, ảnh, hình) ngoài thanh tiêu đề?
      const filled = Array.from(el.querySelectorAll<HTMLElement>("*")).some(
        (c) =>
          !c.closest("[data-ve-bar]") &&
          ((c.childElementCount === 0 && (c.textContent || "").trim()) || ["IMG", "svg", "VIDEO", "CANVAS"].includes(c.tagName)) &&
          c.getBoundingClientRect().width > 2 &&
          visibleOpacity(c, root) > 0.35,
      );
      out.filled = filled;
    }
    return out;
  });
  // mỗi cảnh motion đang hiện: có chữ / ảnh thấy được chưa (phát hiện cảnh mở ra trống)
  const scenes = Array.from(root.querySelectorAll<HTMLElement>('[data-ve="scene"]')).map((sc) => ({
    name: sc.dataset.veName || "",
    layer: sc.dataset.veLayer || "",
    o: Math.round(visibleOpacity(sc, root) * 100) / 100,
    text: leafText(sc).length > 0,
  }));
  // chữ khoá icon (lu:… / si:…) bị in thẳng ra màn hình
  const codes: string[] = [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const m = (n.textContent || "").match(/\b(lu|si):[a-z0-9][\w-]*/i);
    if (m && n.parentElement && visibleOpacity(n.parentElement, root) > 0.35) codes.push(m[0]);
  }
  // eslint-disable-next-line no-console
  console.log("VE_PROBE " + JSON.stringify({ frame, w: W, h: H, face, items, codes, scenes }));
};

/** Gắn với key={frame} để mỗi khung chụp có một lần đo (và một lần delayRender) riêng. */
export const Probe: React.FC<{ W: number; H: number; face: Box | null }> = ({ W, H, face }) => {
  const frame = useCurrentFrame();
  const [handle] = useState(() => delayRender("đo bố cục"));
  const sent = useRef(false);
  useEffect(() => {
    const finish = () => {
      if (sent.current) return;
      sent.current = true;
      try {
        const root = document.querySelector<HTMLElement>("[data-ve-root]");
        if (root) measure(root, frame, W, H, face);
      } catch (e) {
        // eslint-disable-next-line no-console
        console.log("VE_PROBE_ERR " + String(e));
      }
      continueRender(handle);
    };
    (document.fonts?.ready ?? Promise.resolve()).then(() => requestAnimationFrame(() => requestAnimationFrame(finish)));
    const t = setTimeout(finish, 4000);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [frame, handle]);
  return null;
};
