# Source File Catalog

A document for quickly checking the roles of the primary files and directories of port-interest-preprocessor.

It is not an inventory listing every file; it records only the items needed to understand the raw→feature structure and to judge change impact.

It uses paths relative to the repository root and excludes cache, build results, credentials, dumps, and one-time artifacts.

## Usage Principles

| Item | Value |
| --- | --- |
| Basis | Current Preprocessor code and Daily Step 3 structure |
| Included | Primary entrypoints · feature groups · common helpers |
| Excluded | cache · credential · debug · output dump |
| Update | When a file path · responsibility · call order changes |
| Omit | When only internal implementation changes and the responsibility is unchanged |
| Sensitive information | No verbatim credential · host · ARN · command id |

## Root and Common Files

| File | Role |
| --- | --- |
| `AGENTS.md` | Preprocessor code and documentation working rules |
| `README.md` | Current structure · data flow · operational AS-IS |
| `CHANGELOG.md` | Primary change history |
| `db_config.py` | PostgreSQL loader · Production/Shadow run mode · search_path routing |
| `interest_get_holidays.py` | Weekend · Market Holiday check |

### Check When Changing

| Target | Check |
| --- | --- |
| `AGENTS.md` | raw→feature · Step 3 · calculation safety rules |
| `README.md` | Current structure · responsibility boundary · execution risk |
| `CHANGELOG.md` | Record only actual Preprocessor changes |
| `db_config.py` | `INTEREST_DB_*` · `PREPROCESSOR_RUN_MODE` · Production/Shadow search_path |
| Holiday helper | API failure · weekend · Market Holiday · cache |

## Daily Step 3 Orchestration

| File | Role |
| --- | --- |
| `pre_daily.py` | Daily entrypoint that calls each `run()` in sequence |

### Current Stage Composition

| Order | Stage |
| --- | --- |
| 1 | `pre_news_analysis.run()` |
| 2 | `pre_news_event_detection.run()` |
| 3 | `pre_news_daily_aggregator.run()` |
| 4 | `pre_agency_analysis.run()` · commented out · not executed |
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

The actual call order in the code takes precedence.

### Current Commented-out Stage

| Item | Value |
| --- | --- |
| Stage | `pre_agency_analysis.run()` |
| State | Commented out in `pre_daily.py` |
| Automatic execution | Excluded |
| Follow-up risk | Agency aggregator input freshness |
| Activation | A separate functional change |

Do not record a commented-out stage as if it were a running stage.

### Check When Changing

| Item | Value |
| --- | --- |
| Prior input | Existence of raw · analysis · feature |
| Call order | aggregator and total dependency |
| Exception | required stage failure propagation |
| Return value | caller's success determination |
| Total | Subordinate feature success and freshness |
| Re-run | Same trade date idempotency |

Do not change the stage order for documentation-cleanup purposes.

## News Feature

| File | Role |
| --- | --- |
| `pre_news_analysis.py` | News-stock mapping · sentiment · keyword |
| `pre_news_event_detection.py` | event master-based news event |
| `pre_news_daily_aggregator.py` | Stock- and date-level news aggregation |

### I/O and Impact

| Item | Value |
| --- | --- |
| Input | News raw · ticker alias · event basis |
| Intermediate result | News analysis · News event |
| Output | News daily feature |
| Prior relationship | Analysis · Event → Aggregator |
| downstream | Total stock feature |

### Check When Changing

| Item | Value |
| --- | --- |
| Alias | ticker mapping semantics |
| Sentiment | lexicon · score · version |
| Event | keyword · direction · sector weight |
| Duplicates | News · event unique key |
| Freshness | Same trade date input |
| Failure | Whether the aggregator runs after a prior failure |

## Agency Feature

| File | Role |
| --- | --- |
| `pre_agency_analysis.py` | Investment opinion · target price analysis |
| `pre_agency_daily_aggregator.py` | Stock- and date-level report aggregation |

### I/O and Impact

| Item | Value |
| --- | --- |
| Aggregation input | `interest_agency_raw` · `interest_price_raw` (LATERAL) |
| Analysis output | `pre_agency_analysis` · currently not executed in Daily |
| Output | `pre_agency_daily_feature` |
| Dependency | Aggregator is independent of analysis output |
| downstream | Total stock feature |

### Check When Changing

| Item | Value |
| --- | --- |
| Opinion | recommendation normalization |
| Target Price | NULL · 0 · upside |
| Freshness | Analysis and aggregator base date |
| Price join | Prior price data |
| Past values | Do not use as if they were new same-day results |

## Price and Market Feature

| File | Role |
| --- | --- |
| `pre_price.py` | Price daily feature |
| `pre_marketbreadth.py` | Market breadth daily feature |

### Check When Changing

| Item | Value |
| --- | --- |
| Price | Return · momentum · moving average |
| Volatility | lookback · minimum period |
| Missing | Distinguish trading halt from missing data |
| Breadth | universe · market basis |
| Date | raw and feature trade date |
| downstream | Total stock · Total market |

Do not record overall market feature success from only a partial universe.

## Macro Group Feature

