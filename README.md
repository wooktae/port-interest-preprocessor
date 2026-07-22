# port-interest-preprocessor

Crawler가 적재한 raw/history 데이터를 읽어 뉴스, 리서치, 가격, 시장, 매크로, 원자재, 해외지수, 수급과 거래구조 feature를 생성하는 Python 마이크로서비스다.

처리 결과는 PostgreSQL의 `preprocessor` schema에 저장되며, Strategy Research와 Strategy Decision이 후속 입력으로 사용할 수 있다.

이 저장소의 실행 경로는 대량 DB read, delete, insert와 upsert로 이어질 수 있고 일부 단계는 외부 holiday API를 호출할 수 있으므로 정적 분석과 문서 작업을 기본값으로 한다.

## 현재 상태

| 항목 | 값 |
| --- | --- |
| 운영 성격 | AWS Paper Daily Step 3 전처리 |
| 기본 구조 | 독립 실행형 `pre_*.py` script 중심 |
| Daily orchestration | `pre_daily.py` |
| 입력 | `interest` raw/history |
| 출력 | `preprocessor` feature |
| 참조 | `reference` · `legacy` |
| downstream | Strategy Research · Strategy Decision |
| 외부 요청 | Holiday API 가능 |
| Database | PostgreSQL `portfolio` |
| 문서 기본 원칙 | DB · API 실행 없이 정적 확인 |

> `analysis`, `aggregator`, `feature`라는 이름이 붙은 파일도 DB 쓰기와 대량 재계산을 수행할 수 있다. 문서 검증 목적으로 실행하지 않는다.

## 기술 스택

| 항목 | 값 |
| --- | --- |
| Language | Python |
| Database Driver | psycopg2 · psycopg2.extras |
| Database | PostgreSQL |
| HTTP | Requests |
| External API | Holiday API |
| Compute | Container · ECS RunTask 후보 |

## 책임 경계

### 담당 범위

| 영역 | 역할 |
| --- | --- |
| News | 종목 매핑 · 감성 · keyword · event |
| Agency | 투자의견 · 목표가 분석 |
| Price | 가격 feature |
| Market Breadth | 시장 폭 feature |
| Macro | 매크로 daily feature |
| Commodity | 원자재 daily feature |
| Foreign Index | 해외지수 daily feature |
| Flow | 투자자 수급 feature |
| Program | 프로그램 매매 feature |
| Short Sell | 공매도 feature |
| Total Stock | 종목 단위 종합 feature |
| Total Market | 시장 단위 종합 feature |
| Persistence | `preprocessor` schema 생성 · 갱신 |

### 직접 담당하지 않는 범위

| 항목 | 실제 책임 영역 |
| --- | --- |
| 외부 데이터 수집 | port-interest-crawler |
| 전략 연구 · 백테스트 | Strategy Research |
| 전략 판단 | Strategy Decision |
| 주문 계획 | Strategy Execution |
| 주문 제출 · 체결 | port-marketconnector |
| 화면 | port-view |
| Daily 전체 orchestration | Step Functions · Scheduler |

Preprocessor 안에 크롤링, 전략 판단, 주문 생성과 주문 제출 로직을 복제하지 않는다.

## 데이터 흐름

| 단계 | 처리 |
| --- | --- |
| 입력 | Crawler가 적재한 `interest` raw/history |
| 변환 | `pre_*.py` 분석 · 계산 · 집계 |
| 저장 | `preprocessor` feature |
| 참조 | `reference` ticker · universe · 기준정보 |
| 호환 | `legacy` |
| 소비 | Strategy Research · Strategy Decision |

raw가 비어 있거나 최신성이 부족한 경우 정상 0건과 입력 장애를 구분해야 한다.

과거 최신 feature를 당일 신규 결과처럼 재사용하지 않는다.

## Daily Step 3

`pre_daily.py`는 개별 전처리 `run()` entrypoint를 순서대로 호출하는 Daily orchestration 후보다.

### 현재 단계 구성

| 순서 | 단계 |
| --- | --- |
| 1 | `pre_news_analysis.run()` |
| 2 | `pre_news_event_detection.run()` |
| 3 | `pre_news_daily_aggregator.run()` |
| 4 | `pre_agency_analysis.run()` · 주석 처리 · 미실행 |
| 5 | `pre_agency_daily_aggregator.run()` |
| 6 | `pre_commodity.run()` |
| 7 | `pre_foreignindex.run()` |
| 8 | `pre_macroeconomic.run()` |
| 9 | `pre_price.run()` |
| 10 | `pre_marketbreadth.run()` |
| 11 | `pre_investorflow.run()` |
| 12 | `pre_program.run()` |
| 13 | `pre_shortsell.run()` |
| 14 | `pre_total_market_daily_feature.run()` |
| 15 | `pre_total_stock_daily_feature.run()` |

