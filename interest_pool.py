import psycopg2
import psycopg2.extras

DB_CONFIG = {
    "host":"localhost",
    "port":5433,
    "dbname":"interest_crawler",
    "user":"postgres",
    "password":"doflwhsk3768!"
}

def get_db_connection():
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )

def calculate_sentiment_scores():
    """
    종목별로 평균 감성 점수를 계산
    """
    sql = """
    SELECT nr.ticker_id,
           AVG(na.sentiment_score) as avg_sent
    FROM news_analysis na
    JOIN news_raw nr ON na.news_id = nr.id
    GROUP BY nr.ticker_id;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql)
            return cur.fetchall()

def save_interest_pool(ticker_id, pool_type="sentiment_score"):
    """
    interest_pool에 저장
    """
    sql = """
    INSERT INTO interest_pool (ticker_id, pool_type)
    VALUES (%s, %s)
    ON CONFLICT (ticker_id) DO UPDATE
    SET pool_type = EXCLUDED.pool_type;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (ticker_id, pool_type))
            conn.commit()

def main():
    print("[START] interest_pool 자동 생성")

    results = calculate_sentiment_scores()
    for row in results:
        ticker_id = row["ticker_id"]
        avg_sent  = row["avg_sent"]

        # 예시 조건: 평균 감성이 -0.2보다 크면 관심
        if avg_sent > -0.3:
            print(f"  -> 관심 종목 (id={ticker_id}, avg_sent={avg_sent})")
            save_interest_pool(ticker_id, "sentiment_score")

    print("[DONE] interest_pool 반영 완료!")

if __name__ == "__main__":
    main()