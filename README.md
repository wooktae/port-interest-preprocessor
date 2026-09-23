# port-interest-preprocessor

A Python microservice that reads the raw/history data loaded by the Crawler and generates News, Research, Price, Market, Macro, Commodity, Foreign Index, Flow, and market-structure Features.

Processing results are stored in the `preprocessor` schema in PostgreSQL, where Strategy Research and Strategy Decision can consume them as downstream input.

Execution paths in this repository can lead to bulk DB read, delete, insert, and upsert operations, and some stages may call an external holiday API. Static analysis and documentation work are therefore the default.

## Current State

| Item | Value |
| --- | --- |
| Operational nature | AWS Paper Daily Step 3 preprocessing |
| Base structure | Standalone `pre_*.py` scripts |
| Daily orchestration | `pre_daily.py` |
| Input | `interest` raw/history |
| Output | `preprocessor` feature |
| Reference | `reference` · `legacy` |
| downstream | Strategy Research · Strategy Decision |
| External requests | Holiday API possible |
| Database | PostgreSQL `portfolio` |
| Artifact | Docker Image |
| Build | GitHub Actions → CodeBuild |
| Registry | ECR |
| Runtime | ECS Fargate RunTask |
| Operational link | Step Functions `Step3_RunPreprocessor` |
| Run mode | Production default · Shadow validation (`PREPROCESSOR_RUN_MODE`) |
| Deployment pipeline | main push → Candidate build → Data Shadow → approval → Promotion |
| Production activation | Same Candidate Artifact after GitHub production approval |
| Activation method | Fixed Task Definition Revision reference |
| Rollback | Restore the previous Revision |
| Deployment basis | Git SHA Tag + Image Digest |
| Documentation default principle | Static review without DB · API execution |

> Files named `analysis`, `aggregator`, or `feature` can also perform DB writes and bulk recomputation. Do not run them for documentation-validation purposes.

## Technical Stack

| Item | Value |
| --- | --- |
| Language | Python |
| Database Driver | psycopg2 · psycopg2.extras |
| Database | PostgreSQL |
| HTTP | Requests |
| External API | Holiday API |
| Compute | ECS Fargate RunTask |
| Artifact | Docker Image · ECR |
| Build | GitHub Actions → CodeBuild |

## Responsibility Boundary

### In Scope

| Area | Role |
| --- | --- |
| News | Stock mapping · sentiment · keyword · event |
| Agency | Investment opinion · target price analysis |
| Price | Price feature |
| Market Breadth | Market breadth feature |
| Macro | Macro daily feature |
| Commodity | Commodity daily feature |
| Foreign Index | Foreign index daily feature |
| Flow | Investor Flow feature |
| Program | Program Trading feature |
| Short Sell | Short Selling feature |
| Total Stock | Stock-level Total Feature |
| Total Market | Market-level Total Feature |
| Persistence | `preprocessor` schema creation · update |

### Out of Scope

| Item | Actual Responsibility |
| --- | --- |
| External data collection | port-interest-crawler |
| Strategy research · backtest | Strategy Research |
| Strategy decision | Strategy Decision |
| Order planning | Strategy Execution |
| Order submission · fill | port-marketconnector |
| Views | port-view |
| Full Daily orchestration | Step Functions · Scheduler |

Do not duplicate crawling, strategy decision, order creation, or order submission logic inside the Preprocessor.

## Data Flow

| Stage | Handling |
| --- | --- |
| Input | `interest` raw/history loaded by the Crawler |
| Transform | `pre_*.py` analysis · calculation · aggregation |
| Store | `preprocessor` feature |
| Reference | `reference` ticker · universe · reference data |
| Compatibility | `legacy` |
| Consume | Strategy Research · Strategy Decision |

When raw data is empty or lacks freshness, distinguish a normal zero-record result from an input failure.

Do not reuse a previous latest feature as if it were a new same-day result.

## Daily Step 3

`pre_daily.py` is the Daily orchestration candidate that calls each preprocessing `run()` entrypoint in sequence.

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

