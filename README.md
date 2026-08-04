# market-brief

매일 한국 시간 오전 6시, 미국 주요 지수·섹터 Top 5·주요 종목(빅테크+반도체
워치리스트) 등락률과 글로벌 주요 뉴스(한국어 번역 포함)를 자동으로 정리해서
커밋하는 GitHub Actions 자동화. **GitHub Pages로 웹에서 바로 한눈에 볼 수 있음**
— `https://<계정>.github.io/market-brief/`.

- **주요 지수**: S&P 500·나스닥종합·다우존스 전일 등락률.
- **섹터 데이터**: SPDR 섹터 ETF 11종(XLK·XLF·XLE·XLV·XLI·XLY·XLP·XLU·XLB·XLRE·XLC)의
  전일 등락률 상위 5개.
- **주요 종목**: 빅테크(AAPL·MSFT·GOOGL·AMZN·META·NVDA·TSLA) + 반도체·화제성
  종목(PLTR·AMD·AVGO·TSM·INTC) 워치리스트, 등락률 큰 순.
  (위 세 가지 전부 [yfinance](https://github.com/ranaroussi/yfinance)로 조회 — 무료,
  API 키 불필요)
- **뉴스**: [NewsAPI.org](https://newsapi.org) 무료 티어로 business+general 헤드라인을
  섞어서 조회한 뒤 [MyMemory](https://mymemory.translated.net)로 한국어 번역까지 —
  둘 다 API 키 필요(아래 설정 참고, MyMemory는 키 발급 자체가 없이 무료).
- 결과는 두 형태로 커밋됨:
  - `reports/<YYYY-MM-DD>.md` + `reports/latest.md` — git으로 원본 데이터 확인용
  - `docs/index.html`(오늘) + `docs/archive/<날짜>.html` + `docs/archive/index.html`
    (지난 리포트 목록) — GitHub Pages로 렌더링되는 실제 웹 페이지

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
4. **GitHub Pages 활성화** — 저장소 → Settings → Pages → "Build and deployment" →
   Source: **Deploy from a branch**, Branch: **main** / **`/docs`** 선택 → Save.
   저장 후 잠깐 기다리면 `https://<계정>.github.io/market-brief/`에서 바로 보임.
5. **완료** — 이후 매일 06:00(KST)에 자동 실행된다. 바로 테스트하려면 저장소의
   Actions 탭 → "Daily Market Brief" → "Run workflow"(수동 실행 버튼)로 즉시 확인 가능.

## 로컬에서 직접 실행

```bash
pip install -r requirements.txt
export NEWS_API_KEY="<발급받은 키>"
python3 scripts/generate_report.py
```

## 커스터마이징

- 섹터 티커/한글명 매핑: `scripts/fetch_sectors.py`의 `SECTOR_ETFS`
- 지수·주요 종목 워치리스트: `scripts/fetch_movers.py`의 `INDICES`/`WATCHLIST`
- 뉴스 소스·개수: `scripts/fetch_news.py`의 `TOP_HEADLINES_PARAMS_BY_CATEGORY`
  (NewsAPI top-headlines 파라미터, `country`를 다른 국가로 바꾸거나 `category` 조정 가능)
- 뉴스 번역: `scripts/translate.py`(MyMemory 무료 API, 다른 번역 서비스로 교체 가능)
- 실행 시각: `.github/workflows/daily-report.yml`의 `cron`(UTC 기준 — KST는 UTC+9)
- 마크다운 포맷: `scripts/generate_report.py`의 `build_markdown()`
- 웹 페이지(HTML) 디자인·레이아웃: `scripts/render_html.py`
