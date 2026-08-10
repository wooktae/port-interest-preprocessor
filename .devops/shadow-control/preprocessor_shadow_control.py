import argparse
import json
import os
import sys
from datetime import datetime, timezone

import boto3
import psycopg2


DEFAULT_PREFIX = "preprocessor-shadow"

PRODUCTION_SCHEMA = "preprocessor"
SHADOW_SCHEMA = "preprocessor_shadow"

EXPECTED_TABLES = (
    "pre_agency_analysis",
    "pre_agency_daily_feature",
    "pre_commodity_daily_feature",
    "pre_event_keyword",
    "pre_event_master",
    "pre_event_sector_weight",
    "pre_foreignindex_daily_feature",
    "pre_investorflow_daily_feature",
    "pre_macroeconomic_daily_feature",
    "pre_marketbreadth_daily_feature",
    "pre_news_analysis",
    "pre_news_daily_feature",
    "pre_news_event",
    "pre_price_daily_feature",
    "pre_program_daily_feature",
    "pre_shortsell_daily_feature",
    "pre_total_market_daily_feature",
    "pre_total_stock_daily_feature",
)

REFERENCE_TABLES = (
    "pre_event_master",
    "pre_event_keyword",
    "pre_event_sector_weight",
)

CLEANUP_TABLES = tuple(
    table
    for table in EXPECTED_TABLES
    if table not in REFERENCE_TABLES
)

REQUIRED_SHADOW_OUTPUT_TABLES = (
    "pre_agency_daily_feature",
    "pre_commodity_daily_feature",
    "pre_foreignindex_daily_feature",
    "pre_investorflow_daily_feature",
    "pre_macroeconomic_daily_feature",
    "pre_marketbreadth_daily_feature",
    "pre_news_analysis",
    "pre_news_daily_feature",
    "pre_news_event",
    "pre_price_daily_feature",
    "pre_program_daily_feature",
    "pre_shortsell_daily_feature",
    "pre_total_market_daily_feature",
    "pre_total_stock_daily_feature",
)

TRADE_DATE_CORE_TABLES = (
    "pre_agency_daily_feature",
    "pre_commodity_daily_feature",
    "pre_foreignindex_daily_feature",
    "pre_investorflow_daily_feature",
    "pre_macroeconomic_daily_feature",
    "pre_marketbreadth_daily_feature",
    "pre_news_daily_feature",
    "pre_price_daily_feature",
    "pre_program_daily_feature",
    "pre_shortsell_daily_feature",
    "pre_total_market_daily_feature",
    "pre_total_stock_daily_feature",
)

EXPECTED_TABLE_COUNT = 18
EXPECTED_SHADOW_SEQUENCE_COUNT = 10


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(f"{name}_REQUIRED")

    return value


def build_s3_client():
    return boto3.client("s3")


def build_db_connection():
    return psycopg2.connect(
        host=require_env("INTEREST_DB_HOST"),
        port=require_env("INTEREST_DB_PORT"),
        dbname=require_env("INTEREST_DB_NAME"),
        user=require_env("INTEREST_DB_USER"),
        password=require_env("INTEREST_DB_PASSWORD"),
        connect_timeout=15,
        application_name="preprocessor-shadow-control",
    )


def build_evidence(
    *,
    action: str,
    shadow_run_id: str,
    status: str,
) -> dict:
    return {
        "schema_version": "1.0",
        "service": "preprocessor",
        "component": "shadow-control",
        "action": action,
        "shadow_run_id": shadow_run_id,
        "status": status,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def evidence_key(
    *,
    prefix: str,
    shadow_run_id: str,
    name: str,
) -> str:
    prefix = prefix.strip("/")

    return (
        f"{prefix}/"
        f"{shadow_run_id}/"
        f"{name}.json"
    )


def put_evidence(
    *,
    s3,
    bucket: str,
    key: str,
    payload: dict,
) -> str | None:
    body = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    response = s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/json",
    )

    return response.get("VersionId")


def get_evidence(
    *,
    s3,
    bucket: str,
    key: str,
) -> dict:
    response = s3.get_object(
        Bucket=bucket,
        Key=key,
    )

    return json.loads(
        response["Body"].read().decode("utf-8")
    )