### Commented-out Stage

Based on the current static source review, `pre_agency_analysis.run()` is commented out in `pre_daily.py` and is not executed.

| Item | Handling |
| --- | --- |
| Current state | Excluded from Daily automatic execution |
| Follow-up stage | Verify input freshness of `pre_agency_daily_aggregator.py` |
| Uncommenting | A separate functional change |
| Documentation | Do not describe it as a running stage |

Do not aggregate stale agency analysis results as if they were new same-day results.

### Partial Failure

| Risk | Handling |
| --- | --- |
| Mid-stage exception | Verify whether the subsequent Total Feature proceeds |
| Unused return value | Verify the exception propagation method |
| Required failure | Do not record it as an overall success |
| Optional stage | Distinguish commented-out from failed |
| Total Feature | Generate only after verifying subordinate feature freshness |

Do not treat a structure that leaves only a SUCCESS marker while a stage has failed as normal.

## Primary Files

### Orchestration and Helper

| File | Role |
| --- | --- |
| `pre_daily.py` | Daily Step 3 orchestration |
| `db_config.py` | PostgreSQL environment-variable loader |
| `interest_get_holidays.py` | Weekend · Market Holiday check |

### News

| File | Role |
| --- | --- |
| `pre_news_analysis.py` | News-stock mapping · sentiment · keyword |
| `pre_news_event_detection.py` | News event detection |
| `pre_news_daily_aggregator.py` | Stock- and date-level news aggregation |

### Agency

| File | Role |
| --- | --- |
| `pre_agency_analysis.py` | Investment opinion · target price analysis |
| `pre_agency_daily_aggregator.py` | Stock- and date-level report aggregation |

### Price and Market

| File | Role |
| --- | --- |
| `pre_price.py` | Price feature |
| `pre_marketbreadth.py` | Market breadth feature |

### Macro Group

| File | Role |
| --- | --- |
| `pre_macroeconomic.py` | Macro feature |
| `pre_commodity.py` | Commodity feature |
| `pre_foreignindex.py` | Foreign index feature |

### Flow and Market Structure

| File | Role |
| --- | --- |
| `pre_investorflow.py` | Investor Flow feature |
| `pre_program.py` | Program Trading feature |
| `pre_shortsell.py` | Short Selling feature |

### Total Feature

| File | Role |
| --- | --- |
| `pre_total_stock_daily_feature.py` | Stock-level Total Feature |
| `pre_total_market_daily_feature.py` | Market-level Total Feature |

For detailed roles, see the [source file catalog](docs/source-file-catalog.md).

## Feature Area Standards

### News

| Item | Standard |
| --- | --- |
| Mapping | Preserve alias · ticker semantics |
| Sentiment | Verify Sentiment Score basis and version |
| Event | master · keyword · sector weight |
| Duplicates | News · event unique key |
| Order | analysis before aggregator |

### Agency

| Item | Standard |
| --- | --- |
| Opinion | Preserve normalization · score |
| Target Price | Distinguish NULL · 0 |
| Analysis | `pre_agency_analysis.run()` commented out in Daily |
| Aggregator | `interest_agency_raw` direct input · independent of analysis output |
| Past values | Do not use as if they were new same-day results |

### Price and Market Breadth

| Item | Standard |
| --- | --- |
| Price | Return · momentum · moving average |
| Lookback | Preserve the required historical period |
| Missing | Distinguish trading halt from missing data |
| Breadth | universe · market basis |
| Success | Do not record overall success from a partial universe |

### Macro · Commodity · Foreign Index

| Item | Standard |
| --- | --- |
| Mapping | Preserve indicator · source |
| Date | Verify timezone · time lag |
| Holiday | Verify forward-fill policy |
| Missing | Distinguish empty raw from retained previous-day value |
| Failure | Distinguish partial-indicator from full failure |

### Flow · Program · Short Sell

| Item | Standard |
| --- | --- |
| Value meaning | quantity · amount · ratio · sign |
| Join | Join basis with price raw |
| Date | KRX raw latest Trading Day |
| Empty | Distinguish an actual zero-record from not-yet-collected |
| Calculation | division by zero · NULL handling |

