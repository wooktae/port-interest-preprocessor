# CHANGELOG

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
