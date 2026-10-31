// Chụp nhiều khung hình trong một lần mở trình duyệt (nhanh hơn gọi `remotion still` từng ảnh).
// node stills.mjs <bundle> <props.json> <jobs.json> <scale> <số thẻ song song> [trình duyệt]
// jobs.json: [{"frame": 120, "output": "/đường/dẫn/01.jpg"}, ...]
import fs from "node:fs";
import { openBrowser, renderStill, selectComposition } from "@remotion/renderer";

const [serveUrl, propsPath, jobsPath, scale, concurrency, browserExecutable] = process.argv.slice(2);
const inputProps = JSON.parse(fs.readFileSync(propsPath, "utf-8"));
const jobs = JSON.parse(fs.readFileSync(jobsPath, "utf-8"));
const exe = browserExecutable || null;
const browser = await openBrowser("chrome", { browserExecutable: exe, logLevel: "error" });
try {
  const composition = await selectComposition({ serveUrl, id: "Video", inputProps, puppeteerInstance: browser, browserExecutable: exe, logLevel: "error" });
  // vài thẻ song song trong cùng trình duyệt
  const queue = [...jobs];
  const worker = async () => {
    for (let j = queue.shift(); j; j = queue.shift()) {
      await renderStill({
        composition, serveUrl, inputProps, frame: j.frame, output: j.output, scale: Number(scale) || 1,
        imageFormat: "jpeg", jpegQuality: 88, puppeteerInstance: browser, browserExecutable: exe, logLevel: "error", overwrite: true,
      });
      console.log(`ok ${j.output}`);
    }
  };
  await Promise.all(Array.from({ length: Math.max(1, Number(concurrency) || 1) }, worker));
} finally {
  await browser.close({ silent: true });
}
