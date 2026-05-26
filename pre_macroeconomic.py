import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "interest_crawler",
    "user": "postgres",
    "password": "doflwhsk3768!"
}

PROCESSOR_VERSION = "4.0.0"


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def aggregate_macro(conn):

    cur = conn.cursor()

    cur.execute("""
    WITH base AS (
        SELECT
            indicator_name,
            period AS date,
            released_value,

            LAG(released_value) OVER (
                PARTITION BY indicator_name
                ORDER BY period
            ) AS prev_value

        FROM interest_macroeconomic_raw
        WHERE source = 'yfinance'
    ),

    returns AS (
        SELECT
            date,
            indicator_name,

            CASE
                WHEN prev_value IS NULL OR prev_value = 0 THEN NULL

                WHEN indicator_name = 'VIX'
                    THEN (released_value - prev_value) / prev_value

                ELSE LEAST(
                        GREATEST(
                            (released_value - prev_value) / prev_value,
                            -0.2
                        ),
                        0.2
                     )
            END AS daily_return

        FROM base
    ),

    pivoted AS (
        SELECT
            date,

            MAX(CASE WHEN indicator_name = 'VIX' THEN daily_return END) AS vix_return,
            MAX(CASE WHEN indicator_name = 'US10Y' THEN daily_return END) AS us10y_return,
            MAX(CASE WHEN indicator_name = 'US2Y' THEN daily_return END) AS us2y_return,
            MAX(CASE WHEN indicator_name = 'DXY' THEN daily_return END) AS dxy_return,
            MAX(CASE WHEN indicator_name = 'USDKRW' THEN daily_return END) AS usdkrw_return,
            MAX(CASE WHEN indicator_name = 'USDJPY' THEN daily_return END) AS usdjpy_return,
            MAX(CASE WHEN indicator_name = 'USDCNY' THEN daily_return END) AS usdcny_return

        FROM returns
        GROUP BY date
    ),

    filtered AS (
        SELECT *
        FROM pivoted
        WHERE
            vix_return IS NOT NULL
            AND us10y_return IS NOT NULL
            AND dxy_return IS NOT NULL
            AND usdkrw_return IS NOT NULL
    ),

    final AS (
        SELECT
            date,
            vix_return,
            us10y_return,
            us2y_return,
            dxy_return,
            usdkrw_return,
            usdjpy_return,
            usdcny_return,

            ROUND(vix_return, 6) AS vol_pressure,

            CASE
                WHEN us10y_return IS NULL AND us2y_return IS NULL THEN NULL
                ELSE ROUND(
                    us10y_return * 0.75
                  + us2y_return * 0.25
                , 6)
            END AS rate_pressure,

            CASE
                WHEN dxy_return IS NULL AND usdkrw_return IS NULL THEN NULL
                ELSE ROUND(
                    dxy_return * 0.4
                  + usdkrw_return * 0.3
                  + usdcny_return * 0.2
                  - usdjpy_return * 0.1
                , 6)
            END AS fx_pressure

        FROM filtered
    )

    INSERT INTO pre_macroeconomic_daily_feature
    (
        date,
        vix_return,
        us10y_return,
        us2y_return,
        dxy_return,
        usdkrw_return,
        usdjpy_return,
        usdcny_return,
        vol_pressure,
        rate_pressure,
        fx_pressure,
        macro_pressure_score,
        processor_version
    )

    SELECT
        date,
        vix_return,
        us10y_return,
        us2y_return,
        dxy_return,
        usdkrw_return,
        usdjpy_return,
        usdcny_return,
        vol_pressure,
        rate_pressure,
        fx_pressure,

        CASE
            WHEN vol_pressure IS NULL
             AND rate_pressure IS NULL
             AND fx_pressure IS NULL THEN NULL
            ELSE ROUND(
                vol_pressure * 0.4
              + rate_pressure * 0.3
              + fx_pressure * 0.3
            , 6)
        END,

        %s

    FROM final
    WHERE
        (
            vol_pressure IS NOT NULL
            OR rate_pressure IS NOT NULL
            OR fx_pressure IS NOT NULL
        )

    ORDER BY date

    ON CONFLICT (date)
    DO UPDATE SET
        vix_return = EXCLUDED.vix_return,
        us10y_return = EXCLUDED.us10y_return,
        us2y_return = EXCLUDED.us2y_return,
        dxy_return = EXCLUDED.dxy_return,
        usdkrw_return = EXCLUDED.usdkrw_return,
        usdjpy_return = EXCLUDED.usdjpy_return,
        usdcny_return = EXCLUDED.usdcny_return,
        vol_pressure = EXCLUDED.vol_pressure,
        rate_pressure = EXCLUDED.rate_pressure,
        fx_pressure = EXCLUDED.fx_pressure,
        macro_pressure_score = EXCLUDED.macro_pressure_score,
        processor_version = EXCLUDED.processor_version;
    """, (PROCESSOR_VERSION,))

    conn.commit()
    cur.close()


def run():
    print("===== PRE MACRO START =====")

    conn = get_conn()
    aggregate_macro(conn)
    conn.close()

    print("===== PRE MACRO DONE =====")


if __name__ == "__main__":
    run()