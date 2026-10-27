"""Shared PostgreSQL connection configuration module used by the preprocessing scripts.

DB connection details are read from environment variables, and the password has no default.
To accommodate the schema-per-domain transition, a common search_path is injected as a connection option.
"""

import os


PRODUCTION_RUN_MODE = "PRODUCTION"
SHADOW_RUN_MODE = "SHADOW"

PRODUCTION_SEARCH_PATH = (
    "preprocessor,interest,reference,legacy,public"
)

SHADOW_SEARCH_PATH = (
    "preprocessor_shadow,preprocessor,interest,reference,legacy,public"
)


def get_preprocessor_run_mode():
    run_mode = os.getenv(
        "PREPROCESSOR_RUN_MODE",
        PRODUCTION_RUN_MODE,
    ).strip().upper()

    if run_mode not in {
        PRODUCTION_RUN_MODE,
        SHADOW_RUN_MODE,
    }:
        raise RuntimeError(
            "PREPROCESSOR_RUN_MODE must be PRODUCTION or SHADOW"
        )

    return run_mode


def get_preprocessor_search_path():
    run_mode = get_preprocessor_run_mode()

    if run_mode == SHADOW_RUN_MODE:
        return SHADOW_SEARCH_PATH

    return PRODUCTION_SEARCH_PATH


def get_db_config():
    password = os.getenv("INTEREST_DB_PASSWORD")
    if not password:
        raise RuntimeError("INTEREST_DB_PASSWORD environment variable is required")

    search_path = get_preprocessor_search_path()

    return {
        "host": os.getenv("INTEREST_DB_HOST", "localhost"),
        "port": int(os.getenv("INTEREST_DB_PORT", "5433")),
        "dbname": os.getenv("INTEREST_DB_NAME", "portfolio"),
        "user": os.getenv("INTEREST_DB_USER", "postgres"),
        "password": password,
        "options": f"-c search_path={search_path}",
    }