def fetch_table_names(cursor, schema: str) -> list[str]:
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """,
        (schema,),
    )

    return [
        row[0]
        for row in cursor.fetchall()
    ]


def fetch_table_counts(
    cursor,
    *,
    schema: str,
    tables: tuple[str, ...],
) -> dict[str, int]:
    result = {}

    for table in tables:
        cursor.execute(
            f'SELECT COUNT(*) FROM "{schema}"."{table}"'
        )
        result[table] = int(cursor.fetchone()[0])

    return result


def fetch_sequence_count(cursor, schema: str) -> int:
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.sequences
        WHERE sequence_schema = %s
        """,
        (schema,),
    )

    return int(cursor.fetchone()[0])


def fetch_production_sequence_leaks(cursor) -> list[dict]:
    cursor.execute(
        """
        SELECT
            table_name,
            column_name,
            column_default
        FROM information_schema.columns
        WHERE table_schema = %s
          AND column_default LIKE '%%preprocessor.%%nextval%%'
        ORDER BY table_name, column_name
        """,
        (SHADOW_SCHEMA,),
    )

    return [
        {
            "table": row[0],
            "column": row[1],
            "default": row[2],
        }
        for row in cursor.fetchall()
    ]


def validate_table_contract(
    *,
    production_tables: list[str],
    shadow_tables: list[str],
) -> None:
    expected = sorted(EXPECTED_TABLES)

    if production_tables != expected:
        raise RuntimeError(
            "PRODUCTION_TABLE_CONTRACT_MISMATCH"
        )

    if shadow_tables != expected:
        raise RuntimeError(
            "SHADOW_TABLE_CONTRACT_MISMATCH"
        )


def fetch_trade_date_counts(
    cursor,
    *,
    schema: str,
    tables: tuple[str, ...],
    trade_date: str,
) -> dict[str, int]:
    result = {}

    for table in tables:
        cursor.execute(
            f'''
            SELECT COUNT(*)
            FROM "{schema}"."{table}"
            WHERE date = %s
            ''',
            (trade_date,),
        )

        result[table] = int(
            cursor.fetchone()[0]
        )

    return result


def validate_positive_counts(
    *,
    counts: dict[str, int],
    error_prefix: str,
) -> None:
    failures = [
        table
        for table, count in counts.items()
        if count <= 0
    ]

    if failures:
        raise RuntimeError(
            f"{error_prefix}:"
            + ",".join(sorted(failures))
        )


