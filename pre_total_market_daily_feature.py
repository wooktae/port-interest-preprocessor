import psycopg2
from db_config import get_db_config
from datetime import date, timedelta
from interest_get_holidays import is_holiday

PROCESSOR_VERSION = "7.0.0"

# =========================
# MARKET WEIGHTS CONFIG
# =========================

# OUTER WEIGHTS
FLOW_SCALE = 8
FLOW_WEIGHT = 0.48   # 👈 살짝만 줄여

BREADTH_WEIGHT = 0.28  # 👈 핵심 (올려)
MACRO_WEIGHT = 0.10
GLOBAL_WEIGHT = 0.03
COMMODITY_WEIGHT = 0.05
PROGRAM_WEIGHT = 0.06  # 👈 약간 줄여

# =========================
# FLOW INTERNAL WEIGHTS
# =========================
FLOW_W_FGN_5D = 0.40
FLOW_W_FGN_1D = 0.15
FLOW_W_INST_5D = 0.15
FLOW_W_INST_1D = 0.05
FLOW_W_ACCEL = 0.10
FLOW_W_DIFF = 0.05
FLOW_W_STRENGTH = 0.05
FLOW_W_BUY_RATIO = 0.05


def get_conn():
    return psycopg2.connect(**get_db_config())


def get_latest_business_date(market="KR"):
    d = date.today() - timedelta(days=1)

    while is_holiday(d, market):
        d -= timedelta(days=1)

    return d


