# port-interest-preprocessor Working Rules

This document defines the standards applied when modifying the Python preprocessing code, Daily orchestration, feature aggregation, configuration, tests, and documentation of the `port-interest-preprocessor` microservice.

For `port-interest-preprocessor` work, reading this document alone should be enough to understand the work scope, the raw→feature data contract, the Daily Step 3 execution order, DB write risk, upstream/downstream MS responsibilities, and validation principles.

## 0. Highest-Priority Documentation Readability Rules

Apply this section before all other rules for documentation work.

### 0.0 Scope Limitation

The readability rules apply only to content newly written or directly modified in the current task.

Unless the user explicitly requests a full-document cleanup or comprehensive review, do not perform the following work.

| Item | Default Handling |
| --- | --- |
| Full scan of existing documentation | Do not perform |
| Complete README restructuring | Do not perform |
| Large-scale cleanup of historical CHANGELOG entries | Do not perform |
| Creation of a new scanner · audit tool | Do not perform |
| Creation of a sub-agent · orchestrator | Do not perform |

For adjacent content, review only the same table row, bullet group, or short paragraph.

Preserve existing out-of-scope violations and, when necessary, list them only as follow-up candidates.

### 0.1 Table Rules

New standalone summary tables use two columns by default.

The default headers are `Item / Value`.

More specific two-column headers may be used in the following situations.

| Situation | Preferred Headers |
| --- | --- |
| Changes by file | `File / Change` |
| entrypoint description | `File / Role` |
| feature description | `Feature / Role` |
| Validation results | `Item / Result` |
| Configuration summary | `Setting / Value` |
| Risk summary | `Risk / Handling` |
| Test results | `Test / Result` |

When adding a row to an existing table, preserve its existing column structure.

Tables with three or more columns are allowed only in the following cases.

| Condition | Handling |
| --- | --- |
| Explicitly requested by the user | Use the requested structure |
| Preserving the existing table is safer | Keep the existing structure |
| Converting a comparison to two columns would lose meaning | Allow an exception |

### 0.2 Table Cell and Sentence Length

- Keep table cells to no more than two sentences.
- Separate multiple values in one cell with `<br>`.
- Do not place three or more facts in a long sentence within one cell.
- Move lengthy evidence outside the table or link to the relevant document.
- Do not create cells longer than 300 characters or lines longer than 500 characters.
- Do not paste raw logs, complete SQL, complete DB results, and AWS responses into documentation.

### 0.3 Documentation Density

Use the following priority when writing documentation.

1. Short summary
2. Short two-column table
3. Short bullets
4. Link to detailed documentation
5. Long-form text

Do not repeat the same facts at length across the README, CHANGELOG, worklog, and detailed documentation.

### 0.4 Status Indicators

Use only the following five status indicators.

| Indicator | Meaning |
| --- | --- |
| 🔴 | Prohibited · high risk · failure |
| 🟠 | Pending · observing · unconfirmed |
| 🟢 | Complete · successful · ENABLED |
| 🔵 | Reference · information · evidence |
| ⚫ | Not applicable |

Do not add HTML colors when a status indicator is sufficient.

### 0.5 Work Method Restrictions

Perform documentation work in the following order.

1. Confirm the requested scope
2. Read the target file directly
3. Modify only the necessary sections
4. Save as UTF-8 without BOM
5. Perform a short after-check
6. Report a change summary

Unless explicitly requested by the user, do not use the following methods.

- Full workspace scan
- Sub-agent
- Orchestrator
- New scanner
- Content hash matrix
- Temporary files outside the workspace
- Excessive automation scripts

## 1. Scope

### 1.1 Default Working Directory

`C:\Workspaces\port-interest-preprocessor`

### 1.2 Project Role

port-interest-preprocessor is a Python microservice that reads the raw/history data loaded by the Crawler and generates analysis and aggregation features.

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

Currently the repository is centered on root-level executable Python scripts rather than a package layer.

### 1.3 Default Modification Targets