def run_quality_gate(args) -> int:
    shadow_run_id = args.shadow_run_id.strip()

    if not shadow_run_id:
        raise RuntimeError(
            "SHADOW_RUN_ID_REQUIRED"
        )

    trade_date = (
        args.trade_date.strip()
        if args.trade_date
        else ""
    )

    if not trade_date:
        raise RuntimeError(
            "TRADE_DATE_REQUIRED"
        )

    bucket = require_env(
        "PREPROCESSOR_SHADOW_EVIDENCE_BUCKET"
    )

    prefix = os.getenv(
        "PREPROCESSOR_SHADOW_EVIDENCE_PREFIX",
        DEFAULT_PREFIX,
    ).strip()

    s3 = build_s3_client()

    prepare_key = evidence_key(
        prefix=prefix,
        shadow_run_id=shadow_run_id,
        name="prepare",
    )

    prepare = get_evidence(
        s3=s3,
        bucket=bucket,
        key=prepare_key,
    )

    if prepare.get("action") != "PREPARE":
        raise RuntimeError(
            "PREPARE_EVIDENCE_ACTION_INVALID"
        )

    if prepare.get("status") != "PASS":
        raise RuntimeError(
            "PREPARE_EVIDENCE_NOT_PASS"
        )

    production_baseline = (
        prepare.get("production_baseline")
    )

    if not isinstance(
        production_baseline,
        dict,
    ):
        raise RuntimeError(
            "PRODUCTION_BASELINE_MISSING"
        )

    print("PREPARE_EVIDENCE=PASS")
    print(f"TRADE_DATE={trade_date}")

    connection = build_db_connection()

    try:
        connection.set_session(
            readonly=True,
            autocommit=False,
        )

        with connection.cursor() as cursor:
            production_current = (
                fetch_table_counts(
                    cursor,
                    schema=PRODUCTION_SCHEMA,
                    tables=EXPECTED_TABLES,
                )
            )

            changed_tables = sorted(
                table
                for table in EXPECTED_TABLES
                if (
                    int(production_current[table])
                    != int(
                        production_baseline[
                            table
                        ]
                    )
                )
            )

            print(
                "PRODUCTION_CHANGED_TABLE_COUNT="
                f"{len(changed_tables)}"
            )

            if changed_tables:
                raise RuntimeError(
                    "PRODUCTION_INTEGRITY_FAILED:"
                    + ",".join(changed_tables)
                )

            print(
                "PRODUCTION_INTEGRITY=PASS"
            )

            shadow_output_counts = (
                fetch_table_counts(
                    cursor,
                    schema=SHADOW_SCHEMA,
                    tables=(
                        REQUIRED_SHADOW_OUTPUT_TABLES
                    ),
                )
            )

            validate_positive_counts(
                counts=shadow_output_counts,
                error_prefix=(
                    "SHADOW_OUTPUT_MISSING"
                ),
            )

            print(
                "SHADOW_REQUIRED_OUTPUT_COUNT="
                f"{len(shadow_output_counts)}"
            )
            print(
                "SHADOW_OUTPUT_POPULATION=PASS"
            )

            trade_date_counts = (
                fetch_trade_date_counts(
                    cursor,
                    schema=SHADOW_SCHEMA,
                    tables=TRADE_DATE_CORE_TABLES,
                    trade_date=trade_date,
                )
            )

            validate_positive_counts(
                counts=trade_date_counts,
                error_prefix=(
                    "TRADE_DATE_CORE_OUTPUT_MISSING"
                ),
            )

            print(
                "TRADE_DATE_CORE_TABLE_COUNT="
                f"{len(trade_date_counts)}"
            )
            print(
                "TRADE_DATE_CORE_OUTPUT=PASS"
            )

            reference_production = (
                fetch_table_counts(
                    cursor,
                    schema=PRODUCTION_SCHEMA,
                    tables=REFERENCE_TABLES,
                )
            )

            reference_shadow = (
                fetch_table_counts(
                    cursor,
                    schema=SHADOW_SCHEMA,
                    tables=REFERENCE_TABLES,
                )
            )

            if (
                reference_shadow
                != reference_production
            ):
                raise RuntimeError(
                    "REFERENCE_SEED_INTEGRITY_FAILED"
                )

            print(
                "REFERENCE_SEED_INTEGRITY=PASS"
            )

            shadow_sequence_count = (
                fetch_sequence_count(
                    cursor,
                    SHADOW_SCHEMA,
                )
            )

            if (
                shadow_sequence_count
                != EXPECTED_SHADOW_SEQUENCE_COUNT
            ):
                raise RuntimeError(
                    "SHADOW_SEQUENCE_COUNT_MISMATCH"
                )

            leaks = (
                fetch_production_sequence_leaks(
                    cursor
                )
            )

            print(
                "PRODUCTION_SEQUENCE_LEAK_COUNT="
                f"{len(leaks)}"
            )

            if leaks:
                raise RuntimeError(
                    "PRODUCTION_SEQUENCE_LEAK_DETECTED"
                )

            print(
                "SEQUENCE_CONTRACT=PASS"
            )

        connection.rollback()

    finally:
        connection.close()

    evidence = build_evidence(
        action="QUALITY_GATE",
        shadow_run_id=shadow_run_id,
        status="PASS",
    )

    evidence.update(
        {
            "trade_date": trade_date,
            "production_integrity": "PASS",
            "production_changed_table_count": 0,
            "shadow_output_population": "PASS",
            "shadow_output_counts": (
                shadow_output_counts
            ),
            "trade_date_core_output": "PASS",
            "trade_date_core_counts": (
                trade_date_counts
            ),
            "reference_seed_integrity": "PASS",
            "shadow_sequence_count": (
                shadow_sequence_count
            ),
            "production_sequence_leak_count": 0,
            "value_equality_gate": (
                "NOT_APPLICABLE"
            ),
            "value_quality_owner": (
                "PREPROCESSOR_TEAM"
            ),
        }
    )

    key = evidence_key(
        prefix=prefix,
        shadow_run_id=shadow_run_id,
        name="quality-gate",
    )

    version_id = put_evidence(
        s3=s3,
        bucket=bucket,
        key=key,
        payload=evidence,
    )

    print("QUALITY_GATE_EVIDENCE_PUT=PASS")
    print(
        f"QUALITY_GATE_EVIDENCE_KEY={key}"
    )
    print(
        "QUALITY_GATE_EVIDENCE_VERSION_ID="
        f"{version_id or ''}"
    )

    loaded = get_evidence(
        s3=s3,
        bucket=bucket,
        key=key,
    )

    if loaded != evidence:
        raise RuntimeError(
            "QUALITY_GATE_EVIDENCE_MISMATCH"
        )

    print(
        "QUALITY_GATE_EVIDENCE_VERIFY=PASS"
    )
    print(
        "VALUE_EQUALITY_GATE=NOT_APPLICABLE"
    )
    print(
        "VALUE_QUALITY_OWNER=PREPROCESSOR_TEAM"
    )
    print(
        "PREPROCESSOR_SHADOW_QUALITY_GATE=SUCCESS"
    )

    return 0


