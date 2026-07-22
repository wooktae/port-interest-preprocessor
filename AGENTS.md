# port-interest-preprocessor 작업 규칙

이 문서는 `port-interest-preprocessor` 마이크로서비스의 Python 전처리 코드, Daily orchestration, feature 집계, 설정, 테스트와 문서를 수정할 때 적용하는 기준이다.

`port-interest-preprocessor` 관련 작업은 이 문서만 읽어도 작업 범위, raw→feature 데이터 계약, Daily Step 3 실행 순서, DB 쓰기 위험, 상·하위 MS 책임과 검증 원칙을 이해할 수 있어야 한다.

## 0. 최우선 문서 가독성 규칙

모든 문서 작업에서 본 섹션을 최우선으로 적용한다.

### 0.0 적용 범위 제한

가독성 규칙은 이번 작업에서 새로 작성하거나 직접 수정하는 부분에만 적용한다.

사용자가 문서 전체 정리나 전수 점검을 명시하지 않은 경우 아래 작업은 수행하지 않는다.

| 항목 | 기본 처리 |
| --- | --- |
| 기존 문서 전체 전수 스캔 | 수행하지 않음 |
| README 전체 재구성 | 수행하지 않음 |
| CHANGELOG 과거 이력 대량 정리 | 수행하지 않음 |
| 신규 scanner · audit 도구 작성 | 수행하지 않음 |
| sub-agent · orchestrator 생성 | 수행하지 않음 |

변경 인접부는 같은 표 행, 같은 bullet 묶음, 같은 짧은 문단까지만 본다.

범위 밖의 기존 위반은 원본을 유지하고 필요 시 후속 후보로만 남긴다.

### 0.1 표 작성 규칙

새로 만드는 독립 요약 표는 기본적으로 2컬럼으로 작성한다.

기본 헤더는 `항목 / 값`이다.

아래 상황에서는 더 구체적인 2컬럼 헤더를 사용할 수 있다.

| 상황 | 우선 헤더 |
| --- | --- |
| 파일별 변경 | `파일 / 변경` |
| entrypoint 설명 | `파일 / 역할` |
| feature 설명 | `Feature / 역할` |
| 검증 결과 | `항목 / 결과` |
| 설정 정리 | `설정 / 값` |
| 위험 정리 | `위험 / 처리` |
| 테스트 결과 | `테스트 / 결과` |

기존 표에 행을 추가하는 경우 기존 컬럼 구조를 유지한다.

3컬럼 이상 표는 다음 경우에만 허용한다.

| 조건 | 처리 |
| --- | --- |
| 사용자가 명시적으로 요청 | 요청 구조 사용 |
| 기존 표 보존이 더 안전 | 기존 구조 유지 |
| 비교 구조상 2컬럼 변환 시 의미 손실 | 예외 허용 |

### 0.2 표 셀과 문장 길이

- 표 셀은 2문장 이하로 유지한다.
- 한 셀에 여러 값이 있으면 `<br>`로 나눈다.
- 한 셀에 3개 이상의 사실을 장문으로 넣지 않는다.
- 긴 근거는 표 밖 설명이나 관련 문서 링크로 분리한다.
- 300자 초과 셀과 500자 초과 라인을 만들지 않는다.
- raw log, 전체 SQL, 전체 DB 결과와 AWS 응답을 문서에 붙이지 않는다.

### 0.3 문서 밀도

문서 작성 우선순위는 아래를 따른다.

1. 짧은 Summary
2. 짧은 2컬럼 표
3. 짧은 bullet
4. 상세 문서 링크
5. 긴 본문

같은 사실을 README, CHANGELOG, worklog와 상세 문서에 장문으로 반복하지 않는다.

### 0.4 상태 표시

상태 배지는 아래 5종만 사용한다.

| 배지 | 의미 |
| --- | --- |
| 🔴 | 금지 · 고위험 · 실패 |
| 🟠 | 대기 · 관찰 · 미확정 |
| 🟢 | 완료 · 성공 · ENABLED |
| 🔵 | 참고 · 정보 · evidence |
| ⚫ | 해당 없음 |

상태 배지로 충분하면 HTML 색상을 추가하지 않는다.

