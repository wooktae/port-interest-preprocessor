import psycopg2
from psycopg2.extras import execute_batch
import json

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "interest_crawler",
    "user": "postgres",
    "password": "doflwhsk3768!"
}

PROCESSOR_VERSION = "NEWS-DAILY-2.0.0"


def run():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("===== PRE NEWS DAILY FEATURE START =====")

    sql = f"""
    WITH sentiment_base AS (
        SELECT
            p.ticker_code,
            DATE(n.published_at) AS date,
            p.sentiment_score,
            n.published_at
        FROM pre_news_analysis p
        JOIN interest_news_raw n
          ON p.news_id = n.id
    ),

    sentiment_agg AS (
        SELECT
            ticker_code,
            date,
            COUNT(*) AS news_count,

            COUNT(*) FILTER (WHERE sentiment_score > 0.05) AS positive_count,
            COUNT(*) FILTER (WHERE sentiment_score < -0.05) AS negative_count,
            COUNT(*) FILTER (WHERE sentiment_score BETWEEN -0.05 AND 0.05) AS neutral_count,

            ROUND(AVG(sentiment_score), 4) AS avg_sentiment,
            ROUND(SUM(sentiment_score), 4) AS sum_sentiment,
            ROUND(AVG(ABS(sentiment_score)), 4) AS avg_abs_sentiment,
            ROUND(STDDEV(sentiment_score), 4) AS sentiment_stddev,
            ROUND(MAX(sentiment_score), 4) AS max_sentiment,
            ROUND(MIN(sentiment_score), 4) AS min_sentiment
        FROM sentiment_base
        GROUP BY ticker_code, date
    ),

    freshness_base AS (
        SELECT
            p.ticker_code,
            DATE(n.published_at) AS date,
            p.sentiment_score,
            EXTRACT(EPOCH FROM (NOW() - n.published_at)) / 3600.0 AS hours_diff
        FROM pre_news_analysis p
        JOIN interest_news_raw n
          ON p.news_id = n.id
    ),

    freshness_agg AS (
        SELECT
            ticker_code,
            date,
            ROUND(
                SUM(sentiment_score * EXP(-hours_diff / 6.0))
                / NULLIF(SUM(EXP(-hours_diff / 6.0)), 0),
                4
            ) AS freshness_weighted_sentiment
        FROM freshness_base
        GROUP BY ticker_code, date
    ),

    event_base AS (
        SELECT DISTINCT
            p.ticker_code,
            DATE(n.published_at) AS date,
            e.news_id,
            e.event_name,
            e.weight
        FROM pre_news_event e
        JOIN pre_news_analysis p
          ON e.news_id = p.news_id
        JOIN interest_news_raw n
          ON p.news_id = n.id
    ),

    event_agg AS (
        SELECT
            ticker_code,
            date,
            COUNT(DISTINCT news_id) AS event_count,
            COUNT(DISTINCT event_name) AS distinct_event_count,
            ROUND(AVG(weight), 4) AS avg_event_weight,
            ROUND(SUM(weight), 4) AS sum_event_weight,
            ROUND(MAX(weight), 4) AS max_event_weight
        FROM event_base
        GROUP BY ticker_code, date
    ),

    keyword_base AS (
        SELECT
            p.ticker_code,
            DATE(n.published_at) AS date,
            jsonb_array_elements_text(p.keywords) AS keyword
        FROM pre_news_analysis p
        JOIN interest_news_raw n
          ON p.news_id = n.id
    ),

    keyword_filtered AS (
        SELECT *
        FROM keyword_base
        WHERE keyword NOT IN (
            '기자','관련','대해','기준','가능성','하나','만원','억원','종합','특징주'
        )
        AND LENGTH(keyword) >= 2
    ),

    keyword_agg AS (
        SELECT
            ticker_code,
            date,
            to_jsonb(ARRAY_AGG(keyword ORDER BY cnt DESC))::jsonb AS top_keywords
        FROM (
            SELECT
                ticker_code,
                date,
                keyword,
                COUNT(*) AS cnt,
                ROW_NUMBER() OVER (
                    PARTITION BY ticker_code, date
                    ORDER BY COUNT(*) DESC
                ) AS rn
            FROM keyword_filtered
            GROUP BY ticker_code, date, keyword
        ) t
        WHERE rn <= 10
        GROUP BY ticker_code, date
    )

    SELECT
        s.ticker_code,
        s.date,
        s.news_count,
        s.positive_count,
        s.negative_count,
        s.neutral_count,
        s.avg_sentiment,
        s.sum_sentiment,
        s.avg_abs_sentiment,
        s.sentiment_stddev,
        s.max_sentiment,
        s.min_sentiment,

        ROUND(s.positive_count::numeric / NULLIF(s.news_count,0),4),
        ROUND(s.negative_count::numeric / NULLIF(s.news_count,0),4),
        ROUND(s.neutral_count::numeric / NULLIF(s.news_count,0),4),

        ROUND(
            (s.positive_count::numeric - s.negative_count::numeric)
            / NULLIF(s.news_count,0),
            4
        ),

        ROUND(
            LN((s.positive_count + 1)::numeric / (s.negative_count + 1)),
            4
        ),

        COALESCE(e.event_count,0),
        COALESCE(e.distinct_event_count,0),
        e.avg_event_weight,
        e.sum_event_weight,
        e.max_event_weight,

        ROUND(
            COALESCE(e.sum_event_weight,0)
            / NULLIF(s.news_count,0),
            4
        ),

        k.top_keywords,
        f.freshness_weighted_sentiment,

        '{PROCESSOR_VERSION}'   -- 🔥 여기 추가 (중요)

    FROM sentiment_agg s
    LEFT JOIN event_agg e
      ON s.ticker_code = e.ticker_code
     AND s.date = e.date
    LEFT JOIN keyword_agg k
      ON s.ticker_code = k.ticker_code
     AND s.date = k.date
    LEFT JOIN freshness_agg f
      ON s.ticker_code = f.ticker_code
     AND s.date = f.date
    """

    cur.execute(sql)
    rows = cur.fetchall()

    fixed_rows = []

    for row in rows:
        row = list(row)

        # index 23 = top_keywords
        if row[23] is not None:
            row[23] = json.dumps(row[23])

        fixed_rows.append(tuple(row))

    insert_sql = """
    INSERT INTO pre_news_daily_feature (
        ticker_code, date,
        news_count, positive_count, negative_count, neutral_count,
        avg_sentiment, sum_sentiment, avg_abs_sentiment,
        sentiment_stddev, max_sentiment, min_sentiment,
        positive_ratio, negative_ratio, neutral_ratio,
        sentiment_pressure, bullish_bearish_ratio,
        event_count, distinct_event_count,
        avg_event_weight, sum_event_weight, max_event_weight,
        event_pressure,
        top_keywords,
        freshness_weighted_sentiment,
        processor_version
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s)
    ON CONFLICT (ticker_code, date)
    DO UPDATE SET
        news_count = EXCLUDED.news_count,
        positive_count = EXCLUDED.positive_count,
        negative_count = EXCLUDED.negative_count,
        neutral_count = EXCLUDED.neutral_count,
        avg_sentiment = EXCLUDED.avg_sentiment,
        sum_sentiment = EXCLUDED.sum_sentiment,
        avg_abs_sentiment = EXCLUDED.avg_abs_sentiment,
        sentiment_stddev = EXCLUDED.sentiment_stddev,
        max_sentiment = EXCLUDED.max_sentiment,
        min_sentiment = EXCLUDED.min_sentiment,
        positive_ratio = EXCLUDED.positive_ratio,
        negative_ratio = EXCLUDED.negative_ratio,
        neutral_ratio = EXCLUDED.neutral_ratio,
        sentiment_pressure = EXCLUDED.sentiment_pressure,
        bullish_bearish_ratio = EXCLUDED.bullish_bearish_ratio,
        event_count = EXCLUDED.event_count,
        distinct_event_count = EXCLUDED.distinct_event_count,
        avg_event_weight = EXCLUDED.avg_event_weight,
        sum_event_weight = EXCLUDED.sum_event_weight,
        max_event_weight = EXCLUDED.max_event_weight,
        event_pressure = EXCLUDED.event_pressure,
        top_keywords = EXCLUDED.top_keywords,
        freshness_weighted_sentiment = EXCLUDED.freshness_weighted_sentiment,
        processor_version = EXCLUDED.processor_version,
        created_at = now()
    """

    execute_batch(cur, insert_sql, fixed_rows)
    conn.commit()

    cur.close()
    conn.close()

    print(f"[DONE] rows={len(rows)}")


if __name__ == "__main__":
    run()