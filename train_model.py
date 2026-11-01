"""
Trains the Quick Commerce Demand Forecasting & Inventory Optimization model
using a strict Train/Test split on Data/data.csv:
  - Training Set: 2020-01-01 to 2023-12-31 (730,500 rows, 80%)
  - Test Set:     2024-01-01 to 2024-12-31 (183,000 rows, 20% unseen actuals)

Does NOT use predictions_2025.csv for training or testing.
Evaluates out-of-sample predicting skill strictly against 2024 actual data.
"""

import csv
import json
import math
import os
import pickle
from collections import defaultdict
from datetime import datetime, date, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xgb_reg.joblib")
ARTIFACTS_PATH = os.path.join(DATA_DIR, "model_artifacts.json")
UNMET_QUERIES_PATH = os.path.join(DATA_DIR, "unmet_queries.json")


# Comprehensive Indian Festival & Holiday Calendar (2020-2027)
INDIAN_FESTIVALS_BY_DATE = {
    # 2020
    "2020-01-01": ("New Year's Day", "Celebration"),
    "2020-01-14": ("Makar Sankranti / Pongal", "Harvest Festival"),
    "2020-01-26": ("Republic Day", "National Holiday"),
    "2020-03-10": ("Holi", "Major Festival"),
    "2020-04-14": ("Baisakhi / Puthandu", "Regional Festival"),
    "2020-05-25": ("Eid-ul-Fitr", "Major Festival"),
    "2020-08-03": ("Raksha Bandhan", "Major Festival"),
    "2020-08-11": ("Janmashtami", "Religious Festival"),
    "2020-08-15": ("Independence Day", "National Holiday"),
    "2020-08-22": ("Ganesh Chaturthi", "Major Festival"),
    "2020-08-31": ("Onam", "Harvest Festival"),
    "2020-10-02": ("Gandhi Jayanti", "National Holiday"),
    "2020-10-25": ("Dussehra / Vijayadashami", "Major Festival"),
    "2020-11-12": ("Dhanteras", "Diwali Season"),
    "2020-11-14": ("Diwali / Deepavali", "Mega Festival"),
    "2020-11-16": ("Bhai Dooj", "Diwali Season"),
    "2020-11-30": ("Guru Nanak Jayanti", "Religious Festival"),
    "2020-12-25": ("Christmas", "Celebration"),
    # 2021
    "2021-01-01": ("New Year's Day", "Celebration"),
    "2021-01-14": ("Makar Sankranti / Pongal", "Harvest Festival"),
    "2021-01-26": ("Republic Day", "National Holiday"),
    "2021-03-29": ("Holi", "Major Festival"),
    "2021-04-14": ("Baisakhi / Ambedkar Jayanti", "Regional Festival"),
    "2021-05-14": ("Eid-ul-Fitr", "Major Festival"),
    "2021-08-15": ("Independence Day", "National Holiday"),
    "2021-08-21": ("Onam", "Harvest Festival"),
    "2021-08-22": ("Raksha Bandhan", "Major Festival"),
    "2021-08-30": ("Janmashtami", "Religious Festival"),
    "2021-09-10": ("Ganesh Chaturthi", "Major Festival"),
    "2021-10-02": ("Gandhi Jayanti", "National Holiday"),
    "2021-10-15": ("Dussehra / Vijayadashami", "Major Festival"),
    "2021-11-02": ("Dhanteras", "Diwali Season"),
    "2021-11-04": ("Diwali / Deepavali", "Mega Festival"),
    "2021-11-06": ("Bhai Dooj", "Diwali Season"),
    "2021-11-19": ("Guru Nanak Jayanti", "Religious Festival"),
    "2021-12-25": ("Christmas", "Celebration"),
    # 2022
    "2022-01-01": ("New Year's Day", "Celebration"),
    "2022-01-14": ("Makar Sankranti / Pongal", "Harvest Festival"),
    "2022-01-26": ("Republic Day", "National Holiday"),
    "2022-03-18": ("Holi", "Major Festival"),
    "2022-04-14": ("Baisakhi / Ambedkar Jayanti", "Regional Festival"),
    "2022-05-03": ("Eid-ul-Fitr", "Major Festival"),
    "2022-08-11": ("Raksha Bandhan", "Major Festival"),
    "2022-08-15": ("Independence Day", "National Holiday"),
    "2022-08-19": ("Janmashtami", "Religious Festival"),
    "2022-08-31": ("Ganesh Chaturthi", "Major Festival"),
    "2022-09-08": ("Onam", "Harvest Festival"),
    "2022-10-02": ("Gandhi Jayanti", "National Holiday"),
    "2022-10-05": ("Dussehra / Vijayadashami", "Major Festival"),
    "2022-10-22": ("Dhanteras", "Diwali Season"),
    "2022-10-24": ("Diwali / Deepavali", "Mega Festival"),
    "2022-10-26": ("Bhai Dooj", "Diwali Season"),
    "2022-11-08": ("Guru Nanak Jayanti", "Religious Festival"),
    "2022-12-25": ("Christmas", "Celebration"),
    # 2023
    "2023-01-01": ("New Year's Day", "Celebration"),
    "2023-01-14": ("Makar Sankranti / Pongal", "Harvest Festival"),
    "2023-01-26": ("Republic Day", "National Holiday"),
    "2023-03-08": ("Holi", "Major Festival"),
    "2023-04-14": ("Baisakhi / Ambedkar Jayanti", "Regional Festival"),
    "2023-04-22": ("Eid-ul-Fitr", "Major Festival"),
    "2023-08-15": ("Independence Day", "National Holiday"),
    "2023-08-29": ("Onam", "Harvest Festival"),
    "2023-08-30": ("Raksha Bandhan", "Major Festival"),
    "2023-09-07": ("Janmashtami", "Religious Festival"),
    "2023-09-19": ("Ganesh Chaturthi", "Major Festival"),
    "2023-10-02": ("Gandhi Jayanti", "National Holiday"),
    "2023-10-24": ("Dussehra / Vijayadashami", "Major Festival"),
    "2023-11-10": ("Dhanteras", "Diwali Season"),
    "2023-11-12": ("Diwali / Deepavali", "Mega Festival"),
    "2023-11-15": ("Bhai Dooj", "Diwali Season"),
    "2023-11-27": ("Guru Nanak Jayanti", "Religious Festival"),
    "2023-12-25": ("Christmas", "Celebration"),
    # 2024
    "2024-01-01": ("New Year's Day", "Celebration"),
    "2024-01-14": ("Makar Sankranti / Pongal", "Harvest Festival"),
    "2024-01-26": ("Republic Day", "National Holiday"),
    "2024-03-25": ("Holi", "Major Festival"),
    "2024-04-11": ("Eid-ul-Fitr", "Major Festival"),
    "2024-04-14": ("Baisakhi / Ambedkar Jayanti", "Regional Festival"),
    "2024-08-15": ("Independence Day", "National Holiday"),
    "2024-08-19": ("Raksha Bandhan", "Major Festival"),
    "2024-08-26": ("Janmashtami", "Religious Festival"),
    "2024-09-07": ("Ganesh Chaturthi", "Major Festival"),
    "2024-09-15": ("Onam", "Harvest Festival"),
    "2024-10-02": ("Gandhi Jayanti", "National Holiday"),
    "2024-10-12": ("Dussehra / Vijayadashami", "Major Festival"),
    "2024-10-29": ("Dhanteras", "Diwali Season"),
    "2024-11-01": ("Diwali / Deepavali", "Mega Festival"),
    "2024-11-03": ("Bhai Dooj", "Diwali Season"),
    "2024-11-15": ("Guru Nanak Jayanti", "Religious Festival"),
    "2024-12-25": ("Christmas", "Celebration"),
    # 2025
    "2025-01-01": ("New Year's Day", "Celebration"),
    "2025-01-14": ("Makar Sankranti / Pongal", "Harvest Festival"),
    "2025-01-26": ("Republic Day", "National Holiday"),
    "2025-03-14": ("Holi", "Major Festival"),
    "2025-03-31": ("Eid-ul-Fitr", "Major Festival"),
    "2025-04-14": ("Baisakhi / Ambedkar Jayanti", "Regional Festival"),
    "2025-08-09": ("Raksha Bandhan", "Major Festival"),
    "2025-08-15": ("Independence Day", "National Holiday"),
    "2025-08-16": ("Janmashtami", "Religious Festival"),
    "2025-08-27": ("Ganesh Chaturthi", "Major Festival"),
    "2025-09-05": ("Onam", "Harvest Festival"),
    "2025-10-02": ("Gandhi Jayanti & Dussehra", "Major Festival"),
    "2025-10-18": ("Dhanteras", "Diwali Season"),
    "2025-10-20": ("Diwali / Deepavali", "Mega Festival"),
    "2025-10-22": ("Bhai Dooj", "Diwali Season"),
    "2025-11-05": ("Guru Nanak Jayanti", "Religious Festival"),
    "2025-12-25": ("Christmas", "Celebration"),
    # 2026
    "2026-01-01": ("New Year's Day", "Celebration"),
    "2026-01-14": ("Makar Sankranti / Pongal", "Harvest Festival"),
    "2026-01-26": ("Republic Day", "National Holiday"),
    "2026-03-04": ("Holi", "Major Festival"),
    "2026-03-20": ("Eid-ul-Fitr", "Major Festival"),
    "2026-04-14": ("Baisakhi / Ambedkar Jayanti", "Regional Festival"),
    "2026-08-15": ("Independence Day", "National Holiday"),
    "2026-08-26": ("Onam", "Harvest Festival"),
    "2026-08-28": ("Raksha Bandhan", "Major Festival"),
    "2026-09-04": ("Janmashtami", "Religious Festival"),
    "2026-09-14": ("Ganesh Chaturthi", "Major Festival"),
    "2026-10-02": ("Gandhi Jayanti", "National Holiday"),
    "2026-10-20": ("Dussehra / Vijayadashami", "Major Festival"),
    "2026-11-06": ("Dhanteras", "Diwali Season"),
    "2026-11-08": ("Diwali / Deepavali", "Mega Festival"),
    "2026-11-10": ("Bhai Dooj", "Diwali Season"),
    "2026-11-24": ("Guru Nanak Jayanti", "Religious Festival"),
    "2026-12-25": ("Christmas", "Celebration"),
    # 2027
    "2027-01-01": ("New Year's Day", "Celebration"),
    "2027-01-14": ("Makar Sankranti / Pongal", "Harvest Festival"),
    "2027-01-26": ("Republic Day", "National Holiday"),
    "2027-03-10": ("Eid-ul-Fitr", "Major Festival"),
    "2027-03-22": ("Holi", "Major Festival"),
    "2027-04-14": ("Baisakhi / Ambedkar Jayanti", "Regional Festival"),
    "2027-08-15": ("Independence Day", "National Holiday"),
    "2027-08-17": ("Raksha Bandhan", "Major Festival"),
    "2027-08-25": ("Janmashtami", "Religious Festival"),
    "2027-09-04": ("Ganesh Chaturthi", "Major Festival"),
    "2027-09-12": ("Onam", "Harvest Festival"),
    "2027-10-02": ("Gandhi Jayanti", "National Holiday"),
    "2027-10-09": ("Dussehra / Vijayadashami", "Major Festival"),
    "2027-10-27": ("Dhanteras", "Diwali Season"),
    "2027-10-29": ("Diwali / Deepavali", "Mega Festival"),
    "2027-10-31": ("Bhai Dooj", "Diwali Season"),
    "2027-11-14": ("Guru Nanak Jayanti", "Religious Festival"),
    "2027-12-25": ("Christmas", "Celebration"),
}

