# port-interest-preprocessor

## 2026-05-28 문서화/주석 정리

이 저장소는 포트폴리오 관심 데이터 전처리를 담당하는 Python 마이크로서비스 루트다. 현재 구조는 패키지 디렉터리보다 독립 실행형 `pre_*.py` 스크립트 중심이며, `pre_daily.py`가 주요 전처리 후보 스크립트의 `run()` entrypoint를 순서대로 호출하는 orchestration 후보 역할을 한다.

이번 정리에서 전체 파일 역할과 운영 주의사항은 `docs/source-file-catalog.md`에 별도로 정리했다. 각 Python 스크립트에는 기능 로직 변경 없이 모듈 상단 docstring을 추가해 DB 접근, 외부 API 호출 가능성, 생성/갱신 대상 feature 테이블을 빠르게 확인할 수 있도록 했다.

실행 시 대부분의 스크립트는 PostgreSQL raw/pre feature 테이블을 읽거나 upsert한다. `interest_get_holidays.py`는 Nager.Date public holiday API를 호출할 수 있으므로 문서화, 정적 분석, 컴파일 검증 중에는 실제 전처리 실행과 외부 API 호출을 하지 않는다.

주요 설정은 `db_config.py`에서 환경변수로 주입한다. 민감정보 값은 문서, 로그, 예시 출력에 기록하지 않고 환경변수 또는 로컬 설정 파일에서 주입한다.

- `INTEREST_DB_HOST`: PostgreSQL host
- `INTEREST_DB_PORT`: PostgreSQL port
- `INTEREST_DB_NAME`: PostgreSQL database name
- `INTEREST_DB_USER`: PostgreSQL user
- `INTEREST_DB_PASSWORD`: PostgreSQL password, 필수 값이며 실제 값은 기록하지 않는다.

기능 변경 없음: 이번 작업은 파일 카탈로그 작성, README/CHANGELOG/worklog 갱신, Python 파일 설명 주석 추가만 포함한다.

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
- DB connection environment variables
  - `INTEREST_DB_HOST`: PostgreSQL host. Default: `localhost`
  - `INTEREST_DB_PORT`: PostgreSQL port. Default: `5433`
  - `INTEREST_DB_NAME`: PostgreSQL database name. Default: `portfolio`
  - `PORTFOLIO_DB_NAME`: Portfolio PostgreSQL database name을 별도로 사용하는 환경에서는 Default를 `portfolio`로 맞춘다.
  - `INTEREST_DB_USER`: PostgreSQL user. Default: `postgres`
  - `INTEREST_DB_PASSWORD`: PostgreSQL password. Required. Example placeholder: `[REDACTED]`
- processor version 또는 feature 산출 버전
- raw/pre feature 테이블명과 unique key
- 전처리 대상 trade date 또는 business date
- 외부 holiday API 접근 정보

## 데이터베이스 구조

로컬 PostgreSQL 기본 DB name은 `portfolio`다. 기존 `interest_crawler` DB 기준으로 작성된 전처리 연결 설정은 `portfolio` DB를 기본값으로 사용하도록 정리한다.

AWS Migration 준비 관점에서는 단일 PostgreSQL DB `portfolio` 안에 도메인별 schema를 두는 schema-per-domain 구조를 사용한다. 현재 도메인 schema는 `reference`, `interest`, `preprocessor`, `research`, `decision`, `execution`, `connector`, `ops`, `legacy`, `public`로 구분한다.

이 모듈의 DB connection search_path는 아래 순서를 기준으로 한다.

```sql
preprocessor, interest, reference, legacy, public
```

schema-per-domain 전환 후에도 이 모듈의 기존 SQL은 위 search_path를 통해 동작하는 것을 전제로 한다. 즉, 전처리 테이블은 `preprocessor`, raw 관심 데이터는 `interest`, 참조성 데이터는 `reference`, 이전 호환 대상은 `legacy`, 공통 fallback은 `public` 순서로 해석된다.

비밀번호, 토큰, 계좌번호, webhook URL, 실제 사용자 ID 등 민감정보는 환경변수 또는 로컬 전용 설정으로 관리한다. 문서, 예시, 로그에는 실제 값을 쓰지 않고 필요한 경우 `[REDACTED]`로 마스킹한다.

## 외부 의존성

현재 파일에서 확인되는 주요 의존성 후보는 다음과 같다.

- Python
- `psycopg2`
- `psycopg2.extras`
- `requests`
- PostgreSQL
- 외부 holiday API

외부 API 호출, DB DDL/DML은 운영 영향이 있으므로 분석 또는 문서 작업 중에는 실행하지 않는다.

## AWS 운영 구조 관점

이 저장소는 AWS Paper 운영 환경에서 전처리 실행 대상으로 사용될 수 있다. Preprocessor 관점에서만 정리하면 다음과 같다.