실제 호출 순서는 코드가 우선한다.

### 주석 처리 단계

현재 소스 정적 확인 기준 `pre_agency_analysis.run()`은 `pre_daily.py`에서 주석 처리되어 실행되지 않는다.

| 항목 | 처리 |
| --- | --- |
| 현재 상태 | Daily 자동 실행 제외 |
| 후속 단계 | `pre_agency_daily_aggregator.py` 입력 최신성 확인 |
| 주석 해제 | 별도 기능 변경 |
| 문서 | 실행 중인 단계처럼 표현하지 않음 |

오래된 agency analysis 결과를 당일 신규 결과처럼 집계하지 않는다.

### 부분 실패

| 위험 | 처리 |
| --- | --- |
| 중간 단계 예외 | 후속 total feature 진행 여부 확인 |
| 반환값 미사용 | 예외 전파 방식 확인 |
| Required 실패 | 전체 성공으로 기록 금지 |
| Optional 단계 | 주석 처리와 실패를 구분 |
| Total feature | 하위 feature 최신성 확인 후 생성 |

실패한 단계가 있는데 SUCCESS marker만 남는 구조를 정상으로 취급하지 않는다.

## 주요 파일

### Orchestration과 Helper

| 파일 | 역할 |
| --- | --- |
| `pre_daily.py` | Daily Step 3 orchestration |
| `db_config.py` | PostgreSQL 환경변수 loader |
| `interest_get_holidays.py` | 주말 · 공휴일 확인 |

### News

| 파일 | 역할 |
| --- | --- |
| `pre_news_analysis.py` | 뉴스-종목 매핑 · 감성 · keyword |
| `pre_news_event_detection.py` | 뉴스 event 탐지 |
| `pre_news_daily_aggregator.py` | 종목 · 일자 단위 뉴스 집계 |

### Agency

| 파일 | 역할 |
| --- | --- |
| `pre_agency_analysis.py` | 투자의견 · 목표가 분석 |
| `pre_agency_daily_aggregator.py` | 종목 · 일자 단위 리포트 집계 |

### Price와 Market

| 파일 | 역할 |
| --- | --- |
| `pre_price.py` | 가격 feature |
| `pre_marketbreadth.py` | 시장 폭 feature |

### Macro 계열

| 파일 | 역할 |
| --- | --- |
| `pre_macroeconomic.py` | 매크로 feature |
| `pre_commodity.py` | 원자재 feature |
| `pre_foreignindex.py` | 해외지수 feature |

### Flow와 거래구조

| 파일 | 역할 |
| --- | --- |
| `pre_investorflow.py` | 투자자 수급 feature |
| `pre_program.py` | 프로그램 매매 feature |
| `pre_shortsell.py` | 공매도 feature |

### Total Feature

| 파일 | 역할 |
| --- | --- |
| `pre_total_stock_daily_feature.py` | 종목 단위 total feature |
| `pre_total_market_daily_feature.py` | 시장 단위 total feature |

상세 역할은 [소스 파일 카탈로그](docs/source-file-catalog.md)를 참고한다.

## Feature 영역별 기준

### News

| 항목 | 기준 |
| --- | --- |
| Mapping | alias · ticker 의미 유지 |
| Sentiment | score 기준과 version 확인 |
| Event | master · keyword · sector weight |
| 중복 | 뉴스 · event unique key |
| 순서 | analysis 이후 aggregator |

### Agency

| 항목 | 기준 |
| --- | --- |
| Opinion | normalization · score 유지 |
| Target Price | NULL · 0 구분 |
| Analysis | `pre_agency_analysis.run()` Daily 주석 처리 |
| Aggregator | `interest_agency_raw` 직접 입력 · analysis 산출 비의존 |
| 과거 값 | 당일 신규 결과처럼 사용 금지 |

### Price와 Market Breadth

| 항목 | 기준 |
| --- | --- |
| Price | 수익률 · momentum · 이동평균 |
| Lookback | 필요한 과거 기간 유지 |
| Missing | 거래 정지와 누락 구분 |
| Breadth | universe · 시장 기준 |
| 성공 | 부분 universe로 전체 성공 금지 |