| Category | Target |
| --- | --- |
| Python | Root `pre_*.py` and package Python files |
| Daily | `pre_daily.py` |
| Helper | `db_config.py` · holiday helper |
| Tests | `tests` · `test_*.py` |
| Configuration | Environment-variable loader · local config-related code |
| Documentation | `README.md` · `CHANGELOG.md` · `docs` |
| Dependencies | requirements · pyproject · lock-related files |
| Operations | ECS · container execution wrappers and related documentation |
| Container | `Dockerfile` |
| CI | `.devops/codebuild/buildspec.yml` |
| Workflow | `.github/workflows/preprocessor-codebuild.yml` |
| Smoke Test | `.devops/scripts/container-smoke.py` |

Do not modify files that are not included in the current request.

Treat only files that actually exist in the repository as modification targets, and do not create or document files that do not exist.

### 1.4 Other Microservices

The following projects are external dependencies.

- `port-interest-crawler`
- `port-view`
- `port-marketconnector`
- `port_strategy_common`
- `port_strategy_research`
- `port_strategy_decision`
- `port_strategy_execution`

Do not modify code or documentation in another MS unless the current task explicitly requires it.

Cross-service specs under `.kiro` are not automatically included in the port-interest-preprocessor work scope.

## 2. Execution Risk Levels

The preprocessing scripts in this repository can perform bulk DB read, delete, insert, and upsert on execution.

Some paths can also call an external holiday API.

Do not treat every Python file as an ordinary smoke test target.

### 2.1 Highest-risk entrypoints

| File | Risk |
| --- | --- |
| `pre_daily.py` | Runs many preprocessing stages in sequence |
| `pre_total_stock_daily_feature.py` | Bulk combination of many stock features |
| `pre_total_market_daily_feature.py` | Combines many market features · holiday API possible |
| `pre_news_event_detection.py` | Bulk event generation based on event master and keyword |
| `pre_news_daily_aggregator.py` | Bulk update of news daily aggregation |
| `pre_agency_daily_aggregator.py` | Bulk update of report daily aggregation |

Do not run the files above without the user's explicit execution request and confirmation of the target DB environment.

### 2.2 Individual Feature Write Risk

| Area | File |
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

Individual scripts can also perform DB writes and bulk recomputation.

Do not judge a file as read-only just because its name contains analysis or aggregator.

### 2.3 Static Work Defaults

When the user does not specify execution, perform only the following work.

- Read files directly
- Safe text search
- Static code analysis
- Documentation edits
- Test code authoring
- Non-executing syntax review
- Read-only Git status inspection

### 2.4 CI Validation and Approval-required Work

The existing DB · API execution-risk principles are preserved.

CI pipeline validation is divided into work performed without actual operational side effects and work requiring explicit approval.

| Safely Performable Validation | Note |
| --- | --- |
| Python compile | `compileall` |
| Unit Test | DB · external API mock |
| Static Analysis | ruff-based |
| Container Smoke Test | No operational DB write · import only |
| Docker image build | Local image build |
| Read-only Git status inspection | status · diff |

| Approval-required Work | Note |
| --- | --- |
| ECR Push | Registry reflection |
| ECS Task Definition registration | New Revision |
| Step Functions definition change | Revision reference switch |
| ECS RunTask | Actual execution |
| Running `pre_daily.py` | Bulk DB operations |
| Operational DB DML | Data change |
| Actual Holiday API call | External request |

The Container Smoke Test performs module import only and does not call `run()`.

## 3. Data Flow and Responsibility Boundary

### 3.1 Basic Flow

| Stage | Responsibility |
| --- | --- |
| Input | `interest` raw/history loaded by the Crawler |
| Processing | `pre_*.py` analysis · transform · aggregation |
| Store | `preprocessor` feature |
| Reference | `reference` · `legacy` |
| Consume | Strategy Research · Strategy Decision |

### 3.2 Out of Direct Scope

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

### 3.3 Raw→Feature Contract

- Preserve the meaning of the input raw's source, ticker, trade date, and reference timestamp.
- Do not arbitrarily change the feature version and calculation basis.
- When raw is empty or lacks freshness, distinguish a normal zero-record from an input failure.
- Do not delete or rename feature columns used by downstream without an explicit request.
- Generate a total feature only after verifying the success and freshness of subordinate features.
- Do not reuse a previous-day feature as a same-day success result.

