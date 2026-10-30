import { Composition } from "remotion";
import data from "./data.json";
import { BitcoinReel } from "./Reel";
import { BrandSheet } from "./BrandSheet";
import { FPS, H, W } from "./theme";
import { ReelData } from "./types";

const d = data as ReelData;

export const RemotionRoot: React.FC = () => (
  <>
  <Composition id="BrandSheet" component={BrandSheet} fps={FPS} width={1080} height={1920} durationInFrames={1} />
  <Composition
    id="BitcoinReel"
    component={BitcoinReel}
    fps={FPS}
    width={W}
    height={H}
    durationInFrames={Math.round(d.duration * FPS)}
    defaultProps={{ data: d, video: "cut.mp4" }}
  />
  </>
);