| File | Role |
| --- | --- |
| `pre_macroeconomic.py` | Macro daily feature |
| `pre_commodity.py` | Commodity daily feature |
| `pre_foreignindex.py` | Foreign index daily feature |

### Check When Changing

| Item | Value |
| --- | --- |
| Mapping | indicator · ticker · source |
| Date | timezone · market time lag |
| Missing | Distinguish empty raw from retained previous day |
| Fill | Market Holiday forward-fill policy |
| Score | clipping · pressure · regime |
| downstream | Total market feature |

Distinguish partial-indicator missing from full failure.

## Flow and Market Structure Feature

| File | Role |
| --- | --- |
| `pre_investorflow.py` | Investor Flow daily feature |
| `pre_program.py` | Program Trading daily feature |
| `pre_shortsell.py` | Short Selling daily feature |

### Check When Changing

| Item | Value |
| --- | --- |
| Value meaning | quantity · amount · ratio · sign |
| Price join | trading value · ratio calculation |
| Date | KRX raw latest Trading Day |
| Empty | Actual zero-record vs. not-yet-collected |
| Calculation | NULL · division by zero |
| downstream | Total stock · Total market |

Treat changes to spike, pressure, and momentum standards as changes to strategy input.

## Total Feature

| File | Role |
| --- | --- |
| `pre_total_stock_daily_feature.py` | Stock-level Total Feature |
| `pre_total_market_daily_feature.py` | Market-level Total Feature |

### Input Relationships

| Output | Primary Input |
| --- | --- |
| Total Stock | Price · Flow · Short Sell · News · Agency |
| Total Market | Breadth · Foreign Index · Macro · Commodity · Program · Market-level Investor Flow |

### Check When Changing

| Item | Value |
| --- | --- |
| Freshness | Base date of all subordinate features |
| Join | key · cardinality |
| Missing | Do not hide a failed input as NULL |
| Weight | score · gating · penalty |
| Duplicate | join-result row increase |
| Holiday | Distinguish helper failure from SKIP |

Changes to total score, weight, and penalty are not simple refactoring.

Verify the impact on downstream Strategy Research and Strategy Decision.

## Raw→Feature Contract

| Stage | Responsibility |
| --- | --- |
| Input | `interest` raw/history |
| Processing | `pre_*.py` transform · aggregate |
| Output | `preprocessor` feature |
| Reference | `reference` · `legacy` |
| Consume | Strategy Research · Strategy Decision |

### Preservation Standards

| Item | Value |
| --- | --- |
| Source | Input raw source meaning |
| Ticker | Stock identifier |
| Date | trade date · business date |
| Version | feature calculation version |
| Unique key | Duplicate-prevention contract |
| Upsert | Re-run meaning |
| Downstream | column · score compatibility |

Do not reuse a previous latest feature as if it were a new same-day result.

## Database Contract

| Item | Value |
| --- | --- |
| Database | `portfolio` |
| Config loader | `db_config.py` · `get_db_config()` |
| Environment variables | `INTEREST_DB_*` |
| Password | No default |
| Run mode | `PREPROCESSOR_RUN_MODE` · default `PRODUCTION` |
| Production search path | `preprocessor, interest, reference, legacy, public` |
| Shadow search path | `preprocessor_shadow, preprocessor, interest, reference, legacy, public` |

### Schema Responsibilities

| Schema | Role |
| --- | --- |
| `preprocessor` | Production analysis · aggregation feature |
| `preprocessor_shadow` | Candidate Shadow temporary output · cleanup target · not a downstream operational schema |
| `interest` | Crawler raw · history |
| `reference` | ticker · universe · reference data |
| `legacy` | Backward compatibility |
| `public` | fallback search path |

### Check When Changing SQL

| Item | Value |
| --- | --- |
| Table · column | code · migration · DB contract |
| New SQL | schema-qualified whenever possible |
| Existing SQL | connection `search_path` |
| Unique key | `ON CONFLICT` meaning |
| Group key | aggregation unit |
| Join | cardinality · duplicates |
| Delete | target date · ticker · range |
| Transaction | commit · rollback |

Do not print SUCCESS after a failed DB operation.

## Holiday API

| File | Role |
| --- | --- |
| `interest_get_holidays.py` | Nager.Date-based KR · US holiday lookup |
| `pre_total_market_daily_feature.py` | May reference the helper when computing the most recent business day |

### Check When Changing

| Item | Value |
| --- | --- |
| HTTP | timeout · status |
| Country | KR · US |
| Weekend | Distinguish from Market Holiday |
| Cache | In-memory cache |
| Failure | Do not interpret as a normal business day |
| Test | HTTP mock |

Do not call the real API during documentation work and static validation.

## Calculation Safety

| Item | Check |
| --- | --- |
| Lookback | rolling window · minimum period |
| Missing | Distinguish NULL · 0 · negative |
| Outlier | clipping · z-score |
| Type | numeric type · rounding |
| Date | Do not use future data |
| Bias | No look-ahead bias |
| Weight | Verify strategy impact |

Do not use same-day unconfirmed data and future rows in feature calculation.