## 4. Daily Step 3 Orchestration

`pre_daily.py` is the Daily orchestration candidate that calls each preprocessing `run()` entrypoint in sequence.

### 4.1 Current Stage Composition

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

If the documentation and code differ, do not guess; update the documentation based on the current implementation.

### 4.2 Commented-out Stage

Based on the current documentation, `pre_agency_analysis.run()` is commented out in `pre_daily.py`.

- Do not document a commented-out stage as running.
- Do not perform the uncommenting as an ordinary consistency fix.
- Also verify the input dependency of the subsequent `pre_agency_daily_aggregator.py`.
- Verify whether past data is reused and the associated freshness risk.
- Treat stage activation as a separate functional change.

### 4.3 Stage Order Change

Before changing the order, verify the following.

| Item | Check |
| --- | --- |
| Input table | Whether the prior feature was generated |
| Trade date | Whether the same base date is used |
| Aggregator | Whether it depends on analysis output |
| Total feature | Whether all subordinate features completed |
| Failure | Whether subsequent stages proceed after a mid-stage failure |
| Idempotency | Whether re-running causes duplicates |

Do not change the stage order for simple cleanup purposes.

### 4.4 Partial Failure

- Do not merely print a stage failure and treat it as an overall success.
- Verify the child function return value and exception contract.
- Do not generate a total feature after a failure.
- Emit the success marker only after all required stages complete.
- Distinguish a commented-out optional stage from a failed required stage.
- Do not record an unexecuted stage as a success.

## 5. Feature Area Standards

### 5.1 News

| File | Role |
| --- | --- |
| `pre_news_analysis.py` | News-stock mapping · sentiment · keyword |
| `pre_news_event_detection.py` | Event candidate detection |
| `pre_news_daily_aggregator.py` | Stock- and date-level aggregation |

- Preserve the meaning of alias and ticker mapping.
- When changing the Sentiment Score and keyword rule, verify the version and impact scope.
- Verify the dependency on event master, keyword, and sector weight.
- Verify the unique key for duplicate news and duplicate events.
- Do not run the aggregator normally after an analysis failure.

### 5.2 Agency

| File | Role |
| --- | --- |
| `pre_agency_analysis.py` | Investment opinion · target price analysis |
| `pre_agency_daily_aggregator.py` | Stock- and date-level aggregation |

- Preserve the meaning of investment opinion normalization and score.
- Distinguish a missing target price from 0.
- When the analysis stage is inactive, verify the aggregator's input freshness.
- Do not handle stale analysis results as if they were new same-day results.

### 5.3 Price and Market Breadth

| File | Role |
| --- | --- |
| `pre_price.py` | Price feature |
| `pre_marketbreadth.py` | Market breadth feature |

- Verify the adjusted price, return, moving average, and momentum basis.
- Preserve the required lookback period.
- Do not handle a trading halt and a missing price identically.
- Verify the universe and market basis of breadth.
- Do not record overall market success from only a partial universe.

### 5.4 Macro · Commodity · Foreign Index

| File | Role |
| --- | --- |
| `pre_macroeconomic.py` | Macro feature |
| `pre_commodity.py` | Commodity feature |
| `pre_foreignindex.py` | Foreign index feature |

- Preserve indicator names and source mapping.
- Verify time lag and timezone.
- Specify whether Market Holiday forward-fill applies.
- Distinguish empty raw from a retained previous-day value policy.
- Distinguish partial-indicator missing from full failure.

### 5.5 Flow · Program · Short Sell

| File | Role |
| --- | --- |
| `pre_investorflow.py` | Investor Flow feature |
| `pre_program.py` | Program Trading feature |
| `pre_shortsell.py` | Short Selling feature |

- Preserve the meaning of quantity, amount, ratio, and sign.
- Verify the join basis with price raw.
- Verify the KRX raw latest Trading Day.
- Distinguish a zero-record from not-yet-collected.
- Do not hide division by zero and NULL handling.

