# Source File Catalog

port-interest-preprocessor의 주요 파일과 디렉터리 역할을 빠르게 확인하기 위한 문서다.

모든 파일을 나열하는 inventory가 아니라, raw→feature 구조와 변경 영향 판단에 필요한 항목만 기록한다.

repository root 기준 상대 경로를 사용하며 cache, build 결과, credential, dump와 일회성 산출물은 제외한다.

## 사용 원칙

| 항목 | 값 |
| --- | --- |
| 기준 | 현재 Preprocessor 코드와 Daily Step 3 구조 |
| 포함 | 주요 entrypoint · feature 묶음 · 공통 helper |
| 제외 | cache · credential · debug · output dump |
| 갱신 | 파일 경로 · 책임 · 호출 순서가 바뀔 때 |
| 생략 | 내부 구현만 바뀌고 책임이 동일한 경우 |
| 민감정보 | credential · host · ARN · command id 원문 금지 |

## Root와 공통 파일

| 파일 | 역할 |
| --- | --- |
| `AGENTS.md` | Preprocessor 코드와 문서 작업 규칙 |
| `README.md` | 현재 구조 · 데이터 흐름 · 운영 AS-IS |
| `CHANGELOG.md` | 주요 변경 이력 |
| `db_config.py` | PostgreSQL 환경변수 loader |
| `interest_get_holidays.py` | 주말 · 공휴일 확인 |

### 변경 시 확인

| 대상 | 확인 |
| --- | --- |
| `AGENTS.md` | raw→feature · Step 3 · 계산 안전 규칙 |
| `README.md` | 현재 구조 · 책임 경계 · 실행 위험 |
| `CHANGELOG.md` | 실제 Preprocessor 변경만 기록 |
| `db_config.py` | `INTEREST_DB_*` · password · search path |
| Holiday helper | API 실패 · 주말 · 공휴일 · cache |

## Daily Step 3 Orchestration

| 파일 | 역할 |
| --- | --- |
| `pre_daily.py` | 개별 `run()`을 순서대로 호출하는 Daily entrypoint |

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

### 현재 주석 처리 단계

| 항목 | 값 |
| --- | --- |
| 단계 | `pre_agency_analysis.run()` |
| 상태 | `pre_daily.py`에서 주석 처리 |
| 자동 실행 | 제외 |
| 후속 위험 | Agency aggregator 입력 최신성 |
| 활성화 | 별도 기능 변경 |

주석 처리된 단계를 실행 중인 단계처럼 기록하지 않는다.

### 변경 시 확인

| 항목 | 값 |
| --- | --- |
| 선행 입력 | raw · analysis · feature 존재 |
| 호출 순서 | aggregator와 total 의존성 |
| 예외 | required 단계 실패 전파 |
| 반환값 | caller의 성공 판단 |
| Total | 하위 feature 성공과 최신성 |
| 재실행 | 같은 trade date idempotency |

단계 순서를 문서 정리 목적으로 변경하지 않는다.

## News Feature

| 파일 | 역할 |
| --- | --- |
| `pre_news_analysis.py` | 뉴스-종목 매핑 · 감성 · keyword |
| `pre_news_event_detection.py` | event master 기반 뉴스 event |
| `pre_news_daily_aggregator.py` | 종목 · 일자 단위 뉴스 집계 |

### 입출력과 영향

| 항목 | 값 |
| --- | --- |
| 입력 | News raw · ticker alias · event 기준 |
| 중간 결과 | News analysis · News event |
| 출력 | News daily feature |
| 선행 관계 | Analysis · Event → Aggregator |
| downstream | Total stock feature |

### 변경 시 확인

| 항목 | 값 |
| --- | --- |
| Alias | ticker mapping 의미 |
| Sentiment | 사전 · score · version |
| Event | keyword · direction · sector weight |
| 중복 | 뉴스 · event unique key |
| Freshness | 같은 trade date 입력 |
| 실패 | 선행 실패 뒤 aggregator 실행 여부 |