### 0.5 작업 방식 제한

문서 작업은 아래 순서로 진행한다.

1. 요청 범위 확인
2. 대상 파일 직접 읽기
3. 필요한 부분만 수정
4. UTF-8 No BOM 저장
5. 짧은 after-check
6. 변경 요약 보고

사용자가 명시적으로 요청하지 않는 한 아래 방식은 사용하지 않는다.

- 전체 workspace 전수 스캔
- sub-agent
- orchestrator
- 신규 scanner
- content hash matrix
- workspace 밖 임시 파일
- 과도한 자동화 스크립트

## 1. Scope

### 1.1 기본 작업 디렉터리

`C:\Workspaces\port-interest-preprocessor`

### 1.2 프로젝트 역할

port-interest-preprocessor는 Crawler가 적재한 raw/history 데이터를 읽어 분석·집계 feature를 생성하는 Python 마이크로서비스다.

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

### 1.3 기본 수정 대상

| 구분 | 대상 |
| --- | --- |
| Python | 루트 `pre_*.py`와 package Python 파일 |
| Daily | `pre_daily.py` |
| Helper | `db_config.py` · 휴일 helper |
| 테스트 | `tests` · `test_*.py` |
| 설정 | 환경변수 loader · local config 관련 코드 |
| 문서 | `README.md` · `CHANGELOG.md` · `docs` |
| 의존성 | requirements · pyproject · lock 관련 파일 |
| 운영 | ECS · container 실행 wrapper와 관련 문서 |

현재 요청에 포함되지 않은 파일은 수정하지 않는다.

### 1.4 다른 마이크로서비스

아래 프로젝트는 외부 의존 모듈이다.

- `port-interest-crawler`
- `port-view`
- `port-marketconnector`
- `port_strategy_common`
- `port_strategy_research`
- `port_strategy_decision`
- `port_strategy_execution`

현재 작업이 명시적으로 요구하지 않는 한 다른 MS의 코드와 문서는 수정하지 않는다.

`.kiro`의 cross-service spec도 port-interest-preprocessor 작업 범위에 자동 포함하지 않는다.

## 2. 실행 위험 등급

이 저장소의 전처리 스크립트는 실행 시 대량 DB read, delete, insert와 upsert를 수행할 수 있다.

일부 경로는 외부 holiday API도 호출할 수 있다.

모든 Python 파일을 일반적인 smoke test 대상으로 취급하지 않는다.

### 2.1 최고 위험 entrypoint

| 파일 | 위험 |
| --- | --- |
| `pre_daily.py` | 다수 전처리 단계 연쇄 실행 |
| `pre_total_stock_daily_feature.py` | 여러 종목 feature 대량 결합 |
| `pre_total_market_daily_feature.py` | 여러 시장 feature 결합 · 휴일 API 가능 |
| `pre_news_event_detection.py` | event master와 keyword 기반 대량 event 생성 |
| `pre_news_daily_aggregator.py` | 뉴스 일일 집계 대량 갱신 |
| `pre_agency_daily_aggregator.py` | 리포트 일일 집계 대량 갱신 |

위 파일은 사용자의 명시적 실행 요청과 대상 DB 환경 확인 없이 실행하지 않는다.

### 2.2 개별 Feature 쓰기 위험

| 영역 | 파일 |
| --- | --- |
| News | `pre_news_analysis.py` · `pre_news_event_detection.py` |
| Agency | `pre_agency_analysis.py` · `pre_agency_daily_aggregator.py` |
| Price · Market | `pre_price.py` · `pre_marketbreadth.py` |
| Macro | `pre_macroeconomic.py` |
| Commodity | `pre_commodity.py` |
| Foreign Index | `pre_foreignindex.py` |
| Flow | `pre_investorflow.py` |
| Program | `pre_program.py` |
| Short Sell | `pre_shortsell.py` |

개별 스크립트도 DB 쓰기와 대량 재계산을 수행할 수 있다.

이름에 analysis 또는 aggregator가 있다는 이유만으로 read-only라고 판단하지 않는다.

### 2.3 정적 작업 기본값