### Macro · Commodity · Foreign Index

| 항목 | 기준 |
| --- | --- |
| Mapping | indicator · source 유지 |
| Date | timezone · 시차 확인 |
| Holiday | forward-fill 정책 확인 |
| Missing | 빈 raw와 전일 값 유지 구분 |
| 실패 | 일부 지표와 전체 실패 구분 |

### Flow · Program · Short Sell

| 항목 | 기준 |
| --- | --- |
| 값 의미 | 수량 · 금액 · 비율 · sign |
| 결합 | 가격 raw와 join 기준 |
| Date | KRX raw 최신 거래일 |
| Empty | 실제 0건과 미수집 구분 |
| 계산 | division by zero · NULL 처리 |

### Total Feature

| 항목 | 기준 |
| --- | --- |
| 입력 | 모든 하위 feature 최신성 |
| 기준일 | 같은 trade date |
| Join | key · cardinality |
| Missing | 실패 입력을 NULL로 숨기지 않음 |
| Weight | 변경 시 전략 영향 확인 |
| Holiday | API 실패를 정상 SKIP으로 변환 금지 |

## 실행 위험

### Daily

`pre_daily.py`는 여러 전처리 단계를 연쇄 실행한다.

| 위험 | 내용 |
| --- | --- |
| Database | 대량 read · insert · update · upsert |
| Delete | 재생성 범위에 따라 데이터 삭제 가능 |
| Network | Holiday API |
| Failure | 중간 실패 뒤 후속 단계 진행 가능성 |
| Total | 불완전한 입력으로 종합 feature 생성 가능성 |

### 개별 Feature

개별 `pre_*.py`도 DB 쓰기와 대량 재계산을 수행할 수 있다.

특히 아래 파일은 변경 영향이 크다.

| 파일 | 위험 |
| --- | --- |
| `pre_total_stock_daily_feature.py` | 다수 종목 feature 결합 |
| `pre_total_market_daily_feature.py` | 다수 시장 feature 결합 |
| `pre_news_event_detection.py` | event 대량 생성 |
| `pre_news_daily_aggregator.py` | 뉴스 일일 집계 |
| `pre_agency_daily_aggregator.py` | 리포트 일일 집계 |

## 계산 안전

- 계산식 변경 전 feature 정의와 downstream 소비를 확인한다.
- 결측값, 0, 음수와 극단값 처리 의미를 유지한다.
- rolling window와 minimum period를 확인한다.
- rounding과 데이터 타입을 확인한다.
- 미래 날짜와 당일 미확정 데이터를 사용하지 않는다.
- look-ahead bias를 만들지 않는다.
- total score와 weight 변경은 단순 리팩터링으로 취급하지 않는다.

## Database

### 연결 기준

| 항목 | 값 |
| --- | --- |
| Database | `portfolio` |
| Config loader | `db_config.py` · `get_db_config()` |
| 환경변수 | `INTEREST_DB_*` |
| Password | 기본값 없음 |
| search path | `preprocessor, interest, reference, legacy, public` |

운영 환경에서는 Preprocessor 전용 DB user를 사용한다.

문서의 `postgres` 기본값을 운영 권한 기준으로 해석하지 않는다.

### Schema 책임

| Schema | 역할 |
| --- | --- |
| `preprocessor` | 분석 · 집계 feature |
| `interest` | Crawler raw · history |
| `reference` | ticker · universe · 기준정보 |
| `legacy` | 과거 호환 |
| `public` | fallback search path |

Preprocessor는 `research`, `decision`, `execution` 결과를 직접 생성하지 않는다.

### SQL 기준

- 신규 SQL은 가능한 한 schema-qualified 이름을 사용한다.
- 기존 unqualified SQL은 connection `search_path` 기준으로 동작한다.
- unique key와 `ON CONFLICT` 의미를 유지한다.
- aggregation의 group key와 join cardinality를 확인한다.
- delete 후 insert는 대상 일자와 범위를 확인한다.
- transaction과 rollback 경계를 유지한다.
- 부분 적재 뒤 SUCCESS를 출력하지 않는다.

## Holiday API

`interest_get_holidays.py` 또는 이를 참조하는 단계는 외부 holiday API를 호출할 수 있다.

| 항목 | 기준 |
| --- | --- |
| HTTP | timeout · status 확인 |
| 주말 | 공휴일과 구분 |
| 실패 | 정상 영업일로 해석 금지 |
| SKIP | API 장애를 정상 SKIP으로 숨기지 않음 |
| Test | HTTP mock |