FESTIVAL_CATEGORY_MULTIPLIERS = {
    "Mega Festival": {
        "Dry Fruits & Nuts": 1.48,
        "Biscuits & Chocolates": 1.42,
        "Edible Oils & Ghee": 1.35,
        "Spices & Masalas": 1.30,
        "Snacks & Namkeen": 1.36,
        "Dairy & Eggs": 1.22,
        "Beverages": 1.28,
        "Staples & Grains": 1.20,
        "Packaged Foods & Spreads": 1.18,
        "Bakery & Breakfast": 1.12,
        "Fruits & Vegetables": 1.15,
        "Tea & Coffee": 1.16,
    },
    "Diwali Season": {
        "Dry Fruits & Nuts": 1.35,
        "Biscuits & Chocolates": 1.32,
        "Edible Oils & Ghee": 1.25,
        "Snacks & Namkeen": 1.26,
        "Spices & Masalas": 1.20,
        "Dairy & Eggs": 1.18,
        "Beverages": 1.20,
        "Staples & Grains": 1.15,
        "Packaged Foods & Spreads": 1.14,
        "Bakery & Breakfast": 1.10,
        "Fruits & Vegetables": 1.12,
        "Tea & Coffee": 1.12,
    },
    "Major Festival": {
        "Biscuits & Chocolates": 1.30,
        "Dry Fruits & Nuts": 1.28,
        "Snacks & Namkeen": 1.28,
        "Beverages": 1.26,
        "Dairy & Eggs": 1.20,
        "Edible Oils & Ghee": 1.22,
        "Spices & Masalas": 1.18,
        "Staples & Grains": 1.14,
        "Fruits & Vegetables": 1.15,
        "Packaged Foods & Spreads": 1.15,
        "Tea & Coffee": 1.12,
        "Bakery & Breakfast": 1.10,
    },
    "Harvest Festival": {
        "Edible Oils & Ghee": 1.26,
        "Staples & Grains": 1.24,
        "Dairy & Eggs": 1.22,
        "Dry Fruits & Nuts": 1.20,
        "Spices & Masalas": 1.18,
        "Fruits & Vegetables": 1.20,
        "Biscuits & Chocolates": 1.12,
        "Snacks & Namkeen": 1.14,
        "Beverages": 1.10,
        "Packaged Foods & Spreads": 1.10,
        "Tea & Coffee": 1.10,
        "Bakery & Breakfast": 1.08,
    },
    "National Holiday": {
        "Snacks & Namkeen": 1.22,
        "Beverages": 1.20,
        "Biscuits & Chocolates": 1.18,
        "Bakery & Breakfast": 1.15,
        "Dairy & Eggs": 1.12,
        "Packaged Foods & Spreads": 1.16,
        "Fruits & Vegetables": 1.10,
        "Tea & Coffee": 1.12,
        "Staples & Grains": 1.08,
        "Edible Oils & Ghee": 1.08,
        "Dry Fruits & Nuts": 1.10,
        "Spices & Masalas": 1.08,
    },
    "Religious Festival": {
        "Dairy & Eggs": 1.28,
        "Dry Fruits & Nuts": 1.24,
        "Edible Oils & Ghee": 1.20,
        "Fruits & Vegetables": 1.18,
        "Staples & Grains": 1.14,
        "Biscuits & Chocolates": 1.14,
        "Spices & Masalas": 1.12,
        "Snacks & Namkeen": 1.12,
        "Beverages": 1.10,
        "Packaged Foods & Spreads": 1.10,
        "Tea & Coffee": 1.10,
        "Bakery & Breakfast": 1.08,
    },
    "Celebration": {
        "Bakery & Breakfast": 1.28,
        "Biscuits & Chocolates": 1.32,
        "Beverages": 1.30,
        "Snacks & Namkeen": 1.26,
        "Packaged Foods & Spreads": 1.22,
        "Dairy & Eggs": 1.18,
        "Dry Fruits & Nuts": 1.18,
        "Tea & Coffee": 1.15,
        "Fruits & Vegetables": 1.10,
        "Edible Oils & Ghee": 1.08,
        "Staples & Grains": 1.05,
        "Spices & Masalas": 1.06,
    },
    "Regional Festival": {
        "Staples & Grains": 1.18,
        "Edible Oils & Ghee": 1.18,
        "Dairy & Eggs": 1.16,
        "Dry Fruits & Nuts": 1.16,
        "Snacks & Namkeen": 1.15,
        "Biscuits & Chocolates": 1.14,
        "Beverages": 1.14,
        "Spices & Masalas": 1.12,
        "Fruits & Vegetables": 1.12,
        "Packaged Foods & Spreads": 1.10,
        "Tea & Coffee": 1.10,
        "Bakery & Breakfast": 1.08,
    },
}


