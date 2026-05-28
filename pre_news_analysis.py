"""뉴스 원천 데이터를 종목별 감성 분석 후보 데이터로 변환하는 스크립트.

interest_news_raw와 stock_universe를 읽어 종목 매핑, 키워드 추출, 감성 점수를
계산한 뒤 pre_news_analysis에 upsert한다.
"""

import json
import re
import psycopg2
from db_config import get_db_config
from psycopg2.extras import execute_batch
import time

PROCESSOR_VERSION = "SCORE-4.0.0"
BATCH_SIZE = 5000

TEST_LIMIT = 3000
MAX_TICKERS_PER_NEWS = 3


# =========================
# TOKENIZE
# =========================
def tokenize(text):
    return re.findall(r"[가-힣A-Za-z0-9]+", text)


# =========================
# 조사 제거
# =========================
POSTFIX = ["은","는","이","가","을","를","와","과","도","에","에서","의","로","으로","만","까지","부터","랑","이랑"]

def strip_postfix(token):
    for p in POSTFIX:
        if token.endswith(p) and len(token) > len(p)+1:
            return token[:-len(p)]
    return token


# =========================
# 증권사 필터
# =========================
BROKER_KEYWORDS = ["증권", "證", "리포트", "목표가", "투자의견"]

def is_broker_noise(title, token):
    if token in ["SK","한화","키움","미래에셋","삼성","신한","KB"]:
        for k in BROKER_KEYWORDS:
            if k in title:
                return True
    if f"-{token}" in title:
        return True
    return False


# =========================
# 제외 단어
# =========================
EXCLUDE_WORDS = {"대상"}


# =========================
# 키워드 필터
# =========================
STOPWORDS = {"주", "은", "는", "이", "가", "을", "를", "에", "의", "도"}

def clean_keyword(token):
    if len(token) <= 1:
        return None
    if token.isdigit():
        return None
    if token in STOPWORDS:
        return None
    return token


# =========================
# SENTIMENT MAP (추가)
# =========================
SENTIMENT_SCORE_MAP = {

    # =========================
    # EXTREME POSITIVE (+5)
    # =========================
    "상한가": 5,
    "연속 상한가": 5,
    "폭등": 5,
    "초대형 수주": 5,
    "대규모 수주": 5,
    "잭팟": 5,

    # =========================
    # STRONG POSITIVE (+4)
    # =========================
    "급등": 4,
    "급등세": 4,
    "강한 상승": 4,
    "흑자 전환": 4,
    "턴어라운드": 4,
    "어닝 서프라이즈": 4,
    "실적 서프라이즈": 4,
    "신고가": 4,
    "최고가": 4,
    "돌파": 4,
    "재돌파": 4,
    "복귀": 4,

    # =========================
    # POSITIVE (+3)
    # =========================
    "호재": 3,
    "수혜": 3,
    "실적 개선": 3,
    "이익 증가": 3,
    "매출 증가": 3,
    "성장": 3,
    "성장 기대": 3,
    "재평가": 3,
    "밸류 재평가": 3,
    "목표가 상향": 3,
    "상향": 3,
    "상회": 3,
    "개선": 3,
    "회복": 3,
    "급반등": 4,
    "V자 반등": 4,

    # =========================
    # EVENT POSITIVE (+2~3)
    # =========================
    "수주": 3,
    "계약": 3,
    "공급": 3,
    "확대": 3,
    "증설": 3,
    "투자": 3,
    "라이선스": 3,
    "허가": 3,
    "승인": 3,
    "출시": 2,
    "출하": 2,
    "본격화": 3,
    "흥행": 3,
    "진출": 2,
    "확보": 2,

    # =========================
    # WEAK POSITIVE (+1)
    # =========================
    "기대": 1,
    "가능성": 1,
    "관심": 1,

    # =========================
    # EXTREME NEGATIVE (-5)
    # =========================
    "하한가": -5,
    "연속 하한가": -5,
    "폭락": -5,
    "파산": -5,
    "상장폐지": -5,
    "부도": -5,

    # =========================
    # STRONG NEGATIVE (-4)
    # =========================
    "급락": -4,
    "급락세": -4,
    "쇼크": -4,
    "어닝 쇼크": -4,
    "적자 전환": -4,
    "대규모 손실": -4,
    "계약 해지": -4,
    "수주 실패": -4,

    # =========================
    # NEGATIVE (-3)
    # =========================
    "적자": -3,
    "부진": -3,
    "악화": -3,
    "감소": -3,
    "역성장": -3,
    "하향": -3,
    "목표가 하향": -3,
    "밑돌": -3,
    "미달": -3,

    # =========================
    # WEAK NEGATIVE (-1~-2)
    # =========================
    "하락": -2,
    "둔화": -2,
    "우려": -2,
    "리스크": -1,
    "부담": -1,
    "불확실": -2,
    "변동성": -1,

    # =========================
    # 🔥 추가 (상승/탈환 계열)
    # =========================
    "탈환": 4,
    "재탈환": 4,

    "상승세": 3,
    "강세": 3,
    "오름": 2,
    "오르고": 2,
    # 실적
    "사상 최대": 4,
    "최대 실적": 4,
    "호실적": 4,
    "실적 호조": 3,

    # 마감
    "상승 마감": 3,
    "강세 마감": 3,
    "하락 마감": -3,

    "증가": 3,
    "급증": 4,
    "폭증": 4,
    "2배 증가": 5,
    "터치": 3,
    "근접": 2,
    "밟았다": 3,

}

