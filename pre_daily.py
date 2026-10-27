"""Orchestration script that calls the daily preprocessing pipeline in order.

It invokes the run() entrypoint of each pre_* module; during actual execution,
DB reads/writes and external holiday API calls can occur in a chain.
"""

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

# 🔥 added
import pre_price
import pre_investorflow

# 🔥 added
import pre_total_market_daily_feature
import pre_total_stock_daily_feature

def run():

    print("🚀 PREPROCESSOR PIPELINE START")

    # 1️⃣ News NLP analysis
    pre_news_analysis.run()

    # 2️⃣ News event detection
    pre_news_event_detection.run()

    # 3️⃣ News daily aggregation
    pre_news_daily_aggregator.run()

    # 4️⃣ Agency analysis
    #pre_agency_analysis.run()

    # 5️⃣ Agency daily aggregation
    pre_agency_daily_aggregator.run()

    # 6️⃣ Commodity
    pre_commodity.run()

    # 7️⃣ Foreign Index
    pre_foreignindex.run()

    # 9️⃣ Macro
    pre_macroeconomic.run()

    # 🔥 1️⃣2️⃣ PRICE (added)
    pre_price.run()

    # 8️⃣ Market Breadth
    pre_marketbreadth.run()

    # 🔥 1️⃣3️⃣ INVESTORFLOW (added)
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