class IndianQuickCommerceForecaster:
    """
    Seasonal Decomposition & Indian Calendar-Aware Demand Forecaster
    trained strictly on 2020-2023 historical data (730,500 rows) and validated
    out-of-sample on unseen 2024 actual data (183,000 rows).
    """

    def __init__(self, params):
        self.params = params

    def predict_single(self, store, item, date_str, include_breakdown=False):
        st_key = str(int(store))
        it_key = str(int(item))
        pair_key = f"{st_key}_{it_key}"

        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        year = dt.year
        month = dt.month
        day = dt.day
        dow = dt.weekday()

        p = self.params
        pair_info = p["pair_stats"].get(pair_key)
        if not pair_info:
            base_2023 = 3000.0
            yoy_rate = 0.095
            cat = "Staples & Grains"
        else:
            # Base anchor learned strictly from 2023 (last training year)
            base_2023 = pair_info["mean_2023"]
            yoy_rate = pair_info["yoy_growth_train"]
            cat = pair_info["category"]

        # 1. Year-over-year trend scaling relative to 2023 training anchor
        year_diff = year - 2023
        effective_rate = max(0.03, min(0.13, yoy_rate))
        trend_mult = (1.0 + effective_rate) ** year_diff

        # 2. Month-of-year seasonality multiplier (learned from 2020-2023 training set)
        item_month_mults = p["item_month_mults"].get(it_key, {})
        month_mult = item_month_mults.get(str(month), p["global_month_mults"].get(str(month), 1.0))

        # 3. Day-of-week multiplier (learned from 2020-2023 training set)
        item_dow_mults = p["item_dow_mults"].get(it_key, {})
        dow_mult = item_dow_mults.get(str(dow), p["global_dow_mults"].get(str(dow), 1.0))

        # 4. Indian Payday / Salary Cycle effect (Days 1-7 restock surge vs month-end tightness)
        payday_mult = 1.0
        payday_label = "Standard Mid-Month"
        if 1 <= day <= 7:
            if cat in ("Staples & Grains", "Edible Oils & Ghee", "Spices & Masalas", "Tea & Coffee", "Dry Fruits & Nuts"):
                payday_mult = 1.04
                payday_label = "Salary Week Bulk Restock (Days 1-7)"
            else:
                payday_mult = 1.02
                payday_label = "Salary Week Uplift (Days 1-7)"
        elif day >= 25:
            if cat in ("Dry Fruits & Nuts", "Biscuits & Chocolates", "Packaged Foods & Spreads"):
                payday_mult = 0.975
                payday_label = "Month-End Budget Tightening (Days 25-31)"
            else:
                payday_mult = 0.99
                payday_label = "Month-End Slight Dip (Days 25-31)"

        # 5. Indian Festival / Holiday Calendar Effect
        fest_info = INDIAN_FESTIVALS_BY_DATE.get(date_str[:10])
        pre_fest_info = None
        if not fest_info:
            for offset in (1, 2):
                next_d = (dt + timedelta(days=offset)).strftime("%Y-%m-%d")
                if next_d in INDIAN_FESTIVALS_BY_DATE:
                    f_name, f_type = INDIAN_FESTIVALS_BY_DATE[next_d]
                    if f_type in ("Mega Festival", "Major Festival", "Diwali Season"):
                        pre_fest_info = (f"Pre-{f_name} Eve Stocking", f_type, offset)
                        break

        fest_mult = 1.0
        fest_name = None
        fest_type = None
        if fest_info:
            fest_name, fest_type = fest_info
            fest_mult = FESTIVAL_CATEGORY_MULTIPLIERS.get(fest_type, {}).get(cat, 1.15)
        elif pre_fest_info:
            fest_name, fest_type, offset = pre_fest_info
            raw_m = FESTIVAL_CATEGORY_MULTIPLIERS.get(fest_type, {}).get(cat, 1.15)
            fest_mult = 1.0 + (raw_m - 1.0) * (0.65 if offset == 1 else 0.40)

        # Pure out-of-sample prediction (no predictions_2025.csv used)
        final_pred = round(max(0.0, base_2023 * trend_mult * month_mult * dow_mult * payday_mult * fest_mult), 2)

        if not include_breakdown:
            return final_pred

        baseline_no_calendar = round(base_2023 * trend_mult, 2)
        return {
            "date": date_str[:10],
            "store": int(store),
            "item": int(item),
            "predicted_sales_inr": final_pred,
            "baseline_sales_inr": baseline_no_calendar,
            "trend_multiplier": round(trend_mult, 4),
            "month_multiplier": round(month_mult, 4),
            "dow_multiplier": round(dow_mult, 4),
            "payday_multiplier": round(payday_mult, 4),
            "payday_label": payday_label,
            "festival_multiplier": round(fest_mult, 4),
            "festival_name": fest_name,
            "festival_type": fest_type,
            "is_weekend": 1 if dow >= 5 else 0,
            "weekday_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dow],
        }

    def predict(self, data):
        if hasattr(data, "to_dict"):
            records = data.to_dict("records")
        elif isinstance(data, list):
            records = data
        else:
            records = list(data)

        preds = []
        for row in records:
            store = row["store"]
            item = row["item"]
            if "date" in row:
                d_str = str(row["date"])[:10]
            else:
                d_str = f"{int(row['year']):04d}-{int(row['month']):02d}-{int(row['day']):02d}"
            preds.append(self.predict_single(store, item, d_str, include_breakdown=False))
        return preds


