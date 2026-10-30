import { CalculateMetadataFunction, Composition } from "remotion";
import sample from "./sample.json";
import { Props } from "./types";
import { Video } from "./Video";

/** Khổ hình, fps, thời lượng lấy từ dữ liệu dự án (work/data.json, truyền qua --props). */
const calc: CalculateMetadataFunction<Props> = ({ props }) => ({
  width: props.format.w,
  height: props.format.h,
  fps: props.format.fps,
  durationInFrames: Math.max(1, Math.round(props.duration * props.format.fps)),
});

export const RemotionRoot: React.FC = () => (
  <Composition id="Video" component={Video} calculateMetadata={calc} defaultProps={sample as unknown as Props} width={1080} height={1920} fps={30} durationInFrames={300} />
);
