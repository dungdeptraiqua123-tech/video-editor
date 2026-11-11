// Đo bố cục từng ảnh storyboard (soát bố cục tự động, ve/layout.py) cho bộ dựng HyperFrames.
//   node probe.mjs <thư mục dự án HyperFrames> <jobs.json> <probe.json> <trình duyệt>
// jobs.json: [{"t": 12.4, "output": "/đường/dẫn/03.jpg"}, ...]
// Mở index.html?probe ngoài HyperFrames (không cần khung hình video), tua bằng window.__veSeek(t); thành phần Probe ghi
// "VE_PROBE {json}" ra console cho mỗi khung. Ảnh thì `hyperframes snapshot` chụp riêng; file này chỉ lấy số đo.
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import puppeteer from "puppeteer-core";

const [dir, jobsPath, outPath, exe] = process.argv.slice(2);
const jobs = JSON.parse(fs.readFileSync(jobsPath, "utf-8"));
const props = JSON.parse(fs.readFileSync(path.join(dir, "ve", "props.json"), "utf-8"));
const W = props.format.w;
const H = props.format.h;

const types = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".woff2": "font/woff2", ".woff": "font/woff", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".svg": "image/svg+xml" };
const root = path.resolve(dir);
const server = http.createServer((req, res) => {
  const rel = decodeURIComponent(new URL(req.url, "http://127.0.0.1").pathname).replace(/^\/+/, "");
  const file = path.join(root, rel || "index.html");
  if (!file.startsWith(root)) return res.writeHead(403).end();
  const ext = path.extname(file).toLowerCase();
  // video và âm thanh không cần cho việc đo: trả rỗng cho nhanh
  if (/\.(mp4|mov|webm|m4v|mp3|m4a|wav|aac|ogg)$/i.test(file)) return res.writeHead(204).end();
  fs.readFile(file, (err, buf) => {
    if (err) return res.writeHead(404).end();
    res.writeHead(200, { "content-type": types[ext] || "application/octet-stream" }).end(buf);
  });
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const port = server.address().port;

const root0 = typeof process.getuid === "function" && process.getuid() === 0;
const browser = await puppeteer.launch({
  executablePath: exe,
  headless: true,
  args: [...(root0 ? ["--no-sandbox"] : []), "--disable-gpu", "--hide-scrollbars", "--font-render-hinting=none"],
});
const probes = [];
try {
  const page = await browser.newPage();
  await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
  await page.evaluateOnNewDocument(() => {
    window.__veLog = [];
    const log = console.log.bind(console);
    console.log = (...a) => {
      const s = a.map(String).join(" ");
      if (s.startsWith("VE_PROBE")) window.__veLog.push(s);
      else log(...a);
    };
  });
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto(`http://127.0.0.1:${port}/index.html?probe`, { waitUntil: "load", timeout: 120000 });
  await page.waitForFunction(() => typeof window.__veSeek === "function", { timeout: 60000 });
  for (const j of jobs) {
    const lines = await page.evaluate(async (t) => {
      await window.__veReady;
      window.__veLog.length = 0;
      await window.__veSeek(t);
      await new Promise((r) => setTimeout(r, 0));
      return window.__veLog.splice(0);
    }, j.t);
    for (const s of lines) {
      if (s.startsWith("VE_PROBE ")) probes.push({ output: j.output, ...JSON.parse(s.slice(9)) });
      else if (s.startsWith("VE_PROBE_ERR")) probes.push({ output: j.output, error: s });
    }
  }
  if (errors.length) console.error("lỗi trong trang:\n" + errors.slice(0, 5).join("\n"));
} finally {
  await browser.close();
  server.close();
  fs.writeFileSync(outPath, JSON.stringify(probes));
}
console.log(`ok ${probes.length} số đo`);
