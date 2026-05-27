# pre_foreignindex.py

import psycopg2
from db_config import get_db_config

PROCESSOR_VERSION = "2.1.0"


def get_conn():
    return psycopg2.connect(**get_db_config())


def aggregate_foreignindex(conn):

    cur = conn.cursor()

    cur.execute("""
    WITH base AS (
        SELECT
            index_name,
            date,
            close_price,
            LAG(close_price)
                OVER (PARTITION BY index_name ORDER BY date) AS prev_close
        FROM interest_foreignindex_raw
    ),

    returns AS (
        SELECT
            index_name,
            date,
            CASE
                WHEN prev_close IS NULL OR prev_close = 0
                THEN NULL
                ELSE ROUND(((close_price - prev_close) / prev_close)::numeric, 6)
            END AS daily_return
        FROM base
    ),

    pivoted AS (
        SELECT
            date,

            MAX(CASE WHEN index_name = 'SP500' THEN daily_return END) AS sp500_return,
            MAX(CASE WHEN index_name = 'NASDAQ' THEN daily_return END) AS nasdaq_return,
            MAX(CASE WHEN index_name = 'DOWJONES' THEN daily_return END) AS dowjones_return,
            MAX(CASE WHEN index_name = 'NIKKEI225' THEN daily_return END) AS nikkei225_return,
            MAX(CASE WHEN index_name = 'SHANGHAI' THEN daily_return END) AS shanghai_return,
            MAX(CASE WHEN index_name = 'HANGSENG' THEN daily_return END) AS hangseng_return

        FROM returns
        GROUP BY date
    ),

    risk_calc AS (
        SELECT
            date,
            sp500_return,
            nasdaq_return,
            dowjones_return,
            nikkei225_return,
            shanghai_return,
            hangseng_return,

            CASE
                WHEN sp500_return IS NULL
                  OR nasdaq_return IS NULL
                  OR dowjones_return IS NULL
                THEN NULL
                ELSE ROUND(
                    (sp500_return + nasdaq_return + dowjones_return) / 3,
                6)
            END AS us_lead_score,

            CASE
                WHEN nikkei225_return IS NULL
                  OR shanghai_return IS NULL
                  OR hangseng_return IS NULL
                THEN NULL
                ELSE ROUND(
                    (nikkei225_return + shanghai_return + hangseng_return) / 3,
                6)
            END AS asia_lead_score

        FROM pivoted
    ),

    final_calc AS (
        SELECT
            *,
            CASE
                WHEN us_lead_score IS NULL
                THEN NULL
                ELSE ROUND(
                    (us_lead_score * 0.6)
                    + (COALESCE(asia_lead_score, 0) * 0.4),
                6)
            END AS global_risk_score
        FROM risk_calc
    ),

    momentum_calc AS (
        SELECT
            *,
            CASE
                WHEN global_risk_score IS NULL THEN NULL
                ELSE ROUND(
                    SUM(global_risk_score)
                    OVER (
                        ORDER BY date
                        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                    ),
                6)
            END AS global_momentum_3d
        FROM final_calc
    ),

    regime_calc AS (
        SELECT
            *,
            CASE
                WHEN global_risk_score IS NULL THEN NULL

                WHEN global_risk_score > 0.005
                    AND us_lead_score > 0
                THEN 'RISK_ON'

                WHEN global_risk_score < -0.005
                THEN 'RISK_OFF'

                ELSE 'NEUTRAL'
            END AS risk_regime
        FROM momentum_calc
    ),

    filtered AS (
        SELECT *
        FROM regime_calc
        WHERE global_risk_score IS NOT NULL
    )

    INSERT INTO pre_foreignindex_daily_feature
    (
        date,
        sp500_return,
        nasdaq_return,
        dowjones_return,
        nikkei225_return,
        shanghai_return,
        hangseng_return,
        global_risk_score,
        global_momentum_3d,
        risk_regime,
        processor_version
    )

    SELECT
        date,
        sp500_return,
        nasdaq_return,
        dowjones_return,
        nikkei225_return,
        shanghai_return,
        hangseng_return,
        global_risk_score,
        global_momentum_3d,
        risk_regime,
        %s

    FROM filtered

    ON CONFLICT (date)
    DO UPDATE SET
        sp500_return = EXCLUDED.sp500_return,
        nasdaq_return = EXCLUDED.nasdaq_return,
        dowjones_return = EXCLUDED.dowjones_return,
        nikkei225_return = EXCLUDED.nikkei225_return,
        shanghai_return = EXCLUDED.shanghai_return,
        hangseng_return = EXCLUDED.hangseng_return,
        global_risk_score = EXCLUDED.global_risk_score,
        global_momentum_3d = EXCLUDED.global_momentum_3d,
        risk_regime = EXCLUDED.risk_regime,
        processor_version = EXCLUDED.processor_version
    """, (PROCESSOR_VERSION,))

    conn.commit()
    cur.close()


def run():

    print("===== PRE FOREIGNINDEX START =====")

    conn = get_conn()
    aggregate_foreignindex(conn)
    conn.close()

    print("===== PRE FOREIGNINDEX DONE =====")


if __name__ == "__main__":
    run()