## Agency Feature

| 파일 | 역할 |
| --- | --- |
| `pre_agency_analysis.py` | 투자의견 · 목표가 분석 |
| `pre_agency_daily_aggregator.py` | 종목 · 일자 단위 리포트 집계 |

### 입출력과 영향

| 항목 | 값 |
| --- | --- |
| 집계 입력 | `interest_agency_raw` · `interest_price_raw` (LATERAL) |
| 분석 산출 | `pre_agency_analysis` · 현재 Daily 미실행 |
| 출력 | `pre_agency_daily_feature` |
| 의존 | Aggregator는 analysis 산출에 비의존 |
| downstream | Total stock feature |

### 변경 시 확인

| 항목 | 값 |
| --- | --- |
| Opinion | recommendation normalization |
| Target Price | NULL · 0 · upside |
| 최신성 | Analysis와 aggregator 기준일 |
| Price join | 선행 가격 데이터 |
| 과거 값 | 당일 신규 결과처럼 사용 금지 |

## Price와 Market Feature

| 파일 | 역할 |
| --- | --- |
| `pre_price.py` | 가격 daily feature |
| `pre_marketbreadth.py` | 시장 폭 daily feature |

### 변경 시 확인

| 항목 | 값 |
| --- | --- |
| Price | 수익률 · momentum · 이동평균 |
| Volatility | lookback · minimum period |
| Missing | 거래 정지와 누락 구분 |
| Breadth | universe · 시장 기준 |
| Date | raw와 feature trade date |
| downstream | Total stock · Total market |

부분 universe만으로 전체 시장 feature 성공을 기록하지 않는다.

## Macro 계열 Feature

| 파일 | 역할 |
| --- | --- |
| `pre_macroeconomic.py` | 매크로 daily feature |
| `pre_commodity.py` | 원자재 daily feature |
| `pre_foreignindex.py` | 해외지수 daily feature |

### 변경 시 확인

| 항목 | 값 |
| --- | --- |
| Mapping | indicator · ticker · source |
| Date | timezone · 시장 시차 |
| Missing | 빈 raw와 전일 유지 구분 |
| Fill | 휴장일 forward-fill 정책 |
| Score | clipping · pressure · regime |
| downstream | Total market feature |

일부 지표 누락과 전체 실패를 구분한다.

## Flow와 거래구조 Feature

| 파일 | 역할 |
| --- | --- |
| `pre_investorflow.py` | 투자자 수급 daily feature |
| `pre_program.py` | 프로그램 매매 daily feature |
| `pre_shortsell.py` | 공매도 daily feature |

### 변경 시 확인

| 항목 | 값 |
| --- | --- |
| 값 의미 | 수량 · 금액 · 비율 · sign |
| Price join | 거래대금 · ratio 계산 |
| Date | KRX raw 최신 거래일 |
| Empty | 실제 0건과 미수집 |
| 계산 | NULL · division by zero |
| downstream | Total stock · Total market |

spike, pressure와 momentum 기준 변경은 전략 입력 변경으로 취급한다.

## Total Feature

| 파일 | 역할 |
| --- | --- |
| `pre_total_stock_daily_feature.py` | 종목 단위 total feature |
| `pre_total_market_daily_feature.py` | 시장 단위 total feature |

### 입력 관계

| 출력 | 주요 입력 |
| --- | --- |
| Total Stock | Price · Flow · Short Sell · News · Agency |
| Total Market | Breadth · Foreign Index · Macro · Commodity · Program · Market-level Investor Flow |

### 변경 시 확인

| 항목 | 값 |
| --- | --- |
| 최신성 | 모든 하위 feature 기준일 |
| Join | key · cardinality |
| Missing | 실패 입력을 NULL로 숨기지 않음 |
| Weight | score · gating · penalty |
| Duplicate | join 결과 row 증가 |
| Holiday | helper 실패와 SKIP 구분 |

total score, weight와 penalty 변경은 단순 리팩터링이 아니다.

downstream Strategy Research와 Strategy Decision 영향을 확인한다.

