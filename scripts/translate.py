# 영어 뉴스 제목을 한국어로 번역. WHY MyMemory: 키 발급 없이 무료로 쓸 수 있고
# (익명 기준 하루 5000자, 이 프로젝트는 헤드라인 8개/일이라 충분) 별도 계정·과금
# 없이 바로 동작 — 진짜 "요약"은 아니고 기계번역이라 다소 직역투일 수 있지만,
# 영어 원문 그대로보다는 이해하기 훨씬 쉽다.
from __future__ import annotations

import sys

import requests

MYMEMORY_URL = "https://api.mymemory.translated.net/get"


def translate_to_korean(text: str) -> str:
    """실패해도 예외를 던지지 않고 원문을 그대로 돌려준다 — 번역 실패로
    리포트 전체가 깨지면 안 되므로(뉴스 하나 번역 실패는 그 줄만 영어로
    남는 정도의 저하로 처리)."""
    try:
        resp = requests.get(
            MYMEMORY_URL, params={"q": text, "langpair": "en|ko"}, timeout=10,
        )
        resp.raise_for_status()
        payload = resp.json()
        translated = payload.get("responseData", {}).get("translatedText", "")
        # WHY 빈 문자열/원문과 동일한 경우 원문 폴백: MyMemory가 가끔 번역
        # 실패 시 빈 값이나 에러 메시지를 200으로 반환하는 경우가 있음.
        return translated if translated else text
    except Exception as e:
        print(f"번역 실패({text[:30]}...): {e}", file=sys.stderr)
        return text


def translate_articles(articles: list[dict]) -> list[dict]:
    """각 기사의 title을 한국어로 번역해서 title_ko 필드를 추가 — 원문
    title은 그대로 남겨서 링크 텍스트/디버깅에 계속 쓸 수 있게 한다."""
    for a in articles:
        a["title_ko"] = translate_to_korean(a["title"])
    return articles
