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


# -------------------------------------------------
# Recommendation fallback mapping
# -------------------------------------------------

def map_score(rec):

    if not rec:
        return None

    r = rec.strip().lower()

    # Strong Buy
    if "strong" in r or "강력매수" in r or "강매수" in r:
        return 5

    # Buy
    if (
        "buy" in r
        or "매수" in r
        or "outperform" in r
        or "overweight" in r
        or "시장수익률상회" in r
    ):
        return 4

    # Hold
    if (
        "hold" in r
        or "neutral" in r
        or "중립" in r
        or "보유" in r
        or "marketperform" in r
    ):
        return 3

    # Sell
    if (
        "sell" in r
        or "reduce" in r
        or "underperform" in r
        or "marketunderperform" in r
        or "매도" in r
        or "시장수익률하회" in r
        or "비중축소" in r
    ):
        return 2

    return None


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def run():

    print("===== PRE AGENCY START =====")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            r.id,
            r.ticker_code,
            r.company_name,
            r.agency_name,
            r.publish_date,
            r.score,
            r.recommendation,
            r.target_price
        FROM interest_agency_raw r
        LEFT JOIN pre_agency_analysis p
            ON r.id = p.agency_raw_id
        WHERE p.agency_raw_id IS NULL
        ORDER BY r.id
    """)

    rows = cur.fetchall()

    total = len(rows)

    print(f"TARGET ROWS: {total}")

    processed = 0

    for row in rows:

        (
            raw_id,
            ticker,
            company,
            agency,
            publish_date,
            raw_score,
            rec,
            target_price
        ) = row

        # ---------------------------------
        # Score fallback
        # ---------------------------------

        if raw_score is not None:
            rec_score = raw_score
        else:
            rec_score = map_score(rec)

        # ---------------------------------
        # Insert
        # ---------------------------------

        cur.execute("""
            INSERT INTO pre_agency_analysis
            (
                agency_raw_id,
                ticker_code,
                company_name,
                agency_name,
                publish_date,
                recommendation_score,
                target_price,
                processor_version
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (agency_raw_id) DO NOTHING
        """, (
            raw_id,
            ticker,
            company,
            agency,
            publish_date,
            rec_score,
            target_price,
            PROCESSOR_VERSION
        ))

        processed += 1

        if processed % 1000 == 0:
            print(f"PROCESSED: {processed}/{total}")

    conn.commit()

    cur.close()
    conn.close()

    print("===== PRE AGENCY DONE =====")
    print(f"TOTAL PROCESSED: {processed}")


if __name__ == "__main__":
    run()