import pre_news_analysis
import pre_news_event_detection
import pre_news_daily_aggregator

import pre_agency_analysis
import pre_agency_daily_aggregator

import pre_commodity
import pre_foreignindex
import pre_marketbreadth
import pre_macroeconomic

import pre_program
import pre_shortsell

# 🔥 추가
import pre_price
import pre_investorflow

# 🔥 추가
import pre_total_market_daily_feature
import pre_total_stock_daily_feature

def run():

    print("🚀 PREPROCESSOR PIPELINE START")

    # 1️⃣ 뉴스 NLP 분석
    pre_news_analysis.run()

    # 2️⃣ 뉴스 이벤트 탐지
    pre_news_event_detection.run()

    # 3️⃣ 뉴스 Daily 집계
    pre_news_daily_aggregator.run()

    # 4️⃣ Agency 분석
    #pre_agency_analysis.run()

    # 5️⃣ Agency Daily 집계
    pre_agency_daily_aggregator.run()

    # 6️⃣ Commodity
    pre_commodity.run()

    # 7️⃣ Foreign Index
    pre_foreignindex.run()

    # 9️⃣ Macro
    pre_macroeconomic.run()

    # 🔥 1️⃣2️⃣ PRICE (추가)
    pre_price.run()

    # 8️⃣ Market Breadth
    pre_marketbreadth.run()

    # 🔥 1️⃣3️⃣ INVESTORFLOW (추가)
    pre_investorflow.run()

    # 🔟 Program
    pre_program.run()

    # 1️⃣1️⃣ Shortsell
    pre_shortsell.run()

    # 1️⃣4️⃣ TOTAL
    pre_total_market_daily_feature.run()
    pre_total_stock_daily_feature.run()

    print("🎯 PREPROCESSOR PIPELINE END")

if __name__ == "__main__":
    run()