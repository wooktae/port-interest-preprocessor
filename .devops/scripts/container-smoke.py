"""Import-only smoke test for the Preprocessor container.

This script must never call a module's run() function.
"""

import importlib
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


MODULES = [
    "db_config",
    "interest_get_holidays",
    "pre_agency_analysis",
    "pre_agency_daily_aggregator",
    "pre_commodity",
    "pre_daily",
    "pre_foreignindex",
    "pre_investorflow",
    "pre_macroeconomic",
    "pre_marketbreadth",
    "pre_news_analysis",
    "pre_news_daily_aggregator",
    "pre_news_event_detection",
    "pre_price",
    "pre_program",
    "pre_shortsell",
    "pre_total_market_daily_feature",
    "pre_total_stock_daily_feature",
]


def main() -> int:
    print(f"REPOSITORY_ROOT={REPOSITORY_ROOT}")

    for module_name in MODULES:
        module = importlib.import_module(module_name)

        if module_name.startswith("pre_"):
            run_function = getattr(module, "run", None)

            if not callable(run_function):
                raise RuntimeError(
                    f"Missing callable run(): {module_name}"
                )

        print(f"IMPORT_OK={module_name}")

    print(f"PYTHON_VERSION={sys.version.split()[0]}")
    print(f"MODULE_COUNT={len(MODULES)}")
    print("CONTAINER_IMPORT_SMOKE=SUCCESS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())