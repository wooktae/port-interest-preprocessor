import importlib.util
import sys
import types
from pathlib import Path

import pytest


fake_boto3 = types.ModuleType("boto3")


def fake_client(name):
    raise AssertionError(
        "boto3.client must not be called "
        "during pure unit tests"
    )


fake_boto3.client = fake_client
sys.modules["boto3"] = fake_boto3


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
        action="EVIDENCE_SMOKE",
        shadow_run_id="run-123",
        status="PASS",
    )

    assert result["schema_version"] == "1.0"
    assert result["service"] == "preprocessor"
    assert result["component"] == "shadow-control"
    assert result["action"] == "EVIDENCE_SMOKE"
    assert result["shadow_run_id"] == "run-123"
    assert result["status"] == "PASS"
    assert result["recorded_at"]


def test_require_env(monkeypatch):
    monkeypatch.setenv(
        "TEST_SHADOW_ENV",
        "value",
    )

    assert (
        MODULE.require_env(
            "TEST_SHADOW_ENV"
        )
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