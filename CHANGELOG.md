# CHANGELOG

port-interest-preprocessor 코드와 문서의 주요 변경 이력을 기록한다.

## 작성 원칙

| 항목 | 값 |
| --- | --- |
| 기록 범위 | Preprocessor 코드 · feature · orchestration · 설정 · 테스트 · 문서 |
| 제외 범위 | 다른 MS 내부 구현 · 전체 Step Functions 정의 · 일회성 운영 로그 |
| 정렬 | 최신 날짜를 상단에 추가 |
| 분류 | Added · Changed · Fixed · Removed · Security |
| 실행 기록 | 실제 수행한 검증만 기록 |
| 민감정보 | credential · host · ARN · command id 원문 금지 |

## 2026-07-30 — Preprocessor DevOps 구현

### Added

| 항목 | 값 |
| --- | --- |
| CodeBuild BuildSpec | `.devops/codebuild/buildspec.yml` |
| GitHub Actions workflow | `.github/workflows/preprocessor-codebuild.yml` |
| Container Smoke Test | `.devops/scripts/container-smoke.py` |
| Python Compile 검증 | CI gate |
| Unit Test | `tests/test_pre_daily_structure.py` |
| Static Analysis | ruff 기반 CI gate |
| Docker Build | CI gate |
| 선택적 ECR Push | 수동 실행 입력 제어 |
| GitHub OIDC Role | Preprocessor 전용 IAM Role |
| 배포 증적 | Git SHA와 Image Digest 기반 |

### Changed

| 항목 | 값 |
| --- | --- |
| 기본 브랜치 | GitHub Repository main 운영 |
| Build 연계 | GitHub Actions와 CodeBuild 연계 |
| Role 전달 | Repository Variable을 통한 OIDC Role 전달 |
| ECS Revision | 신규 Task Definition Revision 등록 |
| Container Image | ECR Digest로 고정 |
| Step Functions | `Step3_RunPreprocessor`를 신규 Revision으로 전환 |
| Rollback 검증 | 이전 Revision Rollback 후 신규 Revision 재승격 검증 |
| End-to-End | GitHub SHA부터 활성 Revision까지 정합성 검증 |

### Fixed

| 항목 | 값 |
| --- | --- |
| AWS credential provider | GitHub Actions 미설정 문제 해결 |
| Secret · Variable 참조 | Repository Secret과 Variable 참조 방식 불일치 정정 |
| OIDC Role 오사용 | 다른 Repository 전용 Role 오사용 정정 |
| 전용 Role · 최소 권한 | Preprocessor 전용 OIDC Role과 최소 CodeBuild 권한 구성 |
| Trust Policy | immutable OIDC subject 형식에 맞춰 수정 |

### Security

| 항목 | 결과 |
| --- | --- |
| 장기 AWS Access Key | 사용 없음 |
| 인증 | GitHub OIDC 사용 |
| Trust Policy | Repository · branch 제한 |
| 권한 | CodeBuild 프로젝트 단위 최소 권한 |
| credential · secret 원문 | 신규 기록 없음 |
| 운영 DB DML | 실행 없음 |
| 실제 Holiday API 호출 | 없음 |
| 주문 실행 | 없음 |
| ARN · account ID · Digest · Run ID · Build ID | 문서 신규 기록 없음 |
| 실제 수행한 AWS 변경 | OIDC Role 구성 · Task Definition Revision 등록 · Step Functions 참조 전환 |

### Verification

| 항목 | 결과 |
| --- | --- |
| GitHub Actions | 성공 |
| CodeBuild | 성공 |
| ECR Image Push | 성공 |
| ECS Task Definition 신규 Revision | 성공 |
| Step Functions Revision 전환 | 성공 |
| 이전 Revision Rollback | 성공 |
| 신규 Revision 재승격 | 성공 |
| End-to-End 정합성 | 성공 |

## 2026-07-22 — Preprocessor 문서 기준 재정비

### Changed

| 항목 | 값 |
| --- | --- |
| `AGENTS.md` | Preprocessor 전용 작업 규칙으로 전면 재작성 |
| 최우선 규칙 | 신규 독립 표 2컬럼 · 국소 수정 · 긴 셀 금지 |
| 데이터 계약 | `interest` raw → `preprocessor` feature 책임 강화 |
| Daily Step 3 | `pre_daily.py` 호출 순서와 단계 의존성 정리 |
| Agency 단계 | `pre_agency_analysis.run()` 주석 처리 상태 명확화 |
| 부분 실패 | 중간 실패 뒤 total feature 진행 금지 기준 추가 |
| Feature 기준 | News · Agency · Price · Macro · Flow · Total 구분 |
| 계산 안전 | look-ahead bias · rolling window · 미확정 데이터 금지 |
| DB 기준 | unique key · upsert · delete 범위 · transaction 강화 |
| Holiday API | 장애를 정상 영업일 또는 SKIP으로 숨기지 않는 기준 추가 |
| 테스트 기준 | DB · HTTP mock과 join cardinality 검증 중심으로 정리 |
| `README.md` | 현재 상태 · 데이터 흐름 · 실행 위험 중심으로 전면 재구성 |
| 문서 체계 | README · CHANGELOG · source catalog 중심으로 정리 |
| Worklog 정책 | 날짜별 worklog 신규 생성을 중단하고 CHANGELOG로 통합 |
| `docs/source-file-catalog.md` | 5열 장문 목록을 feature 책임 · 데이터 계약 · 변경 영향 중심의 2열 구조로 재구성 |
| Daily Step 3 표 | 4번 `pre_agency_analysis.run()`을 주석 처리 · 미실행로 명시하고 표 제목을 단계 구성으로 통일 |
| Agency 집계 | `pre_agency_daily_aggregator`가 `interest_agency_raw`를 직접 읽어 analysis 산출에 비의존함을 반영 |
| DB 환경변수 | 코드 미사용 `PORTFOLIO_DB_NAME`을 README 설정 표에서 제거 |
| Total Market 입력 | `Market Flow`를 Market-level Investor Flow로 구체화 |
| 운영 wrapper | `Dockerfile`을 source catalog 운영 wrapper 항목에 추가 |

