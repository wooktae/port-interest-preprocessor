import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "interest_crawler",
    "user": "postgres",
    "password": "doflwhsk3768!"
}

PROCESSOR_VERSION = "6.5.0"

# =========================
# FINAL SCORE WEIGHTS
# =========================
FLOW_WEIGHT = 0.50
TAPE_WEIGHT = 0.30
INFO_WEIGHT = 0.05
SHORT_WEIGHT = 0.15
INFO_BONUS = 0.01

# =========================
# FINAL CLIPPING
# =========================
INFO_CLIP = 0.40

# =========================
# FLOW SCORE CONFIG
# =========================
FLOW_W_STRENGTH = 0.55
FLOW_W_ACCEL = 0.12
FLOW_W_MOMENTUM = 0.10
FLOW_W_DIFF_5D = 0.13
FLOW_W_SMART = 0.10
FLOW_SCALE = 1.8

# =========================
# INFO SCORE CONFIG
# =========================
INFO_W_NEWS = 0.60
INFO_W_AGENCY = 0.40
INFO_SCALE = 1.2

NEWS_W_SENTIMENT = 0.50
NEWS_W_EVENT = 0.30
NEWS_W_FRESHNESS = 0.20
FRESHNESS_CLIP = 5.0

AGENCY_W_UPSIDE = 0.70
AGENCY_W_OPINION = 0.30
UPSIDE_MIN = -0.30
UPSIDE_MAX = 1.00

# =========================
# SHORT PENALTY CONFIG
# =========================
SHORT_SCALE = 1.8
SHORT_SPIKE_RAW_PENALTY = 0.10

STRONG_FLOW_SHORT_RELIEF_TH = 0.40
STRONG_FLOW_SHORT_RELIEF_MULT = 0.70

# =========================
# NEUTRAL / GATING CONFIG
# =========================
NEUTRAL_FLOW_ABS_MAX = 0.08
NEUTRAL_TAPE_MIN = -0.10
NEUTRAL_TAPE_MAX = 0.10
NEUTRAL_INFO_ABS_MAX = 0.03
NEUTRAL_LIFT = 0.035

FLOW_NEG_TAPE_GATE_STRONG = -0.25
FLOW_NEG_TAPE_GATE_WEAK = -0.10
FLOW_NEG_TAPE_MULT_STRONG = 0.35
FLOW_NEG_TAPE_MULT_WEAK = 0.60

# =========================
# HARD SHORT THRESHOLD CONFIG
# =========================
HARD_SHORT_PRESSURE_TH = 6.0
HARD_SHORT_ZSCORE_TH = 1.5
HARD_SHORT_MOM_TH = 2.0

