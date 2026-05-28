# 소스 파일 카탈로그

이 문서는 `port-interest-preprocessor` 루트 기준 주요 소스/문서 파일의 역할과 운영 주의사항을 정리한다. build 결과물, cache, `__pycache__`, IDE 임시 파일은 제외한다.

## 운영 전처리 및 orchestration 후보

| 파일 경로 | 한글 제목 | 파일 내용 | 주요 역할 | 수정/운영 시 주의사항 |
|---|---|---|---|---|
| `pre_daily.py` | 일일 전처리 오케스트레이션 | 뉴스, 증권사, 시장/가격, 수급, total feature 전처리를 순서대로 호출한다. | 개별 `run()` entrypoint를 묶는 일일 배치 후보 스크립트다. | 실행 시 여러 DB upsert와 휴일 API helper 호출 가능성이 있으므로 운영 DB/일자 범위 확인 후 실행한다. 기존 호출 순서를 변경하지 않는다. |
| `db_config.py` | 공통 DB 연결 설정 | PostgreSQL 연결 파라미터와 schema search_path를 환경변수 기반으로 구성한다. | 모든 전처리 스크립트의 DB 접속 설정 단일화 지점이다. | `INTEREST_DB_PASSWORD`는 필수 환경변수이며 문서/로그에 실제 값을 기록하지 않는다. |

## 뉴스 전처리 후보

| 파일 경로 | 한글 제목 | 파일 내용 | 주요 역할 | 수정/운영 시 주의사항 |
|---|---|---|---|---|
| `pre_news_analysis.py` | 뉴스 종목/감성 분석 | 뉴스 제목에서 종목 alias, 키워드, 감성 점수를 계산한다. | `interest_news_raw`, `stock_universe`를 읽어 `pre_news_analysis`를 생성/갱신한다. | 감성 사전, 제외어, alias 규칙 변경은 feature 의미를 바꾸므로 별도 검증이 필요하다. |
| `pre_news_event_detection.py` | 뉴스 이벤트 탐지 | 이벤트 master/keyword/sector weight 기준으로 뉴스 이벤트와 방향성을 탐지한다. | `pre_event_*` 기준 테이블과 raw news를 결합해 `pre_news_event`를 upsert한다. | 이벤트 방향성 override와 sector weight는 downstream market/stock feature에 영향을 준다. |
| `pre_news_daily_aggregator.py` | 뉴스 일별 집계 | 뉴스 감성, 이벤트, 키워드, freshness 지표를 종목/일자 단위로 집계한다. | `pre_news_daily_feature` 생성/갱신 담당이다. | `pre_news_analysis`, `pre_news_event` 선행 생성이 필요하다. |

## 증권사 리포트 전처리 후보

| 파일 경로 | 한글 제목 | 파일 내용 | 주요 역할 | 수정/운영 시 주의사항 |
|---|---|---|---|---|
| `pre_agency_analysis.py` | 증권사 리포트 분석 | 원천 리포트의 투자의견을 점수로 정규화하고 목표가 정보를 적재한다. | `interest_agency_raw` 신규 행을 `pre_agency_analysis`로 변환한다. | 추천어 매핑 변경은 recommendation score 의미를 바꾼다. |
| `pre_agency_daily_aggregator.py` | 증권사 일별 집계 | 리포트 수, 추천 점수, 목표가 업사이드 비율을 종목/일자 단위로 계산한다. | `pre_agency_daily_feature` 생성/갱신 담당이다. | 가격 raw와 lateral join을 사용하므로 가격 데이터 선행 적재 여부를 확인한다. |

## 가격/시장 폭 전처리 후보

| 파일 경로 | 한글 제목 | 파일 내용 | 주요 역할 | 수정/운영 시 주의사항 |
|---|---|---|---|---|
| `pre_price.py` | 가격 feature 생성 | 가격 raw에서 수익률, 모멘텀, 이동평균, 변동성, 거래량/캔들 지표를 계산한다. | `pre_price_daily_feature` 생성 담당이다. | total stock feature의 핵심 선행 데이터이므로 컬럼 의미와 unique key를 유지한다. |
| `pre_marketbreadth.py` | 시장 폭 feature 생성 | 상승/하락/보합 수와 거래대금 변화율로 breadth 지표를 만든다. | `pre_marketbreadth_daily_feature` 생성/갱신 담당이다. | total market feature의 기준 일자 집합으로 사용된다. |

## 매크로/원자재/해외지수 전처리 후보

| 파일 경로 | 한글 제목 | 파일 내용 | 주요 역할 | 수정/운영 시 주의사항 |
|---|---|---|---|---|
| `pre_macroeconomic.py` | 매크로 feature 생성 | VIX, 금리, 달러지수, 환율 계열 raw를 압력 점수로 변환한다. | `pre_macroeconomic_daily_feature` 생성/갱신 담당이다. | 현재 `source = 'yfinance'` 조건을 사용한다. source 값 변경은 데이터 범위를 바꾼다. |
| `pre_commodity.py` | 원자재 feature 생성 | WTI, Brent, 금, 은, 구리, 천연가스 수익률과 압력 지표를 계산한다. | `pre_commodity_daily_feature` 생성/갱신 담당이다. | 원자재별 clipping 기준은 feature 의미에 직접 영향을 준다. |
| `pre_foreignindex.py` | 해외지수 feature 생성 | 주요 미국/아시아 지수 수익률로 글로벌 위험 점수와 regime을 계산한다. | `pre_foreignindex_daily_feature` 생성/갱신 담당이다. | index_name 값과 risk regime 기준을 유지한다. |