REVERSAL_WORDS = ["에도 불구하고", "하지만", "불구", "에도"]


# =========================
# STOCK MAP (그대로 유지)
# =========================
SHORT_NAMES = {"SK","LG","GS","CJ","KT","LS","DL"}

def load_alias_map(conn):
    cur = conn.cursor()
    cur.execute("SELECT ticker_code, company_name FROM stock_universe")
    rows = cur.fetchall()
    cur.close()

    alias_map = {}

    for ticker, name in rows:
        name = name.strip()
        alias_map[name] = ticker
        alias_map[name.replace(" ", "")] = ticker

    alias_map.update({
        "KTG": "033780","KT앤지": "033780",
        "FF": "383220","FNF": "383220",
        "SOIL": "010950","S오일": "010950",
        "JYP": "035900","JYPENT": "035900",
        "LSELECTRIC": "010120","CJENM": "035760",
        "서부TD": "006730",
        "삼전": "005930",
        "하닉": "000660",
        "SK하닉": "000660"
    })

    return alias_map


# =========================
# DETECT (절대 수정 없음)
# =========================
def detect(title, alias_map):
    tokens = tokenize(title)

    detected = []
    keywords = []
    seen = set()

    for t in tokens:

        original = t

        if t in EXCLUDE_WORDS:
            continue

        if is_broker_noise(title, t):
            continue

        ticker = alias_map.get(t)

        if not ticker:
            t = strip_postfix(t)
            ticker = alias_map.get(t)

        if t in SHORT_NAMES and original != t:
            ticker = None

        if ticker and ticker not in seen:
            detected.append(ticker)
            seen.add(ticker)
            continue

        kw = clean_keyword(original)
        if kw:
            keywords.append(kw)

    return detected[:MAX_TICKERS_PER_NEWS], keywords


# =========================
# 감성 점수 계산 (추가)
# =========================
def score_sentiment(title):

    text = title
    score = 0
    matched = []

        # 🔥 여기 추가
    percent_patterns = [
        (r"\d+%↑", 3),
        (r"\d+%\s*상승", 3),
        (r"\d+%\s*급등", 4),
        (r"\d+%↓", -3),
        (r"\d+%\s*하락", -3),
        (r"\d+%\s*급락", -4),
    ]

    for pattern, val in percent_patterns:
        if re.search(pattern, text):
            score += val

    reversal_idx = -1
    for r in REVERSAL_WORDS:
        if r in text:
            reversal_idx = text.index(r)
            break

    for phrase, val in sorted(SENTIMENT_SCORE_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        if phrase in text:

            weight = val

            if reversal_idx != -1 and text.index(phrase) > reversal_idx:
                if val > 0:
                    weight = int(val * 0.7)
                else:
                    weight = int(val * 1.3)

            score += weight
            matched.append(phrase)

            text = text.replace(phrase, " ")

    return score, matched


# =========================
# 분류 (추가)
# =========================
def classify(score):
    if score >= 3:
        return score, 0.9, "positive"
    elif score <= -3:
        return score, 0.9, "negative"
    else:
        return score, 0.75, "neutral"


# =========================
# FETCH
# =========================
def fetch_rows(cur):
    cur.execute("""
        SELECT id, title, published_at
        FROM interest_news_raw
        ORDER BY id DESC
    """)
    return cur.fetchall()


# =========================
# MAIN
# =========================
def run():
    print("===== NEWS ANALYSIS (SCORE) START =====")

    start = time.time()

    conn = psycopg2.connect(**get_db_config())
    cur = conn.cursor()

    alias_map = load_alias_map(conn)
    rows = fetch_rows(cur)

    insert_sql = """
        INSERT INTO pre_news_analysis
        (news_id, ticker_code, sentiment_score, keywords,
         confidence_score, sentiment_label,
         processed_at, processor_version,
         published_at, published_date)
        VALUES (%s,%s,%s,%s,%s,%s,now(),%s,%s,%s)
        ON CONFLICT (news_id, ticker_code)
        DO UPDATE SET
            sentiment_score = EXCLUDED.sentiment_score,
            keywords = EXCLUDED.keywords,
            confidence_score = EXCLUDED.confidence_score,
            sentiment_label = EXCLUDED.sentiment_label,
            processed_at = now()
    """

    batch = []
    total = len(rows)

    for i, (news_id, title, published_at) in enumerate(rows):

        tickers, keywords = detect(title, alias_map)

        if not tickers:
            continue

        score, matched_keywords = score_sentiment(title)
        score, confidence, label = classify(score)

        keywords = matched_keywords[:5]

        for t in tickers:
            batch.append((
                news_id,
                t,
                score,
                json.dumps(keywords, ensure_ascii=False),
                confidence,
                label,
                PROCESSOR_VERSION,
                published_at,
                published_at.date()
            ))

        if len(batch) >= BATCH_SIZE:
            execute_batch(cur, insert_sql, batch)
            conn.commit()
            batch.clear()

        if i % 1000 == 0:
            print(f"{i}/{total}")

    if batch:
        execute_batch(cur, insert_sql, batch)
        conn.commit()

    conn.close()

    print(f"===== DONE ({time.time()-start:.2f}s) =====")


if __name__ == "__main__":
    run()