def aggregate_total_market(conn, target_date):
    cur = conn.cursor()

    sql = f"""
    INSERT INTO pre_total_market_daily_feature (
        date,

        global_risk_score,
        global_momentum_3d,
        risk_regime,

        vix_return,
        vol_pressure,
        rate_pressure,
        fx_pressure,
        macro_pressure_score,

        commodity_pressure_score,
        energy_pressure,
        metal_pressure,
        inflation_commodity_score,
        growth_commodity_score,
        energy_shock_flag,
        metal_shock_flag,

        advance_decline_diff_ratio,
        breadth_pressure_score,
        decline_share,
        breadth_thrust_flag,

        program_pressure_score,
        program_momentum_3d,
        program_momentum_5d,
        program_strength_zscore,

        market_foreign_net_ratio_1d,
        market_foreign_net_ratio_3d,
        market_foreign_net_ratio_5d,
        market_foreign_net_ratio_10d,

        market_institution_net_ratio_1d,
        market_institution_net_ratio_3d,
        market_institution_net_ratio_5d,
        market_institution_net_ratio_10d,

        market_foreign_flow_acceleration,
        market_institution_flow_acceleration,
        market_foreign_institution_diff_5d,
        market_flow_strength_score,
        market_foreign_buy_ratio,
        market_institution_buy_ratio,
        flow_pressure_score,

        market_regime_score,

        processor_version
    )
    SELECT
        d.date,

        /* GLOBAL */
        f.global_risk_score,
        f.global_momentum_3d,
        f.risk_regime,

        /* MACRO */
        m.vix_return,
        m.vol_pressure,
        m.rate_pressure,
        m.fx_pressure,
        m.macro_pressure_score,

        /* COMMODITY */
        c.commodity_pressure_score,
        c.energy_pressure,
        c.metal_pressure,
        c.inflation_commodity_score,
        c.growth_commodity_score,
        c.energy_shock_flag,
        c.metal_shock_flag,

        /* BREADTH */
        b.advance_decline_diff_ratio,
        b.breadth_pressure_score,
        b.decline_share,
        b.breadth_thrust_flag,

        /* PROGRAM */
        pg.program_pressure_score,
        pg.program_momentum_3d,
        pg.program_momentum_5d,
        pg.program_strength_zscore,

        /* MARKET FLOW */
        mf.market_foreign_net_ratio_1d,
        mf.market_foreign_net_ratio_3d,
        mf.market_foreign_net_ratio_5d,
        mf.market_foreign_net_ratio_10d,

        mf.market_institution_net_ratio_1d,
        mf.market_institution_net_ratio_3d,
        mf.market_institution_net_ratio_5d,
        mf.market_institution_net_ratio_10d,

        mf.market_foreign_flow_acceleration,
        mf.market_institution_flow_acceleration,
        mf.market_foreign_institution_diff_5d,
        mf.market_flow_strength_score,
        mf.market_foreign_buy_ratio,
        mf.market_institution_buy_ratio,

        /* FLOW PRESSURE SCORE */
        
        (
            COALESCE(mf.market_foreign_net_ratio_5d, 0) * {FLOW_W_FGN_5D}
        + COALESCE(mf.market_foreign_net_ratio_1d, 0) * {FLOW_W_FGN_1D}
        + COALESCE(mf.market_institution_net_ratio_5d, 0) * {FLOW_W_INST_5D}
        + COALESCE(mf.market_institution_net_ratio_1d, 0) * {FLOW_W_INST_1D}
        + COALESCE(mf.market_foreign_flow_acceleration, 0) * {FLOW_W_ACCEL}
        + COALESCE(mf.market_foreign_institution_diff_5d, 0) * {FLOW_W_DIFF}
        + COALESCE(mf.market_flow_strength_score, 0) * {FLOW_W_STRENGTH}
        + ((COALESCE(mf.market_foreign_buy_ratio, 0.5) - 0.5) * 2.0) * {FLOW_W_BUY_RATIO}
        ) * {FLOW_SCALE} AS flow_pressure_score,

        /* 🔥 MARKET SCORE (FIXED) */
        (
            COALESCE(
                SIGN(
                    (
                        COALESCE(mf.market_foreign_net_ratio_5d, 0) * {FLOW_W_FGN_5D}
                    + COALESCE(mf.market_foreign_net_ratio_1d, 0) * {FLOW_W_FGN_1D}
                    + COALESCE(mf.market_institution_net_ratio_5d, 0) * {FLOW_W_INST_5D}
                    + COALESCE(mf.market_institution_net_ratio_1d, 0) * {FLOW_W_INST_1D}
                    + COALESCE(mf.market_foreign_flow_acceleration, 0) * {FLOW_W_ACCEL}
                    + COALESCE(mf.market_foreign_institution_diff_5d, 0) * {FLOW_W_DIFF}
                    + COALESCE(mf.market_flow_strength_score, 0) * {FLOW_W_STRENGTH}
                    + ((COALESCE(mf.market_foreign_buy_ratio, 0.5) - 0.5) * 2.0) * {FLOW_W_BUY_RATIO}
                    )
                )
                *
                POWER(
                    ABS(
                        (
                            COALESCE(mf.market_foreign_net_ratio_5d, 0) * {FLOW_W_FGN_5D}
                        + COALESCE(mf.market_foreign_net_ratio_1d, 0) * {FLOW_W_FGN_1D}
                        + COALESCE(mf.market_institution_net_ratio_5d, 0) * {FLOW_W_INST_5D}
                        + COALESCE(mf.market_institution_net_ratio_1d, 0) * {FLOW_W_INST_1D}
                        + COALESCE(mf.market_foreign_flow_acceleration, 0) * {FLOW_W_ACCEL}
                        + COALESCE(mf.market_foreign_institution_diff_5d, 0) * {FLOW_W_DIFF}
                        + COALESCE(mf.market_flow_strength_score, 0) * {FLOW_W_STRENGTH}
                        + ((COALESCE(mf.market_foreign_buy_ratio, 0.5) - 0.5) * 2.0) * {FLOW_W_BUY_RATIO}
                        )
                    ),
                    0.9
                ),
                0
            ) * {FLOW_SCALE} * {FLOW_WEIGHT}

            + LEAST(GREATEST(COALESCE(b.breadth_pressure_score, 0), -0.5), 0.5) * {BREADTH_WEIGHT}
            + COALESCE(m.macro_pressure_score, 0) * {MACRO_WEIGHT}
            + COALESCE(f.global_risk_score, 0) * {GLOBAL_WEIGHT}
            + COALESCE(c.commodity_pressure_score, 0) * {COMMODITY_WEIGHT}
            + COALESCE(pg.program_strength_zscore, 0) * {PROGRAM_WEIGHT}
        ) AS market_regime_score,

        %s

    FROM (
        SELECT DISTINCT date
        FROM pre_marketbreadth_daily_feature
    ) d

    LEFT JOIN LATERAL (
        SELECT *
        FROM pre_foreignindex_daily_feature f
        WHERE f.date <= d.date
        ORDER BY f.date DESC
        LIMIT 1
    ) f ON TRUE

    LEFT JOIN LATERAL (
        SELECT *
        FROM pre_macroeconomic_daily_feature m
        WHERE m.date <= d.date
        ORDER BY m.date DESC
        LIMIT 1
    ) m ON TRUE

    LEFT JOIN LATERAL (
        SELECT *
        FROM pre_commodity_daily_feature c
        WHERE c.date <= d.date
        ORDER BY c.date DESC
        LIMIT 1
    ) c ON TRUE

    LEFT JOIN pre_marketbreadth_daily_feature b
      ON b.date = d.date

    LEFT JOIN pre_program_daily_feature pg
      ON pg.date = d.date

    LEFT JOIN (
        SELECT
            date,

            /* 1D / 3D : traded_value 가중 */
            SUM(COALESCE(foreign_net_ratio_1d, 0) * COALESCE(traded_value, 0))
                / NULLIF(SUM(COALESCE(traded_value, 0)), 0) AS market_foreign_net_ratio_1d,

            SUM(COALESCE(foreign_net_ratio_3d, 0) * COALESCE(traded_value, 0))
                / NULLIF(SUM(COALESCE(traded_value, 0)), 0) AS market_foreign_net_ratio_3d,

            /* 5D / 10D : traded_value_5d 가중 */
            SUM(COALESCE(foreign_net_ratio_5d, 0) * COALESCE(traded_value_5d, traded_value, 0))
                / NULLIF(SUM(COALESCE(traded_value_5d, traded_value, 0)), 0) AS market_foreign_net_ratio_5d,

            SUM(COALESCE(foreign_net_ratio_10d, 0) * COALESCE(traded_value_5d, traded_value, 0))
                / NULLIF(SUM(COALESCE(traded_value_5d, traded_value, 0)), 0) AS market_foreign_net_ratio_10d,

            SUM(COALESCE(institution_net_ratio_1d, 0) * COALESCE(traded_value, 0))
                / NULLIF(SUM(COALESCE(traded_value, 0)), 0) AS market_institution_net_ratio_1d,

            SUM(COALESCE(institution_net_ratio_3d, 0) * COALESCE(traded_value, 0))
                / NULLIF(SUM(COALESCE(traded_value, 0)), 0) AS market_institution_net_ratio_3d,

            SUM(COALESCE(institution_net_ratio_5d, 0) * COALESCE(traded_value_5d, traded_value, 0))
                / NULLIF(SUM(COALESCE(traded_value_5d, traded_value, 0)), 0) AS market_institution_net_ratio_5d,

            SUM(COALESCE(institution_net_ratio_10d, 0) * COALESCE(traded_value_5d, traded_value, 0))
                / NULLIF(SUM(COALESCE(traded_value_5d, traded_value, 0)), 0) AS market_institution_net_ratio_10d,

            SUM(COALESCE(foreign_flow_acceleration, 0) * COALESCE(traded_value, 0))
                / NULLIF(SUM(COALESCE(traded_value, 0)), 0) AS market_foreign_flow_acceleration,

            SUM(COALESCE(institution_flow_acceleration, 0) * COALESCE(traded_value, 0))
                / NULLIF(SUM(COALESCE(traded_value, 0)), 0) AS market_institution_flow_acceleration,

            SUM(COALESCE(foreign_institution_diff_5d, 0) * COALESCE(traded_value_5d, traded_value, 0))
                / NULLIF(SUM(COALESCE(traded_value_5d, traded_value, 0)), 0) AS market_foreign_institution_diff_5d,

            SUM(COALESCE(flow_strength_score, 0) * COALESCE(traded_value, 0))
                / NULLIF(SUM(COALESCE(traded_value, 0)), 0) AS market_flow_strength_score,

            AVG(
                CASE
                    WHEN foreign_net_ratio_1d > 0 THEN 1.0
                    ELSE 0.0
                END
            ) AS market_foreign_buy_ratio,

            AVG(
                CASE
                    WHEN institution_net_ratio_1d > 0 THEN 1.0
                    ELSE 0.0
                END
            ) AS market_institution_buy_ratio

        FROM pre_investorflow_daily_feature
        GROUP BY date
    ) mf
      ON mf.date = d.date

    WHERE d.date <= %s
      AND (
            f.global_risk_score IS NOT NULL
         OR m.macro_pressure_score IS NOT NULL
         OR c.commodity_pressure_score IS NOT NULL
         OR b.breadth_pressure_score IS NOT NULL
         OR mf.market_foreign_net_ratio_5d IS NOT NULL
      )

    ON CONFLICT (date)
    DO UPDATE SET
        global_risk_score = EXCLUDED.global_risk_score,
        global_momentum_3d = EXCLUDED.global_momentum_3d,
        risk_regime = EXCLUDED.risk_regime,

        vix_return = EXCLUDED.vix_return,
        vol_pressure = EXCLUDED.vol_pressure,
        rate_pressure = EXCLUDED.rate_pressure,
        fx_pressure = EXCLUDED.fx_pressure,
        macro_pressure_score = EXCLUDED.macro_pressure_score,

        commodity_pressure_score = EXCLUDED.commodity_pressure_score,
        energy_pressure = EXCLUDED.energy_pressure,
        metal_pressure = EXCLUDED.metal_pressure,
        inflation_commodity_score = EXCLUDED.inflation_commodity_score,
        growth_commodity_score = EXCLUDED.growth_commodity_score,
        energy_shock_flag = EXCLUDED.energy_shock_flag,
        metal_shock_flag = EXCLUDED.metal_shock_flag,

        advance_decline_diff_ratio = EXCLUDED.advance_decline_diff_ratio,
        breadth_pressure_score = EXCLUDED.breadth_pressure_score,
        decline_share = EXCLUDED.decline_share,
        breadth_thrust_flag = EXCLUDED.breadth_thrust_flag,

        program_pressure_score = EXCLUDED.program_pressure_score,
        program_momentum_3d = EXCLUDED.program_momentum_3d,
        program_momentum_5d = EXCLUDED.program_momentum_5d,
        program_strength_zscore = EXCLUDED.program_strength_zscore,

        market_foreign_net_ratio_1d = EXCLUDED.market_foreign_net_ratio_1d,
        market_foreign_net_ratio_3d = EXCLUDED.market_foreign_net_ratio_3d,
        market_foreign_net_ratio_5d = EXCLUDED.market_foreign_net_ratio_5d,
        market_foreign_net_ratio_10d = EXCLUDED.market_foreign_net_ratio_10d,

        market_institution_net_ratio_1d = EXCLUDED.market_institution_net_ratio_1d,
        market_institution_net_ratio_3d = EXCLUDED.market_institution_net_ratio_3d,
        market_institution_net_ratio_5d = EXCLUDED.market_institution_net_ratio_5d,
        market_institution_net_ratio_10d = EXCLUDED.market_institution_net_ratio_10d,

        market_foreign_flow_acceleration = EXCLUDED.market_foreign_flow_acceleration,
        market_institution_flow_acceleration = EXCLUDED.market_institution_flow_acceleration,
        market_foreign_institution_diff_5d = EXCLUDED.market_foreign_institution_diff_5d,
        market_flow_strength_score = EXCLUDED.market_flow_strength_score,
        market_foreign_buy_ratio = EXCLUDED.market_foreign_buy_ratio,
        market_institution_buy_ratio = EXCLUDED.market_institution_buy_ratio,
        flow_pressure_score = EXCLUDED.flow_pressure_score,

        market_regime_score = EXCLUDED.market_regime_score,

        processor_version = EXCLUDED.processor_version,
        updated_at = now()
    """

    cur.execute(sql, (
        PROCESSOR_VERSION,
        target_date
    ))

    conn.commit()
    cur.close()


def run():
    print("===== PRE TOTAL MARKET START =====")

    conn = get_conn()

    try:
        target_date = get_latest_business_date("KR")
        #print(f"[TARGET DATE] {target_date}")

        aggregate_total_market(conn, target_date)

        #print("[DONE] pre_total_market_daily_feature")

    finally:
        conn.close()

    print("===== PRE TOTAL MARKET END =====")


if __name__ == "__main__":
    run()