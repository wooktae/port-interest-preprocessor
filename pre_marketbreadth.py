# pre_marketbreadth.py

import psycopg2
from db_config import get_db_config

PROCESSOR_VERSION = "2.0.0"


def get_conn():
    return psycopg2.connect(**get_db_config())


def aggregate_marketbreadth(conn):

    cur = conn.cursor()

    cur.execute("""
    WITH base AS (
        SELECT
            date,
            COALESCE(advancers_count, 0) AS advancers_count,
            COALESCE(decliners_count, 0) AS decliners_count,
            COALESCE(unchanged_count, 0) AS unchanged_count,
            total_market_volume,
            LAG(total_market_volume) OVER (
                ORDER BY date
            ) AS prev_volume
        FROM interest_marketbreadth_raw
    ),

    calc AS (
        SELECT
            date,
            advancers_count,
            decliners_count,
            unchanged_count,
            (advancers_count + decliners_count + unchanged_count) AS total_count,

            CASE
                WHEN (advancers_count + decliners_count + unchanged_count) = 0 THEN 0
                ELSE ROUND(
                    advancers_count::numeric
                    / (advancers_count + decliners_count + unchanged_count),
                    6
                )
            END AS advance_decline_ratio,

            -- 🔥 추가: decline_share
            CASE
                WHEN (advancers_count + decliners_count + unchanged_count) = 0 THEN 0
                ELSE ROUND(
                    decliners_count::numeric
                    / (advancers_count + decliners_count + unchanged_count),
                    6
                )
            END AS decline_share,

            CASE
                WHEN (advancers_count + decliners_count + unchanged_count) = 0 THEN 0
                ELSE ROUND(
                    (advancers_count - decliners_count)::numeric
                    / (advancers_count + decliners_count + unchanged_count),
                    6
                )
            END AS advance_decline_diff_ratio,

            CASE
                WHEN total_market_volume IS NULL
                  OR prev_volume IS NULL
                  OR prev_volume = 0
                THEN 0
                ELSE ROUND(
                    (total_market_volume - prev_volume)::numeric
                    / prev_volume,
                    6
                )
            END AS volume_change_ratio
        FROM base
    )

    INSERT INTO pre_marketbreadth_daily_feature
    (
        date,
        advancers,
        decliners,
        unchanged,
        total_count,
        advance_decline_ratio,
        decline_share,              -- 🔥 추가
        advance_decline_diff_ratio,
        volume_change_ratio,
        breadth_pressure_score,
        breadth_thrust_flag,        -- 🔥 추가
        processor_version
    )
    SELECT
        date,
        advancers_count,
        decliners_count,
        unchanged_count,
        total_count,
        advance_decline_ratio,
        decline_share,
        advance_decline_diff_ratio,
        volume_change_ratio,

        ROUND(
            (advance_decline_diff_ratio * 0.7)
            + (volume_change_ratio * 0.3),
            6
        ) AS breadth_pressure_score,

        -- 🔥 추가: thrust flag
        CASE
            WHEN advance_decline_ratio > 0.7 THEN 1
            ELSE 0
        END AS breadth_thrust_flag,

        %s
    FROM calc
    ON CONFLICT (date)
    DO UPDATE SET
        advancers = EXCLUDED.advancers,
        decliners = EXCLUDED.decliners,
        unchanged = EXCLUDED.unchanged,
        total_count = EXCLUDED.total_count,
        advance_decline_ratio = EXCLUDED.advance_decline_ratio,
        decline_share = EXCLUDED.decline_share,                -- 🔥 추가
        advance_decline_diff_ratio = EXCLUDED.advance_decline_diff_ratio,
        volume_change_ratio = EXCLUDED.volume_change_ratio,
        breadth_pressure_score = EXCLUDED.breadth_pressure_score,
        breadth_thrust_flag = EXCLUDED.breadth_thrust_flag,    -- 🔥 추가
        processor_version = EXCLUDED.processor_version
    """, (PROCESSOR_VERSION,))

    conn.commit()
    cur.close()


def run():
    print("===== PRE MARKETBREADTH START =====")
    conn = get_conn()
    aggregate_marketbreadth(conn)
    conn.close()
    print("===== PRE MARKETBREADTH DONE =====")


if __name__ == "__main__":
    run()