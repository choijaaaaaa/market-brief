# 섹터 데이터 + 뉴스 헤드라인을 하루치 마크다운 리포트로 합친다.
from __future__ import annotations

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fetch_news import fetch_top_news
from fetch_sectors import fetch_sector_changes

KST = timezone(timedelta(hours=9))
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def build_markdown(sectors: list[dict], news: list[dict], report_date: str) -> str:
    lines = [f"# 마켓 브리핑 — {report_date}", ""]

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

    lines.append("## 글로벌 주요 뉴스")
    lines.append("")
    if news:
        for n in news:
            source = f" ({n['source']})" if n["source"] else ""
            lines.append(f"- [{n['title']}]({n['url']}){source}")
    else:
        lines.append("_뉴스를 가져오지 못했습니다._")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    now_kst = datetime.now(KST)
    report_date = now_kst.strftime("%Y-%m-%d")

    try:
        sectors = fetch_sector_changes()
    except Exception as e:
        print(f"섹터 수집 실패: {e}", file=sys.stderr)
        sectors = []

    try:
        news = fetch_top_news()
    except Exception as e:
        print(f"뉴스 수집 실패: {e}", file=sys.stderr)
        news = []

    if not sectors and not news:
        # WHY 둘 다 실패면 워크플로우 자체를 실패 처리: 빈 리포트를 그대로
        # 커밋하면 "오늘은 업데이트가 없었나보다"로 조용히 넘어가기 쉽다 —
        # GitHub Actions가 실패로 표시돼야 사람이 원인(API 키 만료 등)을 확인함.
        print("섹터·뉴스 둘 다 수집 실패 — 리포트를 만들지 않습니다", file=sys.stderr)
        sys.exit(1)

    markdown = build_markdown(sectors, news, report_date)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / f"{report_date}.md").write_text(markdown, encoding="utf-8")
    (REPORTS_DIR / "latest.md").write_text(markdown, encoding="utf-8")
    print(f"리포트 생성 완료: reports/{report_date}.md")


if __name__ == "__main__":
    main()