### 5.6 Total Feature

| File | Role |
| --- | --- |
| `pre_total_stock_daily_feature.py` | Stock-level Total Feature |
| `pre_total_market_daily_feature.py` | Market-level Total Feature |

- Verify the freshness and base date of the subordinate feature tables.
- Do not hide a partial subordinate feature failure as NULL.
- Verify the join key and cardinality.
- Prevent row-count increase from a duplicate join.
- Treat total score and weight changes as strategy-impact changes.
- Do not convert a holiday helper failure into a normal SKIP.

## 6. Python Code Authoring Rules

### 6.1 Common Principles

- Prefer preserving existing file names, function names, CLI options, tables, and feature semantics.
- Ensure that module import alone does not trigger a DB connection, external API call, or bulk processing.
- Preserve the `if __name__ == "__main__":` boundary for entrypoints.
- Distinguish the extract, transform, aggregate, and persist stages as much as possible.
- Do not convert a failure into a success, `NO_CHANGE`, or a normal zero-record.
- Do not add a one-time data workaround as a permanent fallback.

### 6.2 Function Contract

- Preserve the meaning of the `run()` return value and exceptions.
- If the caller does not use the return value, verify the failure-propagation method.
- Distinguish optional stages from required stages.
- Do not add hidden global state and import-time side effects.
- The result must be predictable when re-running for the same trade date.

### 6.3 Calculation Logic

- Verify the current feature definition and downstream consumption before changing a formula.
- Preserve the handling semantics of missing values, 0, negatives, and outliers.
- Verify decimal places, rounding, and data types.
- Verify the rolling window and minimum period.
- Do not create look-ahead bias.
- Do not use future dates or same-day unconfirmed data.

### 6.4 Persist

- Preserve the existing unique key and conflict/upsert policy.
- Verify the meaning of trade date, ticker, feature version, and source.
- Preserve transaction and rollback boundaries.
- For a delete-then-insert pattern, verify the target date and range.
- Do not print a success marker after a partial load.
- For bulk loading, verify batch size and commit unit.

## 7. Database Standards

### 7.1 Connection

| Item | Value |
| --- | --- |
| Database | `portfolio` |
| Config loader | `get_db_config()` in `db_config.py` |
| Environment variables | `INTEREST_DB_*` |
| Password | No default |
| Run mode | `PREPROCESSOR_RUN_MODE` · default `PRODUCTION` |
| Production search path | `preprocessor, interest, reference, legacy, public` |
| Shadow search path | `preprocessor_shadow, preprocessor, interest, reference, legacy, public` |

In the real operational environment, a dedicated Preprocessor DB user is used.

Even if a `postgres` default exists in the code or older documentation, do not interpret it as an operational-privilege baseline.

Do not arbitrarily remove the Production/Shadow run mode and search_path routing contract in `db_config.py`.

Do not arbitrarily change the Shadow search_path order.

### 7.2 Schema Responsibilities

| Schema | Role |
| --- | --- |
| `preprocessor` | Production analysis · aggregation feature |
| `preprocessor_shadow` | Candidate Shadow temporary output · cleanup target |
| `interest` | Crawler raw · history |
| `reference` | ticker · universe · reference data |
| `legacy` | Backward compatibility |
| `public` | fallback search path |

Do not perform Production `preprocessor` DML in a Shadow run.

`preprocessor_shadow` is not a downstream operational schema but an isolated output for Candidate validation.

The Preprocessor does not directly produce `research`, `decision`, or `execution` results.

### 7.3 SQL and Upsert

- New SQL uses schema-qualified names whenever possible.
- Verify that existing unqualified SQL is consistent with the connection `search_path`.
- Before modifying SQL, verify columns through the actual code, migrations, or `information_schema.columns`.
- Verify the meaning of unique keys and `ON CONFLICT`.
- Verify the group key and join cardinality of aggregation SQL.
- Verify the delete range and regeneration range.
- Do not print SUCCESS after a failed DB operation.

### 7.4 Freshness and Dates