문서 작업과 정적 분석 중에는 실제 API를 호출하지 않는다.

## 설정

### DB 환경변수

| 환경변수 | 기본값 · 역할 |
| --- | --- |
| `INTEREST_DB_HOST` | `localhost` |
| `INTEREST_DB_PORT` | `5433` |
| `INTEREST_DB_NAME` | `portfolio` |
| `INTEREST_DB_USER` | 환경별 Preprocessor DB user |
| `INTEREST_DB_PASSWORD` | 기본값 없음 |

PowerShell 예시:

```powershell
$env:INTEREST_DB_HOST="localhost"
$env:INTEREST_DB_PORT="5433"
$env:INTEREST_DB_NAME="portfolio"
$env:INTEREST_DB_USER="[REDACTED]"
$env:INTEREST_DB_PASSWORD="[REDACTED]"
```

### 기타 설정

| 범주 | 예시 |
| --- | --- |
| Feature | processor version · weight |
| Date | trade date · business date |
| Database | raw · feature table |
| API | holiday endpoint |
| Runtime | ECS · container 환경변수 |

실제 local config와 credential 값을 문서에 기록하지 않는다.

## AWS 운영

Preprocessor는 AWS Paper Daily Step 3에서 container 또는 ECS RunTask 실행 대상으로 호출될 수 있다.

| 항목 | 책임 |
| --- | --- |
| Preprocessor | feature 처리 entrypoint |
| ECS · Container | 실행 환경 |
| Step Functions | Daily orchestration |
| Scheduler | 실행 시각 |
| Crawler | raw 입력 |
| Strategy | feature 소비 |

실제 cluster, task definition ARN, image URI, subnet과 security group은 외부 운영 사실이다.

문서에는 실제 값을 기록하지 않고 placeholder만 사용한다.

| 값 | Placeholder |
| --- | --- |
| ECS task | `<PREPROCESSOR_ECS_TASK>` |
| ECR image | `<ECR_IMAGE_URI>` |
| Task definition | `<TASK_DEFINITION_ARN>` |
| DB host | `<DB_HOST>` |
| Command id | `<COMMAND_ID>` |

## 실행

각 Python 파일은 독립 entrypoint일 수 있다.

아래 명령은 실행 위험 예시다.

```powershell
python pre_daily.py
```

실행 시 다수 DB 작업과 외부 holiday API 호출이 발생할 수 있다.

## 실행 금지 목록

문서 작업과 정적 분석 중에는 아래 작업을 수행하지 않는다.

- `pre_daily.py` 실행
- 개별 `pre_*.py` 실행
- DB DDL · DML · psql
- Holiday API 호출
- Crawler 실행
- 모델 다운로드 · 학습 · 추론
- ECS · SSM · Scheduler 실행
- Slack 호출

## 보안

다음 값은 코드, 문서와 로그에 원문으로 기록하지 않는다.

- DB password와 connection string
- API key · token
- 실제 DB host · private IP
- AWS account-id
- 실제 ARN
- ECR image URI
- subnet · security group id
- command id
- local absolute path
- Slack webhook URL

Placeholder:

| 값 | Placeholder |
| --- | --- |
| 일반 민감정보 | `[REDACTED]` |
| DB host | `[REDACTED_DB_HOST]` |
| ARN | `[REDACTED_ARN]` |
| command id | `[REDACTED_COMMAND_ID]` |
| ECS task | `<PREPROCESSOR_ECS_TASK>` |
| ECR image | `<ECR_IMAGE_URI>` |
| Task definition | `<TASK_DEFINITION_ARN>` |

## 외부 의존성

| 항목 | 역할 |
| --- | --- |
| Python | Runtime |
| psycopg2 | PostgreSQL |
| psycopg2.extras | Batch · helper |
| Requests | Holiday API |
| PostgreSQL | raw read · feature persistence |

## 문서

| 문서 | 역할 |
| --- | --- |
| `AGENTS.md` | port-interest-preprocessor 작업 규칙 |
| `README.md` | 현재 구조와 운영 AS-IS |
| `CHANGELOG.md` | 주요 변경 이력 |
| `docs/source-file-catalog.md` | 주요 파일과 책임 |

날짜별 `docs/worklog/*.md`는 신규 생성하지 않는다.

코드와 문서 변경 이력은 `CHANGELOG.md`에 기록한다.