사용자가 실행을 명시하지 않은 경우 아래 작업만 수행한다.

- 파일 직접 읽기
- 안전한 텍스트 검색
- 코드 정적 분석
- 문서 수정
- 테스트 코드 작성
- 실행되지 않는 syntax 검토
- 읽기 전용 Git 상태 확인

## 3. 데이터 흐름과 책임 경계

### 3.1 기본 흐름

| 단계 | 책임 |
| --- | --- |
| 입력 | Crawler가 적재한 `interest` raw/history |
| 처리 | `pre_*.py` 분석 · 변환 · 집계 |
| 저장 | `preprocessor` feature |
| 참조 | `reference` · `legacy` |
| 소비 | Strategy Research · Strategy Decision |

### 3.2 직접 책임지지 않는 영역

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

### 3.3 Raw→Feature 계약

- 입력 raw의 source, ticker, trade date와 기준 시각 의미를 유지한다.
- feature version과 계산 기준을 임의 변경하지 않는다.
- raw가 비어 있거나 최신성이 부족하면 정상 0건과 입력 장애를 구분한다.
- downstream이 사용하는 feature column을 명시 요청 없이 삭제하거나 rename하지 않는다.
- total feature는 하위 feature의 성공과 최신성을 확인한 뒤 생성한다.
- 이전 날짜 feature를 당일 성공 결과로 재사용하지 않는다.

## 4. Daily Step 3 Orchestration

`pre_daily.py`는 개별 전처리 `run()` entrypoint를 순서대로 호출하는 Daily orchestration 후보이다.

### 4.1 현재 단계 구성

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

문서와 코드가 다르면 추정하지 말고 현재 구현을 기준으로 문서를 갱신한다.

### 4.2 주석 처리 단계

현재 문서 기준으로 `pre_agency_analysis.run()`은 `pre_daily.py`에서 주석 처리된 상태다.

- 주석 처리된 단계를 실행 중인 것으로 문서화하지 않는다.
- 주석 해제를 일반 정합성 수정으로 수행하지 않는다.
- 후속 `pre_agency_daily_aggregator.py`의 입력 의존성을 함께 확인한다.
- 과거 데이터 재사용 여부와 최신성 위험을 확인한다.
- 단계 활성화는 별도 기능 변경으로 취급한다.

### 4.3 단계 순서 변경

순서 변경 전 아래를 확인한다.

| 항목 | 확인 |
| --- | --- |
| 입력 table | 선행 feature 생성 여부 |
| Trade date | 같은 기준일 사용 여부 |
| Aggregator | analysis 결과 의존 여부 |
| Total feature | 모든 하위 feature 완료 여부 |
| Failure | 중간 실패 뒤 후속 실행 여부 |
| Idempotency | 재실행 시 중복 여부 |

단계 순서를 단순 정리 목적으로 변경하지 않는다.

### 4.4 부분 실패

- 한 단계 실패를 print만 하고 전체 성공으로 처리하지 않는다.
- child 함수 반환값과 예외 계약을 확인한다.
- 실패 뒤 total feature를 생성하지 않는다.
- 성공 marker는 모든 필수 단계 완료 뒤 출력한다.
- 주석 처리된 optional 단계와 실패한 required 단계를 구분한다.
- 실행하지 않은 단계를 성공으로 기록하지 않는다.

## 5. Feature 영역별 기준

### 5.1 News

| 파일 | 역할 |
| --- | --- |
| `pre_news_analysis.py` | 뉴스-종목 매핑 · 감성 · keyword |
| `pre_news_event_detection.py` | event 후보 탐지 |
| `pre_news_daily_aggregator.py` | 종목 · 일자 단위 집계 |

- alias와 ticker mapping 의미를 유지한다.
- 감성 점수와 keyword rule을 변경하면 version과 영향 범위를 확인한다.
- event master, keyword와 sector weight 의존성을 확인한다.
- 중복 뉴스와 중복 event의 unique key를 확인한다.
- analysis 실패 뒤 aggregator를 정상 실행하지 않는다.

### 5.2 Agency

| 파일 | 역할 |
| --- | --- |
| `pre_agency_analysis.py` | 투자의견 · 목표가 분석 |
| `pre_agency_daily_aggregator.py` | 종목 · 일자 단위 집계 |

