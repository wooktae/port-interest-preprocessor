"""시장 휴일 여부를 조회하는 외부 API helper 모듈.

주말을 우선 판정하고, Nager.Date public holiday API를 호출해 KR/US 휴일을
메모리 캐시에 저장한다. 문서화/정적 검증 중에는 호출하지 않는다.
"""

import requests
from datetime import datetime, date

HOLIDAY_API_BASE = "https://date.nager.at/api/v3/PublicHolidays"

# 캐시 (API 호출 최소화)
_cache = {}


def _fetch_holidays(year: int, country_code: str):
    key = (country_code, year)

    if key in _cache:
        return _cache[key]

    url = f"{HOLIDAY_API_BASE}/{year}/{country_code}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()

    holidays = {
        datetime.strptime(r["date"], "%Y-%m-%d").date()
        for r in resp.json()
    }

    _cache[key] = holidays
    return holidays


def is_holiday(target_date: date, market: str) -> bool:
    """
    market:
      - "KR"
      - "US"
    """

    # 주말
    if target_date.weekday() >= 5:
        return True

    # 공휴일
    holidays = _fetch_holidays(target_date.year, market)

    return target_date in holidays
