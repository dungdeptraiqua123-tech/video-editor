import React from "react";
import { AbsoluteFill } from "remotion";
import { Icon } from "./Icons";
import { C, glow } from "./theme";

const SW = [
  { name: "Navy đêm", hex: C.night, use: "Nền chính", ratio: "60%" },
  { name: "Navy thẻ", hex: C.panel, use: "Thẻ, khung", ratio: "" },
  { name: "Xanh dương", hex: C.orange, use: "Màu chủ đạo: nút, nhãn, viền", ratio: "25%" },
  { name: "Xanh sáng", hex: C.sky, use: "Từ khoá, ánh sáng viền", ratio: "" },
  { name: "Vàng hổ phách", hex: C.gold, use: "Điểm nhấn: con số, Bitcoin", ratio: "10%" },
  { name: "Xanh lá / Đỏ", hex: `${C.green} / ${C.red}`, use: "Chỉ dùng cho tăng / giảm", ratio: "5%" },
];

const Label: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{ color: C.sky, fontSize: 24, fontWeight: 800, letterSpacing: 4, textTransform: "uppercase", marginBottom: 18 }}>{children}</div>
);

export const BrandSheet: React.FC = () => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse at 70% 0%, #10306e 0%, ${C.night} 55%)`, fontFamily: C.font, padding: 70, color: C.white }}>
    <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
      <Icon name="btc" size={74} />
      <div>
        <div style={{ fontSize: 26, fontWeight: 800, color: C.sky, letterSpacing: 4 }}>BỘ NHẬN DIỆN</div>
        <div style={{ fontSize: 64, fontWeight: 900, lineHeight: 1.05 }}>BTC DAILY</div>
      </div>
    </div>
    <div style={{ width: 140, height: 8, borderRadius: 4, background: C.orange, boxShadow: glow(C.orange, 12), margin: "26px 0 44px" }} />

    <Label>Bảng màu · tỉ lệ 60 / 25 / 10 / 5</Label>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 18 }}>
      {SW.map((s) => (
        <div key={s.name} style={{ background: C.panel, border: `2px solid ${C.line}`, borderRadius: 22, overflow: "hidden" }}>
          <div style={{ height: 110, display: "flex" }}>
            {s.hex.split(" / ").map((h) => (
              <div key={h} style={{ flex: 1, background: h, borderBottom: `2px solid ${C.line}` }} />
            ))}
          </div>
          <div style={{ padding: "14px 18px 18px" }}>
            <div style={{ fontSize: 28, fontWeight: 800 }}>{s.name} {s.ratio ? <span style={{ color: C.mute, fontWeight: 600 }}>· {s.ratio}</span> : null}</div>
            <div style={{ fontSize: 22, color: C.sky, fontWeight: 600, marginTop: 4 }}>{s.hex.toUpperCase()}</div>
            <div style={{ fontSize: 22, color: C.mute, marginTop: 6, lineHeight: 1.3 }}>{s.use}</div>
          </div>
        </div>
      ))}
    </div>

    <div style={{ display: "flex", gap: 40, marginTop: 50 }}>
      <div style={{ flex: 1 }}>
        <Label>Chữ · Be Vietnam Pro</Label>
        <div style={{ fontSize: 64, fontWeight: 900, lineHeight: 1.1 }}>Tiêu đề 900</div>
        <div style={{ fontSize: 44, fontWeight: 800, marginTop: 8 }}>Phụ đề 800</div>
        <div style={{ fontSize: 32, fontWeight: 600, color: C.mute, marginTop: 8 }}>Nội dung 600</div>
      </div>
      <div style={{ flex: 1.2 }}>
        <Label>Phụ đề · chỉ tô sáng từ khoá</Label>
        <div style={{ fontSize: 46, fontWeight: 800, lineHeight: 1.3, textShadow: "0 3px 12px rgba(0,0,0,0.85)" }}>
          <span style={{ color: C.sky, textShadow: glow(C.sky, 16) }}>Bitcoin</span> đang giữ trên mốc{" "}
          <span style={{ color: C.gold, textShadow: glow(C.gold, 16) }}>86 ngàn</span>
        </div>
        <div style={{ fontSize: 22, color: C.mute, marginTop: 14 }}>Chữ thường theo câu, tối đa 2 dòng. Xanh sáng cho thuật ngữ, vàng cho con số.</div>
      </div>
    </div>

    <div style={{ marginTop: 50 }}>
      <Label>Thành phần</Label>
      <div style={{ display: "flex", gap: 30, alignItems: "flex-start" }}>
        <div style={{ background: "rgba(11,27,63,0.86)", border: `2px solid ${C.line}`, borderRadius: 26, padding: "22px 30px", width: 470 }}>
          <div style={{ color: C.sky, fontSize: 22, fontWeight: 800, letterSpacing: 3 }}>THẺ CHỦ ĐỀ</div>
          <div style={{ fontSize: 40, fontWeight: 800, marginTop: 4 }}>Dòng tiền hôm nay</div>
          {["Volume ETF dương", "BTC mạnh hơn ETH"].map((t) => (
            <div key={t} style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 10 }}>
              <Icon name="check" size={34} color={C.orange} />
              <span style={{ fontSize: 30, fontWeight: 600 }}>{t}</span>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{ alignSelf: "flex-start", background: C.orange, borderRadius: 14, padding: "10px 24px", fontSize: 30, fontWeight: 900, boxShadow: `0 0 26px ${C.orange}66` }}>NHÃN ĐỒ HOẠ</div>
          <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
            <div style={{ width: 120, height: 150, borderRadius: 24, border: `4px solid ${C.sky}`, boxShadow: glow(C.orange, 18), background: "#1b2a4a", display: "flex", alignItems: "center", justifyContent: "center", color: C.mute, fontSize: 20, textAlign: "center" }}>Ô mặt<br />người nói</div>
            <div style={{ fontSize: 22, color: C.mute, width: 230, lineHeight: 1.35 }}>Viền xanh sáng 4px, bo góc 30px, góc trên bên phải</div>
          </div>
        </div>
      </div>
    </div>

    <div style={{ position: "absolute", left: 70, right: 70, bottom: 60, fontSize: 24, color: C.mute, lineHeight: 1.5 }}>
      Quy tắc: xanh lá và đỏ chỉ dành cho tăng / giảm · vàng chỉ cho con số và Bitcoin · chuyển cảnh mờ dần, không quét sọc.
    </div>
  </AbsoluteFill>
);