- 투자의견 normalization과 score 의미를 유지한다.
- 목표가 결측과 0을 구분한다.
- analysis 단계가 비활성일 때 aggregator의 입력 최신성을 확인한다.
- 오래된 analysis 결과를 당일 신규 결과처럼 처리하지 않는다.

### 5.3 Price와 Market Breadth

| 파일 | 역할 |
| --- | --- |
| `pre_price.py` | 가격 feature |
| `pre_marketbreadth.py` | 시장 폭 feature |

- 수정주가, 수익률, 이동평균과 momentum 기준을 확인한다.
- 필요한 lookback 기간을 보존한다.
- 거래 정지와 가격 누락을 동일하게 처리하지 않는다.
- breadth의 universe와 시장 기준을 확인한다.
- 부분 universe만으로 전체 시장 성공을 기록하지 않는다.

### 5.4 Macro · Commodity · Foreign Index

| 파일 | 역할 |
| --- | --- |
| `pre_macroeconomic.py` | 매크로 feature |
| `pre_commodity.py` | 원자재 feature |
| `pre_foreignindex.py` | 해외지수 feature |

- indicator 이름과 source mapping을 유지한다.
- 시차와 timezone을 확인한다.
- 휴장일 forward-fill 여부를 명시한다.
- 빈 raw와 전일 값 유지 정책을 구분한다.
- 일부 지표 누락과 전체 실패를 구분한다.

### 5.5 Flow · Program · Short Sell

| 파일 | 역할 |
| --- | --- |
| `pre_investorflow.py` | 투자자 수급 feature |
| `pre_program.py` | 프로그램 매매 feature |
| `pre_shortsell.py` | 공매도 feature |

- 수량, 금액, 비율과 sign 의미를 유지한다.
- 가격 raw와 결합 기준을 확인한다.
- KRX raw 최신 거래일을 확인한다.
- 0건과 미수집을 구분한다.
- division by zero와 NULL 처리를 숨기지 않는다.

### 5.6 Total Feature

| 파일 | 역할 |
| --- | --- |
| `pre_total_stock_daily_feature.py` | 종목 단위 total feature |
| `pre_total_market_daily_feature.py` | 시장 단위 total feature |

- 하위 feature table의 최신성과 기준일을 확인한다.
- 일부 하위 feature 실패를 NULL로 숨기지 않는다.
- join key와 cardinality를 확인한다.
- 중복 join으로 row 수가 증가하지 않게 한다.
- total score와 weight 변경은 전략 영향 변경으로 취급한다.
- 휴일 helper 실패를 정상 SKIP으로 변환하지 않는다.

## 6. Python 코드 작성 규칙

### 6.1 공통 원칙

- 기존 파일명, 함수명, CLI option, table과 feature 의미를 우선 유지한다.
- module import만으로 DB 연결, 외부 API 호출과 대량 처리가 일어나지 않게 한다.
- entrypoint는 `if __name__ == "__main__":` 경계를 유지한다.
- extract, transform, aggregate와 persist 단계를 가능한 한 구분한다.
- 실패를 성공, `NO_CHANGE` 또는 정상 0건으로 바꾸지 않는다.
- 일회성 데이터 보정을 영구 fallback으로 추가하지 않는다.

### 6.2 함수 계약

- `run()`의 반환값과 예외 의미를 유지한다.
- caller가 반환값을 사용하지 않으면 실패 전파 방식을 확인한다.
- optional 단계와 required 단계를 구분한다.
- 숨은 global state와 import-time side effect를 추가하지 않는다.
- 동일 trade date 재실행 시 결과가 예측 가능해야 한다.

### 6.3 계산 로직

- 계산식 변경 전 현재 feature 정의와 downstream 소비를 확인한다.
- 결측값, 0, 음수와 극단값 처리 의미를 유지한다.
- 소수점, rounding과 데이터 타입을 확인한다.
- rolling window와 minimum period를 확인한다.
- look-ahead bias를 만들지 않는다.
- 미래 날짜 또는 당일 미확정 데이터를 사용하지 않는다.