### Total Feature

| Item | Standard |
| --- | --- |
| Input | Freshness of all subordinate features |
| Base date | Same trade date |
| Join | key · cardinality |
| Missing | Do not hide a failed input as NULL |
| Weight | Verify strategy impact when changed |
| Holiday | Do not convert API failure into a normal SKIP |

## Execution Risk

### Daily

`pre_daily.py` runs multiple preprocessing stages in sequence.

| Risk | Content |
| --- | --- |
| Database | Bulk read · insert · update · upsert |
| Delete | Data deletion possible depending on the regeneration scope |
| Network | Holiday API |
| Failure | Possibility of proceeding after a mid-stage failure |
| Total | Possibility of generating a Total Feature from incomplete input |

### Individual Feature

Each `pre_*.py` can also perform DB writes and bulk recomputation.

The following files in particular have a large change impact.

| File | Risk |
| --- | --- |
| `pre_total_stock_daily_feature.py` | Combines many stock features |
| `pre_total_market_daily_feature.py` | Combines many market features |
| `pre_news_event_detection.py` | Bulk event generation |
| `pre_news_daily_aggregator.py` | News daily aggregation |
| `pre_agency_daily_aggregator.py` | Report daily aggregation |

## Calculation Safety

- Verify the feature definition and downstream consumption before changing a formula.
- Preserve the handling semantics of missing values, 0, negatives, and outliers.
- Verify the rolling window and minimum period.
- Verify rounding and data types.
- Do not use future dates or same-day unconfirmed data.
- Do not create look-ahead bias.
- Do not treat total score and weight changes as simple refactoring.

## Database

### Connection Basis

| Item | Value |
| --- | --- |
| Database | `portfolio` |
| Config loader | `db_config.py` · `get_db_config()` |
| Environment variables | `INTEREST_DB_*` |
| Password | No default |
| Run mode | `PREPROCESSOR_RUN_MODE` · default `PRODUCTION` |
| Production search path | `preprocessor, interest, reference, legacy, public` |
| Shadow search path | `preprocessor_shadow, preprocessor, interest, reference, legacy, public` |

In the operational environment, a dedicated Preprocessor DB user is used.

Do not interpret the `postgres` default in the documentation as an operational-privilege baseline.

Shadow execution is selected with `PREPROCESSOR_RUN_MODE=SHADOW`, and writes are directed to `preprocessor_shadow`.

### Schema Responsibilities

| Schema | Role |
| --- | --- |
| `preprocessor` | Production analysis · aggregation feature |
| `preprocessor_shadow` | Candidate Shadow temporary output · cleanup target |
| `interest` | Crawler raw · history |
| `reference` | ticker · universe · reference data |
| `legacy` | Backward compatibility |
| `public` | fallback search path |

`preprocessor_shadow` is not a downstream operational schema but an isolated output for Candidate validation.

The Preprocessor does not directly produce `research`, `decision`, or `execution` results.

### SQL Basis

- New SQL uses schema-qualified names whenever possible.
- Existing unqualified SQL operates based on the connection `search_path`.
- Preserve the meaning of unique keys and `ON CONFLICT`.
- Verify the group key and join cardinality of aggregations.
- For a delete-then-insert pattern, verify the target date and range.
- Preserve transaction and rollback boundaries.
- Do not print SUCCESS after a partial load.

## Holiday API

`interest_get_holidays.py` or the stages that reference it may call an external holiday API.

| Item | Standard |
| --- | --- |
| HTTP | Verify timeout · status |
| Weekend | Distinguish from Market Holiday |
| Failure | Do not interpret as a normal business day |
| SKIP | Do not hide an API failure as a normal SKIP |
| Test | HTTP mock |

Do not call the real API during documentation work and static analysis.

## Configuration

### DB Environment Variables

