# 전일 글로벌 주요 뉴스 헤드라인 수집. WHY NewsAPI.org: 무료 티어로 하루 1회
# 실행에 충분하고(개발자 티어 100req/day) 키 발급이 간단함 — 실제 헤드라인이라
# LLM이 지어낼 위험이 없다.
from __future__ import annotations

import json
import os
import sys

import requests

NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
# WHY US 상위헤드라인만 쓰는지: NewsAPI 무료 티어는 country 파라미터 없이는
# top-headlines 결과가 부실하다 — 미국 주요 통신사(AP·로이터 등)가 글로벌
# 대형 이슈를 대부분 다루므로 "글로벌 중요 뉴스"의 근사치로 충분하다고 판단.
PARAMS = {"country": "us", "category": "general", "pageSize": 8}


def fetch_top_news() -> list[dict]:
    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
        raise RuntimeError("NEWS_API_KEY 환경변수가 없습니다")

    resp = requests.get(NEWS_API_URL, params={**PARAMS, "apiKey": api_key}, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "ok":
        raise RuntimeError(f"NewsAPI 에러: {payload}")

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


if __name__ == "__main__":
    try:
        news = fetch_top_news()
    except Exception as e:
        print(f"뉴스 수집 실패: {e}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(news, ensure_ascii=False, indent=2))
