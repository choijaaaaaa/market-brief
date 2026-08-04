# reports/*.md와 별개로 GitHub Pages에서 바로 렌더링되는 정적 HTML 대시보드를
# 만든다. WHY: 마크다운 파일만 repo에 던져두면 GitHub 화면에서 파일을 하나씩
# 열어봐야 해서 "한눈에 보기"가 안 된다 — docs/index.html(오늘) +
# docs/archive/<date>.html(과거 회차) + docs/archive/index.html(전체 목록)을
# 매일 같이 갱신해서 브라우저로 바로 훑어볼 수 있게 한다.
from __future__ import annotations

from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
ARCHIVE_DIR = DOCS_DIR / "archive"

# WHY 스타일을 <style> 인라인으로 박아두는지: GitHub Pages는 정적 호스팅이라
# 외부 CDN 의존을 최소화하는 게 안정적이다 — 폰트도 시스템 폰트 스택만 씀.
_STYLE = """
:root {
  --bg: #0f1115; --panel: #171a21; --border: #262b36;
  --ink: #e8eaed; --ink-soft: #9aa1ac;
  --up: #34d399; --down: #f87171; --accent: #60a5fa;
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 24px 16px 60px; background: var(--bg); color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Apple SD Gothic Neo",
    "Malgun Gothic", sans-serif;
}
main { max-width: 720px; margin: 0 auto; }
header { margin-bottom: 24px; }
header h1 { font-size: 22px; margin: 0 0 4px; }
header .nav { font-size: 13px; color: var(--ink-soft); }
header .nav a { color: var(--accent); text-decoration: none; }
header .nav a:hover { text-decoration: underline; }
section { background: var(--panel); border: 1px solid var(--border); border-radius: 12px;
  padding: 18px 20px; margin-bottom: 16px; }
section h2 { font-size: 15px; margin: 0 0 14px; color: var(--ink-soft);
  text-transform: uppercase; letter-spacing: 0.04em; }
table { width: 100%; border-collapse: collapse; font-size: 15px; }
th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid var(--border); }
th { color: var(--ink-soft); font-weight: 500; font-size: 12px; }
tr:last-child td { border-bottom: none; }
.rank { color: var(--ink-soft); width: 28px; }
.ticker { color: var(--ink-soft); font-size: 13px; }
.pct { text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }
.pct.up { color: var(--up); } .pct.down { color: var(--down); }
.news-list { list-style: none; margin: 0; padding: 0; }
.news-list li { padding: 10px 0; border-bottom: 1px solid var(--border); }
.news-list li:last-child { border-bottom: none; }
.news-list a { color: var(--ink); text-decoration: none; font-size: 15px; line-height: 1.4; }
.news-list a:hover { color: var(--accent); }
.news-en { display: block; color: var(--ink-soft); font-size: 12px; margin-top: 2px; }
.news-source { display: block; color: var(--ink-soft); font-size: 12px; margin-top: 3px; }
.empty { color: var(--ink-soft); font-size: 14px; }
footer { text-align: center; color: var(--ink-soft); font-size: 12px; margin-top: 24px; }
footer a { color: var(--accent); }
.archive-list { list-style: none; margin: 0; padding: 0; }
.archive-list li a { display: block; padding: 12px 6px; color: var(--ink);
  text-decoration: none; border-bottom: 1px solid var(--border); font-size: 15px; }
.archive-list li:last-child a { border-bottom: none; }
.archive-list li a:hover { color: var(--accent); }
"""


def _pct_rows(rows: list[dict], name_key: str, sub_key: str, empty_msg: str, limit: int | None = None) -> str:
    if not rows:
        return f'<p class="empty">{empty_msg}</p>'
    shown = rows[:limit] if limit else rows
    trs = []
    for r in shown:
        cls = "up" if r["pct_change"] >= 0 else "down"
        sign = "+" if r["pct_change"] >= 0 else ""
        trs.append(
            f'<tr><td>{r[name_key]}</td><td class="ticker">{r[sub_key]}</td>'
            f'<td class="pct {cls}">{sign}{r["pct_change"]}%</td></tr>'
        )
    return (
        '<table><thead><tr><th></th><th></th><th style="text-align:right">등락률</th>'
        f"</tr></thead><tbody>{''.join(trs)}</tbody></table>"
    )


