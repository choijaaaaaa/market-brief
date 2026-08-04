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
# WHY US 상위헤드라인만 쓰는지: NewsAPI 무료 티어는 country 파라미터 없이는
# top-headlines 결과가 부실하다 — 미국 주요 통신사(AP·로이터 등)가 글로벌
# 대형 이슈를 대부분 다루므로 "글로벌 중요 뉴스"의 근사치로 충분하다고 판단.
TOP_HEADLINES_PARAMS = {"country": "us", "category": "general", "pageSize": 8}


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


def fetch_top_news(for_date: str | None = None) -> list[dict]:
    """for_date 없으면 지금 시점의 top-headlines(NewsAPI가 '오늘'만 제공).
    WHY for_date는 다른 엔드포인트(/v2/everything)를 쓰는지(2026-08-05, 과거
    날짜 백필용): top-headlines는 날짜 파라미터 자체가 없어 항상 "지금"만
    돌려준다 — 특정 과거 날짜의 뉴스가 필요하면 /v2/everything에 from/to를
    그 날짜로 좁혀서 인기순으로 받는다(무료 티어는 최근 1개월까지만 조회 가능)."""
    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
        raise RuntimeError("NEWS_API_KEY 환경변수가 없습니다")

    if for_date:
        params = {
            "q": "world OR global OR international",
            "from": for_date,
            "to": for_date,
            "language": "en",
            "sortBy": "popularity",
            "pageSize": 8,
        }
        resp = requests.get(EVERYTHING_URL, params={**params, "apiKey": api_key}, timeout=15)
    else:
        resp = requests.get(
            TOP_HEADLINES_URL, params={**TOP_HEADLINES_PARAMS, "apiKey": api_key}, timeout=15,
        )

    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "ok":
        raise RuntimeError(f"NewsAPI 에러: {payload}")
    return _articles_from_payload(payload)


if __name__ == "__main__":
    try:
        news = fetch_top_news()
    except Exception as e:
        print(f"뉴스 수집 실패: {e}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(news, ensure_ascii=False, indent=2))
