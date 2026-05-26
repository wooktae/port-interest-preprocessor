# pre_commodity.py

import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "interest_crawler",
    "user": "postgres",
    "password": "doflwhsk3768!"
}

PROCESSOR_VERSION = "2.0.0"


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def aggregate_commodity(conn):

    cur = conn.cursor()

    try:

        cur.execute("""

        WITH base AS (
            SELECT
                commodity_code,
                date,
                price,
                LAG(price) OVER (PARTITION BY commodity_code ORDER BY date) AS prev_close
            FROM interest_commodity_raw
        ),

        returns AS (
            SELECT
                commodity_code,
                date,
                CASE
                    WHEN prev_close IS NULL OR prev_close = 0 THEN NULL
                    ELSE ROUND(((price - prev_close) / prev_close)::numeric, 6)
                END AS raw_return
            FROM base
        ),

        clipped AS (
            SELECT
                commodity_code,
                date,

                CASE
                    WHEN commodity_code = 'NATURAL_GAS' THEN
                        CASE
                            WHEN raw_return > 0.20 THEN 0.20
                            WHEN raw_return < -0.20 THEN -0.20
                            ELSE raw_return
                        END
                    ELSE
                        CASE
                            WHEN raw_return > 0.15 THEN 0.15
                            WHEN raw_return < -0.15 THEN -0.15
                            ELSE raw_return
                        END
                END AS daily_return

            FROM returns
        ),

        pivoted AS (
            SELECT
                date,

                MAX(CASE WHEN commodity_code = 'WTI' THEN daily_return END) AS wti_return,
                MAX(CASE WHEN commodity_code = 'BRENT' THEN daily_return END) AS brent_return,
                MAX(CASE WHEN commodity_code = 'GOLD' THEN daily_return END) AS gold_return,
                MAX(CASE WHEN commodity_code = 'SILVER' THEN daily_return END) AS silver_return,
                MAX(CASE WHEN commodity_code = 'COPPER' THEN daily_return END) AS copper_return,
                MAX(CASE WHEN commodity_code = 'NATURAL_GAS' THEN daily_return END) AS natural_gas_return

            FROM clipped
            GROUP BY date
        ),

        valid_check AS (
            SELECT
                *,
                (
                    (wti_return IS NOT NULL)::int +
                    (brent_return IS NOT NULL)::int +
                    (gold_return IS NOT NULL)::int +
                    (silver_return IS NOT NULL)::int +
                    (copper_return IS NOT NULL)::int +
                    (natural_gas_return IS NOT NULL)::int
                ) AS valid_component_count
            FROM pivoted
        ),

        final AS (
            SELECT
                date,
                wti_return,
                brent_return,
                gold_return,
                silver_return,
                copper_return,
                natural_gas_return,
                valid_component_count,

                CASE
                    WHEN wti_return IS NOT NULL AND brent_return IS NOT NULL
                    THEN ROUND((wti_return + brent_return)/2, 6)
                    ELSE NULL
                END AS energy_pressure,

                CASE
                    WHEN copper_return IS NOT NULL AND gold_return IS NOT NULL
                    THEN ROUND((COALESCE(silver_return, 0) + copper_return)/2 - gold_return, 6)
                    ELSE NULL
                END AS metal_pressure,

                CASE
                    WHEN wti_return IS NOT NULL AND brent_return IS NOT NULL AND gold_return IS NOT NULL
                    THEN ROUND((wti_return + brent_return + gold_return)/3, 6)
                    ELSE NULL
                END AS inflation_commodity_score,

                CASE
                    WHEN copper_return IS NOT NULL AND silver_return IS NOT NULL
                    THEN ROUND((copper_return + silver_return)/2, 6)
                    ELSE NULL
                END AS growth_commodity_score,

                CASE
                    WHEN valid_component_count >= 3
                    THEN ROUND(
                        COALESCE((wti_return + brent_return)/2, 0) +
                        COALESCE((copper_return - gold_return), 0),
                    6)
                    ELSE NULL
                END AS commodity_pressure_score,

                CASE
                    WHEN ABS(wti_return) >= 0.05
                      OR ABS(brent_return) >= 0.05
                      OR ABS(natural_gas_return) >= 0.10
                    THEN TRUE ELSE FALSE
                END AS energy_shock_flag,

                CASE
                    WHEN ABS(copper_return) >= 0.04
                      OR ABS(gold_return) >= 0.03
                    THEN TRUE ELSE FALSE
                END AS metal_shock_flag

            FROM valid_check
        )

        INSERT INTO pre_commodity_daily_feature (
            date,
            wti_return,
            brent_return,
            gold_return,
            silver_return,
            copper_return,
            natural_gas_return,
            commodity_pressure_score,
            energy_pressure,
            metal_pressure,
            inflation_commodity_score,
            growth_commodity_score,
            energy_shock_flag,
            metal_shock_flag,
            valid_component_count,
            processor_version
        )
        SELECT
            date,
            wti_return,
            brent_return,
            gold_return,
            silver_return,
            copper_return,
            natural_gas_return,
            commodity_pressure_score,
            energy_pressure,
            metal_pressure,
            inflation_commodity_score,
            growth_commodity_score,
            energy_shock_flag,
            metal_shock_flag,
            valid_component_count,
            %s
        FROM final
        WHERE commodity_pressure_score IS NOT NULL
        ON CONFLICT (date) DO UPDATE SET
            wti_return = EXCLUDED.wti_return,
            brent_return = EXCLUDED.brent_return,
            gold_return = EXCLUDED.gold_return,
            silver_return = EXCLUDED.silver_return,
            copper_return = EXCLUDED.copper_return,
            natural_gas_return = EXCLUDED.natural_gas_return,
            commodity_pressure_score = EXCLUDED.commodity_pressure_score,
            energy_pressure = EXCLUDED.energy_pressure,
            metal_pressure = EXCLUDED.metal_pressure,
            inflation_commodity_score = EXCLUDED.inflation_commodity_score,
            growth_commodity_score = EXCLUDED.growth_commodity_score,
            energy_shock_flag = EXCLUDED.energy_shock_flag,
            metal_shock_flag = EXCLUDED.metal_shock_flag,
            valid_component_count = EXCLUDED.valid_component_count,
            processor_version = EXCLUDED.processor_version

        """, (PROCESSOR_VERSION,))

        conn.commit()

    finally:
        cur.close()


def run():

    print("===== PRE COMMODITY START =====")

    conn = get_conn()
    aggregate_commodity(conn)
    conn.close()

    print("===== PRE COMMODITY DONE =====")


if __name__ == "__main__":
    run()