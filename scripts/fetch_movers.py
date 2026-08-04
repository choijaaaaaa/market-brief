# 주요 미국 지수 + 시가총액 상위·화제성 높은 개별 종목의 전일 등락률.
# WHY 섹터(ETF)만으로는 부족한지(2026-08-05, "미국쪽 지수랑 주요 종목 어떤게
# 어떻게 되었는지... 예를들어 팔란티어가 엄청 올랐고 반도체 주들이 꽤 올라서
# 나스닥 엄청 불장이였어" 지적): 섹터 등락률(예: "기술 +5%")만으로는 "그래서
# 나스닥이 어떻게 됐는지"·"어떤 개별 종목이 그 움직임을 이끌었는지"가 안
# 보인다 — 지수 자체와 시장에서 자주 언급되는 대형주를 같이 보여준다.
# WHY yfinance의 day_gainers 스크리너 대신 고정 워치리스트인지: 스크리너는
# 그날그날 시가총액 작은 종목이 단순 변동성만으로 상위에 뜨는 경우가 많아서
# (실측: 어느 날은 Wayfair +30%가 1위) "주요 종목"이라 부르기엔 부적절함 —
# 실제로 사람들이 관심 갖는 대형주 고정 목록을 쓰는 게 더 의미있는 신호.
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta

import yfinance as yf

INDICES = {
    "^GSPC": "S&P 500",
    "^IXIC": "나스닥종합",
    "^DJI": "다우존스",
}

WATCHLIST = {
    "AAPL": "애플",
    "MSFT": "마이크로소프트",
    "GOOGL": "알파벳(구글)",
    "AMZN": "아마존",
    "META": "메타",
    "NVDA": "엔비디아",
    "TSLA": "테슬라",
    "PLTR": "팔란티어",
    "AMD": "AMD",
    "AVGO": "브로드컴",
    "TSM": "TSMC",
    "INTC": "인텔",
}


def _pct_changes(tickers: dict[str, str], as_of: str | None = None) -> list[dict]:
    symbols = " ".join(tickers.keys())
    if as_of:
        start = (datetime.strptime(as_of, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d")
        data = yf.download(symbols, start=start, end=as_of, interval="1d", progress=False, group_by="ticker")
    else:
        data = yf.download(symbols, period="5d", interval="1d", progress=False, group_by="ticker")

    results = []
    for symbol, name_ko in tickers.items():
        closes = data[symbol]["Close"].dropna() if len(tickers) > 1 else data["Close"].dropna()
        if len(closes) < 2:
            continue
        prev_close, last_close = closes.iloc[-2], closes.iloc[-1]
        pct_change = (last_close - prev_close) / prev_close * 100
        results.append({
            "symbol": symbol,
            "name_ko": name_ko,
            "pct_change": round(float(pct_change), 2),
            "close": round(float(last_close), 2),
        })
    return results


def fetch_indices(as_of: str | None = None) -> list[dict]:
    return _pct_changes(INDICES, as_of=as_of)


def fetch_watchlist(as_of: str | None = None) -> list[dict]:
    """등락률 큰 순서(하락 포함, 절댓값 아님)로 정렬 — 급등한 종목이 맨 위에
    오게 해서 "무엇이 시장을 이끌었는지"가 바로 보이게 한다."""
    results = _pct_changes(WATCHLIST, as_of=as_of)
    results.sort(key=lambda x: x["pct_change"], reverse=True)
    return results


if __name__ == "__main__":
    out = {"indices": fetch_indices(), "watchlist": fetch_watchlist()}
    if not out["indices"] and not out["watchlist"]:
        print("지수·종목 데이터를 가져오지 못했습니다", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(out, ensure_ascii=False, indent=2))