| Environment Variable | Default · Role |
| --- | --- |
| `INTEREST_DB_HOST` | `localhost` |
| `INTEREST_DB_PORT` | `5433` |
| `INTEREST_DB_NAME` | `portfolio` |
| `INTEREST_DB_USER` | Environment-specific Preprocessor DB user |
| `INTEREST_DB_PASSWORD` | No default |

PowerShell example:

```powershell
$env:INTEREST_DB_HOST="localhost"
$env:INTEREST_DB_PORT="5433"
$env:INTEREST_DB_NAME="portfolio"
$env:INTEREST_DB_USER="[REDACTED]"
$env:INTEREST_DB_PASSWORD="[REDACTED]"
```

### Other Settings

| Category | Example |
| --- | --- |
| Feature | processor version · weight |
| Date | trade date · business date |
| Database | raw · feature table |
| API | holiday endpoint |
| Runtime | ECS · container environment variables |

Do not record actual local config and credential values in the documentation.

## AWS Operations

The Preprocessor runs as an ECS Fargate RunTask in AWS Paper Daily Step 3, and the Step Functions `Step3_RunPreprocessor` holds a fixed reference to the Task Definition Revision.

| Item | Responsibility |
| --- | --- |
| Preprocessor | Feature processing entrypoint |
| ECS Fargate | Execution environment · RunTask |
| Step Functions | Daily orchestration · `Step3_RunPreprocessor` |
| Scheduler | Execution timing |
| Crawler | raw input |
| Strategy | Feature consumption |

The deployment/execution flow is as follows.

main push → GitHub Actions → GitHub OIDC → CodeBuild (CI gate + Docker Build) → ECR Candidate image → digest-pinned Candidate Task Definition → Data Shadow validation → GitHub production approval → Promotion of the same Candidate Task Definition to Step 3

The actual cluster, task definition ARN, image URI, subnet, and security group are external operational facts.

Do not record actual values in the documentation; use placeholders only.

| Value | Placeholder |
| --- | --- |
| ECS task | `<PREPROCESSOR_ECS_TASK>` |
| ECR image | `<ECR_IMAGE_URI>` |
| Task definition | `<TASK_DEFINITION_ARN>` |
| State machine | `<STATE_MACHINE_ARN>` |
| GitHub OIDC Role | `<GITHUB_OIDC_ROLE>` |
| CodeBuild project | `<CODEBUILD_PROJECT>` |
| DB host | `<DB_HOST>` |
| Command id | `<COMMAND_ID>` |

## CI and Container Build

GitHub Actions runs AWS CodeBuild, and CodeBuild performs the CI gate and Docker Build.

| Item | Value |
| --- | --- |
| Python Compile | Syntax verification |
| Unit Test | DB · external API mock |
| Static Analysis | ruff-based |
| Container Smoke Test | import only · `run()` not called |
| Docker Build | Container image build |
| ECR Push | Automatic on main push · controlled by input for `workflow_dispatch` |
| Authentication | GitHub OIDC · Preprocessor-dedicated Role |
| Role passing | Repository Variable-based Role ARN |

- main push automatically performs the Candidate image publish.
- The `workflow_dispatch` auxiliary path controls whether to publish via the `push_image` input, and the default is `true`.
- Separate Candidate build/publish from Production activation.
- Each validation runs in an isolated state without actual operational DB DML or Holiday API calls.
- The Container Smoke Test performs module import only and does not call `run()`.

## ECS Revision Deployment and Rollback

- Read the existing operational Revision as the baseline.
- Pin the new image by ECR Digest.
- Register a new Task Definition Revision.
- Switch only the Preprocessor State in Step Functions to the new Revision.
- Do not unnecessarily change the full State Machine definition.
- For Rollback, change the reference back to the previous Task Definition Revision.
- Verify that no reference to the new Revision remains in the rollback state.
- After validation, the new Revision can be re-promoted.
- If there is a running State Machine execution, halt the definition switch.

## Data Shadow and Production Promotion

Before activating a Candidate image in Production, perform separate Data Shadow validation.

Shadow validation places the Production preprocessor as the Champion and `preprocessor_shadow` as the Challenger.

