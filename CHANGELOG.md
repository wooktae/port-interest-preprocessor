# CHANGELOG

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