HARD_SHORT_PENALTY = 0.12
SPIKE_ONLY_PENALTY = 0.04


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def aggregate_total_stock(conn):
    cur = conn.cursor()

    sql = """
    WITH base AS (
        SELECT
            p.ticker_code,
            p.date,

            /* PRICE */
            p.close_price,
            p.daily_return,
            p.log_return,
            p.momentum_5d,
            p.momentum_20d,
            p.price_vs_ma20,
            p.price_vs_ma60,
            p.volatility_20d,
            p.volume_ratio_5d,
            p.intraday_range,
            p.body_ratio,

            /* INVESTOR */
            i.foreign_net_ratio_5d,
            i.foreign_net_ratio_10d,
            i.institution_net_ratio_5d,
            i.institution_net_ratio_10d,
            i.foreign_hold_change,
            i.smart_money_score,
            i.flow_strength_score,
            i.foreign_flow_acceleration,
            i.foreign_flow_momentum,
            i.foreign_institution_diff_5d,

            /* SHORT */
            s.short_ratio,
            s.short_ratio_avg_5d,
            s.short_ratio_momentum_5d,
            s.short_pressure_score,
            s.short_ratio_zscore_20d,
            s.short_spike_flag,

            /* NEWS */
            n.news_count,
            n.avg_sentiment,
            n.positive_ratio,
            n.negative_ratio,
            n.sentiment_pressure,
            n.event_count,
            n.event_pressure,
            n.freshness_weighted_sentiment,

            /* AGENCY */
            a.report_count,
            a.avg_recommendation_score,
            a.buy_ratio,
            a.sell_ratio,
            a.hold_ratio,
            a.avg_target_price,
            a.target_price_upside_ratio,
            a.no_signal_flag

        FROM pre_price_daily_feature p
        LEFT JOIN pre_investorflow_daily_feature i
            ON p.ticker_code = i.ticker_code
           AND p.date = i.date
        LEFT JOIN pre_shortsell_daily_feature s
            ON p.ticker_code = s.ticker_code
           AND p.date = s.date
        LEFT JOIN pre_news_daily_feature n
            ON p.ticker_code = n.ticker_code
           AND p.date = n.date
        LEFT JOIN pre_agency_daily_feature a
            ON p.ticker_code = a.ticker_code
           AND p.date = a.date
    ),

    /* =========================
       TAPE SCORE
    ========================= */
    tape_calc AS (
        SELECT
            *,
            TANH(
                (
                    COALESCE(momentum_5d, 0) * 0.25 +
                    COALESCE(momentum_20d, 0) * 0.35 +
                    COALESCE(price_vs_ma20, 0) * 0.15 +
                    COALESCE(price_vs_ma60, 0) * 0.10 +
                    COALESCE(volume_ratio_5d, 0) * 0.10 +
                    COALESCE(body_ratio, 0) * 0.05
                ) * 2.8
            ) AS tape_score_raw
        FROM base
    ),

    /* =========================
       FLOW SCORE
    ========================= */
    flow_calc AS (
        SELECT
            *,
            TANH(
                (
                    COALESCE(flow_strength_score, 0) * %(FLOW_W_STRENGTH)s
                  + COALESCE(foreign_flow_acceleration, 0) * %(FLOW_W_ACCEL)s
                  + COALESCE(foreign_flow_momentum, 0) * %(FLOW_W_MOMENTUM)s
                  + COALESCE(foreign_institution_diff_5d, 0) * %(FLOW_W_DIFF_5D)s
                  + COALESCE(smart_money_score, 0) * %(FLOW_W_SMART)s
                ) * %(FLOW_SCALE)s
            ) AS flow_score_raw
        FROM tape_calc
    ),

    /* =========================
       INFO SCORE
    ========================= */
    info_calc AS (
        SELECT
            *,
            CASE
                WHEN COALESCE(news_count, 0) = 0
                 AND COALESCE(report_count, 0) = 0
                THEN 0
                ELSE
                    TANH(
                        (
                            (
                                COALESCE(sentiment_pressure, 0) * %(NEWS_W_SENTIMENT)s
                              + COALESCE(event_pressure, 0) * %(NEWS_W_EVENT)s
                              + (
                                    LEAST(
                                        GREATEST(
                                            COALESCE(freshness_weighted_sentiment, 0),
                                            -%(FRESHNESS_CLIP)s
                                        ),
                                        %(FRESHNESS_CLIP)s
                                    ) / %(FRESHNESS_CLIP)s
                                ) * %(NEWS_W_FRESHNESS)s
                            ) * %(INFO_W_NEWS)s
                            +
                            (
                                CASE
                                    WHEN COALESCE(no_signal_flag, 0) = 1 THEN 0
                                    ELSE
                                        LEAST(
                                            GREATEST(
                                                COALESCE(target_price_upside_ratio, 0),
                                                %(UPSIDE_MIN)s
                                            ),
                                            %(UPSIDE_MAX)s
                                        ) * %(AGENCY_W_UPSIDE)s
                                      + (
                                            COALESCE(buy_ratio, 0) - COALESCE(sell_ratio, 0)
                                        ) * %(AGENCY_W_OPINION)s
                                END
                            ) * %(INFO_W_AGENCY)s
                        ) * %(INFO_SCALE)s
                    )
            END AS info_score_raw
        FROM flow_calc
    ),

    /* =========================
       SHORT PENALTY
    ========================= */
    short_calc AS (
        SELECT
            *,
            TANH(
                (
                    COALESCE(short_ratio_momentum_5d, 0) * 0.35 +
                    CASE
                        WHEN COALESCE(short_spike_flag, false)
                        THEN %(SHORT_SPIKE_RAW_PENALTY)s
                        ELSE 0
                    END +
                    COALESCE(short_ratio_zscore_20d, 0) * 0.15 +
                    COALESCE(short_pressure_score, 0) * 0.25
                ) * %(SHORT_SCALE)s
            ) AS short_penalty_raw,

            CASE
                WHEN COALESCE(short_ratio_zscore_20d, 0) >= %(HARD_SHORT_ZSCORE_TH)s
                 AND COALESCE(short_ratio_momentum_5d, 0) >= %(HARD_SHORT_MOM_TH)s
                THEN %(HARD_SHORT_PENALTY)s

                WHEN COALESCE(short_pressure_score, 0) >= %(HARD_SHORT_PRESSURE_TH)s
                THEN %(HARD_SHORT_PENALTY)s

                WHEN COALESCE(short_spike_flag, false)
                THEN %(SPIKE_ONLY_PENALTY)s

                ELSE 0
            END AS hard_short_penalty
        FROM info_calc
    ),

        /* =========================
       FLOW NEGATIVE -> TAPE GATING
       NEUTRAL GROUP LIFT
       STRONG FLOW -> SHORT RELIEF
    ========================= */
    final_prep AS (
        SELECT
            *,

            CASE
                WHEN flow_score_raw >= 0.3 THEN 1.0
                WHEN flow_score_raw >= 0 THEN 0.6
                ELSE 0.3
            END AS flow_gate_multiplier,

            CASE
                WHEN ABS(COALESCE(flow_score_raw, 0)) <= %(NEUTRAL_FLOW_ABS_MAX)s
                 AND COALESCE(tape_score_raw, 0) BETWEEN %(NEUTRAL_TAPE_MIN)s AND %(NEUTRAL_TAPE_MAX)s
                 AND ABS(COALESCE(info_score_raw, 0)) <= %(NEUTRAL_INFO_ABS_MAX)s
                 AND COALESCE(news_count, 0) = 0
                 AND COALESCE(report_count, 0) = 0
                THEN %(NEUTRAL_LIFT)s
                ELSE 0
            END AS neutral_lift,

            CASE
                WHEN COALESCE(flow_score_raw, 0) > %(STRONG_FLOW_SHORT_RELIEF_TH)s
                THEN %(STRONG_FLOW_SHORT_RELIEF_MULT)s
                ELSE 1.0
            END AS short_penalty_multiplier
        FROM short_calc
    )

    INSERT INTO pre_total_stock_daily_feature (
        ticker_code,
        date,

        close_price,
        daily_return,
        log_return,
        momentum_5d,
        momentum_20d,
        price_vs_ma20,
        price_vs_ma60,
        volatility_20d,
        volume_ratio_5d,
        intraday_range,
        body_ratio,

        foreign_net_ratio_5d,
        foreign_net_ratio_10d,
        institution_net_ratio_5d,
        institution_net_ratio_10d,
        foreign_hold_change,
        smart_money_score,
        foreign_flow_acceleration,
        foreign_flow_momentum,
        foreign_institution_diff_5d,

        short_ratio,
        short_ratio_avg_5d,
        short_ratio_momentum_5d,
        short_pressure_score,
        short_ratio_zscore_20d,
        short_spike_flag,

        news_count,
        avg_sentiment,
        positive_ratio,
        negative_ratio,
        sentiment_pressure,
        event_count,
        event_pressure,
        freshness_weighted_sentiment,

        report_count,
        avg_recommendation_score,
        buy_ratio,
        sell_ratio,
        hold_ratio,
        avg_target_price,
        target_price_upside_ratio,
        no_signal_flag,

        tape_score,
        flow_score,
        info_score,
        final_score,
        has_info_flag,
        processed_at,
        processor_version
    )

    SELECT
        ticker_code,
        date,

        close_price,
        daily_return,
        log_return,
        momentum_5d,
        momentum_20d,
        price_vs_ma20,
        price_vs_ma60,
        volatility_20d,
        volume_ratio_5d,
        intraday_range,
        body_ratio,

        foreign_net_ratio_5d,
        foreign_net_ratio_10d,
        institution_net_ratio_5d,
        institution_net_ratio_10d,
        foreign_hold_change,
        smart_money_score,
        foreign_flow_acceleration,
        foreign_flow_momentum,
        foreign_institution_diff_5d,

        short_ratio,
        short_ratio_avg_5d,
        short_ratio_momentum_5d,
        short_pressure_score,
        short_ratio_zscore_20d,
        short_spike_flag,

        COALESCE(news_count, 0),
        avg_sentiment,
        COALESCE(positive_ratio, 0),
        COALESCE(negative_ratio, 0),
        COALESCE(sentiment_pressure, 0),
        COALESCE(event_count, 0),
        COALESCE(event_pressure, 0),
        freshness_weighted_sentiment,

        COALESCE(report_count, 0),
        avg_recommendation_score,
        COALESCE(buy_ratio, 0),
        COALESCE(sell_ratio, 0),
        COALESCE(hold_ratio, 0),
        avg_target_price,
        target_price_upside_ratio,
        (COALESCE(no_signal_flag, 0) = 1),

        ROUND((tape_score_raw * flow_gate_multiplier)::numeric, 6),
        ROUND(flow_score_raw::numeric, 6),
        ROUND(info_score_raw::numeric, 6),

        ROUND((
            flow_score_raw * %(FLOW_WEIGHT)s
          + (tape_score_raw * flow_gate_multiplier) * %(TAPE_WEIGHT)s
          + LEAST(
                GREATEST(info_score_raw, -%(INFO_CLIP)s),
                %(INFO_CLIP)s
            ) * %(INFO_WEIGHT)s
          - (short_penalty_raw * short_penalty_multiplier) * %(SHORT_WEIGHT)s
          - (hard_short_penalty * short_penalty_multiplier)
          + neutral_lift
          + CASE
                WHEN (COALESCE(news_count, 0) > 0 OR COALESCE(report_count, 0) > 0)
                THEN %(INFO_BONUS)s
                ELSE 0
            END
        )::numeric, 6),

        CASE
            WHEN COALESCE(news_count, 0) > 0
              OR COALESCE(report_count, 0) > 0
            THEN true
            ELSE false
        END,

        now(),
        %(PROCESSOR_VERSION)s

    FROM final_prep

    ON CONFLICT (ticker_code, date)
    DO UPDATE SET
        tape_score = EXCLUDED.tape_score,
        flow_score = EXCLUDED.flow_score,
        info_score = EXCLUDED.info_score,
        final_score = EXCLUDED.final_score,
        processed_at = now(),
        processor_version = EXCLUDED.processor_version,
        updated_at = now()
    """

    params = {
        "PROCESSOR_VERSION": PROCESSOR_VERSION,

        "FLOW_WEIGHT": FLOW_WEIGHT,
        "TAPE_WEIGHT": TAPE_WEIGHT,
        "INFO_WEIGHT": INFO_WEIGHT,
        "SHORT_WEIGHT": SHORT_WEIGHT,
        "INFO_BONUS": INFO_BONUS,

        "INFO_CLIP": INFO_CLIP,

        "FLOW_W_STRENGTH": FLOW_W_STRENGTH,
        "FLOW_W_ACCEL": FLOW_W_ACCEL,
        "FLOW_W_MOMENTUM": FLOW_W_MOMENTUM,
        "FLOW_W_DIFF_5D": FLOW_W_DIFF_5D,
        "FLOW_W_SMART": FLOW_W_SMART,
        "FLOW_SCALE": FLOW_SCALE,

        "INFO_W_NEWS": INFO_W_NEWS,
        "INFO_W_AGENCY": INFO_W_AGENCY,
        "INFO_SCALE": INFO_SCALE,

        "NEWS_W_SENTIMENT": NEWS_W_SENTIMENT,
        "NEWS_W_EVENT": NEWS_W_EVENT,
        "NEWS_W_FRESHNESS": NEWS_W_FRESHNESS,
        "FRESHNESS_CLIP": FRESHNESS_CLIP,

        "AGENCY_W_UPSIDE": AGENCY_W_UPSIDE,
        "AGENCY_W_OPINION": AGENCY_W_OPINION,
        "UPSIDE_MIN": UPSIDE_MIN,
        "UPSIDE_MAX": UPSIDE_MAX,

        "SHORT_SCALE": SHORT_SCALE,

        "NEUTRAL_FLOW_ABS_MAX": NEUTRAL_FLOW_ABS_MAX,
        "NEUTRAL_TAPE_MIN": NEUTRAL_TAPE_MIN,
        "NEUTRAL_TAPE_MAX": NEUTRAL_TAPE_MAX,
        "NEUTRAL_INFO_ABS_MAX": NEUTRAL_INFO_ABS_MAX,
        "NEUTRAL_LIFT": NEUTRAL_LIFT,

        "FLOW_NEG_TAPE_GATE_STRONG": FLOW_NEG_TAPE_GATE_STRONG,
        "FLOW_NEG_TAPE_GATE_WEAK": FLOW_NEG_TAPE_GATE_WEAK,
        "FLOW_NEG_TAPE_MULT_STRONG": FLOW_NEG_TAPE_MULT_STRONG,
        "FLOW_NEG_TAPE_MULT_WEAK": FLOW_NEG_TAPE_MULT_WEAK,

        "HARD_SHORT_PRESSURE_TH": HARD_SHORT_PRESSURE_TH,
        "HARD_SHORT_ZSCORE_TH": HARD_SHORT_ZSCORE_TH,
        "HARD_SHORT_MOM_TH": HARD_SHORT_MOM_TH,
        "HARD_SHORT_PENALTY": HARD_SHORT_PENALTY,

        "SHORT_SPIKE_RAW_PENALTY": SHORT_SPIKE_RAW_PENALTY,

        "STRONG_FLOW_SHORT_RELIEF_TH": STRONG_FLOW_SHORT_RELIEF_TH,
        "STRONG_FLOW_SHORT_RELIEF_MULT": STRONG_FLOW_SHORT_RELIEF_MULT,

        "SPIKE_ONLY_PENALTY": SPIKE_ONLY_PENALTY,
    }

    cur.execute(sql, params)
    conn.commit()
    cur.close()


def run():
    print("===== PRE TOTAL STOCK START =====")

    conn = get_conn()

    try:
        aggregate_total_stock(conn)
        print("[DONE]")
    finally:
        conn.close()

    print("===== END =====")


if __name__ == "__main__":
    run()