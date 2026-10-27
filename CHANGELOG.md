# CHANGELOG

Records the primary change history of port-interest-preprocessor code and documentation.

## Authoring Principles

| Item | Value |
| --- | --- |
| Scope | Preprocessor code · feature · orchestration · configuration · tests · documentation |
| Excluded scope | Other MS internal implementation · full Step Functions definition · one-time operational logs |
| Ordering | Add the latest date at the top |
| Classification | Added · Changed · Fixed · Removed · Security |
| Execution records | Record only validation actually performed |
| Sensitive information | No verbatim credential · host · ARN · command id |

## 2026-08-10 — Preprocessor Data Shadow and Approval-based Promotion

### Added

| Item | Value |
| --- | --- |
| Run mode | `db_config.py` Production/Shadow run mode |
| Shadow routing | `preprocessor_shadow` search_path contract |
| Shadow Control Runner | `.devops/shadow-control/` Prepare · Quality Gate · Cleanup · Verify Cleanup · Evidence |
| Data Shadow Quality Gate | Candidate execution · Shadow output · Production integrity validation |
| Cleanup / Verify Cleanup | Remove Shadow results · 0 residual · no Production DML |
| Shadow orchestration | Separate Preprocessor Shadow validation State Machine |
| Production approval Gate | GitHub `production` Environment manual approval |
| Deployment pipeline | push-based Candidate → Shadow → Approval → Promotion |

### Changed

| Item | Value |
| --- | --- |
| GitHub Actions | Extended to a main push-based Candidate pipeline |
| Candidate Task Definition | Registered with a digest-pinned image |
| Production activation | Separated to after manual approval |
| OIDC trust context | Extended to main branch CI and `production` Environment promotion |
| Step 3 promotion | Changed to be based on the Shadow-tested same Candidate Artifact |

### Fixed

| Item | Value |
| --- | --- |
| Cleanup dependency | Removed Quality Gate PASS dependency · changed to Prepare Evidence basis |
| Sequence cleanup | Applied CONTINUE IDENTITY instead of RESTART IDENTITY |
| Promotion OIDC | Fixed trust condition for `production` Environment subject mismatch |

### Security

| Item | Result |
| --- | --- |
| Production Schema DML | Prohibited |
| Shadow schema | Physically isolated |
| Authentication | GitHub OIDC · no long-lived AWS Access Key |
| Production activation | Manual approval required |
| Rebuild · reregister after approval | Prohibited |
| Verbatim account · ARN · credential | No new record in documentation |

### Verification

| Item | Result |
| --- | --- |
| Shadow DB routing contract test | Success |
| Shadow Control Runner test | Success |
| Prepare | Success |
| Candidate Shadow ECS execution | Success |
| Quality Gate | PASS |
| Cleanup | PASS |
| Verify Cleanup | PASS (READ_ONLY) |
| Production changed table | 0 |
| Shadow residual | 0 |
| Production Integrity | PASS |
| Shadow E2E | SUCCEEDED |
| GitHub production approval | Success |
| Same Candidate Artifact Promotion | Success |
| FAIL-path forced E2E | Not performed |

## 2026-07-30 — Preprocessor DevOps Implementation

### Added

| Item | Value |
| --- | --- |
| CodeBuild BuildSpec | `.devops/codebuild/buildspec.yml` |
| GitHub Actions workflow | `.github/workflows/preprocessor-codebuild.yml` |
| Container Smoke Test | `.devops/scripts/container-smoke.py` |
| Python Compile validation | CI gate |
| Unit Test | `tests/test_pre_daily_structure.py` |
| Static Analysis | ruff-based CI gate |
| Docker Build | CI gate |
| Optional ECR Push | Controlled by manual-run input |
| GitHub OIDC Role | Preprocessor-dedicated IAM Role |
| Deployment evidence | Based on Git SHA and Image Digest |

### Changed

| Item | Value |
| --- | --- |
| Default branch | GitHub Repository main operation |
| Build integration | GitHub Actions and CodeBuild integration |
| Role passing | OIDC Role passed via Repository Variable |
| ECS Revision | Register a new Task Definition Revision |
| Container Image | Pinned by ECR Digest |
| Step Functions | Switch `Step3_RunPreprocessor` to the new Revision |
| Rollback validation | Validate re-promotion of the new Revision after rolling back to the previous Revision |
| End-to-End | Consistency validation from GitHub SHA to the active Revision |

### Fixed

| Item | Value |
| --- | --- |
| AWS credential provider | Resolved GitHub Actions unset issue |
| Secret · Variable reference | Corrected the mismatch between Repository Secret and Variable references |
| OIDC Role misuse | Corrected misuse of another Repository's dedicated Role |
| Dedicated Role · least privilege | Configured a Preprocessor-dedicated OIDC Role and minimal CodeBuild privileges |
| Trust Policy | Fixed to match the immutable OIDC subject format |

### Security

| Item | Result |
| --- | --- |
| Long-lived AWS Access Key | Not used |
| Authentication | GitHub OIDC used |
| Trust Policy | Repository · branch restricted |
| Privileges | CodeBuild project-level least privilege |
| Verbatim credential · secret | No new record |
| Operational DB DML | Not executed |
| Actual Holiday API call | None |
| Order execution | None |
| ARN · account ID · Digest · Run ID · Build ID | No new record in documentation |
| Actual AWS changes performed | OIDC Role configuration · Task Definition Revision registration · Step Functions reference switch |

### Verification

| Item | Result |
| --- | --- |
| GitHub Actions | Success |
| CodeBuild | Success |
| ECR Image Push | Success |
| ECS Task Definition new Revision | Success |
| Step Functions Revision switch | Success |
| Previous Revision Rollback | Success |
| New Revision re-promotion | Success |
| End-to-End consistency | Success |