- Verify the trade date of the input raw and output feature together.
- The latest date of each subordinate feature must match the total feature base date.
- Distinguish Market Holiday, weekend, and source not-yet-published.
- Do not copy a past latest row as if it were a same-day row.
- Prefer the Asia/Seoul basis for timezone.

## 8. Holiday API Standards

`interest_get_holidays.py` or the stages that reference it may call an external holiday API.

- Specify a timeout.
- Do not interpret an HTTP failure as a normal business day.
- Distinguish weekends from Market Holidays.
- Do not hide an API failure as a normal SKIP.
- Use an HTTP mock in tests.
- Do not call the real API during documentation work.

## 9. Configuration and Sensitive Information

### 9.1 Sensitive Information

Do not record the following values verbatim in code, documentation, examples, or logs.

- DB password and full connection string
- API key · token
- Actual DB host and private IP
- AWS account-id
- Actual ARN
- ECR image URI
- subnet · security group id
- command id
- local absolute path
- Slack webhook URL

Use the following placeholders when needed.

| Placeholder | Purpose |
| --- | --- |
| `[REDACTED]` | General sensitive information |
| `[REDACTED_DB_HOST]` | DB host |
| `[REDACTED_ARN]` | ARN |
| `[REDACTED_COMMAND_ID]` | command id |
| `<PREPROCESSOR_ECS_TASK>` | ECS task |
| `<ECR_IMAGE_URI>` | ECR image |
| `<TASK_DEFINITION_ARN>` | task definition |
| `<DB_HOST>` | DB host |

### 9.2 Configuration Changes

When changing a configuration key or loader, also verify the following.

1. `db_config.py`
2. The relevant `pre_*.py`
3. `pre_daily.py`
4. README
5. ECS · container environment variables
6. downstream feature consumer
7. Test fixtures

Do not read actual local config and credential values and move them into the documentation.

## 10. AWS Operational Standards

### 10.1 Execution Environment

The Preprocessor runs as an ECS Fargate RunTask in AWS Paper Daily Step 3, and the Step Functions `Step3_RunPreprocessor` holds a fixed reference to the Task Definition Revision.

| Item | Responsibility |
| --- | --- |
| Preprocessor | Feature processing entrypoint (`pre_daily.py`) |
| ECS Fargate | Execution environment · RunTask |
| Step Functions | Daily orchestration · `Step3_RunPreprocessor` |
| Scheduler | Execution timing |
| Crawler | raw input |
| Strategy | Feature consumption |

The actual cluster, task definition ARN, image URI, and network settings are external operational facts.

Do not call AWS APIs or change resources unless explicitly requested by the user.

When writing operational commands, do not record actual ARNs, account-id, subnet, security group, and command id in the documentation.

### 10.2 DevOps Operational Standards

| Item | Value |
| --- | --- |
| Artifact | Docker Image |
| Registry | ECR |
| Build | GitHub Actions → CodeBuild |
| CI gate | Python Compile · Unit Test · Static Analysis · Container Smoke Test |
| Deployment | Register a new ECS Task Definition Revision |
| Activation | Switch the fixed Revision reference of Step Functions `Step3_RunPreprocessor` |
| Image basis | Git SHA-based Tag and Image Digest |
| Rollback | Restore the Step Functions reference to the previous Task Definition Revision |
| Re-promotion | Re-activate the validated new Revision |

- The deployment philosophy is to separate Candidate build/publish from Production activation.
- main push automatically publishes the Candidate image but does not immediately mean Production activation.
- The Candidate is promoted only after passing Data Shadow validation and GitHub production manual approval.
- What is currently complete is CI, Candidate build/publish, Data Shadow validation (PASS E2E), GitHub approval-based Promotion, Rollback, and End-to-End consistency validation.
- The FAIL-path forced E2E was not performed, so it is not recorded as complete.

### 10.3 GitHub OIDC Rules

