import psycopg2
from db_config import get_db_config

PROCESSOR_VERSION = "3.0.0"


def get_conn():
    return psycopg2.connect(**get_db_config())


def aggregate_program(conn):
    cur = conn.cursor()

    cur.execute("""
    WITH price AS (
        SELECT
            price_date AS date,
            SUM(volume * close_price) AS traded_value
        FROM interest_price_raw
        GROUP BY price_date
    ),

    base AS (
        SELECT
            p.trade_date AS date,
            p.arbitrage_net_amount,
            p.nonarb_net_amount,
            p.total_net_amount,
            pr.traded_value
        FROM interest_program_raw p
        LEFT JOIN price pr
          ON p.trade_date = pr.date
    ),

    ratio AS (
        SELECT
            date,
            arbitrage_net_amount,
            nonarb_net_amount,
            total_net_amount,
            traded_value,

            CASE
                WHEN traded_value IS NULL OR traded_value = 0 THEN NULL
                ELSE ROUND((arbitrage_net_amount / traded_value)::numeric, 12)
            END AS arbitrage_ratio,

            CASE
                WHEN traded_value IS NULL OR traded_value = 0 THEN NULL
                ELSE ROUND((nonarb_net_amount / traded_value)::numeric, 12)
            END AS nonarb_ratio,

            CASE
                WHEN traded_value IS NULL OR traded_value = 0 THEN NULL
                ELSE ROUND((total_net_amount / traded_value)::numeric, 12)
            END AS program_ratio

        FROM base
    ),

    enriched AS (
        SELECT
            *,

            /* 핵심 pressure: 원본 ratio 기반 */
            CASE
                WHEN arbitrage_ratio IS NULL AND nonarb_ratio IS NULL THEN NULL
                ELSE ROUND(
                    COALESCE(nonarb_ratio, 0) * 0.7
                  + COALESCE(arbitrage_ratio, 0) * 0.3,
                    12
                )
            END AS program_pressure_score_raw

        FROM ratio
    ),

    momentum AS (
        SELECT
            *,

            ROUND(
                AVG(program_ratio)
                OVER (
                    ORDER BY date
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                ),
                12
            ) AS program_momentum_3d,

            ROUND(
                AVG(program_ratio)
                OVER (
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                ),
                12
            ) AS program_momentum_5d,

            ROUND(
                (
                    total_net_amount
                    - AVG(total_net_amount) OVER (
                        ORDER BY date
                        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                    )
                )
                /
                NULLIF(
                    STDDEV(total_net_amount) OVER (
                        ORDER BY date
                        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                    ),
                    0
                ),
                6
            ) AS program_strength_zscore

        FROM enriched
    )

    INSERT INTO pre_program_daily_feature (
        date,

        arbitrage_net_amount,
        nonarb_net_amount,
        total_net_amount,

        arbitrage_ratio,
        nonarb_ratio,
        program_ratio,

        program_pressure_score,

        program_momentum_3d,
        program_momentum_5d,
        program_strength_zscore,

        processor_version,
        updated_at
    )

    SELECT
        date,

        arbitrage_net_amount,
        nonarb_net_amount,
        total_net_amount,

        arbitrage_ratio,
        nonarb_ratio,
        program_ratio,

        program_pressure_score_raw,

        program_momentum_3d,
        program_momentum_5d,
        program_strength_zscore,

        %s,
        now()

    FROM momentum
    ORDER BY date

    ON CONFLICT (date)
    DO UPDATE SET
        arbitrage_net_amount = EXCLUDED.arbitrage_net_amount,
        nonarb_net_amount = EXCLUDED.nonarb_net_amount,
        total_net_amount = EXCLUDED.total_net_amount,

        arbitrage_ratio = EXCLUDED.arbitrage_ratio,
        nonarb_ratio = EXCLUDED.nonarb_ratio,
        program_ratio = EXCLUDED.program_ratio,

        program_pressure_score = EXCLUDED.program_pressure_score,

        program_momentum_3d = EXCLUDED.program_momentum_3d,
        program_momentum_5d = EXCLUDED.program_momentum_5d,
        program_strength_zscore = EXCLUDED.program_strength_zscore,

        processor_version = EXCLUDED.processor_version,
        updated_at = now()
    """, (PROCESSOR_VERSION,))

    conn.commit()
    cur.close()


def run():
    print("===== PRE PROGRAM START =====")

    conn = get_conn()

    try:
        aggregate_program(conn)
    finally:
        conn.close()

    print("===== PRE PROGRAM DONE =====")


if __name__ == "__main__":
    run()