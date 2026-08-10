import importlib.util
import sys
import types
from pathlib import Path

import pytest


fake_boto3 = types.ModuleType("boto3")


def fake_boto3_client(name):
    raise AssertionError(
        "boto3.client must not run "
        "during pure unit tests"
    )


fake_boto3.client = fake_boto3_client
sys.modules["boto3"] = fake_boto3


fake_psycopg2 = types.ModuleType("psycopg2")


def fake_connect(**kwargs):
    raise AssertionError(
        "psycopg2.connect must not run "
        "during pure unit tests"
    )


fake_psycopg2.connect = fake_connect
sys.modules["psycopg2"] = fake_psycopg2


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "preprocessor_shadow_control.py"
)

SPEC = importlib.util.spec_from_file_location(
    "shadow_control",
    MODULE_PATH,
)

MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_evidence_key():
    result = MODULE.evidence_key(
        prefix="preprocessor-shadow",
        shadow_run_id="run-123",
        name="prepare",
    )

    assert result == (
        "preprocessor-shadow/"
        "run-123/"
        "prepare.json"
    )


def test_evidence_key_normalizes_slashes():
    result = MODULE.evidence_key(
        prefix="/preprocessor-shadow/",
        shadow_run_id="run-123",
        name="final",
    )

    assert result == (
        "preprocessor-shadow/"
        "run-123/"
        "final.json"
    )


def test_build_evidence_contract():
    result = MODULE.build_evidence(
        action="PREPARE",
        shadow_run_id="run-123",
        status="PASS",
    )

    assert result["schema_version"] == "1.0"
    assert result["service"] == "preprocessor"
    assert result["component"] == "shadow-control"
    assert result["action"] == "PREPARE"
    assert result["shadow_run_id"] == "run-123"
    assert result["status"] == "PASS"
    assert result["recorded_at"]


def test_require_env(monkeypatch):
    monkeypatch.setenv(
        "TEST_SHADOW_ENV",
        "value",
    )

    assert (
        MODULE.require_env("TEST_SHADOW_ENV")
        == "value"
    )


def test_require_env_missing(monkeypatch):
    monkeypatch.delenv(
        "TEST_SHADOW_ENV",
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match="TEST_SHADOW_ENV_REQUIRED",
    ):
        MODULE.require_env(
            "TEST_SHADOW_ENV"
        )


def test_default_prefix():
    assert (
        MODULE.DEFAULT_PREFIX
        == "preprocessor-shadow"
    )


def test_expected_table_contract():
    assert len(MODULE.EXPECTED_TABLES) == 18
    assert (
        MODULE.EXPECTED_TABLE_COUNT
        == 18
    )


def test_reference_table_contract():
    assert MODULE.REFERENCE_TABLES == (
        "pre_event_master",
        "pre_event_keyword",
        "pre_event_sector_weight",
    )


def test_expected_sequence_contract():
    assert (
        MODULE.EXPECTED_SHADOW_SEQUENCE_COUNT
        == 10
    )


def test_validate_table_contract_pass():
    tables = sorted(
        MODULE.EXPECTED_TABLES
    )

    MODULE.validate_table_contract(
        production_tables=tables,
        shadow_tables=tables,
    )


def test_validate_production_table_failure():
    tables = sorted(
        MODULE.EXPECTED_TABLES
    )

    with pytest.raises(
        RuntimeError,
        match="PRODUCTION_TABLE_CONTRACT_MISMATCH",
    ):
        MODULE.validate_table_contract(
            production_tables=tables[:-1],
            shadow_tables=tables,
        )


def test_validate_shadow_table_failure():
    tables = sorted(
        MODULE.EXPECTED_TABLES
    )

    with pytest.raises(
        RuntimeError,
        match="SHADOW_TABLE_CONTRACT_MISMATCH",
    ):
        MODULE.validate_table_contract(
            production_tables=tables,
            shadow_tables=tables[:-1],
        )


def test_prepare_cli_action(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "shadow-control",
            "--action",
            "PREPARE",
            "--shadow-run-id",
            "run-123",
        ],
    )

    args = MODULE.parse_args()

    assert args.action == "PREPARE"
    assert args.shadow_run_id == "run-123"