## Raw→Feature Contract

| 단계 | 책임 |
| --- | --- |
| 입력 | `interest` raw/history |
| 처리 | `pre_*.py` transform · aggregate |
| 출력 | `preprocessor` feature |
| 참조 | `reference` · `legacy` |
| 소비 | Strategy Research · Strategy Decision |

### 유지 기준

| 항목 | 값 |
| --- | --- |
| Source | 입력 raw source 의미 |
| Ticker | 종목 식별자 |
| Date | trade date · business date |
| Version | feature 계산 버전 |
| Unique key | 중복 방지 계약 |
| Upsert | 재실행 의미 |
| Downstream | column · score 호환 |

과거 최신 feature를 당일 신규 결과처럼 재사용하지 않는다.

## Database Contract

| 항목 | 값 |
| --- | --- |
| Database | `portfolio` |
| Config loader | `db_config.py` · `get_db_config()` |
| 환경변수 | `INTEREST_DB_*` |
| Password | 기본값 없음 |
| search path | `preprocessor, interest, reference, legacy, public` |

### Schema 책임

| Schema | 역할 |
| --- | --- |
| `preprocessor` | 분석 · 집계 feature |
| `interest` | Crawler raw · history |
| `reference` | ticker · universe · 기준정보 |
| `legacy` | 과거 호환 |
| `public` | fallback search path |

### SQL 변경 시 확인

| 항목 | 값 |
| --- | --- |
| Table · column | 코드 · migration · DB 계약 |
| 신규 SQL | 가능한 한 schema-qualified |
| 기존 SQL | connection `search_path` |
| Unique key | `ON CONFLICT` 의미 |
| Group key | aggregation 단위 |
| Join | cardinality · 중복 |
| Delete | 대상 일자 · ticker · 범위 |
| Transaction | commit · rollback |

실패한 DB 작업 뒤 SUCCESS를 출력하지 않는다.

## Holiday API

| 파일 | 역할 |
| --- | --- |
| `interest_get_holidays.py` | Nager.Date 기반 KR · US 휴일 조회 |
| `pre_total_market_daily_feature.py` | 최근 영업일 계산 시 helper 참조 가능 |

### 변경 시 확인

| 항목 | 값 |
| --- | --- |
| HTTP | timeout · status |
| Country | KR · US |
| Weekend | 공휴일과 구분 |
| Cache | 메모리 cache |
| 실패 | 정상 영업일로 해석 금지 |
| Test | HTTP mock |

문서 작업과 정적 검증 중에는 실제 API를 호출하지 않는다.

## 계산 안전

| 항목 | 확인 |
| --- | --- |
| Lookback | rolling window · minimum period |
| Missing | NULL · 0 · 음수 구분 |
| Outlier | clipping · z-score |
| Type | numeric type · rounding |
| Date | 미래 데이터 사용 금지 |
| Bias | look-ahead bias 금지 |
| Weight | 전략 영향 확인 |

당일 미확정 데이터와 미래 row를 feature 계산에 사용하지 않는다.

## External Dependencies

| 항목 | 역할 |
| --- | --- |
| Python | Runtime |
| psycopg2 | PostgreSQL |
| psycopg2.extras | Batch · helper |
| Requests | Holiday API |
| PostgreSQL | raw read · feature persistence |

실제 DB와 외부 API를 문서 검증이나 unit test에서 사용하지 않는다.

## Tests

| 변경 | 검증 |
| --- | --- |
| Python 문법 | 안전한 compile check |
| 순수 계산 | 고정 입력 fixture |
| News mapping | alias · keyword fixture |
| Event | direction · sector weight |
| Aggregator | group key · duplicate |
| Rolling | lookback · boundary |
| Total | join cardinality · missing input |
| Holiday | HTTP mock · 주말 · 공휴일 |
| Daily | 호출 순서 · 예외 전파 mock |
| Repository | SQL · parameter · upsert |
| 문서 | 링크 · 사실 · 가독성 |

