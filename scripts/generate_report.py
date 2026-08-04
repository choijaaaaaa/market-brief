# 지수·섹터·주요 종목·뉴스를 하루치 마크다운 리포트로 합친다.
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fetch_movers import fetch_indices, fetch_watchlist
from fetch_news import fetch_top_news
from fetch_sectors import fetch_sector_changes
from render_html import write_pages
from translate import translate_articles

KST = timezone(timedelta(hours=9))
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def _pct_table(rows: list[dict], name_key: str, sub_key: str) -> list[str]:
    lines = ["| 종목 | | 등락률 |", "|---|---|---|"]
    for r in rows:
        sign = "+" if r["pct_change"] >= 0 else ""
        lines.append(f"| {r[name_key]} | {r[sub_key]} | {sign}{r['pct_change']}% |")
    return lines


def build_markdown(
    indices: list[dict], sectors: list[dict], watchlist: list[dict], news: list[dict], report_date: str,
) -> str:
    lines = [f"# 마켓 브리핑 — {report_date}", ""]

    lines.append("## 주요 지수")
    lines.append("")
    if indices:
        lines += _pct_table(indices, "name_ko", "symbol")
    else:
        lines.append("_지수 데이터를 가져오지 못했습니다._")
    lines.append("")

    lines.append("## 전일 미국 주식시장 주도 섹터 Top 5")
    lines.append("")
    if sectors:
        lines.append("| 순위 | 섹터 | 티커 | 등락률 |")
        lines.append("|---|---|---|---|")
        for i, s in enumerate(sectors[:5], 1):
            sign = "+" if s["pct_change"] >= 0 else ""
            lines.append(f"| {i} | {s['name_ko']} | {s['ticker']} | {sign}{s['pct_change']}% |")
    else:
        lines.append("_섹터 데이터를 가져오지 못했습니다._")
    lines.append("")

    lines.append("## 주요 종목 (섹터별)")
    lines.append("")
    if watchlist:
        lines.append("| 종목 | 소속 섹터 | 종목 등락률 | 섹터 전체 등락률 |")
        lines.append("|---|---|---|---|")
        for w in watchlist:
            sign = "+" if w["pct_change"] >= 0 else ""
            sector_pct = w.get("sector_pct")
            sector_sign = "+" if (sector_pct is not None and sector_pct >= 0) else ""
            sector_cell = f"{sector_sign}{sector_pct}%" if sector_pct is not None else "—"
            lines.append(
                f"| {w['name_ko']}({w['symbol']}) | {w['sector_name_ko']} | "
                f"{sign}{w['pct_change']}% | {sector_cell} |"
            )
    else:
        lines.append("_종목 데이터를 가져오지 못했습니다._")
    lines.append("")

    lines.append("## 글로벌 주요 뉴스")
    lines.append("")
    if news:
        for n in news:
            source = f" ({n['source']})" if n["source"] else ""
            title = n.get("title_ko") or n["title"]
            lines.append(f"- [{title}]({n['url']}){source}")
    else:
        lines.append("_뉴스를 가져오지 못했습니다._")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    # WHY --date(2026-08-05, 백필용): 매일 스케줄 실행은 인자 없이 "지금" 기준
    # 그대로 쓰고, 과거 날짜 리포트를 나중에 채워 넣을 때만 이 옵션으로 특정
    # 날짜를 지정한다 — 뉴스는 그 날짜의 실제 기사(NewsAPI /v2/everything)를
    # 쓰고, 지수·섹터·종목도 그 날짜까지의 실측 종가로 계산한다(지어내지 않음).
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="YYYY-MM-DD, 생략하면 오늘(KST)")
    parser.add_argument(
        "--no-latest", action="store_true",
        help="latest.md를 갱신하지 않음 — 과거 날짜 백필 시 최신본을 덮어쓰지 않기 위함",
    )
    args = parser.parse_args()

    report_date = args.date or datetime.now(KST).strftime("%Y-%m-%d")

    try:
        indices = fetch_indices(as_of=args.date)
    except Exception as e:
        print(f"지수 수집 실패: {e}", file=sys.stderr)
        indices = []

    try:
        sectors = fetch_sector_changes(as_of=args.date)
    except Exception as e:
        print(f"섹터 수집 실패: {e}", file=sys.stderr)
        sectors = []

    try:
        # WHY sector_pct_by_etf를 넘기는지(2026-08-05, "각 종목이 어떤 섹터에
        # 해당하는지, 그 섹터의 전체 등락 %가 어떻게되었는지도... 어떤 섹터가
        # 주목을 받았는지가 궁금해서"): 위에서 이미 구한 섹터 등락률(전체 11개,
        # sectors는 top5로 자르기 전 원본)을 종목별로 매칭시켜서, 종목이
        # 소속 섹터 성과와 같이 정렬·표시되게 한다.
        sector_pct_by_etf = {s["ticker"]: s["pct_change"] for s in sectors}
        watchlist = fetch_watchlist(as_of=args.date, sector_pct_by_etf=sector_pct_by_etf)
    except Exception as e:
        print(f"주요 종목 수집 실패: {e}", file=sys.stderr)
        watchlist = []

    try:
        news = fetch_top_news(for_date=args.date)
        news = translate_articles(news)
    except Exception as e:
        print(f"뉴스 수집 실패: {e}", file=sys.stderr)
        news = []

    if not indices and not sectors and not watchlist and not news:
        # WHY 전부 실패면 워크플로우 자체를 실패 처리: 빈 리포트를 그대로
        # 커밋하면 "오늘은 업데이트가 없었나보다"로 조용히 넘어가기 쉽다 —
        # GitHub Actions가 실패로 표시돼야 사람이 원인(API 키 만료 등)을 확인함.
        print("지수·섹터·종목·뉴스 전부 수집 실패 — 리포트를 만들지 않습니다", file=sys.stderr)
        sys.exit(1)

    markdown = build_markdown(indices, sectors, watchlist, news, report_date)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / f"{report_date}.md").write_text(markdown, encoding="utf-8")
    if not args.no_latest:
        (REPORTS_DIR / "latest.md").write_text(markdown, encoding="utf-8")

    # WHY UI(GitHub Pages)도 마크다운과 같이 갱신하는지(2026-08-05, "ui 접근하면
    # 한눈에 볼수있게 잘해놔야지" 지적): 마크다운만 repo에 던져두면 파일을
    # 하나씩 열어봐야 해서 "한눈에 보기"가 안 됐다 — docs/index.html(오늘) +
    # docs/archive/(과거 회차 전체)를 매 실행마다 같이 만든다.
    write_pages(indices, sectors, watchlist, news, report_date, is_latest=not args.no_latest)

    print(f"리포트 생성 완료: reports/{report_date}.md, docs/archive/{report_date}.html")


if __name__ == "__main__":
    main()
