"""공매도 원천 데이터를 종목/일자 단위 short feature로 집계하는 스크립트.

interest_shortsell_raw에서 공매도 비율 평균, 모멘텀, z-score, spike flag,
pressure score를 계산해 pre_shortsell_daily_feature에 저장한다.
"""

import psycopg2
from db_config import get_db_config

PROCESSOR_VERSION = "3.0.0"


def get_conn():
    return psycopg2.connect(**get_db_config())


def aggregate_shortsell(conn):

    cur = conn.cursor()

    cur.execute("""

    WITH base AS (
        SELECT
            ticker_code,
            trade_date AS date,
            short_volume,
            short_amount,
            total_volume,
            short_ratio
        FROM interest_shortsell_raw
    ),

    enriched AS (
        SELECT
            ticker_code,
            date,

            short_volume,
            short_amount,
            total_volume,
            short_ratio,

            -- ✅ 평균 (기존 momentum → avg)
            AVG(short_ratio)
                OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                ) AS short_ratio_avg_3d,

            AVG(short_ratio)
                OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                ) AS short_ratio_avg_5d,

            -- ✅ diff momentum
            short_ratio
                - LAG(short_ratio,3)
                  OVER (PARTITION BY ticker_code ORDER BY date)
                AS short_ratio_momentum_3d,

            short_ratio
                - LAG(short_ratio,5)
                  OVER (PARTITION BY ticker_code ORDER BY date)
                AS short_ratio_momentum_5d,

            -- ✅ zscore (20d)
            CASE
                WHEN STDDEV(short_ratio)
                     OVER (
                        PARTITION BY ticker_code
                        ORDER BY date
                        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                     ) IS NULL
                  OR STDDEV(short_ratio)
                     OVER (
                        PARTITION BY ticker_code
                        ORDER BY date
                        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                     ) = 0
                THEN NULL
                ELSE (
                    short_ratio
                    - AVG(short_ratio)
                      OVER (
                        PARTITION BY ticker_code
                        ORDER BY date
                        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                      )
                )
                /
                STDDEV(short_ratio)
                OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                )
            END AS short_ratio_zscore_20d

        FROM base
    )

    INSERT INTO pre_shortsell_daily_feature (

        ticker_code,
        date,

        short_volume,
        short_amount,
        total_volume,

        short_ratio,

        short_ratio_avg_3d,
        short_ratio_avg_5d,

        short_ratio_momentum_3d,
        short_ratio_momentum_5d,

        short_ratio_zscore_20d,

        short_spike_flag,

        short_pressure_score,

        processor_version,
        updated_at

    )

    SELECT

        ticker_code,
        date,

        short_volume,
        short_amount,
        total_volume,

        short_ratio,

        short_ratio_avg_3d,
        short_ratio_avg_5d,

        short_ratio_momentum_3d,
        short_ratio_momentum_5d,

        short_ratio_zscore_20d,

        -- ✅ spike flag
        CASE
            WHEN short_ratio_zscore_20d IS NOT NULL
             AND short_ratio_zscore_20d >= 2
            THEN TRUE
            ELSE FALSE
        END AS short_spike_flag,

        -- ✅ pressure score (개선 버전)
        CASE
            WHEN short_ratio IS NULL THEN NULL
            ELSE ROUND(
                (
                    COALESCE(short_ratio,0) * 0.5
                  + COALESCE(short_ratio_zscore_20d,0) * 0.3
                  + COALESCE(short_ratio_momentum_5d,0) * 0.2
                )::numeric,
                6
            )
        END AS short_pressure_score,

        %s,
        now()

    FROM enriched

    ON CONFLICT (ticker_code, date)
    DO UPDATE SET

        short_volume = EXCLUDED.short_volume,
        short_amount = EXCLUDED.short_amount,
        total_volume = EXCLUDED.total_volume,

        short_ratio = EXCLUDED.short_ratio,

        short_ratio_avg_3d = EXCLUDED.short_ratio_avg_3d,
        short_ratio_avg_5d = EXCLUDED.short_ratio_avg_5d,

        short_ratio_momentum_3d = EXCLUDED.short_ratio_momentum_3d,
        short_ratio_momentum_5d = EXCLUDED.short_ratio_momentum_5d,

        short_ratio_zscore_20d = EXCLUDED.short_ratio_zscore_20d,

        short_spike_flag = EXCLUDED.short_spike_flag,

        short_pressure_score = EXCLUDED.short_pressure_score,

        processor_version = EXCLUDED.processor_version,
        updated_at = now()

    """, (PROCESSOR_VERSION,))

    conn.commit()
    cur.close()


def run():

    print("===== PRE SHORTSELL START =====")

    conn = get_conn()

    try:
        aggregate_shortsell(conn)
    finally:
        conn.close()

    print("===== PRE SHORTSELL DONE =====")


if __name__ == "__main__":
    run()
