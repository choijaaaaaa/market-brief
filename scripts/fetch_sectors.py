# 전일 미국 주식시장 섹터별 등락률 집계. WHY: 개별 종목이 아니라 SPDR 섹터 ETF
# 11개(S&P 500 GICS 섹터 표준)의 일간 수익률로 "어느 섹터가 주도했는지"를 판단 —
# yfinance는 키 없이 무료로 쓸 수 있고 수치가 실측 데이터라 LLM 요약보다 신뢰도가 높다.
from __future__ import annotations

import json
import sys

import yfinance as yf

SECTOR_ETFS = {
    "XLK": "기술",
    "XLF": "금융",
    "XLE": "에너지",
    "XLV": "헬스케어",
    "XLI": "산업재",
    "XLY": "임의소비재",
    "XLP": "필수소비재",
    "XLU": "유틸리티",
    "XLB": "소재",
    "XLRE": "부동산",
    "XLC": "커뮤니케이션",
}


def fetch_sector_changes() -> list[dict]:
    """각 섹터 ETF의 최근 두 거래일 종가로 전일 등락률(%)을 구한다.
    WHY period="5d": 공휴일·주말이 껴도 최근 2개 거래일이 확실히 포함되도록
    여유를 둠(period="2d"는 직전 거래일이 공휴일이면 데이터가 하나만 남을 수 있음)."""
    tickers = " ".join(SECTOR_ETFS.keys())
    data = yf.download(tickers, period="5d", interval="1d", progress=False, group_by="ticker")

    results = []
    for ticker, name_ko in SECTOR_ETFS.items():
        closes = data[ticker]["Close"].dropna()
        if len(closes) < 2:
            continue
        prev_close, last_close = closes.iloc[-2], closes.iloc[-1]
        pct_change = (last_close - prev_close) / prev_close * 100
        results.append({
            "ticker": ticker,
            "name_ko": name_ko,
            "pct_change": round(float(pct_change), 2),
            "close": round(float(last_close), 2),
            "date": str(closes.index[-1].date()),
        })

    results.sort(key=lambda x: x["pct_change"], reverse=True)
    return results


if __name__ == "__main__":
    sectors = fetch_sector_changes()
    if not sectors:
        print("섹터 데이터를 가져오지 못했습니다", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(sectors, ensure_ascii=False, indent=2))
