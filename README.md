# port-interest-preprocessor

포트폴리오 관심 데이터 전처리를 담당하는 Python 마이크로서비스 루트다. 수집 계층에서 적재한 raw 데이터를 읽어 뉴스, 증권사 리포트, 가격, 시장 폭, 매크로, 원자재, 해외지수, 투자자 수급, 프로그램 매매, 공매도, total feature 계열 테이블로 가공하는 스크립트들이 모여 있다.

이 문서는 현재 로컬 파일 구조와 import/entrypoint 확인 결과를 기준으로 작성했다. 실제 전처리 실행, 외부 API 호출, DB DDL/DML, 크롤링, 주문 실행은 수행하지 않았다.

## 현재 구조

현재 루트는 패키지 디렉터리보다 독립 실행형 Python 스크립트 중심이다.

- orchestration 후보
  - `pre_daily.py`: 뉴스, 증권사, 원자재, 해외지수, 매크로, 가격, 시장 폭, 수급, 프로그램, 공매도, total market/stock feature 전처리를 순서대로 호출하는 일일 전처리 후보.
- 뉴스 전처리 후보
  - `pre_news_analysis.py`: `interest_news_raw`와 종목 alias를 기반으로 뉴스-종목 매핑, 감성 점수, 키워드 등 `pre_news_analysis` 후보 데이터를 생성.
  - `pre_news_event_detection.py`: 이벤트 master/keyword/sector weight를 사용해 뉴스 이벤트 후보를 탐지하고 `pre_news_event` 계열로 적재.
  - `pre_news_daily_aggregator.py`: 뉴스 분석 결과를 종목/일자 단위 `pre_news_daily_feature`로 집계.
- 증권사 리포트 전처리 후보
  - `pre_agency_analysis.py`: 증권사 raw 리포트의 투자의견/목표가 정보를 점수화해 `pre_agency_analysis` 후보 데이터를 생성.
  - `pre_agency_daily_aggregator.py`: 증권사 리포트 분석 결과를 종목/일자 단위 `pre_agency_daily_feature`로 집계.
- 가격/시장 전처리 후보
  - `pre_price.py`: 가격 raw 데이터를 종목/일자 단위 가격 feature로 가공.
  - `pre_marketbreadth.py`: 시장 폭 raw 데이터를 일자 단위 market breadth feature로 가공.
- 매크로/원자재/해외지수 전처리 후보
  - `pre_macroeconomic.py`: `interest_macroeconomic_raw` 기반 VIX, 금리, 환율 등 매크로 daily feature 생성.
  - `pre_commodity.py`: `interest_commodity_raw` 기반 WTI, Brent, gold, silver, copper, natural gas 등 원자재 daily feature 생성.
  - `pre_foreignindex.py`: `interest_foreignindex_raw` 기반 SP500, NASDAQ, Dow Jones, Nikkei, Shanghai, Hang Seng 등 해외지수 daily feature 생성.
- 수급/거래 구조 전처리 후보
  - `pre_investorflow.py`: 투자자 수급 raw와 가격 raw를 결합해 외국인/기관 순매수, 보유율, flow momentum 등 종목/일자 feature 생성.
  - `pre_program.py`: 프로그램 매매 raw를 일자 단위 feature로 가공.
  - `pre_shortsell.py`: 공매도 raw를 종목/일자 단위 feature로 가공.
- total feature 전처리 후보
  - `pre_total_stock_daily_feature.py`: 가격, 수급, 공매도, 뉴스, 증권사 feature를 결합해 종목/일자 total stock feature 생성.
  - `pre_total_market_daily_feature.py`: 시장 폭, 해외지수, 매크로, 원자재, 프로그램, 시장 수급을 결합해 일자 단위 total market feature 생성. 휴일 판정 helper를 참조한다.
- 보조 후보
  - `interest_get_holidays.py`: 외부 holiday API를 조회하는 휴일 helper 후보. 외부 API 호출이 있으므로 문서화 작업 중 실행하지 않는다.
- 로컬 산출물 후보
  - `__pycache__/`, `*.pyc`, 테스트/임시 스크립트는 운영 소스로 단정하지 않고 필요 시 정리 대상으로 취급한다.

## 주요 기능

- raw 수집 테이블을 읽어 `pre_*_daily_feature` 계열 feature 테이블로 변환
- 뉴스 제목 기반 종목 매핑, 감성/키워드 점수화, 이벤트 탐지
- 증권사 리포트 투자의견/목표가 기반 feature 생성
- 가격 momentum, 시장 폭, 매크로 압력, 원자재 압력, 해외지수 수익률 feature 생성
- 투자자 수급, 프로그램 매매, 공매도 기반 수급/거래 구조 feature 생성
- 종목 단위 total stock feature와 시장 단위 total market feature 생성
- `pre_daily.py`를 통한 일일 전처리 orchestration 후보 제공

## 실행 방법

각 스크립트는 독립 실행형 `run()` 또는 `main()` entrypoint를 가진 파일이 많다. 다만 실행 시 DB 연결, upsert, 외부 holiday API 호출이 발생할 수 있으므로 운영 환경에서만 의도적으로 실행해야 한다.

예시 형식:

```powershell
python pre_daily.py
```

문서화/분석 작업 중에는 위 명령을 실행하지 않는다. 개별 전처리도 DB DDL/DML 또는 대량 upsert를 수행할 수 있으므로 대상 테이블, 입력 raw 테이블, unique key/upsert 정책, 처리 일자 범위를 확인한 뒤 실행해야 한다.

## 설정 방법

현재 스크립트들은 DB 접속정보, 처리 버전, 외부 holiday API URL 또는 로컬 환경 설정을 사용할 수 있다.

민감정보는 코드, 문서, 로그, 예시 출력에 기록하지 않는다. 필요한 값은 환경변수 또는 local config로 분리하고 문서에는 `[REDACTED]`로 마스킹한다.

주요 설정 유형:

- PostgreSQL host, port, database, user, password
- processor version 또는 feature 산출 버전
- raw/pre feature 테이블명과 unique key
- 전처리 대상 trade date 또는 business date
- 외부 holiday API 접근 정보

## 외부 의존성

현재 파일에서 확인되는 주요 의존성 후보는 다음과 같다.

- Python
- `psycopg2`
- `psycopg2.extras`
- `requests`
- PostgreSQL
- 외부 holiday API

외부 API 호출, DB DDL/DML은 운영 영향이 있으므로 분석 또는 문서 작업 중에는 실행하지 않는다.

## 안전 제약

- 실제 전처리 실행 금지
- 외부 API 호출 금지
- DB DDL/DML 직접 실행 금지
- 크롤링 실행 금지
- 주문 제출 또는 주문 실행 금지
- 민감정보 값 출력 또는 문서 기록 금지
- 민감정보가 필요하면 `[REDACTED]`로 마스킹
- test/debug/cache/output dump 파일은 운영 소스로 단정하지 않고 후보 또는 로컬 산출물로만 표현

## 검증

문서만 수정한 경우에는 변경 범위만 확인한다.

```powershell
git status --short
git diff --stat
```

코드 수정 시에는 외부 요청, 전처리 실행, 모델 실행, DB 쓰기, 주문 실행이 포함되지 않는 검증만 선택한다. 실행 위험이 있으면 완료 보고에 검증 한계를 남긴다.
