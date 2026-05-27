import psycopg2
from db_config import get_db_config

PROCESSOR_VERSION = "3.0.0"


def get_conn():
    return psycopg2.connect(**get_db_config())


def aggregate_daily(conn):
    cur = conn.cursor()

    sql = """
    WITH raw_base AS (
        SELECT
            r.ticker_code,
            r.publish_date::date AS date,
            r.agency_name,
            NULLIF(BTRIM(r.recommendation), '') AS recommendation_raw,
            r.target_price
        FROM interest_agency_raw r
        WHERE r.ticker_code IS NOT NULL
          AND r.publish_date IS NOT NULL
    ),

    normalized AS (
        SELECT
            b.ticker_code,
            b.date,
            b.agency_name,
            b.recommendation_raw,
            b.target_price,

            CASE
                WHEN UPPER(REPLACE(BTRIM(b.recommendation_raw), ' ', '')) IN ('STRONGBUY')
                    OR b.recommendation_raw = '강력매수'
                    THEN 5

                WHEN UPPER(REPLACE(BTRIM(b.recommendation_raw), ' ', '')) IN (
                    'BUY','OUTPERFORM','MARKETOUTPERFORM'
                )
                    OR b.recommendation_raw IN ('매수','시장수익률상회')
                    THEN 4

                WHEN UPPER(REPLACE(BTRIM(b.recommendation_raw), ' ', '')) IN (
                    'HOLD','NEUTRAL','MARKETPERFORM'
                )
                    OR b.recommendation_raw IN ('중립')
                    THEN 3

                WHEN UPPER(REPLACE(BTRIM(b.recommendation_raw), ' ', '')) IN (
                    'UNDERPERFORM','MARKETUNDERPERFORM','REDUCE'
                )
                    OR b.recommendation_raw IN ('매도','시장수익률하회')
                    THEN 2

                WHEN UPPER(REPLACE(BTRIM(b.recommendation_raw), ' ', '')) IN ('SELL')
                    THEN 1

                WHEN b.recommendation_raw IN ('없음','투자의견없음')
                    THEN NULL

                ELSE NULL
            END::numeric(6,4) AS recommendation_score
        FROM raw_base b
    ),

    daily_agg AS (
        SELECT
            n.ticker_code,
            n.date,

            COUNT(*)::int AS report_count,
            COUNT(n.recommendation_score)::int AS recommendation_report_count,
            COUNT(n.target_price)::int AS target_price_report_count,

            ROUND(AVG(n.recommendation_score)::numeric, 4) AS avg_recommendation_score,

            ROUND(
                SUM(CASE WHEN n.recommendation_score >= 4 THEN 1 ELSE 0 END)::numeric
                / NULLIF(COUNT(n.recommendation_score), 0),
                4
            ) AS buy_ratio,

            ROUND(
                SUM(CASE WHEN n.recommendation_score = 3 THEN 1 ELSE 0 END)::numeric
                / NULLIF(COUNT(n.recommendation_score), 0),
                4
            ) AS hold_ratio,

            ROUND(
                SUM(CASE WHEN n.recommendation_score <= 2 THEN 1 ELSE 0 END)::numeric
                / NULLIF(COUNT(n.recommendation_score), 0),
                4
            ) AS sell_ratio,

            ROUND(AVG(n.target_price)::numeric, 0) AS avg_target_price,
            ROUND(STDDEV_POP(n.target_price)::numeric, 0) AS target_price_std,

            CASE
                WHEN COUNT(n.recommendation_score) = 0 THEN 1
                ELSE 0
            END AS no_signal_flag

        FROM normalized n
        GROUP BY n.ticker_code, n.date
    ),

    price_base AS (
        SELECT
            d.ticker_code,
            d.date,
            p.close_price,
            p.raw_upside
        FROM daily_agg d
        LEFT JOIN LATERAL (
            SELECT 
                ip.close_price,
                ((d.avg_target_price - ip.close_price) / ip.close_price::numeric) AS raw_upside
            FROM interest_price_raw ip
            WHERE ip.ticker_code = d.ticker_code
            AND ip.price_date <= d.date
            AND ip.close_price IS NOT NULL
            AND ip.close_price > 0
            ORDER BY ip.price_date DESC
            LIMIT 1
        ) p ON TRUE
    )

    INSERT INTO pre_agency_daily_feature (
        ticker_code,
        date,
        report_count,
        recommendation_report_count,
        target_price_report_count,
        avg_recommendation_score,
        buy_ratio,
        hold_ratio,
        sell_ratio,
        avg_target_price,
        target_price_std,
        target_price_upside_ratio,
        no_signal_flag,
        processor_version
    )
    SELECT
        a.ticker_code,
        a.date,
        a.report_count,
        a.recommendation_report_count,
        a.target_price_report_count,
        a.avg_recommendation_score,
        a.buy_ratio,
        a.hold_ratio,
        a.sell_ratio,
        a.avg_target_price,
        a.target_price_std,

        /* ✅ upside clipping */
       CASE
            WHEN a.avg_target_price IS NOT NULL
            AND pb.raw_upside IS NOT NULL
            THEN
                CASE
                    WHEN pb.raw_upside > 1 THEN 1
                    WHEN pb.raw_upside < -0.5 THEN -0.5
                    ELSE ROUND(pb.raw_upside, 4)
                END
            ELSE NULL
        END AS target_price_upside_ratio,
        a.no_signal_flag,
        %s

    FROM daily_agg a
    LEFT JOIN price_base pb
      ON a.ticker_code = pb.ticker_code
     AND a.date = pb.date

    ON CONFLICT (ticker_code, date)
    DO UPDATE SET
        report_count = EXCLUDED.report_count,
        recommendation_report_count = EXCLUDED.recommendation_report_count,
        target_price_report_count = EXCLUDED.target_price_report_count,
        avg_recommendation_score = EXCLUDED.avg_recommendation_score,
        buy_ratio = EXCLUDED.buy_ratio,
        hold_ratio = EXCLUDED.hold_ratio,
        sell_ratio = EXCLUDED.sell_ratio,
        avg_target_price = EXCLUDED.avg_target_price,
        target_price_std = EXCLUDED.target_price_std,
        target_price_upside_ratio = EXCLUDED.target_price_upside_ratio,
        no_signal_flag = EXCLUDED.no_signal_flag,
        processor_version = EXCLUDED.processor_version,
        updated_at = now()
    """

    cur.execute(sql, (PROCESSOR_VERSION,))
    print(f"affected rows: {cur.rowcount}")

    conn.commit()
    cur.close()


def run():
    print("===== PRE AGENCY DAILY AGG START =====")

    conn = get_conn()

    try:
        aggregate_daily(conn)
        print("===== PRE AGENCY DAILY AGG DONE =====")
    except Exception as e:
        conn.rollback()
        print("ERROR:", e)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run()