def cleanup_shadow_tables(
    cursor,
) -> None:
    if len(CLEANUP_TABLES) != 15:
        raise RuntimeError(
            "CLEANUP_TABLE_COUNT_INVALID"
        )

    for table in CLEANUP_TABLES:
        if table in REFERENCE_TABLES:
            raise RuntimeError(
                f"REFERENCE_TABLE_CLEANUP_FORBIDDEN:{table}"
            )

    qualified = ", ".join(
        f'"{SHADOW_SCHEMA}"."{table}"'
        for table in CLEANUP_TABLES
    )

    sql = (
        f"TRUNCATE TABLE {qualified} "
        "CONTINUE IDENTITY"
    )

    if (
        f'"{PRODUCTION_SCHEMA}".'
        in sql
    ):
        raise RuntimeError(
            "PRODUCTION_SCHEMA_CLEANUP_FORBIDDEN"
        )

    cursor.execute(sql)


def run_verify_cleanup(args) -> int:
    shadow_run_id = args.shadow_run_id.strip()

    if not shadow_run_id:
        raise RuntimeError(
            "SHADOW_RUN_ID_REQUIRED"
        )

    bucket = require_env(
        "PREPROCESSOR_SHADOW_EVIDENCE_BUCKET"
    )

    prefix = os.getenv(
        "PREPROCESSOR_SHADOW_EVIDENCE_PREFIX",
        DEFAULT_PREFIX,
    ).strip()

    s3 = build_s3_client()

    prepare_key = evidence_key(
        prefix=prefix,
        shadow_run_id=shadow_run_id,
        name="prepare",
    )

    cleanup_key = evidence_key(
        prefix=prefix,
        shadow_run_id=shadow_run_id,
        name="cleanup",
    )

    prepare = get_evidence(
        s3=s3,
        bucket=bucket,
        key=prepare_key,
    )

    cleanup = get_evidence(
        s3=s3,
        bucket=bucket,
        key=cleanup_key,
    )

    if prepare.get("action") != "PREPARE":
        raise RuntimeError(
            "PREPARE_EVIDENCE_ACTION_INVALID"
        )

    if prepare.get("status") != "PASS":
        raise RuntimeError(
            "PREPARE_EVIDENCE_NOT_PASS"
        )

    production_baseline = (
        prepare.get("production_baseline")
    )

    if not isinstance(
        production_baseline,
        dict,
    ):
        raise RuntimeError(
            "PRODUCTION_BASELINE_MISSING"
        )

    if cleanup.get("action") != "CLEANUP":
        raise RuntimeError(
            "CLEANUP_EVIDENCE_ACTION_INVALID"
        )

    if cleanup.get("status") != "PASS":
        raise RuntimeError(
            "CLEANUP_EVIDENCE_NOT_PASS"
        )

    print("PREPARE_EVIDENCE=PASS")
    print("CLEANUP_EVIDENCE=PASS")

    connection = build_db_connection()

    try:
        connection.set_session(
            readonly=True,
            autocommit=False,
        )

        with connection.cursor() as cursor:
            shadow_tables = fetch_table_names(
                cursor,
                SHADOW_SCHEMA,
            )

            expected_tables = set(
                EXPECTED_TABLES
            )

            actual_tables = set(
                shadow_tables
            )

            missing_tables = sorted(
                expected_tables - actual_tables
            )

            unexpected_tables = sorted(
                actual_tables - expected_tables
            )

            if missing_tables:
                raise RuntimeError(
                    "SHADOW_TABLES_MISSING:"
                    + ",".join(missing_tables)
                )

            if unexpected_tables:
                raise RuntimeError(
                    "SHADOW_TABLES_UNEXPECTED:"
                    + ",".join(unexpected_tables)
                )

            print(
                "SHADOW_TABLE_COUNT="
                f"{len(actual_tables)}"
            )
            print(
                "SHADOW_TABLE_STRUCTURE=PASS"
            )

            residual_counts = fetch_table_counts(
                cursor,
                schema=SHADOW_SCHEMA,
                tables=CLEANUP_TABLES,
            )

            residual_tables = sorted(
                table
                for table, count
                in residual_counts.items()
                if int(count) != 0
            )

            print(
                "SHADOW_RESIDUAL_TABLE_COUNT="
                f"{len(residual_tables)}"
            )

            if residual_tables:
                raise RuntimeError(
                    "SHADOW_CLEANUP_RESIDUAL:"
                    + ",".join(residual_tables)
                )

            print(
                "SHADOW_RESIDUAL_ZERO=PASS"
            )

            reference_production = (
                fetch_table_counts(
                    cursor,
                    schema=PRODUCTION_SCHEMA,
                    tables=REFERENCE_TABLES,
                )
            )

            reference_shadow = (
                fetch_table_counts(
                    cursor,
                    schema=SHADOW_SCHEMA,
                    tables=REFERENCE_TABLES,
                )
            )

            if (
                reference_shadow
                != reference_production
            ):
                raise RuntimeError(
                    "REFERENCE_SEED_INTEGRITY_FAILED"
                )

            print(
                "REFERENCE_SEED_INTEGRITY=PASS"
            )

            production_current = (
                fetch_table_counts(
                    cursor,
                    schema=PRODUCTION_SCHEMA,
                    tables=EXPECTED_TABLES,
                )
            )

            changed_tables = sorted(
                table
                for table in EXPECTED_TABLES
                if (
                    int(production_current[table])
                    != int(
                        production_baseline[table]
                    )
                )
            )

            print(
                "PRODUCTION_CHANGED_TABLE_COUNT="
                f"{len(changed_tables)}"
            )

            if changed_tables:
                raise RuntimeError(
                    "PRODUCTION_INTEGRITY_FAILED:"
                    + ",".join(changed_tables)
                )

            print(
                "PRODUCTION_INTEGRITY=PASS"
            )

            shadow_sequence_count = (
                fetch_sequence_count(
                    cursor,
                    SHADOW_SCHEMA,
                )
            )

            print(
                "SHADOW_SEQUENCE_COUNT="
                f"{shadow_sequence_count}"
            )

            if (
                shadow_sequence_count
                != EXPECTED_SHADOW_SEQUENCE_COUNT
            ):
                raise RuntimeError(
                    "SHADOW_SEQUENCE_COUNT_MISMATCH"
                )

            leaks = (
                fetch_production_sequence_leaks(
                    cursor
                )
            )

            print(
                "PRODUCTION_SEQUENCE_LEAK_COUNT="
                f"{len(leaks)}"
            )

            if leaks:
                raise RuntimeError(
                    "PRODUCTION_SEQUENCE_LEAK_DETECTED"
                )

            print(
                "SEQUENCE_CONTRACT=PASS"
            )

        connection.rollback()

    finally:
        connection.close()

    evidence = build_evidence(
        action="VERIFY_CLEANUP",
        shadow_run_id=shadow_run_id,
        status="PASS",
    )

    evidence.update(
        {
            "shadow_table_count": (
                len(actual_tables)
            ),
            "shadow_table_structure": "PASS",
            "cleanup_table_count": (
                len(CLEANUP_TABLES)
            ),
            "residual_table_count": 0,
            "residual_counts": residual_counts,
            "reference_seed_integrity": "PASS",
            "reference_shadow": reference_shadow,
            "production_integrity": "PASS",
            "production_changed_table_count": 0,
            "shadow_sequence_count": (
                shadow_sequence_count
            ),
            "production_sequence_leak_count": 0,
            "db_mode": "READ_ONLY",
        }
    )

    key = evidence_key(
        prefix=prefix,
        shadow_run_id=shadow_run_id,
        name="verify-cleanup",
    )

    version_id = put_evidence(
        s3=s3,
        bucket=bucket,
        key=key,
        payload=evidence,
    )

    print(
        "VERIFY_CLEANUP_EVIDENCE_PUT=PASS"
    )
    print(
        f"VERIFY_CLEANUP_EVIDENCE_KEY={key}"
    )
    print(
        "VERIFY_CLEANUP_EVIDENCE_VERSION_ID="
        f"{version_id or ''}"
    )

    loaded = get_evidence(
        s3=s3,
        bucket=bucket,
        key=key,
    )

    if loaded != evidence:
        raise RuntimeError(
            "VERIFY_CLEANUP_EVIDENCE_MISMATCH"
        )

    print(
        "VERIFY_CLEANUP_EVIDENCE_VERIFY=PASS"
    )
    print(
        "PREPROCESSOR_SHADOW_VERIFY_CLEANUP=SUCCESS"
    )

    return 0