## 2026-07-22 — Preprocessor Documentation Standard Reorganization

### Changed

| Item | Value |
| --- | --- |
| `AGENTS.md` | Fully rewritten as Preprocessor-dedicated working rules |
| Top-priority rules | New standalone tables 2-column · local edits · no long cells |
| Data contract | Strengthened `interest` raw → `preprocessor` feature responsibility |
| Daily Step 3 | Organized `pre_daily.py` call order and stage dependencies |
| Agency stage | Clarified the commented-out state of `pre_agency_analysis.run()` |
| Partial failure | Added the standard prohibiting Total Feature progression after a mid-stage failure |
| Feature standards | Distinguished News · Agency · Price · Macro · Flow · Total |
| Calculation safety | Prohibited look-ahead bias · rolling window · unconfirmed data |
| DB standards | Strengthened unique key · upsert · delete range · transaction |
| Holiday API | Added the standard not to hide a failure as a normal business day or SKIP |
| Test standards | Organized around DB · HTTP mock and join cardinality validation |
| `README.md` | Fully restructured around current state · data flow · execution risk |
| Documentation system | Organized around README · CHANGELOG · source catalog |
| Worklog policy | Stopped creating date-specific worklogs and consolidated into the CHANGELOG |
| `docs/source-file-catalog.md` | Restructured the 5-column long-form list into a 2-column structure centered on feature responsibility · data contract · change impact |
| Daily Step 3 table | Marked stage 4 `pre_agency_analysis.run()` as commented out · not executed and unified the table title to stage composition |
| Agency aggregation | Reflected that `pre_agency_daily_aggregator` reads `interest_agency_raw` directly and is independent of analysis output |
| DB environment variables | Removed the code-unused `PORTFOLIO_DB_NAME` from the README configuration table |
| Total Market input | Specified `Market Flow` as Market-level Investor Flow |
| Operational wrapper | Added `Dockerfile` to the source catalog operational wrapper items |

### Security

| Item | Result |
| --- | --- |
| Python code changes | None |
| `pre_daily.py` · individual `pre_*.py` execution | 0 |
| DB · Holiday API execution | 0 |
| Crawler · Model · AWS · Slack execution | 0 |
| Git write commands | 0 |
| New verbatim sensitive-info records | 0 |

## 2026-07-01 — AWS Step 3 and Responsibility Boundary Documentation

### Added

| Item | Value |
| --- | --- |
| AWS operational structure | Daily Step 3 preprocessing execution unit |
| Execution candidate | ECS RunTask · container |
| Responsibility boundary | Separated from collection · strategy · order · View |
| Data flow | Crawler raw → Preprocessor feature → Strategy |
| Daily order | `pre_daily.py` current call order |
| Agency state | `pre_agency_analysis.run()` commented out |
| Source catalog | Execution-risk summary |
| Worklog | `docs/worklog/2026-07-01.md` |

### Changed

| Item | Value |
| --- | --- |
| `pre_daily.py` documentation | Reflected the inactive state of Agency analysis |
| Source catalog | Reflected Step 3 execution candidates and cautions |

### Security

| Item | Result |
| --- | --- |
| Python · SQL changes | None |
| Preprocessing · API · DB execution | 0 |
| Model · Crawler · order execution | 0 |
| AWS · Slack execution | 0 |
| New verbatim sensitive-info records | 0 |

## 2026-05-28 — Source Catalog and Module Docstring

### Added

| Item | Value |
| --- | --- |
| `docs/source-file-catalog.md` | Primary file roles and operational cautions |
| Module docstring | Python preprocessing scripts · DB · Holiday helper |
| Worklog | `docs/worklog/2026-05-28.md` |

### Changed

| Item | Value |
| --- | --- |
| README | Reflected documentation · comment cleanup content |
| Documentation structure | Source catalog location guidance |

### Security

| Item | Result |
| --- | --- |
| Functional changes | None |
| SQL · Step order · function signature changes | None |
| DB · API execution | 0 |
| New verbatim sensitive-info records | 0 |

## 2026-05-27 — DB Configuration Externalization

### Added

| Item | Value |
| --- | --- |
| Database | PostgreSQL `portfolio` |
| Schema structure | schema-per-domain |
| search path | `preprocessor, interest, reference, legacy, public` |

### Changed

| Item | Value |
| --- | --- |
| DB loader | `get_db_config()` in `db_config.py` |
| Environment variables | `INTEREST_DB_*` |
| Database name | `portfolio` default |
| SQL compatibility | search path assumption of existing unqualified SQL |

### Security

| Item | Result |
| --- | --- |
| Hardcoded password | Removed from preprocessing scripts |
| Secret management | Environment variables or local-only config |
| Verbatim documentation record | password · token · account · webhook prohibited |

## 2026-05-26 — Initial Documentation and Legacy Cleanup

### Added

| Item | Value |
| --- | --- |
| `AGENTS.md` | Initial Preprocessor working rules |
| `README.md` | Project structure draft |
| Worklog | `docs/worklog/2026-05-26.md` |

### Removed

| Item | Value |
| --- | --- |
| `preprocessor_v1.py` | legacy candidate |
| `interest_pool.py` | legacy candidate |
| `pre_total_daily_feature.py` | legacy total feature |
| `test_pre_news_analysis.py` | removed test candidate |
| `__pycache__/` | cache artifact |

### Changed

| Item | Value |
| --- | --- |
| README structure | Reflected deleted files and legacy dependency cleanup |
| Documentation basis | Static review of current files and import · entrypoint |

### Security

| Item | Result |
| --- | --- |
| Preprocessing · API · DB execution | 0 |
| Crawler · order execution | 0 |
| New verbatim sensitive-info records | 0 |
