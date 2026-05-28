"""투자자 수급 원천 데이터를 종목/일자 단위 flow feature로 집계하는 스크립트.

interest_investorflow_raw와 가격 원천 데이터를 결합해 외국인/기관 순매수,
보유율, smart money, flow momentum 지표를 pre_investorflow_daily_feature에 저장한다.
"""

import psycopg2
from db_config import get_db_config

PROCESSOR_VERSION = "3.5.0"


def get_conn():
    return psycopg2.connect(**get_db_config())


def aggregate_investorflow(conn):
    cur = conn.cursor()

    sql = """
    WITH base AS (
        SELECT
            f.ticker_code,
            f.trade_date AS date,
            f.foreign_net,
            f.institution_net,
            f.foreign_hold_ratio,
            p.close_price,
            p.volume,

            CASE
                WHEN p.close_price IS NULL OR p.volume IS NULL OR p.volume = 0
                THEN NULL
                ELSE (p.close_price * p.volume)::numeric
            END AS traded_value,

            CASE
                WHEN p.close_price IS NULL
                THEN NULL
                ELSE (f.foreign_net * p.close_price)::numeric
            END AS foreign_net_value,

            CASE
                WHEN p.close_price IS NULL
                THEN NULL
                ELSE (f.institution_net * p.close_price)::numeric
            END AS institution_net_value,

            LAG(f.foreign_hold_ratio) OVER (
                PARTITION BY f.ticker_code
                ORDER BY f.trade_date
            ) AS prev_foreign_hold_ratio

        FROM interest_investorflow_raw f
        LEFT JOIN LATERAL (
            SELECT
                p.close_price,
                p.volume
            FROM interest_price_raw p
            WHERE p.ticker_code = f.ticker_code
              AND p.price_date <= f.trade_date
            ORDER BY p.price_date DESC
            LIMIT 1
        ) p ON TRUE
    ),

    rolling AS (
        SELECT
            ticker_code,
            date,

            foreign_net AS foreign_net_1d,
            institution_net AS institution_net_1d,

            CASE
                WHEN COUNT(*) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                ) = 3
                THEN SUM(foreign_net) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                )
                ELSE NULL
            END AS foreign_net_3d,

            CASE
                WHEN COUNT(*) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                ) = 5
                THEN SUM(foreign_net) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                )
                ELSE NULL
            END AS foreign_net_5d,

            CASE
                WHEN COUNT(*) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                ) = 10
                THEN SUM(foreign_net) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                )
                ELSE NULL
            END AS foreign_net_10d,

            CASE
                WHEN COUNT(*) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                ) = 3
                THEN SUM(institution_net) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                )
                ELSE NULL
            END AS institution_net_3d,

            CASE
                WHEN COUNT(*) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                ) = 5
                THEN SUM(institution_net) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                )
                ELSE NULL
            END AS institution_net_5d,

            CASE
                WHEN COUNT(*) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                ) = 10
                THEN SUM(institution_net) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                )
                ELSE NULL
            END AS institution_net_10d,

            foreign_net_value AS foreign_net_value_1d,

            CASE
                WHEN COUNT(*) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                ) = 3
                THEN SUM(foreign_net_value) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                )
                ELSE NULL
            END AS foreign_net_value_3d,

            CASE
                WHEN COUNT(*) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                ) = 5
                THEN SUM(foreign_net_value) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                )
                ELSE NULL
            END AS foreign_net_value_5d,

            CASE
                WHEN COUNT(*) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                ) = 10
                THEN SUM(foreign_net_value) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                )
                ELSE NULL
            END AS foreign_net_value_10d,

            institution_net_value AS institution_net_value_1d,

            CASE
                WHEN COUNT(*) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                ) = 3
                THEN SUM(institution_net_value) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                )
                ELSE NULL
            END AS institution_net_value_3d,

            CASE
                WHEN COUNT(*) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                ) = 5
                THEN SUM(institution_net_value) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                )
                ELSE NULL
            END AS institution_net_value_5d,

            CASE
                WHEN COUNT(*) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                ) = 10
                THEN SUM(institution_net_value) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                )
                ELSE NULL
            END AS institution_net_value_10d,

            traded_value,

            CASE
                WHEN COUNT(*) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                ) = 3
                THEN SUM(traded_value) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                )
                ELSE NULL
            END AS traded_value_3d,

            CASE
                WHEN COUNT(*) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                ) = 5
                THEN SUM(traded_value) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                )
                ELSE NULL
            END AS traded_value_5d,

            CASE
                WHEN COUNT(*) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                ) = 10
                THEN SUM(traded_value) OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                )
                ELSE NULL
            END AS traded_value_10d,

            foreign_hold_ratio,

            CASE
                WHEN prev_foreign_hold_ratio IS NULL
                THEN NULL
                ELSE ROUND(
                    (foreign_hold_ratio - prev_foreign_hold_ratio)::numeric,
                    6
                )
            END AS foreign_hold_change

        FROM base
    ),

    normalized AS (
        SELECT
            ticker_code,
            date,

            foreign_net_1d,
            foreign_net_3d,
            foreign_net_5d,
            foreign_net_10d,

            institution_net_1d,
            institution_net_3d,
            institution_net_5d,
            institution_net_10d,

            foreign_net_value_1d,
            foreign_net_value_3d,
            foreign_net_value_5d,
            foreign_net_value_10d,

            institution_net_value_1d,
            institution_net_value_3d,
            institution_net_value_5d,
            institution_net_value_10d,

            traded_value,
            traded_value_3d,
            traded_value_5d,
            traded_value_10d,

            foreign_hold_ratio,
            foreign_hold_change,

            CASE
                WHEN traded_value IS NULL OR traded_value = 0 OR foreign_net_value_1d IS NULL
                THEN NULL
                ELSE ROUND((foreign_net_value_1d / traded_value)::numeric, 10)
            END AS foreign_net_ratio_1d,

            CASE
                WHEN traded_value_3d IS NULL OR traded_value_3d = 0 OR foreign_net_value_3d IS NULL
                THEN NULL
                ELSE ROUND((foreign_net_value_3d / traded_value_3d)::numeric, 10)
            END AS foreign_net_ratio_3d,

            CASE
                WHEN traded_value_5d IS NULL OR traded_value_5d = 0 OR foreign_net_value_5d IS NULL
                THEN NULL
                ELSE ROUND((foreign_net_value_5d / traded_value_5d)::numeric, 10)
            END AS foreign_net_ratio_5d,

            CASE
                WHEN traded_value_10d IS NULL OR traded_value_10d = 0 OR foreign_net_value_10d IS NULL
                THEN NULL
                ELSE ROUND((foreign_net_value_10d / traded_value_10d)::numeric, 10)
            END AS foreign_net_ratio_10d,

            CASE
                WHEN traded_value IS NULL OR traded_value = 0 OR institution_net_value_1d IS NULL
                THEN NULL
                ELSE ROUND((institution_net_value_1d / traded_value)::numeric, 10)
            END AS institution_net_ratio_1d,

            CASE
                WHEN traded_value_3d IS NULL OR traded_value_3d = 0 OR institution_net_value_3d IS NULL
                THEN NULL
                ELSE ROUND((institution_net_value_3d / traded_value_3d)::numeric, 10)
            END AS institution_net_ratio_3d,

            CASE
                WHEN traded_value_5d IS NULL OR traded_value_5d = 0 OR institution_net_value_5d IS NULL
                THEN NULL
                ELSE ROUND((institution_net_value_5d / traded_value_5d)::numeric, 10)
            END AS institution_net_ratio_5d,

            CASE
                WHEN traded_value_10d IS NULL OR traded_value_10d = 0 OR institution_net_value_10d IS NULL
                THEN NULL
                ELSE ROUND((institution_net_value_10d / traded_value_10d)::numeric, 10)
            END AS institution_net_ratio_10d

        FROM rolling
    ),

    scored AS (
        SELECT
            ticker_code,
            date,

            foreign_net_1d,
            foreign_net_3d,
            foreign_net_5d,
            foreign_net_10d,

            institution_net_1d,
            institution_net_3d,
            institution_net_5d,
            institution_net_10d,

            foreign_net_value_5d,
            institution_net_value_5d,
            traded_value_5d,

            foreign_net_ratio_1d,
            foreign_net_ratio_3d,
            foreign_net_ratio_5d,
            foreign_net_ratio_10d,

            institution_net_ratio_1d,
            institution_net_ratio_3d,
            institution_net_ratio_5d,
            institution_net_ratio_10d,

            CASE
                WHEN (
                    ABS(COALESCE(foreign_net_ratio_5d, 0))
                    + ABS(COALESCE(institution_net_ratio_5d, 0))
                ) = 0
                THEN NULL
                ELSE ROUND(
                    (
                        foreign_net_ratio_5d
                        /
                        (
                            ABS(COALESCE(foreign_net_ratio_5d, 0))
                            + ABS(COALESCE(institution_net_ratio_5d, 0))
                        )
                    )::numeric,
                    6
                )
            END AS foreign_inst_ratio,

            foreign_hold_ratio,
            foreign_hold_change,

            ROUND(
                (
                    COALESCE(foreign_net_ratio_5d, 0) * 0.7
                    + COALESCE(institution_net_ratio_5d, 0) * 0.3
                )::numeric,
                6
            ) AS smart_money_score,

            traded_value,

            ROUND(
                (
                    COALESCE(foreign_net_ratio_3d, 0)
                    - COALESCE(foreign_net_ratio_10d, 0)
                )::numeric,
                10
            ) AS foreign_flow_acceleration,

            ROUND(
                (
                    COALESCE(institution_net_ratio_3d, 0)
                    - COALESCE(institution_net_ratio_10d, 0)
                )::numeric,
                10
            ) AS institution_flow_acceleration,

            ROUND(
                (
                    COALESCE(foreign_net_ratio_5d, 0)
                    - COALESCE(institution_net_ratio_5d, 0)
                )::numeric,
                10
            ) AS foreign_institution_diff_5d,

            ROUND(
                (
                    COALESCE(foreign_net_ratio_1d, 0)
                    - COALESCE(foreign_net_ratio_3d, 0)
                )::numeric,
                10
            ) AS foreign_flow_momentum,

            ROUND(
                (
                    COALESCE(foreign_net_ratio_5d, 0)
                    * LN(1 + GREATEST(COALESCE(traded_value_5d, 0), 0) / 1000000000.0)
                )::numeric,
                6
            ) AS flow_strength_score,

            ROUND(
                PERCENT_RANK() OVER (
                    PARTITION BY date
                    ORDER BY foreign_net_ratio_5d
                )::numeric,
                6
            ) AS flow_rank_pct,

            ROUND(
                PERCENT_RANK() OVER (
                    PARTITION BY date
                    ORDER BY (
                        COALESCE(foreign_net_ratio_5d, 0) * 0.7
                        + COALESCE(institution_net_ratio_5d, 0) * 0.3
                    )
                )::numeric,
                6
            ) AS smart_money_rank_pct

        FROM normalized
    )

    INSERT INTO pre_investorflow_daily_feature (
        ticker_code,
        date,

        foreign_net_1d,
        foreign_net_3d,
        foreign_net_5d,
        foreign_net_10d,

        institution_net_1d,
        institution_net_3d,
        institution_net_5d,
        institution_net_10d,

        foreign_inst_ratio,
        foreign_hold_ratio,
        foreign_hold_change,
        smart_money_score,

        created_at,
        processor_version,
        traded_value,

        foreign_net_ratio_1d,
        foreign_net_ratio_3d,
        foreign_net_ratio_5d,
        foreign_net_ratio_10d,

        institution_net_ratio_1d,
        institution_net_ratio_3d,
        institution_net_ratio_5d,
        institution_net_ratio_10d,

        updated_at,

        foreign_net_value_5d,
        institution_net_value_5d,
        traded_value_5d,
        flow_strength_score,
        flow_rank_pct,
        smart_money_rank_pct,

        foreign_flow_acceleration,
        institution_flow_acceleration,
        foreign_institution_diff_5d,
        foreign_flow_momentum
    )
    SELECT
        ticker_code,
        date,

        foreign_net_1d,
        foreign_net_3d,
        foreign_net_5d,
        foreign_net_10d,

        institution_net_1d,
        institution_net_3d,
        institution_net_5d,
        institution_net_10d,

        foreign_inst_ratio,
        foreign_hold_ratio,
        foreign_hold_change,
        smart_money_score,

        now(),
        %s,
        traded_value,

        foreign_net_ratio_1d,
        foreign_net_ratio_3d,
        foreign_net_ratio_5d,
        foreign_net_ratio_10d,

        institution_net_ratio_1d,
        institution_net_ratio_3d,
        institution_net_ratio_5d,
        institution_net_ratio_10d,

        now(),

        foreign_net_value_5d,
        institution_net_value_5d,
        traded_value_5d,
        flow_strength_score,
        flow_rank_pct,
        smart_money_rank_pct,

        foreign_flow_acceleration,
        institution_flow_acceleration,
        foreign_institution_diff_5d,
        foreign_flow_momentum
    FROM scored

    ON CONFLICT (ticker_code, date)
    DO UPDATE SET
        foreign_net_1d = EXCLUDED.foreign_net_1d,
        foreign_net_3d = EXCLUDED.foreign_net_3d,
        foreign_net_5d = EXCLUDED.foreign_net_5d,
        foreign_net_10d = EXCLUDED.foreign_net_10d,

        institution_net_1d = EXCLUDED.institution_net_1d,
        institution_net_3d = EXCLUDED.institution_net_3d,
        institution_net_5d = EXCLUDED.institution_net_5d,
        institution_net_10d = EXCLUDED.institution_net_10d,

        foreign_inst_ratio = EXCLUDED.foreign_inst_ratio,
        foreign_hold_ratio = EXCLUDED.foreign_hold_ratio,
        foreign_hold_change = EXCLUDED.foreign_hold_change,
        smart_money_score = EXCLUDED.smart_money_score,

        traded_value = EXCLUDED.traded_value,

        foreign_net_ratio_1d = EXCLUDED.foreign_net_ratio_1d,
        foreign_net_ratio_3d = EXCLUDED.foreign_net_ratio_3d,
        foreign_net_ratio_5d = EXCLUDED.foreign_net_ratio_5d,
        foreign_net_ratio_10d = EXCLUDED.foreign_net_ratio_10d,

        institution_net_ratio_1d = EXCLUDED.institution_net_ratio_1d,
        institution_net_ratio_3d = EXCLUDED.institution_net_ratio_3d,
        institution_net_ratio_5d = EXCLUDED.institution_net_ratio_5d,
        institution_net_ratio_10d = EXCLUDED.institution_net_ratio_10d,

        foreign_net_value_5d = EXCLUDED.foreign_net_value_5d,
        institution_net_value_5d = EXCLUDED.institution_net_value_5d,
        traded_value_5d = EXCLUDED.traded_value_5d,
        flow_strength_score = EXCLUDED.flow_strength_score,
        flow_rank_pct = EXCLUDED.flow_rank_pct,
        smart_money_rank_pct = EXCLUDED.smart_money_rank_pct,

        foreign_flow_acceleration = EXCLUDED.foreign_flow_acceleration,
        institution_flow_acceleration = EXCLUDED.institution_flow_acceleration,
        foreign_institution_diff_5d = EXCLUDED.foreign_institution_diff_5d,
        foreign_flow_momentum = EXCLUDED.foreign_flow_momentum,

        processor_version = EXCLUDED.processor_version,
        updated_at = now();
    """

    cur.execute(sql, (PROCESSOR_VERSION,))
    conn.commit()
    cur.close()


def run():
    print("===== PRE INVESTORFLOW START =====")
    conn = get_conn()
    try:
        aggregate_investorflow(conn)
    finally:
        conn.close()
    print("===== PRE INVESTORFLOW DONE =====")


if __name__ == "__main__":
    run()
