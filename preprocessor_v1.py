import json
import time
import psycopg2
import psycopg2.extras
import numpy as np

from datetime import datetime
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT
from transformers import pipeline

# === DB 설정 ===
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "interest_crawler",
    "user": "postgres",
    "password": "doflwhsk3768!"
}

# === NLP/ML 모델 로딩 ===
# 1) 임베딩 모델 (Sentence BERT)
embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# 2) 감성 분석 모델 (Huggingface pipeline)
sentiment_classifier = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment"
)

# 3) 키워드 추출 모델 (KeyBERT)
kw_model = KeyBERT(model=embed_model)

# === DB 헬퍼 ===
def get_db_connection():
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )

def fetch_raw_news():
    sql = "SELECT id, news_title, news_body FROM news_raw;"
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql)
            return [dict(row) for row in cur.fetchall()]

def save_analysis_record(news_id, sentiment, keywords, vector):
    sql = """
    INSERT INTO news_analysis
        (news_id, sentiment_score, keywords, summary_vector, processed_at)
    VALUES (%s, %s, %s, %s, NOW())
    ON CONFLICT DO NOTHING;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                news_id,
                sentiment,
                keywords,
                json.dumps(vector)  # JSONB 저장
            ))
            conn.commit()

# === 메인 분석 로직 ===
def main():
    print("[START] Interest-Preprocessor 분석 시작")

    raw_news_list = fetch_raw_news()
    if not raw_news_list:
        print("news_raw 테이블에 데이터 없음")
        return

    for row in raw_news_list:
        news_id = row["id"]
        title = row["news_title"] or ""
        body  = row["news_body"] or ""
        text  = f"{title} {body}"

        # === 1) 감성 분석 ===
        try:
            result = sentiment_classifier(text[:512])  # model에 제한된 길이 입력
            sentiment_label = result[0]["label"]
            # score를 -1.0~1.0 범위로 재정규화
            sentiment_score = (result[0]["score"] * 
                (1 if "POSITIVE" in sentiment_label else -1))
        except Exception as e:
            sentiment_score = 0.0

        # === 2) 키워드 추출 ===
        try:
            kws = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), top_n=5)
            keywords = [k for k, _ in kws]
        except Exception as e:
            keywords = []

        # === 3) 임베딩 벡터 생성 ===
        try:
            embedding_vec = embed_model.encode(text).tolist()
        except Exception as e:
            embedding_vec = []

        # === 4) DB 저장 ===
        save_analysis_record(news_id, sentiment_score, keywords, embedding_vec)

        print(f"[ANALYZED] news_id={news_id}, sent={sentiment_score}, kws={keywords}")
        time.sleep(0.1)

    print("[DONE] Interest-Preprocessor 분석 완료!")

if __name__ == "__main__":
    main()