| Item | Value |
| --- | --- |
| Run mode | `PREPROCESSOR_RUN_MODE` (`PRODUCTION` · `SHADOW`) |
| Shadow write | `preprocessor_shadow` schema isolation |
| Input | Same Production Raw · Reference |
| Shadow Identity | `PREPROCESSOR_SHADOW_RUN_ID` (DevOps Evidence Identity) |
| Quality Gate scope | Candidate execution · Shadow output · Trade Date core output |
| Integrity | 0 Production changes · Reference seed integrity |
| Isolation | Schema · sequence isolation contract |
| Cleanup | Remove Shadow execution results · 0 residual · no Production DML |
| Value quality comparison | `value_equality_gate = NOT_APPLICABLE` |
| Promotion approval | GitHub `production` Environment manual approval |
| Promotion target | Shadow-tested same Candidate Task Definition |

Core contract:

- Shadow validation is a separate execution boundary from the Production Daily orchestration.
- The DevOps Quality Gate does not require the Candidate feature values to be identical to Production.
- Feature value quality and tolerance ranges are the Preprocessor team's responsibility and may be extended to differential comparison in the future.
- Cleanup is performed based on valid Prepare Evidence rather than a Quality Gate PASS, and both PASS and FAIL converge to a common Cleanup.
- Do not promote before Cleanup · Verify Cleanup · Production Integrity are complete.
- Do not promote before a Shadow PASS and GitHub production approval.
- Do not rebuild the image or re-register the Task Definition after approval.
- Shadow validation itself does not perform automatic Production Promotion.

The full Shadow State Machine definition, IAM Policy, actual ARNs, and S3 Evidence details are managed in the port-devops repository.

## Execution

Each Python file may be an independent entrypoint.

The command below is an execution-risk example.

```powershell
python pre_daily.py
```

Running it can trigger many DB operations and external holiday API calls.

## Execution Prohibition List

Do not perform the following during documentation work and static analysis.

- Running `pre_daily.py`
- Running individual `pre_*.py`
- DB DDL · DML · psql
- Holiday API calls
- Running the Crawler
- Model download · training · inference
- ECS · SSM · Scheduler execution
- Slack calls

## Security

Do not record the following values verbatim in code, documentation, or logs.

- DB password and connection string
- API key · token
- Actual DB host · private IP
- AWS account-id
- Actual ARN
- ECR image URI
- Full Image Digest value
- GitHub Actions Run ID · CodeBuild Build ID
- subnet · security group id
- command id
- local absolute path
- Slack webhook URL

Placeholder:

| Value | Placeholder |
| --- | --- |
| General sensitive information | `[REDACTED]` |
| DB host | `[REDACTED_DB_HOST]` |
| ARN | `[REDACTED_ARN]` |
| command id | `[REDACTED_COMMAND_ID]` |
| ECS task | `<PREPROCESSOR_ECS_TASK>` |
| ECR image | `<ECR_IMAGE_URI>` |
| Task definition | `<TASK_DEFINITION_ARN>` |
| State machine | `<STATE_MACHINE_ARN>` |
| GitHub OIDC Role | `<GITHUB_OIDC_ROLE>` |
| CodeBuild project | `<CODEBUILD_PROJECT>` |

Record the Git SHA-based Image Tag, ECR Image Digest pinning, ECS Task Definition Revision, and Step Functions active Revision by meaning rather than by their full actual values.

## External Dependencies

| Item | Role |
| --- | --- |
| Python | Runtime |
| psycopg2 | PostgreSQL |
| psycopg2.extras | Batch · helper |
| Requests | Holiday API |
| PostgreSQL | raw read · feature persistence |

## Documents

| Document | Role |
| --- | --- |
| `AGENTS.md` | port-interest-preprocessor working rules |
| `README.md` | Current structure and operational AS-IS |
| `CHANGELOG.md` | Primary change history |
| `docs/source-file-catalog.md` | Primary files and responsibilities |

Do not create date-specific `docs/worklog/*.md` files.

Record code and documentation change history in `CHANGELOG.md`.