- GitHub Actions does not use long-lived AWS Access Keys.
- AWS authentication uses GitHub OIDC.
- A per-Repository dedicated IAM Role is used.
- Trust restricts the Repository and execution context, and allows main branch CI and `production` Environment promotion separately.
- Maintain the subject-restriction principle based on immutable repository identity.
- The Role ARN is passed via a GitHub Repository Variable.
- Grant the OIDC Role only the necessary least privilege.
- Do not reuse another Repository's OIDC Role.
- Do not record the actual Role ARN, owner ID, or repository ID numbers.

### 10.4 Deployment · Rollback Validation Standards

| Completion Criterion | Check |
| --- | --- |
| Local · remote SHA | Local SHA matches remote main SHA |
| GitHub Actions | head SHA match |
| CodeBuild | resolved source version match |
| Image Tag | Verify the Git SHA-based Tag |
| ECR consistency | Verify Tag and Digest consistency |
| ECS pinning | Verify Digest pinning of the Task Definition container image |
| Step Functions | Verify the active Task Definition Revision |
| Rollback | Verify 0 references to the new Revision afterward |
| Re-promotion | Re-verify the active Revision and Digest |
| Switch timing | Switch the definition when there is no running Step Functions execution |

### 10.5 Data Shadow and Promotion Rules

Perform Data Shadow validation before activating a Candidate in Production.

| Item | Value |
| --- | --- |
| Champion | Production `preprocessor` |
| Challenger | `preprocessor_shadow` |
| Input | Same Production Raw · Reference |
| Quality Gate value comparison | `value_equality_gate = NOT_APPLICABLE` |
| Promotion approval | GitHub `production` Environment manual approval |
| Promotion target | Shadow-tested same Candidate Task Definition |

Follow the rules below during Kiro work.

- Do not arbitrarily remove or change the Production/Shadow run mode contract and Shadow search_path order.
- Do not perform Production `preprocessor` DML in a Shadow run.
- Do not propagate the Shadow concept and filter responsibility to downstream such as Research · Decision.
- Do not merge Shadow validation directly into the Production Daily orchestration.
- Maintain Cleanup · Verify Cleanup · Production Integrity as the Promotion Gate.
- Do not arbitrarily promote feature value equality to a required DevOps Gate.
- Separate Candidate build/publish from Production activation.
- Do not bypass the `production` Environment manual approval.
- Do not rebuild the image or re-register the Task Definition after approval.
- Promote only the Shadow-tested same Artifact.

The full Shadow State Machine definition, IAM Policy, actual ARNs, and S3 Evidence details are within the port-devops repository scope and are not duplicated in this repository's documentation.

## 11. Execution Restrictions

Do not perform the following work unless explicitly requested by the user.

| Category | Prohibited Work |
| --- | --- |
| Preprocessor | Running `pre_daily.py` · individual `pre_*.py` |
| Database | DDL · DML · migration · psql |
| Network | holiday API calls |
| Crawler | External data collection execution |
| Model | download · training · inference |
| AWS | ECS · SSM · Scheduler execution or change |
| Slack | webhook or notifier calls |
| Git | add · commit · push · reset · restore |

Run read-only validation only within the user-requested scope.

## 12. Tests and Validation

### 12.1 Basic Principles

- Prefer unit tests that are possible without a real DB and external API.
- Isolate DB connection, holiday HTTP, and filesystem with mocks or stubs.
- Do not use real credentials and operational environment variables in tests.
- Do not run a full bulk feature regeneration as an ordinary test.
- Use small fixtures and a limited trade date.

### 12.2 Minimum Validation by Change

| Change Target | Minimum Validation |
| --- | --- |
| Python syntax | Safe compile check |
| Pure calculation | Fixed-input fixture |
| News mapping | alias · keyword fixture |
| Aggregator | group key · duplicate test |
| Rolling feature | lookback · boundary test |
| Total feature | join cardinality · missing input |
| Holiday | HTTP mock · weekend · Market Holiday |
| Daily orchestration | call order · exception propagation mock |
| Repository | SQL · parameter · upsert test |
| Documentation | links · facts · readability |

For files with execution-risk imports, first check for side effects even during compile.

Do not record validation that could not be run as complete; record the reason it was not run.

## 13. Documentation Management Rules

### 13.1 README.md

The README describes the current structure and operational AS-IS of port-interest-preprocessor.