### 6.4 Persist

- 기존 unique key와 conflict/upsert 정책을 유지한다.
- trade date, ticker, feature version과 source 의미를 확인한다.
- transaction과 rollback 경계를 유지한다.
- delete 후 insert는 대상 일자와 범위를 확인한다.
- 부분 적재 후 성공 marker를 출력하지 않는다.
- 대량 적재는 batch size와 commit 단위를 확인한다.

## 7. Database 기준

### 7.1 연결

| 항목 | 값 |
| --- | --- |
| Database | `portfolio` |
| Config loader | `db_config.py`의 `get_db_config()` |
| 환경변수 | `INTEREST_DB_*` |
| Password | 기본값 없음 |
| search path | `preprocessor, interest, reference, legacy, public` |

실제 운영 환경에서는 Preprocessor 전용 DB user를 사용한다.

`postgres` 기본값이 코드나 과거 문서에 있더라도 운영 권한 기준으로 해석하지 않는다.

### 7.2 Schema 책임

| Schema | 역할 |
| --- | --- |
| `preprocessor` | 분석 · 집계 feature |
| `interest` | Crawler raw · history |
| `reference` | ticker · universe · 기준정보 |
| `legacy` | 과거 호환 |
| `public` | fallback search path |

Preprocessor는 `research`, `decision`, `execution`의 결과를 직접 생성하지 않는다.

### 7.3 SQL과 Upsert

- 신규 SQL은 가능한 한 schema-qualified 이름을 사용한다.
- 기존 unqualified SQL은 connection `search_path`와 정합성을 확인한다.
- SQL 수정 전 실제 코드, migration 또는 `information_schema.columns`로 컬럼을 확인한다.
- unique key와 `ON CONFLICT` 의미를 확인한다.
- aggregation SQL의 group key와 join cardinality를 확인한다.
- delete 범위와 재생성 범위를 확인한다.
- 실패한 DB 작업 뒤 SUCCESS를 출력하지 않는다.

### 7.4 최신성과 일자

- 입력 raw와 출력 feature의 trade date를 함께 확인한다.
- 각 하위 feature의 최신일이 total feature 기준일과 일치해야 한다.
- 휴일, 주말과 원천 미공개를 구분한다.
- 과거 최신 row를 당일 row처럼 복사하지 않는다.
- timezone은 Asia/Seoul 기준을 우선한다.

## 8. Holiday API 기준

`interest_get_holidays.py` 또는 이를 참조하는 단계는 외부 holiday API를 호출할 수 있다.

- timeout을 명시한다.
- HTTP 실패를 정상 영업일로 해석하지 않는다.
- 주말과 공휴일을 구분한다.
- API 실패를 정상 SKIP으로 숨기지 않는다.
- test에서는 HTTP mock을 사용한다.
- 문서 작업 중 실제 API를 호출하지 않는다.

## 9. 설정과 민감정보

### 9.1 민감정보

아래 값은 코드, 문서, 예시와 로그에 원문으로 기록하지 않는다.

- DB password와 전체 connection string
- API key · token
- 실제 DB host와 private IP
- AWS account-id
- 실제 ARN
- ECR image URI
- subnet · security group id
- command id
- local absolute path
- Slack webhook URL

필요한 경우 아래 placeholder를 사용한다.

| Placeholder | 용도 |
| --- | --- |
| `[REDACTED]` | 일반 민감정보 |
| `[REDACTED_DB_HOST]` | DB host |
| `[REDACTED_ARN]` | ARN |
| `[REDACTED_COMMAND_ID]` | command id |
| `<PREPROCESSOR_ECS_TASK>` | ECS task |
| `<ECR_IMAGE_URI>` | ECR image |
| `<TASK_DEFINITION_ARN>` | task definition |
| `<DB_HOST>` | DB host |

### 9.2 설정 변경

설정 key나 loader를 변경하면 아래를 함께 확인한다.

1. `db_config.py`
2. 해당 `pre_*.py`
3. `pre_daily.py`
4. README
5. ECS · container 환경변수
6. downstream feature consumer
7. 테스트 fixture

실제 local config와 credential 값을 읽어 문서에 옮기지 않는다.

