import json
import re
import time
import psycopg2
from db_config import get_db_config
from psycopg2.extras import execute_batch

PROCESSOR_VERSION = "EVENT-3.0.0"
BATCH_SIZE = 5000

# 필요하면 테스트용
TEST_LIMIT = None
# TEST_LIMIT = 3000


# =========================
# TOKENIZE
# =========================
def tokenize(text):
    return re.findall(r"[가-힣A-Za-z0-9]+", text or "")


# =========================
# FETCH NEWS
# =========================
def fetch_news_rows(cur):
    sql = """
        SELECT id, title, published_at
        FROM interest_news_raw
        ORDER BY id DESC
    """
    if TEST_LIMIT:
        sql += f" LIMIT {int(TEST_LIMIT)}"

    cur.execute(sql)
    return cur.fetchall()


# =========================
# LOAD EVENT MASTER
# =========================
def load_event_master(cur):
    cur.execute("""
        SELECT event_name, sector_kr, COALESCE(base_weight, 1.00)
        FROM pre_event_master
    """)
    rows = cur.fetchall()

    event_master = {}
    for event_name, sector_kr, base_weight in rows:
        event_master[event_name] = {
            "sector_kr": sector_kr,
            "base_weight": float(base_weight or 1.0)
        }
    return event_master


# =========================
# LOAD EVENT KEYWORDS
# =========================
def load_event_keywords(cur):
    cur.execute("""
        SELECT event_name, keyword, COALESCE(keyword_weight, 1.00)
        FROM pre_event_keyword
        ORDER BY event_name, length(keyword) DESC, keyword_weight DESC
    """)
    rows = cur.fetchall()

    event_keywords = {}

    for event_name, keyword, keyword_weight in rows:
        event_keywords.setdefault(event_name, []).append({
            "keyword": keyword.strip(),
            "keyword_weight": float(keyword_weight or 1.0)
        })

    return event_keywords


# =========================
# LOAD EVENT SECTOR WEIGHTS
# =========================
def load_event_sector_weights(cur):
    cur.execute("""
        SELECT event_name, sector_kr, COALESCE(weight, 1.00)
        FROM pre_event_sector_weight
        ORDER BY event_name, weight DESC, sector_kr
    """)
    rows = cur.fetchall()

    sector_weights = {}

    for event_name, sector_kr, weight in rows:
        sector_weights.setdefault(event_name, []).append({
            "sector_kr": sector_kr,
            "weight": float(weight or 1.0)
        })

    return sector_weights


