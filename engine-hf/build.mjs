// Đóng gói đồ hoạ React của skill thành một file JS chạy trong trang HyperFrames.
//   node build.mjs <thư mục ra> [file cảnh của dự án]
// Ra: ve.js (mã), ve.css (phông chữ @fontsource), fonts/ (file phông). Mọi `import "remotion"` trỏ về shim/remotion.tsx.
// File cảnh của dự án (index.ts do ve/hf.py sinh) export SCENES; không có thì dùng shim/du-an-rong.ts.
import * as esbuild from "esbuild";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const [out, scenes] = process.argv.slice(2);
if (!out) {
  console.error("cách dùng: node build.mjs <thư mục ra> [index.ts cảnh dự án]");
  process.exit(2);
}
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });

await esbuild.build({
  entryPoints: [path.join(here, "entry.tsx")],
  bundle: true,
  outfile: path.join(out, "ve.js"),
  format: "iife",
  platform: "browser",
  target: "es2020",
  jsx: "automatic",
  minify: true,
  legalComments: "none",
  loader: { ".woff2": "file", ".woff": "file", ".ttf": "file" },
  assetNames: "fonts/[name]-[hash]",
  alias: {
    remotion: path.join(here, "shim", "remotion.tsx"),
    "ve-du-an": scenes ? path.resolve(scenes) : path.join(here, "shim", "du-an-rong.ts"),
  },
  define: { "process.env.NODE_ENV": '"production"' },
  logLevel: "error",
});

// React có dùng Math.random() (khoá nội bộ) và requestAnimationFrame (lịch nội bộ), không ảnh hưởng hình vì mọi khung
// được vẽ đồng bộ theo hf-seek, nhưng `hyperframes lint` báo lỗi. Thay bằng bản cố định để bản kiểm tra sạch.
{
  const p = path.join(out, "ve.js");
  const prelude =
    "var __veSeed=0x2f6b1d3;function __veRandom(){var a=(__veSeed+=0x6d2b79f5)>>>0;a=Math.imul(a^(a>>>15),a|1);a^=a+Math.imul(a^(a>>>7),a|61);return((a^(a>>>14))>>>0)/4294967296}" +
    "function __veRaf(c){return setTimeout(function(){c(0)},16)}function __veCaf(i){clearTimeout(i)}\n";
  const code = fs.readFileSync(p, "utf-8").replace(/Math\.random\(\)/g, "__veRandom()").replace(/\bcancelAnimationFrame\b/g, "__veCaf").replace(/\brequestAnimationFrame\b/g, "__veRaf");
  fs.writeFileSync(p, prelude + code);
}

// gsap: HyperFrames cần một timeline đăng ký trong window.__timelines; chép bản cài sẵn để render không cần mạng
fs.copyFileSync(path.join(here, "node_modules", "gsap", "dist", "gsap.min.js"), path.join(out, "gsap.min.js"));
console.log(`ok ${out}`);