## 10. AWS 운영 기준

Preprocessor는 AWS Paper Daily Step 3에서 container 또는 ECS RunTask 실행 대상으로 호출될 수 있다.

| 항목 | 책임 |
| --- | --- |
| Preprocessor | feature 처리 entrypoint |
| ECS · Container | 실행 환경 |
| Step Functions | Daily orchestration |
| Scheduler | 실행 시각 |
| Crawler | raw 입력 |
| Strategy | feature 소비 |

실제 cluster, task definition ARN, image URI와 network 설정은 외부 운영 사실이다.

사용자가 명시적으로 요청하지 않는 한 AWS API를 호출하거나 리소스를 변경하지 않는다.

운영 명령 작성 시 실제 ARN, account-id, subnet, security group과 command id를 문서에 남기지 않는다.

## 11. 실행 제한

사용자가 명시적으로 요청하지 않는 한 아래 작업을 수행하지 않는다.

| 구분 | 금지 작업 |
| --- | --- |
| Preprocessor | `pre_daily.py` · 개별 `pre_*.py` 실행 |
| Database | DDL · DML · migration · psql |
| Network | holiday API 호출 |
| Crawler | 외부 데이터 수집 실행 |
| Model | 다운로드 · 학습 · 추론 |
| AWS | ECS · SSM · Scheduler 실행 또는 변경 |
| Slack | webhook 또는 notifier 호출 |
| Git | add · commit · push · reset · restore |

읽기 전용 검증도 사용자의 요청 범위에서만 수행한다.

## 12. 테스트와 검증

### 12.1 기본 원칙

- 실제 DB와 외부 API 없이 가능한 unit test를 우선한다.
- DB connection, holiday HTTP와 filesystem을 mock 또는 stub으로 격리한다.
- 실제 credential과 운영 환경변수를 테스트에 사용하지 않는다.
- 대량 feature 전체 재생성을 일반 test로 실행하지 않는다.
- 작은 fixture와 제한된 trade date를 사용한다.

### 12.2 변경별 최소 검증

| 변경 대상 | 최소 검증 |
| --- | --- |
| Python 문법 | 안전한 compile check |
| 순수 계산 | 고정 입력 fixture |
| News mapping | alias · keyword fixture |
| Aggregator | group key · duplicate test |
| Rolling feature | lookback · boundary test |
| Total feature | join cardinality · missing input |
| Holiday | HTTP mock · 주말 · 공휴일 |
| Daily orchestration | 호출 순서 · 예외 전파 mock |
| Repository | SQL · parameter · upsert test |
| 문서 | 링크 · 사실 · 가독성 |

실행 위험 import가 있는 파일은 compile 과정에서도 side effect 여부를 먼저 확인한다.

실행하지 못한 검증은 완료로 기록하지 않고 사유를 남긴다.

## 13. 문서 관리 규칙

### 13.1 README.md

README는 port-interest-preprocessor의 현재 구조와 운영 AS-IS를 설명한다.

README에 포함할 내용:

- 프로젝트 역할
- raw→feature 데이터 흐름
- 주요 feature 영역
- Daily Step 3 순서
- 주석 처리 단계
- DB와 schema
- holiday API
- AWS 운영 경계
- 설정과 보안
- 실행 제한
- 상세 문서 링크

다른 MS와 Step Functions 전체 정의를 장문으로 복사하지 않는다.

### 13.2 CHANGELOG.md

CHANGELOG는 port-interest-preprocessor 코드와 문서의 주요 변경만 기록한다.

- 최신 날짜를 상단에 추가한다.
- `Added`, `Changed`, `Fixed`, `Removed`, `Security`를 필요에 따라 사용한다.
- 실제 Preprocessor 변경만 기록한다.
- 일회성 command id, raw log와 DB row 결과를 기록하지 않는다.
- 신규 섹션부터 2컬럼 표 중심으로 작성한다.
- 과거 이력은 별도 요청이 없으면 원본을 유지한다.

### 13.3 docs

새 문서를 만들기 전에 README, CHANGELOG와 기존 docs에 흡수 가능한지 먼저 확인한다.

