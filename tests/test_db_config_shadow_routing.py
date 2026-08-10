"""Shadow DB routing contract tests.

These tests validate search_path selection without opening a database
connection or executing the preprocessing pipeline.
"""

import pytest

import db_config


def test_default_run_mode_is_production(monkeypatch):
    monkeypatch.delenv("PREPROCESSOR_RUN_MODE", raising=False)

    assert db_config.get_preprocessor_run_mode() == "PRODUCTION"
    assert (
        db_config.get_preprocessor_search_path()
        == "preprocessor,interest,reference,legacy,public"
    )


def test_explicit_production_run_mode(monkeypatch):
    monkeypatch.setenv("PREPROCESSOR_RUN_MODE", "PRODUCTION")

    assert db_config.get_preprocessor_run_mode() == "PRODUCTION"
    assert (
        db_config.get_preprocessor_search_path()
        == "preprocessor,interest,reference,legacy,public"
    )


def test_shadow_run_mode_routes_shadow_schema_first(monkeypatch):
    monkeypatch.setenv("PREPROCESSOR_RUN_MODE", "SHADOW")

    assert db_config.get_preprocessor_run_mode() == "SHADOW"
    assert (
        db_config.get_preprocessor_search_path()
        == "preprocessor_shadow,preprocessor,interest,reference,legacy,public"
    )


def test_run_mode_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("PREPROCESSOR_RUN_MODE", "shadow")

    assert db_config.get_preprocessor_run_mode() == "SHADOW"


def test_invalid_run_mode_is_rejected(monkeypatch):
    monkeypatch.setenv("PREPROCESSOR_RUN_MODE", "INVALID")

    with pytest.raises(
        RuntimeError,
        match="PREPROCESSOR_RUN_MODE must be PRODUCTION or SHADOW",
    ):
        db_config.get_preprocessor_run_mode()


def test_db_config_uses_production_search_path(monkeypatch):
    monkeypatch.setenv("INTEREST_DB_PASSWORD", "test-only")
    monkeypatch.setenv("PREPROCESSOR_RUN_MODE", "PRODUCTION")

    config = db_config.get_db_config()

    assert (
        config["options"]
        == "-c search_path=preprocessor,interest,reference,legacy,public"
    )


def test_db_config_uses_shadow_search_path(monkeypatch):
    monkeypatch.setenv("INTEREST_DB_PASSWORD", "test-only")
    monkeypatch.setenv("PREPROCESSOR_RUN_MODE", "SHADOW")

    config = db_config.get_db_config()

    assert (
        config["options"]
        == "-c search_path=preprocessor_shadow,preprocessor,interest,reference,legacy,public"
    )


def test_db_password_is_still_required(monkeypatch):
    monkeypatch.delenv("INTEREST_DB_PASSWORD", raising=False)

    with pytest.raises(
        RuntimeError,
        match="INTEREST_DB_PASSWORD environment variable is required",
    ):
        db_config.get_db_config()