## 수급/거래 구조 전처리 후보

| 파일 경로 | 한글 제목 | 파일 내용 | 주요 역할 | 수정/운영 시 주의사항 |
|---|---|---|---|---|
| `pre_investorflow.py` | 투자자 수급 feature 생성 | 외국인/기관 순매수, 보유율, 거래대금 가중 수급 지표를 계산한다. | `pre_investorflow_daily_feature` 생성/갱신 담당이다. | 가격 raw와 결합하므로 가격 데이터 누락 시 일부 ratio가 null이 될 수 있다. |
| `pre_program.py` | 프로그램 매매 feature 생성 | 차익/비차익/전체 프로그램 매매 금액을 거래대금 대비 비율과 모멘텀으로 변환한다. | `pre_program_daily_feature` 생성/갱신 담당이다. | 시장 전체 거래대금 집계 기준이 바뀌면 program ratio 의미가 달라진다. |
| `pre_shortsell.py` | 공매도 feature 생성 | 공매도 비율 평균, 모멘텀, z-score, spike flag, pressure score를 계산한다. | `pre_shortsell_daily_feature` 생성/갱신 담당이다. | spike/pressure 기준 변경은 total stock 최종 점수에 영향을 준다. |

## Total feature 전처리 후보

| 파일 경로 | 한글 제목 | 파일 내용 | 주요 역할 | 수정/운영 시 주의사항 |
|---|---|---|---|---|
| `pre_total_market_daily_feature.py` | 시장 total feature 생성 | 시장 폭, 해외지수, 매크로, 원자재, 프로그램, 시장 수급을 결합한다. | `pre_total_market_daily_feature`와 market regime score 생성 담당이다. | 최근 영업일 계산에 `interest_get_holidays.py`를 사용하므로 외부 holiday API 호출 가능성이 있다. |
| `pre_total_stock_daily_feature.py` | 종목 total feature 생성 | 가격, 수급, 공매도, 뉴스, 증권사 feature를 결합해 최종 종목 점수를 계산한다. | `pre_total_stock_daily_feature`와 final score 생성 담당이다. | weight/gating/penalty 상수 변경은 전략 입력값 의미를 바꾸므로 기능 변경으로 취급한다. |

## 보조/외부 연동 후보

| 파일 경로 | 한글 제목 | 파일 내용 | 주요 역할 | 수정/운영 시 주의사항 |
|---|---|---|---|---|
| `interest_get_holidays.py` | 휴일 조회 helper | Nager.Date public holiday API로 KR/US 휴일을 조회하고 메모리 캐시에 저장한다. | total market의 최근 영업일 계산 보조 함수다. | 외부 API 호출이 발생하므로 문서화/정적 검증 중에는 실행하지 않는다. |

## 문서 파일

| 파일 경로 | 한글 제목 | 파일 내용 | 주요 역할 | 수정/운영 시 주의사항 |
|---|---|---|---|---|
| `AGENTS.md` | 작업 규칙 문서 | 프로젝트 범위, 금지 작업, 보안/Git/검증 규칙을 정의한다. | Codex 작업 시 적용할 저장소 운영 지침이다. | 민감정보 값은 기록하지 않고, 루트 밖 파일 수정은 명시 요청이 있을 때만 수행한다. |
| `README.md` | 프로젝트 개요 문서 | 프로젝트 역할, 파일 구조, 실행/설정 방법, 안전 제약을 설명한다. | 신규 작업자와 AWS Migration 정리 작업의 진입 문서다. | 실행 예시는 실제 DB/API 호출 가능성을 함께 안내해야 한다. |
| `CHANGELOG.md` | 변경 이력 문서 | 날짜별 주요 변경사항과 기능 변경 여부를 기록한다. | 문서화, 구조 정리, 보안 관련 변경 추적에 사용한다. | 실제 변경된 내용만 짧게 기록한다. |
| `docs/source-file-catalog.md` | 소스 파일 카탈로그 | 루트 기준 파일별 역할, 책임, 운영 주의사항을 정리한다. | AWS Migration 전 파일 이해와 정리 후보 판단 기준을 제공한다. | unused/legacy 의심 파일은 삭제하지 않고 정리 후보로만 표시한다. |
| `docs/worklog/2026-05-26.md` | 2026-05-26 작업 기록 | 초기 문서화와 legacy/test/cache 정리 작업 내용을 기록한다. | 과거 작업 이력 확인용 문서다. | 기존 들여쓰기와 상태 표기 형식을 유지한다. |
| `docs/worklog/2026-05-27.md` | 2026-05-27 작업 기록 | DB 설정 환경변수화와 schema-per-domain 문서화 작업을 기록한다. | AWS Migration 준비 관련 전일 작업 이력이다. | 실제 DB 접속 정보 값은 기록하지 않는다. |
| `docs/worklog/2026-05-28.md` | 2026-05-28 작업 기록 | 미커밋 변경 확인, 파일 카탈로그, 설명 주석 추가 작업을 기록한다. | 이번 문서화/주석 정리 작업 이력이다. | 기능 변경 없음과 검증 한계를 명시한다. |

## 정리 후보

현재 `rg --files` 기준으로 루트에 남아 있는 운영 소스 외 unused/legacy 의심 파일은 별도로 확인되지 않았다. 향후 test/debug/cache/model output dump 파일이 발견되면 삭제하지 말고 이 문서에 정리 후보로 표시한 뒤 별도 승인 절차를 따른다.