# =========================
# TEXT NORMALIZE
# =========================
def normalize_text(text):
    text = (text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


# =========================
# EVENT DIRECTION
# =========================
def infer_event_direction(event_name, title):

    # 🔥 1. 시장 하락 override (최우선)
    market_negative = ["하락", "급락", "폭락", "약세"]
    for w in market_negative:
        if w in title:
            return "negative"

    # 🔥 2. 전쟁 강제 negative
    if "전쟁" in event_name:
        return "negative"

    # 🔥 1. 기대 감소 먼저 (특수 케이스)
    if "기대" in title and ("둔화" in title or "뚝" in title or "약화" in title):
        return "negative"

    # 기존 코드 그대로
    negative_override = [
    "소멸", "우려", "둔화", "악화", "충격", "공포",
    "하방", "압력", "부담", "뚝" ]

    for w in negative_override:
        if w in title:
            return "negative"

    positive_override = ["급등", "호재", "강세"]
    for w in positive_override:
        if w in title:
            return "positive"

    positive_markers = ["상승", "인하", "회복", "확대", "성장"]
    negative_markers = ["하락", "인상", "침체"]

    for w in negative_markers:
        if w in event_name:
            return "negative"

    for w in positive_markers:
        if w in event_name:
            return "positive"

    return "neutral"


# =========================
# CONFIDENCE
# =========================
def calc_confidence(total_keyword_weight, matched_count):
    """
    너무 복잡하게 안 가고,
    1~2개 핵심 키워드만 잡혀도 높은 confidence를 주는 방식.
    """
    if matched_count <= 0:
        return 0.0

    confidence = total_keyword_weight / 1.5
    if matched_count >= 2:
        confidence += 0.10

    return round(min(1.0, confidence), 4)


# =========================
# DETECT EVENTS FROM TITLE ONLY
# =========================
def detect_events(title, event_keywords):
    text = normalize_text(title)

    detected = []

    for event_name, keyword_rows in event_keywords.items():

        # 🔥 1. 가짜 전쟁 필터 (여기 추가)
        if "전쟁" in text:
            fake_war_keywords = ["표 전쟁", "경쟁", "패권 경쟁", "시장 전쟁", "치킨 게임", "비만약 전쟁"]
            if any(fw in text for fw in fake_war_keywords):
                if "전쟁" in event_name:
                    continue

        matched_keywords = []
        total_keyword_weight = 0.0

        # 긴 키워드 우선
        for row in keyword_rows:
            kw = row["keyword"]
            kw_weight = row["keyword_weight"]

            if kw and kw in text:
                matched_keywords.append(kw)
                total_keyword_weight += kw_weight

        if matched_keywords:
            confidence = calc_confidence(
                total_keyword_weight=total_keyword_weight,
                matched_count=len(matched_keywords)
            )

            detected.append({
                "event_name": event_name,
                "matched_keywords": matched_keywords,
                "matched_keyword_count": len(matched_keywords),
                "keyword_score_sum": round(total_keyword_weight, 4),
                "event_confidence": confidence
            })

    return detected

# =========================
# BUILD INSERT ROWS
# =========================
def build_insert_rows(news_id, title, published_at,
                      detected_events, event_master, sector_weights):
    rows = []

    published_date = published_at.date() if published_at else None

    for event in detected_events:
        event_name = event["event_name"]
        confidence = event["event_confidence"]

        master = event_master.get(event_name)
        if not master:
            continue

        base_weight = float(master.get("base_weight", 1.0))
        direction = infer_event_direction(event_name, title)

        # 섹터 확장 테이블이 있으면 그걸 우선 사용
        mapped_sectors = sector_weights.get(event_name, [])

        # 혹시 sector mapping이 없으면 master의 대표 sector라도 1건 생성
        if not mapped_sectors:
            fallback_sector = master.get("sector_kr")
            if fallback_sector:
                mapped_sectors = [{
                    "sector_kr": fallback_sector,
                    "weight": 1.0
                }]

        for s in mapped_sectors:
            sector_kr = s["sector_kr"]
            sector_weight = float(s["weight"])

            final_weight = round(confidence * base_weight * sector_weight, 4)

            rows.append((
                news_id,                 # news_id
                event_name,              # event_name
                sector_kr,               # sector_kr
                final_weight,            # weight
                published_at,            # news_published_at
                PROCESSOR_VERSION,       # processor_version
                published_date,          # published_date
                confidence,              # event_confidence
                direction                # event_direction
            ))

    return rows


# =========================
# MAIN
# =========================
def run():
    print("===== PRE NEWS EVENT START =====")
    start = time.time()

    conn = psycopg2.connect(**get_db_config())
    cur = conn.cursor()

    print("[STEP] load event dictionaries...")
    event_master = load_event_master(cur)
    event_keywords = load_event_keywords(cur)
    sector_weights = load_event_sector_weights(cur)

    print(f"[INFO] event_master={len(event_master)}")
    print(f"[INFO] event_keywords={sum(len(v) for v in event_keywords.values())}")
    print(f"[INFO] sector_weights={sum(len(v) for v in sector_weights.values())}")

    print("[STEP] fetch news rows...")
    news_rows = fetch_news_rows(cur)
    total = len(news_rows)
    print(f"[INFO] total_news={total}")

    insert_sql = """
        INSERT INTO pre_news_event
        (
            news_id,
            event_name,
            sector_kr,
            weight,
            news_published_at,
            processor_version,
            published_date,
            event_confidence,
            event_direction
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (news_id, event_name, sector_kr)
        DO UPDATE SET
            weight = EXCLUDED.weight,
            news_published_at = EXCLUDED.news_published_at,
            processor_version = EXCLUDED.processor_version,
            published_date = EXCLUDED.published_date,
            event_confidence = EXCLUDED.event_confidence,
            event_direction = EXCLUDED.event_direction,
            detected_at = now()
    """

    batch = []

    detected_news_count = 0
    detected_event_count = 0
    inserted_row_count = 0

    for i, (news_id, title, published_at) in enumerate(news_rows, start=1):
        title = normalize_text(title)

        if not title:
            continue

        detected_events = detect_events(title, event_keywords)

        if not detected_events:
            continue

        detected_news_count += 1
        detected_event_count += len(detected_events)

        rows = build_insert_rows(
            news_id=news_id,
            title=title,
            published_at=published_at,
            detected_events=detected_events,
            event_master=event_master,
            sector_weights=sector_weights
        )

        if rows:
            batch.extend(rows)
            inserted_row_count += len(rows)

        if len(batch) >= BATCH_SIZE:
            execute_batch(cur, insert_sql, batch)
            conn.commit()
            batch.clear()

        if i % 1000 == 0:
            elapsed = time.time() - start
            print(
                f"[PROGRESS] {i}/{total} ({i/total*100:.2f}%) | "
                f"detected_news={detected_news_count} | "
                f"detected_events={detected_event_count} | "
                f"rows={inserted_row_count} | "
                f"elapsed={elapsed:.1f}s"
            )

    if batch:
        execute_batch(cur, insert_sql, batch)
        conn.commit()
        batch.clear()

    cur.close()
    conn.close()

    elapsed = time.time() - start
    print("===== DONE =====")
    print(
        f"[SUMMARY] total_news={total}, "
        f"detected_news={detected_news_count}, "
        f"detected_events={detected_event_count}, "
        f"inserted_rows={inserted_row_count}, "
        f"elapsed={elapsed:.2f}s"
    )


if __name__ == "__main__":
    run()