"""Preprocessor orchestration structure tests.

These tests validate the production entrypoint without connecting to the
database or running the preprocessing pipeline.
"""

import ast
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PRE_DAILY_PATH = REPOSITORY_ROOT / "pre_daily.py"

EXPECTED_RUN_ORDER = [
    "pre_news_analysis.run",
    "pre_news_event_detection.run",
    "pre_news_daily_aggregator.run",
    "pre_agency_daily_aggregator.run",
    "pre_commodity.run",
    "pre_foreignindex.run",
    "pre_macroeconomic.run",
    "pre_price.run",
    "pre_marketbreadth.run",
    "pre_investorflow.run",
    "pre_program.run",
    "pre_shortsell.run",
    "pre_total_market_daily_feature.run",
    "pre_total_stock_daily_feature.run",
]


def load_tree() -> ast.Module:
    source = PRE_DAILY_PATH.read_text(encoding="utf-8-sig")
    return ast.parse(source, filename=str(PRE_DAILY_PATH))


def call_name(node: ast.Call) -> str | None:
    function = node.func

    if isinstance(function, ast.Name):
        return function.id

    if isinstance(function, ast.Attribute) and isinstance(
        function.value,
        ast.Name,
    ):
        return f"{function.value.id}.{function.attr}"

    return None


def test_pre_daily_has_main_guard() -> None:
    tree = load_tree()

    guards = [
        node
        for node in tree.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and ast.unparse(node.test) == "__name__ == '__main__'"
    ]

    assert len(guards) == 1

    guard_calls = [
        call_name(node.value)
        for node in guards[0].body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
    ]

    assert guard_calls == ["run"]


def test_pre_daily_run_order() -> None:
    tree = load_tree()

    run_functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "run"
    ]

    assert len(run_functions) == 1

    actual_calls = [
        call_name(node.value)
        for node in run_functions[0].body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
    ]

    pipeline_calls = [
        name
        for name in actual_calls
        if name is not None and name.startswith("pre_")
    ]

    assert pipeline_calls == EXPECTED_RUN_ORDER