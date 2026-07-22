# CHANGELOG

## 2026-07-01

### Added

- `README.md`에 AWS 운영 구조 관점 섹션을 추가해 Preprocessor가 AWS Paper Daily Step 3에서 ECS RunTask 또는 컨테이너 실행 대상으로 호출될 수 있음을 명시하고, 실제 cluster/task-definition ARN/image URI/subnet/security group/command id는 원문으로 기록하지 않고 `<PREPROCESSOR_ECS_TASK>` 등 마스킹 표기로만 사용한다는 원칙을 문서화했다.
- `README.md`에 Preprocessor 책임 경계 섹션을 추가해 담당 역할과 직접 책임지지 않는 영역(수집, 판단, 주문, 체결, 백테스트, View, Daily Batch 전체 orchestration)을 분리해 정리했다.
- `README.md`에 데이터 흐름 관점 섹션을 추가해 Crawler → `interest` schema raw → Preprocessor `preprocessor` schema feature → StrategyDecision/StrategyResearch 후속 소비 관계를 Preprocessor 관점에서만 서술했다.
- `README.md`에 Daily Step 3 전처리 흐름 섹션을 추가해 `pre_daily.py`의 현재 소스 기준 호출 순서를 정리하고, `pre_agency_analysis.run()`이 현재 주석 처리되어 실행되지 않는 상태를 명시했다.
- `docs/source-file-catalog.md`에 실행 위험 요약 섹션을 추가해 DB read/upsert 가능 파일, 외부 holiday API 호출 가능 파일, 대량 feature 갱신 가능 파일을 분류했다.
- `docs/worklog/2026-07-01.md`를 생성해 이번 문서 최신화 작업을 계획/완료 형식으로 기록했다.

### Changed

- `docs/source-file-catalog.md`의 `pre_daily.py` 및 `pre_agency_analysis.py` 항목에 현재 `pre_daily.py`에서 `pre_agency_analysis.run()` 호출이 주석 처리되어 있다는 정적 확인 결과를 반영했다.
- `docs/source-file-catalog.md`의 `pre_daily.py` 주의사항에 AWS Paper Daily Step 3에서 ECS RunTask 또는 컨테이너 실행 대상으로 호출될 수 있다는 Preprocessor 관점 설명을 추가했다.

### Notes

- 이번 작업은 문서 최신화만 포함한다. Python 코드, SQL, batch step 순서, 함수 시그니처, DB schema/table/column 이름은 변경하지 않았다.
- View, MarketConnector, Crawler, StrategyExecution, StrategyDecision, StrategyResearch, Scheduler, Step Functions, Lambda 등 다른 MS의 내부 구현 상세와 세부 운영 로그(state machine step, command id, 실행 시간, DB after-check row)는 Preprocessor 문서 범위 밖으로 두고 반영하지 않았다.
- 실제 cluster 이름, task definition ARN, image URI, subnet, security group, command id, DB password, secret ARN, IAM Role ARN, connection string 원문은 문서에 기록하지 않았다.
- 실제 전처리 실행, 외부 API 호출, 모델 다운로드/학습/추론, DB DDL/DML, 크롤링, 주문 실행, backfill, validation job은 수행하지 않았다.

## 2026-05-28

### Added

- `docs/source-file-catalog.md`를 추가해 루트 기준 주요 소스/문서 파일의 역할, 책임, 운영 주의사항을 정리했다.
- Python 전처리 스크립트와 `db_config.py`, `interest_get_holidays.py`에 한글 module docstring을 추가했다.
- `docs/worklog/2026-05-28.md`에 작업 전 git 상태 확인, 파일 카탈로그 작성, 설명 주석 추가, 검증 결과 기록 항목을 추가했다.

### Changed

- `README.md`에 2026-05-28 문서화/주석 정리 내용과 파일 카탈로그 위치를 반영했다.

### Notes

- 작업 전 미커밋 변경사항은 확인되지 않았다.
- 2026-05-27 변경사항은 기존 CHANGELOG와 worklog 기준으로 DB 설정 환경변수화, schema-per-domain/search_path 문서화, 민감정보 제거 작업으로 확인했다.
- 기능 변경 없음. SQL, batch step 순서, 함수 시그니처, DB table/column 이름은 변경하지 않았다.

## 2026-05-27

### Added

- Documented the local PostgreSQL `portfolio` DB and schema-per-domain structure for AWS Migration readiness.
- Documented this module's DB `search_path`: `preprocessor, interest, reference, legacy, public`.

### Changed

- DB connection settings were externalized to `INTEREST_DB_*` environment variables through `db_config.py`.
- Preprocessing scripts now resolve PostgreSQL connection parameters at connection time with `get_db_config()`.
- DB name documentation now treats `portfolio` as the default for `INTEREST_DB_NAME` and compatible `PORTFOLIO_DB_NAME` usage.
- Clarified that existing SQL continues to work through the configured `search_path` after schema-per-domain migration.

### Security

- Removed hardcoded PostgreSQL password values from preprocessing scripts.
- Clarified that passwords, tokens, account numbers, webhook URLs, and other sensitive values must stay in environment variables or local-only config and must not be written into documentation.

## 2026-05-26

### Added

- 초기 프로젝트 문서 초안을 추가했다.
  - `AGENTS.md`
  - `README.md`
  - `docs/worklog/2026-05-26.md`

### Removed

- 사용하지 않는 legacy/test/cache 후보를 정리했다.
  - `preprocessor_v1.py`
  - `interest_pool.py`
  - `pre_total_daily_feature.py`
  - `test_pre_news_analysis.py`
  - `__pycache__/`

### Changed

- 삭제된 파일과 제거된 모델 기반 legacy 의존성에 맞춰 `README.md`의 현재 구조와 외부 의존성 설명을 갱신했다.

### Notes

- 현재 로컬 파일 구조와 스크립트 import/entrypoint 확인 결과를 기준으로 작성했다.
- 실제 전처리 실행, 외부 API 호출, DB DDL/DML, 크롤링, 주문 실행은 수행하지 않았다.
- 민감정보 값은 문서에 기록하지 않았다.