## External Dependencies

| Item | Role |
| --- | --- |
| Python | Runtime |
| psycopg2 | PostgreSQL |
| psycopg2.extras | Batch · helper |
| Requests | Holiday API |
| PostgreSQL | raw read · feature persistence |

Do not use the real DB and external APIs in documentation validation or unit tests.

## Tests

| Change | Validation |
| --- | --- |
| Python syntax | Safe compile check |
| Pure calculation | Fixed-input fixture |
| News mapping | alias · keyword fixture |
| Event | direction · sector weight |
| Aggregator | group key · duplicate |
| Rolling | lookback · boundary |
| Total | join cardinality · missing input |
| Holiday | HTTP mock · weekend · Market Holiday |
| Daily | call order · exception propagation mock |
| Repository | SQL · parameter · upsert |
| Documentation | links · facts · readability |

When there is an execution-risk import, prioritize a static review of the file body.

## AWS and Operational Wrapper

| Item | Role |
| --- | --- |
| `pre_daily.py` | Step 3 execution entrypoint |
| `Dockerfile` | Container build · default CMD `pre_daily.py` |
| ECS Fargate | Execution environment · RunTask |
| Step Functions | Daily orchestration · `Step3_RunPreprocessor` |
| Scheduler | Execution timing |

## DevOps Wrapper

| File | Role |
| --- | --- |
| `.devops/codebuild/buildspec.yml` | CodeBuild CI gate · Docker image build · conditional ECR Push |
| `.github/workflows/preprocessor-codebuild.yml` | Candidate build → Shadow validation → production approval → Promotion orchestration |
| `.devops/scripts/container-smoke.py` | Container import smoke test · `run()` not called |

### Shadow Control Runner

| File | Role |
| --- | --- |
| `.devops/shadow-control/preprocessor_shadow_control.py` | Prepare · Quality Gate · Cleanup · Verify Cleanup · Evidence |
| `.devops/shadow-control/Dockerfile` | Shadow Control Runner image |
| `.devops/shadow-control/requirements.txt` | boto3 · psycopg2 dependencies |
| `.devops/shadow-control/tests/test_shadow_control.py` | Control Runner pure contract test |

### Check When Changing

| Item | Value |
| --- | --- |
| CI gate | Python Compile · Unit Test · Static Analysis · Container Smoke Test |
| Image | Git SHA-based Tag · ECR Digest pinning |
| Push | Automatic on main push · `workflow_dispatch` input-controlled |
| Authentication | GitHub OIDC · Repository Variable Role ARN |
| Shadow validation | Run the Candidate Task Definition in Shadow · Quality Gate · Cleanup |
| Approval | GitHub `production` Environment manual approval |
| Deployment | Promote the Shadow-tested same Candidate Task Definition to Step 3 |

The repository contains the DevOps wrappers, the Shadow Control Runner, and the `Dockerfile` above; there are no shell · PowerShell · batch wrappers.

The Shadow Control Runner detailed logic consists of Prepare baseline, Quality Gate, Cleanup (CONTINUE IDENTITY), Verify Cleanup (READ_ONLY), and S3 Evidence recording.

The full Shadow State Machine definition, actual ARNs, and S3 Evidence details are within the port-devops repository scope.

Do not determine the actual AWS state from repository files alone.

## Documents

| Document | Role |
| --- | --- |
| `AGENTS.md` | Preprocessor working rules |
| `README.md` | Current structure and operational AS-IS |
| `CHANGELOG.md` | Primary change history |
| `docs/source-file-catalog.md` | Primary files and responsibilities |

Do not create date-specific `docs/worklog/*.md` files.

If past worklogs are retained, treat them only as historical records.

## External Dependency Modules

| Module | Relationship |
| --- | --- |
| `port-interest-crawler` | raw/history input |
| `port_strategy_research` | feature consumption · backtest |
| `port_strategy_decision` | feature consumption · strategy decision |
| `port_strategy_execution` | Follow-up order planning |
| `port-marketconnector` | Order · broker integration |
| `port-view` | Execution state · views |
| Step Functions · Scheduler | Full orchestration |

Do not automatically include other MS internal code and documentation in the Preprocessor change scope.

## Cleanup Candidates

Do not add files outside the currently confirmed operational sources to the catalog.

If the following files are confirmed in the future, do not delete them; mark them only as cleanup candidates.

- test · debug temporary files
- cache · `__pycache__`
- model output dump
- one-time patch
- scripts with unknown usage

Decide separately after confirming actual import, call relationships, and ownership responsibility.

## Catalog Update Conditions

| Change | Handling |
| --- | --- |
| Create · delete · rename a primary Python file | Update |
| Change `pre_daily.py` call order | Update |
| Change feature responsibility · I/O | Update |
| Change commented-out stage | Update |
| Change DB loader · schema role | Update |
| Change Holiday helper role | Update |
| Change scripts · ECS wrapper | Update |
| Create · delete a document or change its role | Update |
| Change only internal implementation · same responsibility | May be omitted |

When updating the catalog, do not recreate the full repository inventory.

Check only the changed area and adjacent items.