def run_cleanup(args) -> int:
    shadow_run_id = args.shadow_run_id.strip()

    if not shadow_run_id:
        raise RuntimeError(
            "SHADOW_RUN_ID_REQUIRED"
        )

    bucket = require_env(
        "PREPROCESSOR_SHADOW_EVIDENCE_BUCKET"
    )

    prefix = os.getenv(
        "PREPROCESSOR_SHADOW_EVIDENCE_PREFIX",
        DEFAULT_PREFIX,
    ).strip()

    s3 = build_s3_client()

    prepare_key = evidence_key(
        prefix=prefix,
        shadow_run_id=shadow_run_id,
        name="prepare",
    )

    prepare = get_evidence(
        s3=s3,
        bucket=bucket,
        key=prepare_key,
    )

    if prepare.get("action") != "PREPARE":
        raise RuntimeError(
            "PREPARE_EVIDENCE_ACTION_INVALID"
        )

    if prepare.get("status") != "PASS":
        raise RuntimeError(
            "PREPARE_EVIDENCE_NOT_PASS"
        )

    print("PREPARE_EVIDENCE=PASS")

    quality_gate_status = "UNAVAILABLE"

    quality_key = evidence_key(
        prefix=prefix,
        shadow_run_id=shadow_run_id,
        name="quality-gate",
    )

    try:
        quality = get_evidence(
            s3=s3,
            bucket=bucket,
            key=quality_key,
        )

        if quality.get("action") == "QUALITY_GATE":
            quality_gate_status = str(
                quality.get(
                    "status",
                    "UNKNOWN",
                )
            )
    except Exception:
        quality_gate_status = "UNAVAILABLE"

    print(
        "QUALITY_GATE_STATUS_FOR_CLEANUP="
        f"{quality_gate_status}"
    )

    connection = build_db_connection()

    try:
        connection.set_session(
            readonly=False,
            autocommit=False,
        )

        with connection.cursor() as cursor:
            before_counts = fetch_table_counts(
                cursor,
                schema=SHADOW_SCHEMA,
                tables=CLEANUP_TABLES,
            )

            reference_before = fetch_table_counts(
                cursor,
                schema=SHADOW_SCHEMA,
                tables=REFERENCE_TABLES,
            )

            cleanup_shadow_tables(
                cursor
            )

            after_counts = fetch_table_counts(
                cursor,
                schema=SHADOW_SCHEMA,
                tables=CLEANUP_TABLES,
            )

            residual_tables = sorted(
                table
                for table, count
                in after_counts.items()
                if count != 0
            )

            if residual_tables:
                raise RuntimeError(
                    "SHADOW_CLEANUP_RESIDUAL:"
                    + ",".join(
                        residual_tables
                    )
                )

            reference_after = fetch_table_counts(
                cursor,
                schema=SHADOW_SCHEMA,
                tables=REFERENCE_TABLES,
            )

            if reference_after != reference_before:
                raise RuntimeError(
                    "REFERENCE_TABLE_CHANGED_BY_CLEANUP"
                )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    print(
        f"CLEANUP_TABLE_COUNT="
        f"{len(CLEANUP_TABLES)}"
    )
    print(
        "SHADOW_CLEANUP_RESIDUAL_COUNT=0"
    )
    print(
        "REFERENCE_TABLE_PRESERVATION=PASS"
    )

    evidence = build_evidence(
        action="CLEANUP",
        shadow_run_id=shadow_run_id,
        status="PASS",
    )

    evidence.update(
        {
            "cleanup_schema": SHADOW_SCHEMA,
            "cleanup_table_count": (
                len(CLEANUP_TABLES)
            ),
            "cleanup_tables": list(
                CLEANUP_TABLES
            ),
            "before_counts": before_counts,
            "after_counts": after_counts,
            "residual_table_count": 0,
            "reference_before": (
                reference_before
            ),
            "reference_after": (
                reference_after
            ),
            "production_schema_dml": (
                "FORBIDDEN"
            ),
            "quality_gate_status": (
                quality_gate_status
            ),
        }
    )

    key = evidence_key(
        prefix=prefix,
        shadow_run_id=shadow_run_id,
        name="cleanup",
    )

    version_id = put_evidence(
        s3=s3,
        bucket=bucket,
        key=key,
        payload=evidence,
    )

    print("CLEANUP_EVIDENCE_PUT=PASS")
    print(f"CLEANUP_EVIDENCE_KEY={key}")
    print(
        "CLEANUP_EVIDENCE_VERSION_ID="
        f"{version_id or ''}"
    )

    loaded = get_evidence(
        s3=s3,
        bucket=bucket,
        key=key,
    )

    if loaded != evidence:
        raise RuntimeError(
            "CLEANUP_EVIDENCE_MISMATCH"
        )

    print("CLEANUP_EVIDENCE_VERIFY=PASS")
    print(
        "PREPROCESSOR_SHADOW_CLEANUP=SUCCESS"
    )

    return 0