### Security

| 항목 | 결과 |
| --- | --- |
| Python 코드 변경 | 없음 |
| `pre_daily.py` · 개별 `pre_*.py` 실행 | 0건 |
| DB · Holiday API 실행 | 0건 |
| Crawler · Model · AWS · Slack 실행 | 0건 |
| Git write 명령 | 0건 |
| 민감정보 원문 신규 기록 | 0건 |

## 2026-07-01 — AWS Step 3와 책임 경계 문서화

### Added

| 항목 | 값 |
| --- | --- |
| AWS 운영 구조 | Daily Step 3 전처리 실행 단위 |
| 실행 후보 | ECS RunTask · container |
| 책임 경계 | 수집 · 전략 · 주문 · View와 분리 |
| 데이터 흐름 | Crawler raw → Preprocessor feature → Strategy |
| Daily 순서 | `pre_daily.py` 현재 호출 순서 |
| Agency 상태 | `pre_agency_analysis.run()` 주석 처리 |
| Source catalog | 실행 위험 요약 |
| Worklog | `docs/worklog/2026-07-01.md` |

### Changed

| 항목 | 값 |
| --- | --- |
| `pre_daily.py` 문서 | Agency analysis 비활성 상태 반영 |
| Source catalog | Step 3 실행 후보와 주의사항 반영 |

### Security

| 항목 | 결과 |
| --- | --- |
| Python · SQL 변경 | 없음 |
| 전처리 · API · DB 실행 | 0건 |
| Model · Crawler · 주문 실행 | 0건 |
| AWS · Slack 실행 | 0건 |
| 민감정보 원문 신규 기록 | 0건 |

## 2026-05-28 — Source Catalog와 Module Docstring

### Added

| 항목 | 값 |
| --- | --- |
| `docs/source-file-catalog.md` | 주요 파일 역할과 운영 주의사항 |
| Module docstring | Python 전처리 script · DB · Holiday helper |
| Worklog | `docs/worklog/2026-05-28.md` |

### Changed

| 항목 | 값 |
| --- | --- |
| README | 문서화 · 주석 정리 내용 반영 |
| 문서 구조 | Source catalog 위치 안내 |

### Security

| 항목 | 결과 |
| --- | --- |
| 기능 변경 | 없음 |
| SQL · Step 순서 · 함수 시그니처 변경 | 없음 |
| DB · API 실행 | 0건 |
| 민감정보 원문 신규 기록 | 0건 |

## 2026-05-27 — DB 설정 외부화

### Added

| 항목 | 값 |
| --- | --- |
| Database | PostgreSQL `portfolio` |
| Schema 구조 | schema-per-domain |
| search path | `preprocessor, interest, reference, legacy, public` |

### Changed

| 항목 | 값 |
| --- | --- |
| DB loader | `db_config.py`의 `get_db_config()` |
| 환경변수 | `INTEREST_DB_*` |
| Database name | `portfolio` 기본값 |
| SQL 호환 | 기존 unqualified SQL의 search path 전제 |

### Security

| 항목 | 결과 |
| --- | --- |
| Hardcoded password | 전처리 script에서 제거 |
| Secret 관리 | 환경변수 또는 local-only config |
| 문서 원문 기록 | password · token · account · webhook 금지 |

## 2026-05-26 — 초기 문서와 Legacy 정리

### Added

| 항목 | 값 |
| --- | --- |
| `AGENTS.md` | 초기 Preprocessor 작업 규칙 |
| `README.md` | 프로젝트 구조 초안 |
| Worklog | `docs/worklog/2026-05-26.md` |

### Removed

| 항목 | 값 |
| --- | --- |
| `preprocessor_v1.py` | legacy 후보 |
| `interest_pool.py` | legacy 후보 |
| `pre_total_daily_feature.py` | legacy total feature |
| `test_pre_news_analysis.py` | 제거된 test 후보 |
| `__pycache__/` | cache 산출물 |

### Changed

| 항목 | 값 |
| --- | --- |
| README 구조 | 삭제 파일과 legacy 의존성 정리 반영 |
| 문서 기준 | 현재 파일과 import · entrypoint 정적 확인 |

### Security

| 항목 | 결과 |
| --- | --- |
| 전처리 · API · DB 실행 | 0건 |
| Crawler · 주문 실행 | 0건 |
| 민감정보 원문 신규 기록 | 0건 |
