# market-brief

매일 한국 시간 오전 6시, 전일 미국 주식시장 주도 섹터 Top 5와 글로벌 주요 뉴스를
자동으로 정리해서 `reports/`에 커밋하는 GitHub Actions 자동화.

- **섹터 데이터**: SPDR 섹터 ETF 11종(XLK·XLF·XLE·XLV·XLI·XLY·XLP·XLU·XLB·XLRE·XLC)의
  전일 등락률을 [yfinance](https://github.com/ranaroussi/yfinance)로 조회(무료, API 키
  불필요) — 상위 5개를 표로 정리.
- **뉴스**: [NewsAPI.org](https://newsapi.org) 무료 티어로 미국 상위 헤드라인 조회 —
  API 키 필요(아래 설정 참고).
- 결과는 `reports/<YYYY-MM-DD>.md` + `reports/latest.md`(항상 최신본)로 커밋됨.

## 최초 설정 (한 번만)

1. **GitHub 저장소 생성** — 이 폴더를 그대로 push할 새 저장소를 만든다(공개/비공개
   무관, Actions는 둘 다 무료 티어에서 동작).
   ```
   cd ~/Desktop/project/market-brief
   git init
   git add .
   git commit -m "chore: market-brief 초기 설정"
   git remote add origin <새 저장소 URL>
   git push -u origin main
   ```
2. **NewsAPI 키 발급** — https://newsapi.org/register 에서 무료 가입 → API 키 발급
   (무료 티어: 하루 100 요청, 이 프로젝트는 하루 1회만 쓰므로 충분).
3. **저장소에 시크릿 등록** — GitHub 저장소 → Settings → Secrets and variables →
   Actions → New repository secret:
   - Name: `NEWS_API_KEY`
   - Value: 위에서 발급받은 키
4. **완료** — 이후 매일 06:00(KST)에 자동 실행된다. 바로 테스트하려면 저장소의
   Actions 탭 → "Daily Market Brief" → "Run workflow"(수동 실행 버튼)로 즉시 확인 가능.

## 로컬에서 직접 실행

```bash
pip install -r requirements.txt
export NEWS_API_KEY="<발급받은 키>"
python3 scripts/generate_report.py
```

## 커스터마이징

- 섹터 티커/한글명 매핑: `scripts/fetch_sectors.py`의 `SECTOR_ETFS`
- 뉴스 소스·개수: `scripts/fetch_news.py`의 `PARAMS`(NewsAPI top-headlines 파라미터,
  `country`를 다른 국가로 바꾸거나 `category` 조정 가능)
- 실행 시각: `.github/workflows/daily-report.yml`의 `cron`(UTC 기준 — KST는 UTC+9)
- 리포트 포맷: `scripts/generate_report.py`의 `build_markdown()`