def run_evidence_smoke(args) -> int:
    bucket = require_env(
        "PREPROCESSOR_SHADOW_EVIDENCE_BUCKET"
    )

    prefix = os.getenv(
        "PREPROCESSOR_SHADOW_EVIDENCE_PREFIX",
        DEFAULT_PREFIX,
    ).strip()

    shadow_run_id = args.shadow_run_id.strip()

    if not shadow_run_id:
        raise RuntimeError("SHADOW_RUN_ID_REQUIRED")

    key = evidence_key(
        prefix=prefix,
        shadow_run_id=shadow_run_id,
        name="control-runner-smoke",
    )

    payload = build_evidence(
        action="EVIDENCE_SMOKE",
        shadow_run_id=shadow_run_id,
        status="PASS",
    )

    s3 = build_s3_client()

    version_id = put_evidence(
        s3=s3,
        bucket=bucket,
        key=key,
        payload=payload,
    )

    print("S3_PUT=PASS")
    print(f"EVIDENCE_BUCKET={bucket}")
    print(f"EVIDENCE_KEY={key}")
    print(
        f"EVIDENCE_VERSION_ID="
        f"{version_id or ''}"
    )

    loaded = get_evidence(
        s3=s3,
        bucket=bucket,
        key=key,
    )

    print("S3_GET=PASS")

    if loaded != payload:
        raise RuntimeError(
            "EVIDENCE_CONTENT_MISMATCH"
        )

    print("S3_CONTENT_VERIFY=PASS")
    print(
        "PREPROCESSOR_SHADOW_CONTROL_"
        "EVIDENCE=SUCCESS"
    )

    return 0


