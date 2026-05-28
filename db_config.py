"""전처리 스크립트에서 공통으로 사용하는 PostgreSQL 연결 설정 모듈.

DB 접속 정보는 환경변수에서 읽고, 비밀번호는 기본값을 두지 않는다.
schema-per-domain 전환을 고려해 공통 search_path를 연결 옵션으로 주입한다.
"""

import os


def get_db_config():
    password = os.getenv("INTEREST_DB_PASSWORD")
    if not password:
        raise RuntimeError("INTEREST_DB_PASSWORD environment variable is required")

    return {
        "host": os.getenv("INTEREST_DB_HOST", "localhost"),
        "port": int(os.getenv("INTEREST_DB_PORT", "5433")),
        "dbname": os.getenv("INTEREST_DB_NAME", "portfolio"),
        "user": os.getenv("INTEREST_DB_USER", "postgres"),
        "password": password,
        "options": "-c search_path=preprocessor,interest,reference,legacy,public",
    }