def test_required_shadow_output_contract():
    assert len(
        MODULE.REQUIRED_SHADOW_OUTPUT_TABLES
    ) == 14

    assert (
        "pre_agency_analysis"
        not in MODULE.REQUIRED_SHADOW_OUTPUT_TABLES
    )

    for table in MODULE.REFERENCE_TABLES:
        assert (
            table
            not in MODULE.REQUIRED_SHADOW_OUTPUT_TABLES
        )


def test_trade_date_core_contract():
    assert len(
        MODULE.TRADE_DATE_CORE_TABLES
    ) == 12

    assert (
        "pre_total_market_daily_feature"
        in MODULE.TRADE_DATE_CORE_TABLES
    )

    assert (
        "pre_total_stock_daily_feature"
        in MODULE.TRADE_DATE_CORE_TABLES
    )


def test_validate_positive_counts_pass():
    MODULE.validate_positive_counts(
        counts={
            "a": 1,
            "b": 10,
        },
        error_prefix="FAIL",
    )


def test_validate_positive_counts_failure():
    with pytest.raises(
        RuntimeError,
        match="SHADOW_OUTPUT_MISSING",
    ):
        MODULE.validate_positive_counts(
            counts={
                "good": 1,
                "bad": 0,
            },
            error_prefix=(
                "SHADOW_OUTPUT_MISSING"
            ),
        )


def test_quality_gate_cli_action(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "shadow-control",
            "--action",
            "QUALITY_GATE",
            "--shadow-run-id",
            "run-123",
            "--trade-date",
            "2026-08-07",
        ],
    )

    args = MODULE.parse_args()

    assert args.action == "QUALITY_GATE"
    assert args.shadow_run_id == "run-123"
    assert args.trade_date == "2026-08-07"

def test_cleanup_table_contract():
    assert len(MODULE.CLEANUP_TABLES) == 15

    for table in MODULE.REFERENCE_TABLES:
        assert table not in MODULE.CLEANUP_TABLES


def test_cleanup_table_union_contract():
    combined = set(
        MODULE.CLEANUP_TABLES
    ) | set(
        MODULE.REFERENCE_TABLES
    )

    assert combined == set(
        MODULE.EXPECTED_TABLES
    )


class FakeCleanupCursor:
    def __init__(self):
        self.sql = None

    def execute(self, sql):
        self.sql = sql


def test_cleanup_sql_contract():
    cursor = FakeCleanupCursor()

    MODULE.cleanup_shadow_tables(
        cursor
    )

    assert cursor.sql.startswith(
        "TRUNCATE TABLE "
    )

    assert (
        "CONTINUE IDENTITY"
        in cursor.sql
    )

    assert (
        '"preprocessor_shadow".'
        in cursor.sql
    )

    assert (
        '"preprocessor".'
        not in cursor.sql
    )

    for table in MODULE.CLEANUP_TABLES:
        assert (
            f'"{MODULE.SHADOW_SCHEMA}"'
            f'."{table}"'
            in cursor.sql
        )

    for table in MODULE.REFERENCE_TABLES:
        assert (
            f'"{MODULE.SHADOW_SCHEMA}"'
            f'."{table}"'
            not in cursor.sql
        )


def test_cleanup_cli_action(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "shadow-control",
            "--action",
            "CLEANUP",
            "--shadow-run-id",
            "run-123",
        ],
    )

    args = MODULE.parse_args()

    assert args.action == "CLEANUP"
    assert args.shadow_run_id == "run-123"

def test_verify_cleanup_cli_action(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "shadow-control",
            "--action",
            "VERIFY_CLEANUP",
            "--shadow-run-id",
            "run-123",
        ],
    )

    args = MODULE.parse_args()

    assert args.action == "VERIFY_CLEANUP"
    assert args.shadow_run_id == "run-123"


def test_verify_cleanup_is_distinct_action():
    assert MODULE.run_verify_cleanup is not MODULE.run_cleanup


def test_cleanup_tables_and_references_cover_expected():
    assert (
        set(MODULE.CLEANUP_TABLES)
        | set(MODULE.REFERENCE_TABLES)
    ) == set(MODULE.EXPECTED_TABLES)


def test_verify_cleanup_expected_table_count():
    assert len(MODULE.EXPECTED_TABLES) == 18
    assert len(MODULE.CLEANUP_TABLES) == 15
    assert len(MODULE.REFERENCE_TABLES) == 3