def run_prepare(args) -> int:
    shadow_run_id = args.shadow_run_id.strip()

    if not shadow_run_id:
        raise RuntimeError("SHADOW_RUN_ID_REQUIRED")

    bucket = require_env(
        "PREPROCESSOR_SHADOW_EVIDENCE_BUCKET"
    )

    prefix = os.getenv(
        "PREPROCESSOR_SHADOW_EVIDENCE_PREFIX",
        DEFAULT_PREFIX,
    ).strip()

    evidence = build_evidence(
        action="PREPARE",
        shadow_run_id=shadow_run_id,
        status="STARTED",
    )

    print(f"SHADOW_RUN_ID={shadow_run_id}")
    print("PREPARE_DB_MODE=READ_ONLY")

    connection = build_db_connection()

    try:
        connection.set_session(
            readonly=True,
            autocommit=False,
        )

        with connection.cursor() as cursor:
            production_tables = fetch_table_names(
                cursor,
                PRODUCTION_SCHEMA,
            )

            shadow_tables = fetch_table_names(
                cursor,
                SHADOW_SCHEMA,
            )

            print(
                f"PRODUCTION_TABLE_COUNT="
                f"{len(production_tables)}"
            )
            print(
                f"SHADOW_TABLE_COUNT="
                f"{len(shadow_tables)}"
            )

            validate_table_contract(
                production_tables=production_tables,
                shadow_tables=shadow_tables,
            )

            if len(production_tables) != EXPECTED_TABLE_COUNT:
                raise RuntimeError(
                    "PRODUCTION_TABLE_COUNT_MISMATCH"
                )

            if len(shadow_tables) != EXPECTED_TABLE_COUNT:
                raise RuntimeError(
                    "SHADOW_TABLE_COUNT_MISMATCH"
                )

            print("TABLE_CONTRACT=PASS")

            production_counts = fetch_table_counts(
                cursor,
                schema=PRODUCTION_SCHEMA,
                tables=EXPECTED_TABLES,
            )

            reference_production = fetch_table_counts(
                cursor,
                schema=PRODUCTION_SCHEMA,
                tables=REFERENCE_TABLES,
            )

            reference_shadow = fetch_table_counts(
                cursor,
                schema=SHADOW_SCHEMA,
                tables=REFERENCE_TABLES,
            )

            if reference_shadow != reference_production:
                raise RuntimeError(
                    "SHADOW_REFERENCE_SEED_MISMATCH"
                )

            print("REFERENCE_SEED_CONTRACT=PASS")

            shadow_sequence_count = fetch_sequence_count(
                cursor,
                SHADOW_SCHEMA,
            )

            print(
                f"SHADOW_SEQUENCE_COUNT="
                f"{shadow_sequence_count}"
            )

            if (
                shadow_sequence_count
                != EXPECTED_SHADOW_SEQUENCE_COUNT
            ):
                raise RuntimeError(
                    "SHADOW_SEQUENCE_COUNT_MISMATCH"
                )

            leaks = fetch_production_sequence_leaks(
                cursor
            )

            print(
                f"PRODUCTION_SEQUENCE_LEAK_COUNT="
                f"{len(leaks)}"
            )

            if leaks:
                raise RuntimeError(
                    "PRODUCTION_SEQUENCE_LEAK_DETECTED"
                )

            print("SEQUENCE_CONTRACT=PASS")

        connection.rollback()

    finally:
        connection.close()

    evidence.update(
        {
            "status": "PASS",
            "db_mode": "READ_ONLY",
            "production_schema": PRODUCTION_SCHEMA,
            "shadow_schema": SHADOW_SCHEMA,
            "production_table_count": len(
                production_tables
            ),
            "shadow_table_count": len(
                shadow_tables
            ),
            "shadow_sequence_count": (
                shadow_sequence_count
            ),
            "production_sequence_leak_count": 0,
            "production_baseline": (
                production_counts
            ),
            "reference_seed": {
                "production": reference_production,
                "shadow": reference_shadow,
            },
        }
    )

    key = evidence_key(
        prefix=prefix,
        shadow_run_id=shadow_run_id,
        name="prepare",
    )

    s3 = build_s3_client()

    version_id = put_evidence(
        s3=s3,
        bucket=bucket,
        key=key,
        payload=evidence,
    )

    print("PREPARE_EVIDENCE_PUT=PASS")
    print(f"PREPARE_EVIDENCE_KEY={key}")
    print(
        f"PREPARE_EVIDENCE_VERSION_ID="
        f"{version_id or ''}"
    )

    loaded = get_evidence(
        s3=s3,
        bucket=bucket,
        key=key,
    )

    if loaded != evidence:
        raise RuntimeError(
            "PREPARE_EVIDENCE_CONTENT_MISMATCH"
        )

    print("PREPARE_EVIDENCE_VERIFY=PASS")
    print("PREPROCESSOR_SHADOW_PREPARE=SUCCESS")

    return 0


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--action",
        required=True,
        choices=[
            "EVIDENCE_SMOKE",
            "PREPARE",
            "QUALITY_GATE",
            "CLEANUP",
            "VERIFY_CLEANUP",
        ],
    )

    parser.add_argument(
        "--shadow-run-id",
        required=True,
    )

    parser.add_argument(
        "--trade-date",
        required=False,
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if args.action == "EVIDENCE_SMOKE":
            return run_evidence_smoke(args)

        if args.action == "PREPARE":
            return run_prepare(args)

        if args.action == "QUALITY_GATE":
            return run_quality_gate(args)

        if args.action == "CLEANUP":
            return run_cleanup(args)

        if args.action == "VERIFY_CLEANUP":
            return run_verify_cleanup(args)

        raise RuntimeError(
            f"UNSUPPORTED_ACTION:{args.action}"
        )

    except Exception as exc:
        print(
            "SHADOW_CONTROL_FAILED="
            f"{type(exc).__name__}:{exc}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())