"""가격 원천 데이터를 종목/일자 단위 가격 feature로 변환하는 스크립트.

interest_price_raw를 기반으로 수익률, 모멘텀, 이동평균, 변동성, 거래량,
캔들 관련 지표를 계산해 pre_price_daily_feature에 저장한다.
"""

import psycopg2
from db_config import get_db_config

PROCESSOR_VERSION = "1.0.0"


def get_conn():
    return psycopg2.connect(**get_db_config())


def aggregate_price(conn):

    cur = conn.cursor()

    cur.execute("""

    WITH base AS (

        SELECT
            ticker_code,
            price_date AS date,

            open_price,
            high_price,
            low_price,
            close_price,
            volume,

            LAG(close_price)
                OVER (PARTITION BY ticker_code ORDER BY price_date)
                AS prev_close,

            LAG(volume)
                OVER (PARTITION BY ticker_code ORDER BY price_date)
                AS prev_volume

        FROM interest_price_raw
    ),

    returns AS (

        SELECT
            ticker_code,
            date,

            open_price,
            high_price,
            low_price,
            close_price,
            volume,

            prev_close,
            prev_volume,

            CASE
                WHEN prev_close IS NULL
                THEN NULL
                ELSE ROUND(
                    ((close_price / prev_close) - 1)::numeric
                ,6)
            END AS daily_return,

            CASE
                WHEN prev_close IS NULL
                THEN NULL
                ELSE ROUND(
                    LN(close_price / prev_close)::numeric
                ,6)
            END AS log_return,

            CASE
                WHEN prev_volume IS NULL OR prev_volume = 0
                THEN NULL
                ELSE ROUND(
                    ((volume::numeric / prev_volume) - 1)
                ,6)
            END AS volume_change

        FROM base
    ),

    momentum AS (

        SELECT
            *,

            ROUND(
                ((close_price / LAG(close_price,3)
                OVER (PARTITION BY ticker_code ORDER BY date)) - 1)::numeric
            ,6) AS momentum_3d,

            ROUND(
                ((close_price / LAG(close_price,5)
                OVER (PARTITION BY ticker_code ORDER BY date)) - 1)::numeric
            ,6) AS momentum_5d,

            ROUND(
                ((close_price / LAG(close_price,10)
                OVER (PARTITION BY ticker_code ORDER BY date)) - 1)::numeric
            ,6) AS momentum_10d,

            ROUND(
                ((close_price / LAG(close_price,20)
                OVER (PARTITION BY ticker_code ORDER BY date)) - 1)::numeric
            ,6) AS momentum_20d

        FROM returns
    ),

    moving_avg AS (

        SELECT
            *,

            ROUND(
                AVG(close_price)
                OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                )::numeric
            ,6) AS ma_5,

            ROUND(
                AVG(close_price)
                OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                )::numeric
            ,6) AS ma_10,

            ROUND(
                AVG(close_price)
                OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                )::numeric
            ,6) AS ma_20,

            ROUND(
                AVG(close_price)
                OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 59 PRECEDING AND CURRENT ROW
                )::numeric
            ,6) AS ma_60,

            ROUND(
                AVG(volume)
                OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                )::numeric
            ,6) AS avg_volume_5d

        FROM momentum
    ),

    volatility AS (

        SELECT
            *,

            ROUND(
                STDDEV_SAMP(daily_return)
                OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                )::numeric
            ,6) AS volatility_5d,

            ROUND(
                STDDEV_SAMP(daily_return)
                OVER (
                    PARTITION BY ticker_code
                    ORDER BY date
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                )::numeric
            ,6) AS volatility_20d

        FROM moving_avg
    )

    INSERT INTO pre_price_daily_feature (

        ticker_code,
        date,

        close_price,

        daily_return,
        log_return,

        momentum_3d,
        momentum_5d,
        momentum_10d,
        momentum_20d,

        ma_5,
        ma_10,
        ma_20,
        ma_60,

        price_vs_ma5,
        price_vs_ma20,
        price_vs_ma60,

        volatility_5d,
        volatility_20d,

        volume,
        volume_change,
        volume_ratio_5d,

        intraday_range,
        body_ratio,
        upper_shadow_ratio,
        lower_shadow_ratio,

        processor_version

    )

    SELECT

        ticker_code,
        date,

        close_price,

        daily_return,
        log_return,

        momentum_3d,
        momentum_5d,
        momentum_10d,
        momentum_20d,

        ma_5,
        ma_10,
        ma_20,
        ma_60,

        ROUND(((close_price / ma_5) - 1)::numeric,6),
        ROUND(((close_price / ma_20) - 1)::numeric,6),
        ROUND(((close_price / ma_60) - 1)::numeric,6),

        volatility_5d,
        volatility_20d,

        volume,
        volume_change,

        CASE
            WHEN avg_volume_5d = 0 OR avg_volume_5d IS NULL
            THEN NULL
            ELSE ROUND((volume / avg_volume_5d)::numeric,6)
        END,

        ROUND(((high_price - low_price) / close_price)::numeric,6),

        ROUND((ABS(close_price - open_price) / close_price)::numeric,6),

        ROUND(((high_price - GREATEST(open_price,close_price)) / close_price)::numeric,6),

        ROUND(((LEAST(open_price,close_price) - low_price) / close_price)::numeric,6),

        %s

    FROM volatility
    ORDER BY ticker_code, date

    ON CONFLICT (ticker_code, date)
    DO NOTHING

    """, (PROCESSOR_VERSION,))

    conn.commit()
    cur.close()


def run():

    print("===== PRE PRICE START =====")

    conn = get_conn()

    aggregate_price(conn)

    conn.close()

    print("===== PRE PRICE DONE =====")


if __name__ == "__main__":
    run()
