# 주요 미국 지수 + 11개 GICS 섹터 대표 종목의 전일 등락률.
# WHY 섹터(ETF)만으로는 부족한지(2026-08-05, "미국쪽 지수랑 주요 종목 어떤게
# 어떻게 되었는지... 팔란티어가 엄청 올랐고 반도체 주들이 꽤 올라서 나스닥
# 엄청 불장이였어" 지적): 섹터 등락률(예: "기술 +5%")만으로는 "그래서 나스닥이
# 어떻게 됐는지"·"어떤 개별 종목이 그 움직임을 이끌었는지"가 안 보인다.
# WHY 종목마다 소속 섹터를 붙이는지(2026-08-05, "각 종목이 어떤 섹터에
# 해당하는지, 그 섹터의 전체 등락 %가 어떻게되었는지도... 모든 섹터의
# 대표주자를 하나씩은 넣어줘 — 어떤 섹터가 주목을 받았는지가 궁금해서"):
# 처음엔 테크·반도체 위주 12종목이었는데, 그러면 애초에 그 섹터들만 보이고
# 나머지 8개 섹터(금융·에너지·헬스케어 등)는 아예 안 보였다 — 11개 섹터
# 전부 대표 종목을 최소 1개씩 넣고, fetch_sectors.SECTOR_ETFS와 같은 섹터
# 키(XLK 등)로 묶어서 "이 종목이 속한 섹터가 오늘 전체적으로 어땠는지"를
# 바로 대조할 수 있게 한다.
# WHY yfinance의 day_gainers 스크리너 대신 고정 워치리스트인지: 스크리너는
# 그날그날 시가총액 작은 종목이 단순 변동성만으로 상위에 뜨는 경우가 많아서
# (실측: 어느 날은 Wayfair +30%가 1위) "주요 종목"이라 부르기엔 부적절함 —
# 실제로 사람들이 관심 갖는 대형주 고정 목록을 쓰는 게 더 의미있는 신호.
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta

import yfinance as yf

from fetch_sectors import SECTOR_ETFS

INDICES = {
    "^GSPC": "S&P 500",
    "^IXIC": "나스닥종합",
    "^DJI": "다우존스",
}

# ticker -> (한글명, 소속 섹터 ETF 키). 섹터당 최소 1개, 화제성 높은
# 기술/반도체 섹터(XLK)만 예외적으로 여러 개(원 요청이 이 섹터 얘기였음).
WATCHLIST = {
    # XLK — 기술
    "NVDA": ("엔비디아", "XLK"),
    "AAPL": ("애플", "XLK"),
    "MSFT": ("마이크로소프트", "XLK"),
    "PLTR": ("팔란티어", "XLK"),
    "AMD": ("AMD", "XLK"),
    "AVGO": ("브로드컴", "XLK"),
    "TSM": ("TSMC", "XLK"),
    "INTC": ("인텔", "XLK"),
    # XLC — 커뮤니케이션
    "GOOGL": ("알파벳(구글)", "XLC"),
    "META": ("메타", "XLC"),
    # XLY — 임의소비재
    "AMZN": ("아마존", "XLY"),
    "TSLA": ("테슬라", "XLY"),
    # XLF — 금융
    "JPM": ("JP모건", "XLF"),
    # XLE — 에너지
    "XOM": ("엑슨모빌", "XLE"),
    # XLV — 헬스케어
    "UNH": ("유나이티드헬스", "XLV"),
    # XLI — 산업재
    "CAT": ("캐터필러", "XLI"),
    # XLP — 필수소비재
    "PG": ("P&G", "XLP"),
    # XLU — 유틸리티
    "NEE": ("넥스트에라에너지", "XLU"),
    # XLB — 소재
    "LIN": ("린데", "XLB"),
    # XLRE — 부동산
    "PLD": ("프로로지스", "XLRE"),
}


def _pct_changes(symbols_list: list[str], as_of: str | None = None) -> dict[str, dict]:
    """symbol -> {pct_change, close} — 여러 티커를 한 번에 받아 종목/지수
    양쪽에서 재사용."""
    tickers = " ".join(symbols_list)
    if as_of:
        start = (datetime.strptime(as_of, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d")
        data = yf.download(tickers, start=start, end=as_of, interval="1d", progress=False, group_by="ticker")
    else:
        data = yf.download(tickers, period="5d", interval="1d", progress=False, group_by="ticker")

    out = {}
    for symbol in symbols_list:
        closes = data[symbol]["Close"].dropna() if len(symbols_list) > 1 else data["Close"].dropna()
        if len(closes) < 2:
            continue
        prev_close, last_close = closes.iloc[-2], closes.iloc[-1]
        pct_change = (last_close - prev_close) / prev_close * 100
        out[symbol] = {"pct_change": round(float(pct_change), 2), "close": round(float(last_close), 2)}
    return out


def fetch_indices(as_of: str | None = None) -> list[dict]:
    changes = _pct_changes(list(INDICES.keys()), as_of=as_of)
    return [
        {"symbol": sym, "name_ko": name, **changes[sym]}
        for sym, name in INDICES.items() if sym in changes
    ]


def fetch_watchlist(as_of: str | None = None, sector_pct_by_etf: dict[str, float] | None = None) -> list[dict]:
    """섹터 등락률 큰 순으로 묶고, 같은 섹터 안에서는 종목 등락률 큰 순으로
    정렬 — "어떤 섹터가 주목받았는지"가 위에서부터 바로 보이게 한다.
    sector_pct_by_etf가 없으면(단독 호출 등) 종목 자체 등락률로만 정렬."""
    changes = _pct_changes(list(WATCHLIST.keys()), as_of=as_of)
    results = []
    for symbol, (name_ko, sector_etf) in WATCHLIST.items():
        if symbol not in changes:
            continue
        results.append({
            "symbol": symbol,
            "name_ko": name_ko,
            "sector_etf": sector_etf,
            "sector_name_ko": SECTOR_ETFS.get(sector_etf, sector_etf),
            "sector_pct": (sector_pct_by_etf or {}).get(sector_etf),
            **changes[symbol],
        })

    if sector_pct_by_etf:
        results.sort(key=lambda x: (x["sector_pct"] if x["sector_pct"] is not None else -999, x["pct_change"]), reverse=True)
    else:
        results.sort(key=lambda x: x["pct_change"], reverse=True)
    return results


if __name__ == "__main__":
    from fetch_sectors import fetch_sector_changes

    sectors = fetch_sector_changes()
    sector_pct = {s["ticker"]: s["pct_change"] for s in sectors}
    out = {"indices": fetch_indices(), "watchlist": fetch_watchlist(sector_pct_by_etf=sector_pct)}
    if not out["indices"] and not out["watchlist"]:
        print("지수·종목 데이터를 가져오지 못했습니다", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(out, ensure_ascii=False, indent=2))