실행 위험 import가 있으면 파일 본문 정적 확인을 우선한다.

## AWS와 운영 Wrapper

| 항목 | 역할 |
| --- | --- |
| `pre_daily.py` | Step 3 실행 entrypoint |
| `Dockerfile` | 컨테이너 빌드 · 기본 CMD `pre_daily.py` |
| ECS Fargate | 실행 환경 · RunTask |
| Step Functions | Daily orchestration · `Step3_RunPreprocessor` |
| Scheduler | 실행 시각 |

## DevOps Wrapper

| 파일 | 역할 |
| --- | --- |
| `.devops/codebuild/buildspec.yml` | CodeBuild CI gate · Docker image build · 선택적 ECR Push |
| `.github/workflows/preprocessor-codebuild.yml` | GitHub Actions trigger · CodeBuild 실행 · OIDC 인증 |
| `.devops/scripts/container-smoke.py` | Container import smoke test · `run()` 미호출 |

### 변경 시 확인

| 항목 | 값 |
| --- | --- |
| CI gate | Python Compile · Unit Test · Static Analysis · Container Smoke Test |
| Image | Git SHA 기반 Tag · ECR Digest 고정 |
| Push | 선택적 · 수동 실행 입력 제어 |
| 인증 | GitHub OIDC · Repository Variable Role ARN |
| 배포 | 신규 ECS Task Definition Revision · Step Functions 참조 전환 |

repository에는 위 DevOps wrapper와 `Dockerfile`이 확인되며 shell · PowerShell · batch wrapper는 없다.

실제 AWS 상태를 repository 파일만으로 확정하지 않는다.

## Documents

| 문서 | 역할 |
| --- | --- |
| `AGENTS.md` | Preprocessor 작업 규칙 |
| `README.md` | 현재 구조와 운영 AS-IS |
| `CHANGELOG.md` | 주요 변경 이력 |
| `docs/source-file-catalog.md` | 주요 파일과 책임 |

날짜별 `docs/worklog/*.md`는 신규 생성하지 않는다.

과거 worklog를 유지하는 경우 역사 기록으로만 취급한다.

## 외부 의존 모듈

| 모듈 | 관계 |
| --- | --- |
| `port-interest-crawler` | raw/history 입력 |
| `port_strategy_research` | feature 소비 · 백테스트 |
| `port_strategy_decision` | feature 소비 · 전략 판단 |
| `port_strategy_execution` | 후속 주문 계획 |
| `port-marketconnector` | 주문 · broker 연동 |
| `port-view` | 실행 상태 · 화면 |
| Step Functions · Scheduler | 전체 orchestration |

다른 MS의 내부 코드와 문서는 Preprocessor 변경 범위에 자동 포함하지 않는다.

## 정리 후보

현재 확인된 운영 소스 밖 파일은 카탈로그에 추가하지 않는다.

향후 아래 파일이 확인되면 삭제하지 말고 정리 후보로만 표시한다.

- test · debug 임시 파일
- cache · `__pycache__`
- 모델 output dump
- 일회성 patch
- 사용처 불명 script

실제 import, 호출 관계와 소유 책임을 확인한 뒤 별도 결정한다.

## 카탈로그 갱신 조건

| 변경 | 처리 |
| --- | --- |
| 주요 Python 파일 생성 · 삭제 · 이름 변경 | 갱신 |
| `pre_daily.py` 호출 순서 변경 | 갱신 |
| Feature 책임 · 입출력 변경 | 갱신 |
| 주석 처리 단계 변경 | 갱신 |
| DB loader · schema 역할 변경 | 갱신 |
| Holiday helper 역할 변경 | 갱신 |
| scripts · ECS wrapper 변경 | 갱신 |
| 문서 생성 · 삭제 · 역할 변경 | 갱신 |
| 내부 구현만 변경 · 책임 동일 | 생략 가능 |

카탈로그 갱신 시 전체 repository inventory를 새로 만들지 않는다.

변경된 영역과 인접 항목만 확인한다.
