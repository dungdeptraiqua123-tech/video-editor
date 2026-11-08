"""Giá thật cho biểu đồ: tải lịch sử giá coin từ CoinGecko (API công khai, miễn phí) hoặc nhập từ file CSV.

`video-editor gia <dự án> --coin bitcoin --den 2025-10-02 --ngay 30` ghi data/gia-bitcoin.json trong dự án.
Khung đồ hoạ `chart`/`price` có `"data": {"coin": "bitcoin", "ngay": 7}` thì build tự điền số liệu thật:
đường giá, nhãn ngày và giá cao/thấp, nguồn; tag có thể neo vào điểm "cuoi" (giá cuối), "cao", "thap".
"""
from __future__ import annotations

import csv
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .env import VEError, info, read_json, write_json

API = "https://api.coingecko.com/api/v3"
UA = "video-editor/0.3 (+skill dựng video)"
POINTS = 28  # số điểm vẽ trên biểu đồ, đủ mượt mà không rối

# tên quen gọi → id của CoinGecko
ALIAS = {"btc": "bitcoin", "eth": "ethereum", "sol": "solana", "bnb": "binancecoin", "xrp": "ripple", "doge": "dogecoin", "ada": "cardano", "usdt": "tether", "ton": "the-open-network", "sui": "sui", "ltc": "litecoin", "dot": "polkadot", "link": "chainlink"}


def coin_id(c: str) -> str:
    c = c.strip().lower()
    return ALIAS.get(c, c)


def data_file(root: Path, coin: str) -> Path:
    return Path(root) / "data" / f"gia-{coin_id(coin)}.json"


def _get(url: str) -> dict:
    headers = {"User-Agent": UA, "Accept": "application/json"}
    key = os.environ.get("COINGECKO_API_KEY")
    if key:
        headers["x-cg-demo-api-key"] = key
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(4 * (attempt + 1))
                continue
            if e.code == 404:
                raise VEError(f"CoinGecko không có coin \"{url.split('/coins/')[1].split('/')[0]}\".", "Dùng id của CoinGecko, ví dụ bitcoin, ethereum, solana (tra ở coingecko.com, phần API id).")
            raise VEError(f"CoinGecko trả lỗi {e.code}.", "Thử lại sau ít phút (giới hạn lượt gọi miễn phí), hoặc đặt COINGECKO_API_KEY (khoá Demo miễn phí), hoặc nhập file CSV: `--csv`.")
        except (urllib.error.URLError, TimeoutError) as e:
            raise VEError(f"Không kết nối được api.coingecko.com ({e}).", "Kiểm tra mạng, hoặc tải CSV giá từ sàn/TradingView rồi nhập: `video-editor gia <dự án> --csv gia.csv`.")
    raise VEError("CoinGecko từ chối do gọi quá nhiều.", "Đợi 1 phút rồi chạy lại.")


def fetch(coin: str, end: str | None = None, days: int = 30, vs: str = "usd") -> dict:
    """Lịch sử giá `days` ngày kết thúc ở ngày `end` (YYYY-MM-DD, mặc định hôm nay)."""
    cid = coin_id(coin)
    if end:
        try:
            to = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
        except ValueError:
            raise VEError(f"Ngày \"{end}\" sai định dạng.", "Ghi theo dạng năm-tháng-ngày, ví dụ 2025-10-02.")
    else:
        to = datetime.now(timezone.utc)
    frm = to - timedelta(days=days)
    url = f"{API}/coins/{cid}/market_chart/range?vs_currency={vs}&from={int(frm.timestamp())}&to={int(to.timestamp())}"
    d = _get(url)
    prices = [[int(t), float(p)] for t, p in d.get("prices", [])]
    if len(prices) < 2:
        raise VEError(f"CoinGecko không trả đủ dữ liệu giá cho {cid} trong khoảng này.", "Gói miễn phí chỉ cho xem 365 ngày gần nhất. Chọn ngày gần hơn hoặc nhập CSV.")
    return {"coin": cid, "vs": vs, "prices": prices, "source": "CoinGecko", "fetched": datetime.now(timezone.utc).isoformat(timespec="seconds"), "end": end, "days": days}


def from_csv(path: Path, coin: str, vs: str = "usd") -> dict:
    """CSV có cột ngày (date/time/ngay/thoi_gian) và cột giá (close/price/gia). Ngày dạng YYYY-MM-DD hoặc dấu thời gian."""
    rows = list(csv.DictReader(Path(path).read_text(encoding="utf-8-sig").splitlines()))
    if not rows:
        raise VEError(f"File {path} trống.")
    keys = {k.lower().strip(): k for k in rows[0]}
    dk = next((keys[k] for k in ("date", "time", "timestamp", "ngay", "ngày", "thoi_gian") if k in keys), None)
    pk = next((keys[k] for k in ("close", "price", "gia", "giá", "đóng cửa") if k in keys), None)
    if not dk or not pk:
        raise VEError(f"CSV cần cột ngày và cột giá. Đang có: {', '.join(rows[0])}.", "Đặt tên cột là date và close (hoặc ngay và gia).")
    out = []
    for r in rows:
        v = str(r[dk]).strip()
        try:
            ts = int(float(v) * (1 if float(v) > 1e11 else 1000))
        except ValueError:
            ts = int(datetime.fromisoformat(v[:19]).replace(tzinfo=timezone.utc).timestamp() * 1000)
        out.append([ts, float(str(r[pk]).replace(",", ""))])
    out.sort()
    return {"coin": coin_id(coin), "vs": vs, "prices": out, "source": Path(path).name, "fetched": datetime.now(timezone.utc).isoformat(timespec="seconds"), "end": None, "days": None}