def _news_items(news: list[dict]) -> str:
    if not news:
        return '<p class="empty">뉴스를 가져오지 못했습니다.</p>'
    items = []
    for n in news:
        source = f'<span class="news-source">{n["source"]}</span>' if n["source"] else ""
        title_ko = n.get("title_ko") or n["title"]
        # WHY 영어 원문도 작게 같이 보여주는지: 기계번역이 가끔 어색할 수
        # 있어서(2026-08-05, "축약해서 브리핑을 해줘야 의미가 있지" 반영 —
        # MyMemory 무료 번역), 원문을 작은 글씨로 남겨 대조 가능하게 한다.
        items.append(
            f'<li><a href="{n["url"]}" target="_blank" rel="noopener">{title_ko}</a>'
            f'<span class="news-en">{n["title"]}</span>{source}</li>'
        )
    return f'<ul class="news-list">{"".join(items)}</ul>'


def render_page(
    indices: list[dict], sectors: list[dict], watchlist: list[dict], news: list[dict],
    report_date: str, nav_html: str,
) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>마켓 브리핑 — {report_date}</title>
<style>{_STYLE}</style>
</head>
<body>
<main>
<header>
  <h1>📊 마켓 브리핑 — {report_date}</h1>
  <div class="nav">{nav_html}</div>
</header>
<section>
  <h2>주요 지수</h2>
  {_pct_rows(indices, "name_ko", "symbol", "지수 데이터를 가져오지 못했습니다.")}
</section>
<section>
  <h2>전일 미국 주식시장 주도 섹터 Top 5</h2>
  {_pct_rows(sectors, "name_ko", "ticker", "섹터 데이터를 가져오지 못했습니다.", limit=5)}
</section>
<section>
  <h2>주요 종목</h2>
  {_pct_rows(watchlist, "name_ko", "symbol", "종목 데이터를 가져오지 못했습니다.")}
</section>
<section>
  <h2>글로벌 주요 뉴스</h2>
  {_news_items(news)}
</section>
<footer>매일 06:00(KST) 자동 갱신 · <a href="https://github.com/choijaaaaaa/market-brief">GitHub</a></footer>
</main>
</body>
</html>
"""


def render_archive_index(dates: list[str]) -> str:
    items = "".join(f'<li><a href="{d}.html">{d}</a></li>' for d in dates)
    body = f'<ul class="archive-list">{items}</ul>' if dates else '<p class="empty">아직 리포트가 없습니다.</p>'
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>마켓 브리핑 — 지난 리포트</title>
<style>{_STYLE}</style>
</head>
<body>
<main>
<header>
  <h1>📚 지난 리포트</h1>
  <div class="nav"><a href="../">← 오늘 리포트로</a></div>
</header>
<section>{body}</section>
</main>
</body>
</html>
"""


def write_pages(
    indices: list[dict], sectors: list[dict], watchlist: list[dict], news: list[dict],
    report_date: str, *, is_latest: bool,
) -> None:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    archive_page = render_page(indices, sectors, watchlist, news, report_date, '<a href="../">← 오늘 리포트로</a>')
    (ARCHIVE_DIR / f"{report_date}.html").write_text(archive_page, encoding="utf-8")

    # WHY 파일명(날짜) 기준으로 다시 스캔하는지: 매 실행마다 그 시점까지 쌓인
    # 모든 회차를 정확히 반영해야 해서(과거 백필로 중간에 새 날짜가 끼어들
    # 수도 있음) — 이번에 만든 페이지만 append하지 않고 항상 전체를 다시 훑는다.
    dates = sorted(p.stem for p in ARCHIVE_DIR.glob("*.html") if p.stem != "index")
    (ARCHIVE_DIR / "index.html").write_text(render_archive_index(list(reversed(dates))), encoding="utf-8")

    if is_latest:
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        latest_page = render_page(indices, sectors, watchlist, news, report_date, '<a href="archive/">지난 리포트 보기 →</a>')
        (DOCS_DIR / "index.html").write_text(latest_page, encoding="utf-8")