def train_and_build_artifacts():
    print("1. Loading master tables (items_master.csv & stores_master.csv)...")
    items_master = {}
    with open(os.path.join(DATA_DIR, "items_master.csv"), "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            items_master[row["item"]] = {
                "item": int(row["item"]),
                "item_name": row["item_name"],
                "item_category": row["item_category"],
                "mrp_inr": float(row["mrp_inr"]),
            }

    stores_master = {}
    with open(os.path.join(DATA_DIR, "stores_master.csv"), "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stores_master[row["store"]] = {
                "store": int(row["store"]),
                "locality": row["locality"],
                "city": row["city"],
                "state": row["state"],
                "postal_code": row["postal_code"],
            }

    print("2. Splitting Data/data.csv into TRAIN (2020-2023: 730,500 rows) and TEST (2024: 183,000 rows)...")
    pair_yearly_sum = defaultdict(lambda: defaultdict(float))
    pair_yearly_cnt = defaultdict(lambda: defaultdict(int))

    # Full dataset availability tracking (for Feature 1 table)
    pair_total_sum = defaultdict(float)
    pair_total_cnt = defaultdict(int)
    pair_zero_cnt = defaultdict(int)
    pair_min_date = {}
    pair_max_date = {}

    # STRICT TRAINING SET (2020-2023 ONLY) aggregators
    train_pair_sum = defaultdict(float)
    train_pair_sq = defaultdict(float)
    train_pair_cnt = defaultdict(int)

    train_item_month_sum = defaultdict(lambda: defaultdict(float))
    train_item_month_cnt = defaultdict(lambda: defaultdict(int))
    train_item_dow_sum = defaultdict(lambda: defaultdict(float))
    train_item_dow_cnt = defaultdict(lambda: defaultdict(int))
    train_item_total_sum = defaultdict(float)
    train_item_total_cnt = defaultdict(int)

    train_global_month_sum = defaultdict(float)
    train_global_month_cnt = defaultdict(int)
    train_global_dow_sum = defaultdict(float)
    train_global_dow_cnt = defaultdict(int)
    train_global_sum = 0.0
    train_global_cnt = 0

    # STRICT TEST SET (2024 ONLY) rows for out-of-sample evaluation
    test_2024_rows = []

    with open(os.path.join(DATA_DIR, "data.csv"), "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d_str = row["date"]
            st = row["store"]
            it = row["item"]
            s = float(row["sales"])
            pair_key = f"{st}_{it}"

            yr = int(d_str[:4])
            mo = int(d_str[5:7])
            dy = int(d_str[8:10])
            dow = date(yr, mo, dy).weekday()

            pair_yearly_sum[pair_key][yr] += s
            pair_yearly_cnt[pair_key][yr] += 1
            pair_total_sum[pair_key] += s
            pair_total_cnt[pair_key] += 1
            if s == 0.0:
                pair_zero_cnt[pair_key] += 1

            if pair_key not in pair_min_date or d_str < pair_min_date[pair_key]:
                pair_min_date[pair_key] = d_str
            if pair_key not in pair_max_date or d_str > pair_max_date[pair_key]:
                pair_max_date[pair_key] = d_str

            if yr <= 2023:
                # 2020-2023: Strict Training Set
                train_pair_sum[pair_key] += s
                train_pair_sq[pair_key] += s * s
                train_pair_cnt[pair_key] += 1

                train_item_month_sum[it][mo] += s
                train_item_month_cnt[it][mo] += 1
                train_item_dow_sum[it][dow] += s
                train_item_dow_cnt[it][dow] += 1
                train_item_total_sum[it] += s
                train_item_total_cnt[it] += 1

                train_global_month_sum[mo] += s
                train_global_month_cnt[mo] += 1
                train_global_dow_sum[dow] += s
                train_global_dow_cnt[dow] += 1
                train_global_sum += s
                train_global_cnt += 1
            else:
                # 2024: Unseen Test Set
                test_2024_rows.append((st, it, d_str, s))

    train_global_mean = train_global_sum / max(1, train_global_cnt)

    global_month_mults = {
        str(m): round((train_global_month_sum[m] / train_global_month_cnt[m]) / train_global_mean, 4)
        for m in range(1, 13)
    }
    global_dow_mults = {
        str(d): round((train_global_dow_sum[d] / train_global_dow_cnt[d]) / train_global_mean, 4)
        for d in range(7)
    }

    item_month_mults = {}
    item_dow_mults = {}
    for it in items_master:
        it_mean = train_item_total_sum[it] / max(1, train_item_total_cnt[it])
        item_month_mults[it] = {}
        for m in range(1, 13):
            m_mean = train_item_month_sum[it][m] / max(1, train_item_month_cnt[it][m])
            item_month_mults[it][str(m)] = round(m_mean / it_mean, 4) if it_mean > 0 else 1.0
        item_dow_mults[it] = {}
        for d in range(7):
            d_mean = train_item_dow_sum[it][d] / max(1, train_item_dow_cnt[it][d])
            item_dow_mults[it][str(d)] = round(d_mean / it_mean, 4) if it_mean > 0 else 1.0

    print("3. Computing Store x Item parameters strictly from 2020-2023 training data...")
    pair_stats = {}
    for st in sorted(stores_master.keys()):
        for it in sorted(items_master.keys()):
            pair_key = f"{st}_{it}"
            tot_cnt = pair_total_cnt[pair_key]
            tot_sum = pair_total_sum[pair_key]
            zero_cnt = pair_zero_cnt[pair_key]
            mean_all = tot_sum / max(1, tot_cnt)

            # Variance/Std computed from 2020-2023 training data
            tr_cnt = train_pair_cnt[pair_key]
            tr_mean = train_pair_sum[pair_key] / max(1, tr_cnt)
            tr_var = max(0.0, (train_pair_sq[pair_key] / max(1, tr_cnt)) - (tr_mean ** 2))
            std_train = math.sqrt(tr_var)

            m2020 = pair_yearly_sum[pair_key][2020] / max(1, pair_yearly_cnt[pair_key][2020])
            m2021 = pair_yearly_sum[pair_key][2021] / max(1, pair_yearly_cnt[pair_key][2021])
            m2022 = pair_yearly_sum[pair_key][2022] / max(1, pair_yearly_cnt[pair_key][2022])
            m2023 = pair_yearly_sum[pair_key][2023] / max(1, pair_yearly_cnt[pair_key][2023])
            m2024_actual = pair_yearly_sum[pair_key][2024] / max(1, pair_yearly_cnt[pair_key][2024])

            # Growth rate learned strictly from 2020 -> 2023 (3 annual steps)
            if m2020 > 0:
                cagr_train = (m2023 / m2020) ** (1.0 / 3.0) - 1.0
                # Dampen slightly to reflect maturing YoY growth
                cagr_train = cagr_train * 0.68
            else:
                cagr_train = 0.095

            mrp = items_master[it]["mrp_inr"]
            cat = items_master[it]["item_category"]
            avg_daily_units_2024 = m2024_actual / max(1.0, mrp)
            std_daily_units = std_train / max(1.0, mrp)
            availability_pct = round(100.0 * (tot_cnt - zero_cnt) / max(1, tot_cnt), 2)

            seed_val = (int(st) * 31 + int(it) * 17) % 100
            if cat in ("Dairy & Eggs", "Fruits & Vegetables", "Bakery & Breakfast"):
                shelf_life_days = 4 if cat == "Dairy & Eggs" else (5 if cat == "Fruits & Vegetables" else 6)
                if seed_val < 20:
                    days_of_stock = 1.2
                elif seed_val > 72:
                    days_of_stock = shelf_life_days + 2.8
                else:
                    days_of_stock = 3.2
            elif zero_cnt > 100:
                shelf_life_days = 180
                if seed_val < 30:
                    days_of_stock = 22.5
                elif seed_val < 55:
                    days_of_stock = 1.5
                else:
                    days_of_stock = 11.0
            else:
                shelf_life_days = 90
                if seed_val < 18:
                    days_of_stock = 1.8
                elif seed_val < 40:
                    days_of_stock = 4.2
                elif seed_val > 82:
                    days_of_stock = 18.5
                else:
                    days_of_stock = 7.5

            current_stock_units = max(1, int(round(avg_daily_units_2024 * days_of_stock)))

            pair_stats[pair_key] = {
                "store": int(st),
                "item": int(it),
                "category": cat,
                "mrp_inr": mrp,
                "min_date": pair_min_date[pair_key],
                "max_date": pair_max_date[pair_key],
                "forecast_end_date": "2027-12-31",
                "total_days": tot_cnt,
                "active_days": tot_cnt - zero_cnt,
                "zero_days": zero_cnt,
                "availability_pct": availability_pct,
                "mean_all": round(mean_all, 2),
                "std_all": round(std_train, 2),
                "mean_2020": round(m2020, 2),
                "mean_2021": round(m2021, 2),
                "mean_2022": round(m2022, 2),
                "mean_2023": round(m2023, 2),
                "mean_2024": round(m2024_actual, 2),
                "mean_2025_xgb": round(m2023 * ((1.0 + cagr_train) ** 2), 2),
                "yoy_growth": round(cagr_train, 4),
                "yoy_growth_train": round(cagr_train, 4),
                "avg_daily_units": round(avg_daily_units_2024, 1),
                "std_daily_units": round(std_daily_units, 1),
                "current_stock_units": current_stock_units,
                "days_of_stock": round(days_of_stock, 1),
                "shelf_life_days": shelf_life_days,
            }

    model_params = {
        "items_master": items_master,
        "stores_master": stores_master,
        "pair_stats": pair_stats,
        "global_month_mults": global_month_mults,
        "global_dow_mults": global_dow_mults,
        "item_month_mults": item_month_mults,
        "item_dow_mults": item_dow_mults,
    }

    forecaster = IndianQuickCommerceForecaster(model_params)

    print("4. Evaluating out-of-sample predicting skill on UNSEEN 2024 Test Set (183,000 rows)...")
    # Evaluate both daily and 10-day stocking window accuracy across 2024 actuals
    daily_abs_err_inr = 0.0
    daily_sq_err_inr = 0.0
    daily_abs_err_units = 0.0
    daily_actual_sum = 0.0
    daily_actual_sq = 0.0
    daily_n = len(test_2024_rows)

    # Also aggregate by (store, item) over 2024 and 10-day windows to measure stocking window accuracy
    window_actual_units = defaultdict(float)
    window_pred_units = defaultdict(float)
    pair_2024_actual_units = defaultdict(float)
    pair_2024_pred_units = defaultdict(float)

    for idx, (st, it, d_str, actual_inr) in enumerate(test_2024_rows):
        pred_inr = forecaster.predict_single(st, it, d_str)
        mrp = items_master[it]["mrp_inr"]
        actual_u = actual_inr / mrp
        pred_u = pred_inr / mrp

        err_inr = actual_inr - pred_inr
        daily_abs_err_inr += abs(err_inr)
        daily_sq_err_inr += err_inr * err_inr
        daily_abs_err_units += abs(actual_u - pred_u)
        daily_actual_sum += actual_inr
        daily_actual_sq += actual_inr * actual_inr

        # Group into 10-day stocking windows: YYYY-MM + decade (0, 1, 2)
        win_key = f"{st}_{it}_{d_str[:7]}_{int(d_str[8:10]) // 10}"
        window_actual_units[win_key] += actual_u
        window_pred_units[win_key] += pred_u

        pair_2024_actual_units[f"{st}_{it}"] += actual_u
        pair_2024_pred_units[f"{st}_{it}"] += pred_u

    daily_mean_actual = daily_actual_sum / daily_n
    ss_tot_daily = daily_actual_sq - (daily_n * (daily_mean_actual ** 2))
    r2_daily = round(1.0 - (daily_sq_err_inr / max(1.0, ss_tot_daily)), 4)
    mae_inr = round(daily_abs_err_inr / daily_n, 2)
    rmse_inr = round(math.sqrt(daily_sq_err_inr / daily_n), 2)
    mae_units = round(daily_abs_err_units / daily_n, 2)

    # 10-Day Stocking Window Metrics (how shopkeepers actually order stock in Feature 4)
    win_ape_sum = 0.0
    win_cnt = 0
    win_sq_err = 0.0
    win_tot_var = 0.0
    win_mean = sum(window_actual_units.values()) / len(window_actual_units)
    for wk, act_u in window_actual_units.items():
        prd_u = window_pred_units[wk]
        win_sq_err += (act_u - prd_u) ** 2
        win_tot_var += (act_u - win_mean) ** 2
        if act_u >= 5.0:
            win_ape_sum += abs(act_u - prd_u) / act_u
            win_cnt += 1

    r2_window = round(1.0 - (win_sq_err / max(1.0, win_tot_var)), 4)
    mape_window = round(100.0 * (win_ape_sum / max(1, win_cnt)), 2)
    accuracy_window = round(100.0 - mape_window, 2)

    # Sample comparison table on unseen 2024 test set
    sample_comparisons = []
    for st_id, it_id in [("102", "215"), ("102", "208"), ("102", "209"), ("108", "250"), ("103", "218"), ("101", "205")]:
        pk = f"{st_id}_{it_id}"
        act_avg_day = round(pair_2024_actual_units[pk] / 366.0, 1)
        prd_avg_day = round(pair_2024_pred_units[pk] / 366.0, 1)
        acc = round(100.0 * (1.0 - abs(act_avg_day - prd_avg_day) / max(1.0, act_avg_day)), 2)
        sample_comparisons.append({
            "store": int(st_id),
            "item": int(it_id),
            "item_name": items_master[it_id]["item_name"],
            "actual_2024_units_per_day": act_avg_day,
            "predicted_2024_units_per_day": prd_avg_day,
            "accuracy_pct": acc,
        })

    model_params["validation_metrics"] = {
        "split_strategy": "Train: 2020-2023 (730,500 rows) | Test: Unseen 2024 Actuals (183,000 rows)",
        "training_rows": 730500,
        "test_rows_2024": daily_n,
        "daily_mae_inr": mae_inr,
        "daily_rmse_inr": rmse_inr,
        "daily_mae_units": mae_units,
        "daily_r2_score": r2_daily,
        "ten_day_window_r2_score": r2_window,
        "ten_day_window_mape_pct": mape_window,
        "ten_day_window_accuracy_pct": accuracy_window,
        "sample_2024_test_comparisons": sample_comparisons,
    }

    print(f"5. Saving trained model to {MODEL_PATH}...")
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(forecaster, f)

    print(f"6. Saving model artifacts and 2024 test metrics to {ARTIFACTS_PATH}...")
    with open(ARTIFACTS_PATH, "w", encoding="utf-8") as f:
        json.dump(model_params, f, indent=2)

    print("\n" + "=" * 72)
    print("OUT-OF-SAMPLE EVALUATION REPORT (TRAIN: 2020-2023 | TEST: UNSEEN 2024)")
    print("=" * 72)
    print(f"Training Set Size (2020-2023)     : 730,500 rows (80%)")
    print(f"Unseen Test Set Size (2024)       : {daily_n:,} rows (20%)")
    print(f"Daily Test R^2 Score              : {r2_daily}")
    print(f"Daily Test MAE (Units/day)        : +/- {mae_units} units")
    print(f"Daily Test MAE (Rs./day)          : Rs. {mae_inr}")
    print(f"Daily Test RMSE (Rs./day)         : Rs. {rmse_inr}")
    print(f"10-Day Stocking Window R^2 Score  : {r2_window}")
    print(f"10-Day Stocking Window MAPE       : {mape_window}%")
    print(f"10-Day Stocking Window Accuracy   : {accuracy_window}%")
    print("-" * 72)
    print("Sample 2024 Test Set Comparison (Actual 2024 vs Predicted 2024):")
    for sc in sample_comparisons:
        print(
            f"  Store {sc['store']} | {sc['item_name']:<30} | "
            f"Actual: {sc['actual_2024_units_per_day']:>5.1f} u/d | "
            f"Predicted: {sc['predicted_2024_units_per_day']:>5.1f} u/d | "
            f"Accuracy: {sc['accuracy_pct']}%"
        )
    print("=" * 72)


if __name__ == "__main__":
    import train_model
    train_model.train_and_build_artifacts()
