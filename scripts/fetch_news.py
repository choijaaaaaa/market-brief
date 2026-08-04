# 전일 글로벌 주요 뉴스 헤드라인 수집. WHY NewsAPI.org: 무료 티어로 하루 1회
# 실행에 충분하고(개발자 티어 100req/day) 키 발급이 간단함 — 실제 헤드라인이라
# LLM이 지어낼 위험이 없다.
from __future__ import annotations

import json
import os
import sys

import requests

TOP_HEADLINES_URL = "https://newsapi.org/v2/top-headlines"
EVERYTHING_URL = "https://newsapi.org/v2/everything"
# WHY business+general 둘 다 부르는지(2026-08-05, "오늘자 실시간으로 시황
# 확인하는데 뉴스가 부족하지 않을까" 지적): category=general만 쓰니 실제로
# 정치·이민·산불·전염병 같은 시황과 무관한 헤드라인 위주로 나왔다(보잉 인증
# 정도만 시장 관련) — business는 실적·연준·무역 등 섹터 등락과 바로 붙는
# 뉴스를 주지만, 그것만 쓰면 시장에 큰 영향을 주는 지정학 이슈(예: 이란
# 정세)처럼 겉보기엔 일반 카테고리인 뉴스를 놓친다. 두 카테고리를 각각
# 불러서 합친다 — 무료 티어(하루 100요청)로 하루 1회 실행에 호출 2번은
# 충분히 여유 있음.
TOP_HEADLINES_PARAMS_BY_CATEGORY = {
    "business": {"country": "us", "category": "business", "pageSize": 5},
    "general": {"country": "us", "category": "general", "pageSize": 6},
}
MAX_ARTICLES = 8


def _articles_from_payload(payload: dict) -> list[dict]:
    articles = []
    for a in payload.get("articles", []):
        if not a.get("title") or a["title"] == "[Removed]":
            continue
        articles.append({
            "title": a["title"],
            "source": a.get("source", {}).get("name", ""),
            "url": a.get("url", ""),
            "published_at": a.get("publishedAt", ""),
        })
    return articles


def _fetch_top_headlines(category: str, api_key: str) -> list[dict]:
    params = TOP_HEADLINES_PARAMS_BY_CATEGORY[category]
    resp = requests.get(TOP_HEADLINES_URL, params={**params, "apiKey": api_key}, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "ok":
        raise RuntimeError(f"NewsAPI 에러({category}): {payload}")
    return _articles_from_payload(payload)


def fetch_top_news(for_date: str | None = None) -> list[dict]:
    """for_date 없으면 지금 시점의 top-headlines(business 5개 + general
    4개, business 먼저) — NewsAPI가 top-headlines는 항상 '지금'만 제공.
    WHY for_date는 다른 엔드포인트(/v2/everything)를 쓰는지(2026-08-05, 과거
    날짜 백필용): top-headlines는 날짜 파라미터 자체가 없어 항상 "지금"만
    돌려준다 — 특정 과거 날짜의 뉴스가 필요하면 /v2/everything에 from/to를
    그 날짜로 좁혀서 인기순으로 받는다(무료 티어는 최근 1개월까지만 조회 가능,
    ⚠️ 로컬호스트 밖에서는 articles가 항상 빈 배열로 옴 — README 참고)."""
    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
        raise RuntimeError("NEWS_API_KEY 환경변수가 없습니다")

    if for_date:
        params = {
            "q": "business OR market OR economy OR world OR global",
            "from": for_date,
            "to": for_date,
            "language": "en",
            "sortBy": "popularity",
            "pageSize": 8,
        }
        resp = requests.get(EVERYTHING_URL, params={**params, "apiKey": api_key}, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("status") != "ok":
            raise RuntimeError(f"NewsAPI 에러: {payload}")
        return _articles_from_payload(payload)

    # WHY business를 general보다 많이 요청해도 실제로는 적게 오는 경우가
    # 흔함(2026-08-05 실측: business pageSize=5 요청해도 2~3개만 옴 — 그
    # 시점에 NewsAPI가 US business로 태그한 기사 자체가 적은 것) — general
    # pageSize를 넉넉히 잡아서 합친 뒤 8개로 자르면, business가 부족한
    # 날에도 총 개수가 안정적으로 채워진다.
    articles = _fetch_top_headlines("business", api_key) + _fetch_top_headlines("general", api_key)
    # WHY url 기준 dedupe: 두 카테고리 결과가 가끔 같은 기사를 동시에 포함함
    # (예: 대형 경제 이슈가 general에도 걸리는 경우) — 제목이 아니라 url로
    # 판정하는 이유는 같은 기사도 매체마다 제목을 살짝 다르게 걸 수 있어서.
    seen_urls = set()
    deduped = []
    for a in articles:
        if a["url"] in seen_urls:
            continue
        seen_urls.add(a["url"])
        deduped.append(a)
    return deduped[:MAX_ARTICLES]


if __name__ == "__main__":
    try:
        news = fetch_top_news()
    except Exception as e:
        print(f"뉴스 수집 실패: {e}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(news, ensure_ascii=False, indent=2))