Content to include in the README:

- Project role
- raw→feature data flow
- Primary feature areas
- Daily Step 3 order
- Commented-out stage
- DB and schema
- holiday API
- AWS operational boundary
- Configuration and security
- Execution restrictions
- Links to detailed documentation

Do not copy other MS and the full Step Functions definition at length.

### 13.2 CHANGELOG.md

The CHANGELOG records only the primary changes to port-interest-preprocessor code and documentation.

- Add the latest date at the top.
- Use `Added`, `Changed`, `Fixed`, `Removed`, `Security` as needed.
- Record only actual Preprocessor changes.
- Do not record one-time command ids, raw logs, and DB row results.
- Use primarily two-column tables in new sections.
- Preserve historical entries unless separately requested otherwise.

### 13.3 docs

Before creating a new document, first determine whether it can be incorporated into the README, CHANGELOG, and existing docs.

Do not create date-specific `docs/worklog/*.md` files.

Record code and documentation change history in `CHANGELOG.md`.

### 13.4 Automatic source-file-catalog.md Updates

When `docs/source-file-catalog.md` exists and one of the following changes occurs, determine within the same task whether it must be updated.

| Change | Handling |
| --- | --- |
| Create · delete · rename a primary Python file | Update the catalog |
| Change `pre_daily.py` call order | Update orchestration |
| Change feature responsibility | Update roles and I/O |
| Change commented-out stage | Update the current active state |
| Change DB loader · schema role | Update the Database section |
| Change Holiday helper role | Update external dependencies |
| Change scripts · ECS wrapper | Update the operations section |
| Create · delete a document or change its role | Update the Documents section |
| Change only internal implementation · same responsibility | May be omitted |

The catalog is not an inventory of every file.

Record only entrypoints, feature groups, and responsibilities meaningful to operations and maintenance.

## 14. Git Rules

Only read-only status inspection is allowed by default.

| Allowed | Prohibited |
| --- | --- |
| `git status --short`<br>`git diff --stat`<br>`git diff --check` | `git add`<br>`git commit`<br>`git push`<br>`git reset`<br>`git restore`<br>`git checkout`<br>`git stash` |

Do not create a commit unless explicitly requested by the user.

## 15. Completion Report

At completion, report only the following and keep it concise.

| Item | Content |
| --- | --- |
| Changed files | Files actually modified |
| Key changes | Summary of functional or documentation changes |
| Data contract | raw · feature · downstream impact |
| Execution risk | DB · API · AWS paths not executed |
| Validation | Static checks and tests performed |
| Not performed | Validation that could not be run |
| Security | Whether sensitive values were recorded verbatim |
| Follow-up | Only items that actually remain |

Distinguish work performed by the operator from work performed by Kiro.

## 16. Completion Checklist

- [ ] Were only the requested port-interest-preprocessor files modified?
- [ ] Were other MS and `.kiro` files left unchanged unless needed?
- [ ] Were the highest-priority documentation readability rules applied?
- [ ] Do new standalone tables use two columns by default?
- [ ] Were long cells and lines avoided?
- [ ] Was the raw→feature data contract preserved?
- [ ] Was the Daily Step 3 call order verified?
- [ ] Was a commented-out stage not mistaken for a running one?
- [ ] Were the analysis and aggregator dependencies verified?
- [ ] Was subordinate feature freshness verified before the total feature?
- [ ] Were subsequent stages not treated as success after a partial failure?
- [ ] Was DB unique key · upsert · transaction consistency verified?
- [ ] Was trade date and timezone consistency verified?
- [ ] Was look-ahead bias avoided?
- [ ] Was a Holiday API failure not treated as a normal business day?
- [ ] Were sensitive values kept out of the documentation verbatim?
- [ ] Was validation appropriate to the change scope performed?
- [ ] If file structure or responsibility changed, was `docs/source-file-catalog.md` checked?
- [ ] Were no date-specific `docs/worklog/*.md` files created?
- [ ] Were files saved as UTF-8 without BOM?
- [ ] Were only actual changes reflected in the README and CHANGELOG?