날짜별 `docs/worklog/*.md`는 신규 생성하지 않는다.

코드와 문서 변경 이력은 `CHANGELOG.md`에 기록한다.

### 13.4 source-file-catalog.md 자동 갱신

`docs/source-file-catalog.md`가 존재하는 경우 아래 변경이 발생하면 같은 작업에서 갱신 여부를 반드시 확인한다.

| 변경 | 처리 |
| --- | --- |
| 주요 Python 파일 생성 · 삭제 · 이름 변경 | 카탈로그 갱신 |
| `pre_daily.py` 호출 순서 변경 | orchestration 갱신 |
| Feature 책임 변경 | 역할과 입출력 갱신 |
| 주석 처리 단계 변경 | 현재 활성 상태 갱신 |
| DB loader · schema 역할 변경 | Database 항목 갱신 |
| Holiday helper 역할 변경 | 외부 의존성 갱신 |
| scripts · ECS wrapper 변경 | 운영 항목 갱신 |
| 문서 생성 · 삭제 · 역할 변경 | Documents 항목 갱신 |
| 내부 구현만 변경 · 책임 동일 | 생략 가능 |

카탈로그는 전체 파일 inventory가 아니다.

운영과 유지보수에 의미 있는 entrypoint, feature 묶음과 책임만 기록한다.

## 14. Git 규칙

기본적으로 읽기 전용 상태 확인만 허용한다.

| 허용 | 금지 |
| --- | --- |
| `git status --short`<br>`git diff --stat`<br>`git diff --check` | `git add`<br>`git commit`<br>`git push`<br>`git reset`<br>`git restore`<br>`git checkout`<br>`git stash` |

사용자가 명시적으로 요청하지 않는 한 commit을 생성하지 않는다.

## 15. 완료 보고

작업 완료 시 아래만 짧게 보고한다.

| 항목 | 내용 |
| --- | --- |
| 변경 파일 | 실제 수정한 파일 |
| 핵심 변경 | 기능 또는 문서 변경 요약 |
| 데이터 계약 | raw · feature · downstream 영향 |
| 실행 위험 | 실행하지 않은 DB · API · AWS 경로 |
| 검증 | 수행한 정적 검사와 test |
| 미수행 | 실행하지 못한 검증 |
| 보안 | 민감정보 원문 기록 여부 |
| 후속 | 실제로 남은 항목만 기록 |

운영자가 수행한 작업과 Kiro가 수행한 작업을 구분한다.

## 16. 완료 체크리스트

- [ ] 요청된 port-interest-preprocessor 파일만 수정했는가?
- [ ] 다른 MS와 `.kiro` 파일을 불필요하게 수정하지 않았는가?
- [ ] 최우선 문서 가독성 규칙을 적용했는가?
- [ ] 신규 독립 표를 기본 2컬럼으로 작성했는가?
- [ ] 긴 셀과 긴 라인을 만들지 않았는가?
- [ ] raw→feature 데이터 계약을 유지했는가?
- [ ] Daily Step 3 호출 순서를 확인했는가?
- [ ] 주석 처리된 단계를 실행 중으로 오해하지 않았는가?
- [ ] analysis와 aggregator 의존성을 확인했는가?
- [ ] total feature 전에 하위 feature 최신성을 확인했는가?
- [ ] 부분 실패 뒤 후속 단계를 성공 처리하지 않았는가?
- [ ] DB unique key · upsert · transaction 정합을 확인했는가?
- [ ] trade date와 timezone 정합을 확인했는가?
- [ ] look-ahead bias를 만들지 않았는가?
- [ ] Holiday API 실패를 정상 영업일로 처리하지 않았는가?
- [ ] 민감정보 원문을 기록하지 않았는가?
- [ ] 변경 범위에 맞는 안전한 검증을 수행했는가?
- [ ] 파일 구조나 책임이 바뀌면 `docs/source-file-catalog.md`를 확인했는가?
- [ ] 날짜별 `docs/worklog/*.md`를 새로 만들지 않았는가?
- [ ] UTF-8 No BOM으로 저장했는가?
- [ ] 실제 수정 내용만 README와 CHANGELOG에 반영했는가?