def save(root: Path, d: dict) -> Path:
    p = data_file(root, d["coin"])
    p.parent.mkdir(parents=True, exist_ok=True)
    write_json(p, d)
    return p


def summary(d: dict, days: int | None = None) -> dict:
    ps = window(d, days)
    vals = [p for _, p in ps]
    first, last = vals[0], vals[-1]
    return {"first": first, "last": last, "high": max(vals), "low": min(vals), "pct": (last / first - 1) * 100 if first else 0.0,
            "from": _day(ps[0][0]), "to": _day(ps[-1][0])}


def window(d: dict, days: int | None) -> list:
    ps = d["prices"]
    if days:
        cut = ps[-1][0] - days * 86400_000
        ps = [p for p in ps if p[0] >= cut] or ps
    return ps


def _day(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%d/%m")


def money(v: float, vs: str = "usd") -> str:
    sym = "$" if vs == "usd" else ""
    if v >= 1000:
        return f"{sym}{v / 1000:,.1f}K".replace(".0K", "K")
    return f"{sym}{v:,.2f}" if v < 10 else f"{sym}{v:,.0f}"


def downsample(ps: list, n: int = POINTS) -> list:
    if len(ps) <= n:
        return ps
    step = (len(ps) - 1) / (n - 1)
    return [ps[round(i * step)] for i in range(n)]


def apply(g: dict, root: Path) -> list[str]:
    """Điền số liệu thật vào khung có "data". Trả về các dòng ghi chú (giá thật) để in cho người dựng đối chiếu với lời nói."""
    spec = g.pop("data", None)
    if not spec:
        return []
    if isinstance(spec, str):
        spec = {"coin": spec}
    coin = spec.get("coin", "bitcoin")
    p = data_file(root, coin)
    if not p.exists():
        raise VEError(f"Chưa có dữ liệu giá {coin_id(coin)} (data/{p.name}).", f"Chạy `video-editor gia {root} --coin {coin_id(coin)} --den <ngày quay>` trước.")
    d = read_json(p)
    days = spec.get("ngay") or spec.get("days")
    s = summary(d, days)
    vs = d.get("vs", "usd")
    if g.get("type") == "chart":
        ps = downsample(window(d, days))
        g["points"] = [round(v, 2) for _, v in ps]
        g.setdefault("up", s["last"] >= s["first"])
        g["xLabels"] = [_day(ps[0][0]), _day(ps[-1][0])]
        g["yLabels"] = [money(min(g["points"]), vs), money(max(g["points"]), vs)]
        g["source"] = f"Nguồn: {d.get('source', 'CoinGecko')} · giá {vs.upper()}"
        idx = {"cuoi": len(ps) - 1, "last": len(ps) - 1, "dau": 0, "first": 0,
               "cao": max(range(len(ps)), key=lambda i: ps[i][1]), "max": max(range(len(ps)), key=lambda i: ps[i][1]),
               "thap": min(range(len(ps)), key=lambda i: ps[i][1]), "min": min(range(len(ps)), key=lambda i: ps[i][1])}
        for tag in g.get("tags", []):
            if isinstance(tag.get("i"), str):
                key = tag["i"].lower()
                if key not in idx:
                    raise VEError(f"tag \"{tag.get('text')}\" có i = \"{tag['i']}\" không hiểu.", "Với biểu đồ giá thật, i nhận số thứ tự điểm hoặc cuoi, dau, cao, thap.")
                tag["i"] = idx[key]
            if tag.get("text") == "auto":
                tag["text"] = money(ps[tag["i"]][1], vs)
    elif g.get("type") == "price":
        g["value"] = round(s["last"], 2)
        g.setdefault("prefix", "$" if vs == "usd" else "")
        if "change" not in g:
            g["change"] = f"{s['pct']:+.1f}% / {days or d.get('days') or ''} ngày".replace(" /  ngày", "").replace(".", ",")
            g["up"] = s["pct"] >= 0
    return [f"{coin_id(coin)} {s['from']}–{s['to']}: đầu {money(s['first'], vs)}, cuối {money(s['last'], vs)}, cao {money(s['high'], vs)}, thấp {money(s['low'], vs)} ({s['pct']:+.1f}%)"]


def run_cmd(root: Path, coin: str, end: str | None, days: int, csv_path: str | None) -> Path:
    d = from_csv(Path(csv_path), coin) if csv_path else fetch(coin, end, days)
    p = save(root, d)
    s = summary(d)
    info(f"✓ {len(d['prices'])} mốc giá {d['coin']} ({s['from']}–{s['to']}) → {p}")
    info(f"  đầu {money(s['first'])} · cuối {money(s['last'])} · cao {money(s['high'])} · thấp {money(s['low'])} · {s['pct']:+.1f}%")
    info("  Dùng trong khung đồ hoạ: \"data\": {\"coin\": \"" + d["coin"] + "\", \"ngay\": 7}. Đối chiếu số người nói với giá thật ở trên.")
    return p