- Preprocessor는 AWS Paper Daily Step 3 구간에서 전처리 실행 단위로 호출될 수 있다.
- 실행 형태는 ECS RunTask 또는 컨테이너 실행 대상으로 `pre_daily.py` 또는 개별 `pre_*.py` entrypoint를 호출하는 구조를 상정한다.
- 실제 cluster 이름, task definition ARN, image URI, subnet, security group, command id는 문서에 원문으로 기록하지 않는다.
- AWS 리소스 값이 필요하면 아래 형식으로 마스킹해 표기한다.
  - `<PREPROCESSOR_ECS_TASK>`
  - `<ECR_IMAGE_URI>`
  - `<TASK_DEFINITION_ARN>`
  - `<DB_HOST>`
  - `<COMMAND_ID>`
- Scheduler, EventBridge, Step Functions의 개별 state/step 상세, Lambda 내부 구현, DB after-check 쿼리 결과의 세부 row는 Preprocessor 문서 범위 밖으로 두고 참조하지 않는다.

## 책임 경계

Preprocessor의 역할과 직접 책임지지 않는 영역을 분리해 정리한다.

### Preprocessor가 담당하는 역할

- `interest` schema에 적재된 raw/history 데이터를 읽어 `preprocessor` schema feature 테이블을 생성하거나 갱신한다.
- 뉴스 분석, 뉴스 이벤트 탐지, 뉴스 일일 feature 집계를 담당한다.
- 증권사 리포트 분석과 일일 feature 집계를 담당한다.
- 가격, 시장 폭, 매크로, 원자재, 해외지수 daily feature 생성을 담당한다.
- 투자자 수급, 프로그램 매매, 공매도 기반 수급/거래 구조 feature 생성을 담당한다.
- 종목 단위 total stock feature와 시장 단위 total market feature 생성을 담당한다.
- AWS Paper Daily Step 3에서 전처리 실행 단위로 호출될 수 있다.

### Preprocessor가 직접 책임지지 않는 영역

- 외부 데이터 수집 자체(KRX, Naver, yfinance 등 크롤링 실행)는 Crawler 책임이다.
- 매수/매도 판단, 주문 생성, 주문 제출, 체결 조회, 잔고/보유 snapshot 갱신은 StrategyDecision과 MarketConnector 책임이다.
- 백테스트와 리포트 생성은 StrategyResearch 책임이다.
- 실행 상태 조회 UI, 승인 UI, 화면 렌더링은 View 책임이다.
- Daily Batch 전체 orchestration, Scheduler 라인업, Step Functions state machine은 상위 orchestration 계층 책임이며 Preprocessor 내부 실행 책임이 아니다.

## 데이터 흐름 관점

Preprocessor 관점에서 상/하위 MS와의 데이터 연결 관계는 다음과 같다.

- 입력: Crawler가 적재한 `interest` schema의 raw/history 데이터.
- 처리: 이 저장소의 `pre_*.py` 스크립트가 `preprocessor` schema에 feature 테이블을 생성/갱신한다.
- 참조: 종목/유니버스/공통 참조 데이터는 `reference` schema에서 조회할 수 있고, 이전 호환 대상은 `legacy` schema에서 조회할 수 있다.
- 출력 소비: `preprocessor` schema의 total feature는 StrategyDecision과 StrategyResearch 후속 MS의 입력으로 사용될 수 있다. 다만 후속 MS의 전략 판단 로직, 주문 생성 로직, 백테스트 로직은 Preprocessor 문서 범위에서 다루지 않는다.

## Daily Step 3 전처리 흐름

`pre_daily.py`는 개별 전처리 스크립트의 `run()` entrypoint를 순서대로 호출하는 orchestration 후보다. 현재 소스 정적 확인 기준 호출 순서는 다음과 같다.

1. `pre_news_analysis.run()`
2. `pre_news_event_detection.run()`
3. `pre_news_daily_aggregator.run()`
4. `pre_agency_analysis.run()` (현재 소스에서 주석 처리되어 실행되지 않음)
5. `pre_agency_daily_aggregator.run()`
6. `pre_commodity.run()`
7. `pre_foreignindex.run()`
8. `pre_macroeconomic.run()`
9. `pre_price.run()`
10. `pre_marketbreadth.run()`
11. `pre_investorflow.run()`
12. `pre_program.run()`
13. `pre_shortsell.run()`
14. `pre_total_market_daily_feature.run()`
15. `pre_total_stock_daily_feature.run()`

실제 실행 시 각 단계는 DB read/upsert와 `pre_total_market_daily_feature`에 의한 외부 holiday API 호출 가능성이 연쇄적으로 발생할 수 있다. 문서 작업 중에는 실행하지 않는다.

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
