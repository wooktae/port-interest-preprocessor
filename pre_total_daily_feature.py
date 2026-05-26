import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "interest_crawler",
    "user": "postgres",
    "password": "doflwhsk3768!"
}

PROCESSOR_VERSION = "1.3.0"


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def truncate_table(conn):

    cur = conn.cursor()

    print("기존 TOTAL FEATURE 삭제")

    cur.execute("""
    TRUNCATE TABLE pre_total_daily_feature
    RESTART IDENTITY
    """)

    conn.commit()
    cur.close()

    print("삭제 완료")


def build_total_feature(conn):

    cur = conn.cursor()

    print("TOTAL FEATURE 생성 시작")

    cur.execute("""

WITH all_dates AS (

SELECT DISTINCT date
FROM (

SELECT date FROM pre_news_daily_feature
UNION ALL
SELECT date FROM pre_agency_daily_feature
UNION ALL
SELECT date FROM pre_foreignindex_daily_feature
UNION ALL
SELECT date FROM pre_commodity_daily_feature
UNION ALL
SELECT date FROM pre_marketbreadth_daily_feature
UNION ALL
SELECT date FROM pre_macroeconomic_daily_feature

) t

)

INSERT INTO pre_total_daily_feature
(
ticker_code,
date,

news_count,
news_avg_sentiment,
news_positive_ratio,
news_negative_ratio,
news_neutral_ratio,

report_count,
avg_recommendation_score,
agency_avg_sentiment,
avg_target_price,
target_up_ratio,
target_down_ratio,

sp500_return,
nasdaq_return,
dowjones_return,
nikkei225_return,
shanghai_return,
hangseng_return,
vix_return,
global_risk_score,

wti_return,
brent_return,
gold_return,
silver_return,
copper_return,
natural_gas_return,
commodity_pressure_score,

advancers,
decliners,
advance_decline_ratio,
advance_decline_diff_ratio,
volume_change_ratio,
breadth_pressure_score,

vix_macro_return,
us10y_return,
us2y_return,
dxy_return,
usdkrw_return,
usdjpy_return,
usdcny_return,
macro_pressure_score,

processor_version
)

SELECT

u.ticker_code,
d.date,

COALESCE(n.news_count,0),
COALESCE(n.avg_sentiment,0),
COALESCE(n.positive_ratio,0),
COALESCE(n.negative_ratio,0),
COALESCE(n.neutral_ratio,0),

COALESCE(a.report_count,0),
COALESCE(a.avg_recommendation_score,0),
COALESCE(a.avg_sentiment,0),
COALESCE(a.avg_target_price,0),
COALESCE(a.target_up_ratio,0),
COALESCE(a.target_down_ratio,0),

COALESCE(f.sp500_return,0),
COALESCE(f.nasdaq_return,0),
COALESCE(f.dowjones_return,0),
COALESCE(f.nikkei225_return,0),
COALESCE(f.shanghai_return,0),
COALESCE(f.hangseng_return,0),
COALESCE(f.vix_return,0),
COALESCE(f.global_risk_score,0),

COALESCE(c.wti_return,0),
COALESCE(c.brent_return,0),
COALESCE(c.gold_return,0),
COALESCE(c.silver_return,0),
COALESCE(c.copper_return,0),
COALESCE(c.natural_gas_return,0),
COALESCE(c.commodity_pressure_score,0),

COALESCE(m.advancers,0),
COALESCE(m.decliners,0),
COALESCE(m.advance_decline_ratio,0),
COALESCE(m.advance_decline_diff_ratio,0),
COALESCE(m.volume_change_ratio,0),
COALESCE(m.breadth_pressure_score,0),

COALESCE(macro.vix_return,0),
COALESCE(macro.us10y_return,0),
COALESCE(macro.us2y_return,0),
COALESCE(macro.dxy_return,0),
COALESCE(macro.usdkrw_return,0),
COALESCE(macro.usdjpy_return,0),
COALESCE(macro.usdcny_return,0),
COALESCE(macro.macro_pressure_score,0),

%s

FROM stock_universe u
CROSS JOIN all_dates d

LEFT JOIN pre_news_daily_feature n
ON u.ticker_code = n.ticker_code
AND d.date = n.date

LEFT JOIN pre_agency_daily_feature a
ON u.ticker_code = a.ticker_code
AND d.date = a.date

LEFT JOIN pre_foreignindex_daily_feature f
ON d.date = f.date

LEFT JOIN pre_commodity_daily_feature c
ON d.date = c.date

LEFT JOIN pre_marketbreadth_daily_feature m
ON d.date = m.date

LEFT JOIN pre_macroeconomic_daily_feature macro
ON d.date = macro.date

ORDER BY
u.ticker_code,
d.date

""", (PROCESSOR_VERSION,))

    conn.commit()
    cur.close()

    print("TOTAL FEATURE 생성 완료")


def run():

    print("===== BUILD TOTAL FEATURE START =====")

    conn = get_conn()

    truncate_table(conn)

    build_total_feature(conn)

    conn.close()

    print("===== BUILD TOTAL FEATURE DONE =====")


if __name__ == "__main__":
    run()