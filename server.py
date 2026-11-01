from datetime import datetime, date, timedelta
import csv
import json
import math
import os
import pickle
from flask import Flask, request, render_template
from flask.json import jsonify

# Ensure compatibility with train_model.py pickle class definition
from train_model import (
    IndianQuickCommerceForecaster,
    INDIAN_FESTIVALS_BY_DATE,
    FESTIVAL_CATEGORY_MULTIPLIERS,
    train_and_build_artifacts,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
MODEL_PATH = os.path.join(BASE_DIR, "xgb_reg.joblib")
ARTIFACTS_PATH = os.path.join(DATA_DIR, "model_artifacts.json")
UNMET_QUERIES_PATH = os.path.join(DATA_DIR, "unmet_queries.json")

# Auto-build artifacts if missing
if not os.path.exists(MODEL_PATH) or not os.path.exists(ARTIFACTS_PATH):
    train_and_build_artifacts()

with open(ARTIFACTS_PATH, "r", encoding="utf-8") as f:
    ARTIFACTS = json.load(f)

import sys
setattr(sys.modules["__main__"], "IndianQuickCommerceForecaster", IndianQuickCommerceForecaster)

try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
except Exception:
    model = IndianQuickCommerceForecaster(ARTIFACTS)


def load_unmet_queries():
    if not os.path.exists(UNMET_QUERIES_PATH):
        return []
    with open(UNMET_QUERIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_unmet_queries(queries):
    with open(UNMET_QUERIES_PATH, "w", encoding="utf-8") as f:
        json.dump(queries, f, indent=2)


def weekend_or_weekday(year, month, day):
    d = datetime(year, month, day)
    return 1 if d.weekday() > 4 else 0


def which_day(year, month, day):
    return datetime(year, month, day).weekday()


def get_dates_between(start_str, end_str, date_format="%Y-%m-%d"):
    start_date = datetime.strptime(start_str, date_format).date()
    end_date = datetime.strptime(end_str, date_format).date()
    if end_date < start_date:
        start_date, end_date = end_date, start_date
    # Cap range to 366 days per request to keep response snappy
    if (end_date - start_date).days > 366:
        end_date = start_date + timedelta(days=366)

    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime(date_format))
        current_date += timedelta(days=1)
    return dates


app = Flask(__name__, template_folder="templates", static_folder="static")


# =====================================================================
# MAIN DASHBOARD & ORIGINAL /predict API
# =====================================================================

@app.route("/")
def index():
    # If requested by an API client expecting plain text and not HTML, still render dashboard for browser
    accept = request.headers.get("Accept", "")
    if "text/html" in accept or "*/*" in accept or not accept:
        return render_template("index.html")
    return (
        "Hello, You just reached Kush Chaudhary's server hosting the greatest inventory system of all time\n"
        "Please reach out to /predict url to get data for 2025+\n"
    )


@app.route("/ping")
def ping():
    return (
        "Hello, You just reached Kush Chaudhary's server hosting the greatest inventory system of all time\n"
        "Please reach out to /predict url to get data for 2025\n"
    )


@app.route("/predict", methods=["POST"])
def predict():
    if not request.is_json:
        return jsonify({"Empty-Error": "Please input json format data in this link"}), 400

    input_data = request.get_json()

    expected_fields = {
        "store": (int, float),
        "item": (int, float),
        "start_date": (str,),
        "end_date": (str,),
    }

    missing_fields = []
    invalid_format_fields = []

    for field, expected_types in expected_fields.items():
        if field not in input_data:
            missing_fields.append(field)
        elif not isinstance(input_data[field], expected_types):
            invalid_format_fields.append(
                {
                    "Field": field,
                    "Received-Type": type(input_data[field]).__name__,
                }
            )

    if missing_fields:
        return jsonify({"Field-Empty": f"Missing required fields: {missing_fields}"}), 400

    if invalid_format_fields:
        return jsonify(
            {
                "Invalid-Data-Error": "Invalid data format detected",
                "Details": invalid_format_fields,
            }
        ), 400

    try:
        start_date = input_data.get("start_date")
        end_date = input_data.get("end_date")
        store_id = int(input_data.get("store"))
        item_id = int(input_data.get("item"))

        dates = get_dates_between(start_date, end_date)
        score_dict = {}
        for d_str in dates:
            score_dict[d_str] = model.predict_single(store_id, item_id, d_str, include_breakdown=False)

        # If caller passes {"raw_dict": true}, return object directly; otherwise preserve original json.dumps format
        if input_data.get("raw_dict"):
            return jsonify(score_dict)
        return jsonify(json.dumps(score_dict))

    except Exception as e:
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500


# =====================================================================
# METADATA & OVERVIEW API
# =====================================================================

@app.route("/api/metadata", methods=["GET"])
def api_metadata():
    stores = sorted(ARTIFACTS["stores_master"].values(), key=lambda x: x["store"])
    items = sorted(ARTIFACTS["items_master"].values(), key=lambda x: x["item"])
    categories = sorted(list({it["item_category"] for it in items}))
    unmet = load_unmet_queries()
    triggered_alerts = [q for q in unmet if q["query_count"] > q.get("threshold", 100)]

    return jsonify(
        {
            "stores": stores,
            "items": items,
            "categories": categories,
            "validation_metrics": ARTIFACTS.get("validation_metrics", {}),
            "unmet_alerts_count": len(triggered_alerts),
        }
    )


# =====================================================================
# FEATURE 1: DATA AVAILABILITY TABLE API
# =====================================================================

@app.route("/api/availability", methods=["GET"])
def api_availability():
    store_filter = request.args.get("store", "all")
    category_filter = request.args.get("category", "all")
    status_filter = request.args.get("status", "all")
    search_q = request.args.get("search", "").strip().lower()

    stores_master = ARTIFACTS["stores_master"]
    items_master = ARTIFACTS["items_master"]
    pair_stats = ARTIFACTS["pair_stats"]

    rows = []
    # Also compute Store x Category availability heatmap matrix
    heatmap = {}
    for st_id, st_info in stores_master.items():
        heatmap[st_id] = {
            "store": st_info["store"],
            "city": st_info["city"],
            "locality": st_info["locality"],
            "categories": {},
        }

    cat_sums = {}
    for pair_key, st_data in pair_stats.items():
        st_str = str(st_data["store"])
        it_str = str(st_data["item"])
        st_info = stores_master[st_str]
        it_info = items_master[it_str]
        cat = it_info["item_category"]

        hm_key = (st_str, cat)
        cat_sums.setdefault(hm_key, []).append(st_data["availability_pct"])

        # Determine stock health status
        doi = st_data["days_of_stock"]
        shelf = st_data["shelf_life_days"]
        avail = st_data["availability_pct"]

        if doi <= 2.0:
            stock_status = "CRITICAL_LOW"
            stock_label = "Critical Low Stock"
        elif doi > shelf or doi >= 16.0:
            stock_status = "OVERSTOCK"
            stock_label = "Overstocked (Discount Candidate)"
        elif avail < 95.0:
            stock_status = "HISTORICAL_GAPS"
            stock_label = "Frequent Stockout History"
        else:
            stock_status = "HEALTHY"
            stock_label = "Healthy Availability"

        if store_filter != "all" and st_str != str(store_filter):
            continue
        if category_filter != "all" and cat.lower() != category_filter.lower():
            continue
        if status_filter != "all" and stock_status != status_filter:
            continue
        if search_q:
            haystack = f"{it_info['item_name']} {cat} {st_info['city']} {st_info['locality']} {it_str}".lower()
            if search_q not in haystack:
                continue

        rows.append(
            {
                "store": st_data["store"],
                "store_name": f"{st_info['city']} - {st_info['locality']}",
                "city": st_info["city"],
                "state": st_info["state"],
                "item": st_data["item"],
                "item_name": it_info["item_name"],
                "category": cat,
                "mrp_inr": it_info["mrp_inr"],
                "min_date": st_data["min_date"],
                "max_date": st_data["max_date"],
                "forecast_end_date": st_data["forecast_end_date"],
                "total_days": st_data["total_days"],
                "active_days": st_data["active_days"],
                "zero_days": st_data["zero_days"],
                "availability_pct": avail,
                "mean_2024_inr": st_data["mean_2024"],
                "mean_2025_xgb_inr": st_data["mean_2025_xgb"],
                "avg_daily_units": st_data["avg_daily_units"],
                "std_daily_units": st_data["std_daily_units"],
                "yoy_growth_pct": round(st_data["yoy_growth"] * 100.0, 2),
                "current_stock_units": st_data["current_stock_units"],
                "days_of_stock": doi,
                "shelf_life_days": shelf,
                "stock_status": stock_status,
                "stock_label": stock_label,
            }
        )

    for (st_str, cat), vals in cat_sums.items():
        heatmap[st_str]["categories"][cat] = round(sum(vals) / len(vals), 2)

    # Sort rows by availability_pct ascending so gaps/critical items stand out, or by store/item
    sort_by = request.args.get("sort_by", "store_item")
    if sort_by == "availability_asc":
        rows.sort(key=lambda r: (r["availability_pct"], r["store"], r["item"]))
    elif sort_by == "stock_asc":
        rows.sort(key=lambda r: (r["days_of_stock"], r["store"], r["item"]))
    elif sort_by == "sales_desc":
        rows.sort(key=lambda r: -r["mean_2024_inr"])
    else:
        rows.sort(key=lambda r: (r["store"], r["item"]))

    total_matches = len(rows)
    avg_avail = round(sum(r["availability_pct"] for r in rows) / max(1, total_matches), 2)
    critical_count = sum(1 for r in rows if r["stock_status"] == "CRITICAL_LOW")
    overstock_count = sum(1 for r in rows if r["stock_status"] == "OVERSTOCK")
    zero_days_sum = sum(r["zero_days"] for r in rows)

    return jsonify(
        {
            "summary": {
                "total_records": total_matches,
                "avg_availability_pct": avg_avail,
                "critical_low_stock_count": critical_count,
                "overstock_count": overstock_count,
                "total_zero_sales_days": zero_days_sum,
                "historical_span": "2020-01-01 to 2024-12-31 (1,827 days/item)",
                "forecast_span": "2025-01-01 to 2027-12-31 (1,095 days/item)",
            },
            "heatmap": list(heatmap.values()),
            "rows": rows[:250],  # Return up to 250 rows for fast DOM rendering
        }
    )


# =====================================================================
# FEATURE 2: CALENDAR EFFECT ENGINE API
# =====================================================================

@app.route("/api/calendar-effect", methods=["POST"])
def api_calendar_effect():
    data = request.get_json() or {}
    store_id = int(data.get("store", 102))
    item_id = int(data.get("item", 204))
    start_date = data.get("start_date", "2026-10-15")
    end_date = data.get("end_date", "2026-11-15")

    dates = get_dates_between(start_date, end_date)
    st_info = ARTIFACTS["stores_master"].get(str(store_id), {})
    it_info = ARTIFACTS["items_master"].get(str(item_id), {})
    mrp = float(it_info.get("mrp_inr", 100.0))
    cat = it_info.get("item_category", "Staples & Grains")

    daily_series = []
    festival_events = []
    weekend_days = 0
    payday_days = 0
    total_predicted = 0.0
    total_baseline = 0.0

    for d_str in dates:
        bd = model.predict_single(store_id, item_id, d_str, include_breakdown=True)
        # Compute what sales would be WITHOUT weekend, payday, or festival boosts (pure seasonally adjusted baseline)
        pure_base = round(bd["baseline_sales_inr"] * bd["month_multiplier"], 2)
        pred_inr = bd["predicted_sales_inr"]
        pred_units = round(pred_inr / max(1.0, mrp), 1)
        base_units = round(pure_base / max(1.0, mrp), 1)

        total_predicted += pred_inr
        total_baseline += pure_base

        if bd["is_weekend"]:
            weekend_days += 1
        if bd["payday_multiplier"] > 1.0:
            payday_days += 1

        reasons = []
        if bd["festival_name"]:
            fest_pct = round((bd["festival_multiplier"] - 1.0) * 100.0, 1)
            reasons.append(f"{bd['festival_name']} (+{fest_pct}%)")
            festival_events.append(
                {
                    "date": d_str,
                    "name": bd["festival_name"],
                    "type": bd["festival_type"],
                    "multiplier": bd["festival_multiplier"],
                    "uplift_pct": fest_pct,
                    "predicted_sales_inr": pred_inr,
                    "predicted_units": pred_units,
                }
            )
        if bd["is_weekend"]:
            dow_pct = round((bd["dow_multiplier"] - 1.0) * 100.0, 1)
            reasons.append(f"{bd['weekday_name']} Surge ({'+' if dow_pct >= 0 else ''}{dow_pct}%)")
        if bd["payday_multiplier"] != 1.0:
            pd_pct = round((bd["payday_multiplier"] - 1.0) * 100.0, 1)
            reasons.append(f"{bd['payday_label']} ({'+' if pd_pct >= 0 else ''}{pd_pct}%)")

        daily_series.append(
            {
                "date": d_str,
                "weekday": bd["weekday_name"],
                "is_weekend": bd["is_weekend"],
                "predicted_sales_inr": pred_inr,
                "baseline_sales_inr": pure_base,
                "predicted_units": pred_units,
                "baseline_units": base_units,
                "dow_multiplier": bd["dow_multiplier"],
                "month_multiplier": bd["month_multiplier"],
                "payday_multiplier": bd["payday_multiplier"],
                "festival_multiplier": bd["festival_multiplier"],
                "festival_name": bd["festival_name"],
                "reasons": reasons if reasons else ["Normal Weekday Baseline"],
            }
        )

    net_calendar_lift_inr = round(total_predicted - total_baseline, 2)
    net_calendar_lift_pct = round(100.0 * net_calendar_lift_inr / max(1.0, total_baseline), 2)

    # Also return learned Day-of-Week profile and Month-of-Year profile for this item
    item_dow = ARTIFACTS["item_dow_mults"].get(str(item_id), ARTIFACTS["global_dow_mults"])
    item_month = ARTIFACTS["item_month_mults"].get(str(item_id), ARTIFACTS["global_month_mults"])

    dow_profile = [
        {"day": name, "multiplier": item_dow.get(str(i), 1.0), "uplift_pct": round((item_dow.get(str(i), 1.0) - 1.0) * 100, 1)}
        for i, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    ]
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_profile = [
        {"month": month_names[m - 1], "multiplier": item_month.get(str(m), 1.0), "uplift_pct": round((item_month.get(str(m), 1.0) - 1.0) * 100, 1)}
        for m in range(1, 13)
    ]

    return jsonify(
        {
            "store": st_info,
            "item": it_info,
            "summary": {
                "days_analyzed": len(dates),
                "total_predicted_inr": round(total_predicted, 2),
                "total_baseline_inr": round(total_baseline, 2),
                "net_calendar_lift_inr": net_calendar_lift_inr,
                "net_calendar_lift_pct": net_calendar_lift_pct,
                "total_predicted_units": int(math.ceil(total_predicted / max(1.0, mrp))),
                "festival_days_count": len(festival_events),
                "weekend_days_count": weekend_days,
                "payday_days_count": payday_days,
                "category": cat,
            },
            "daily_series": daily_series,
            "festival_events": festival_events,
            "dow_profile": dow_profile,
            "month_profile": month_profile,
        }
    )


# =====================================================================
# FEATURE 3: HOW TO GIVE DISCOUNT (RULE-BASED TIERED DISCOUNT ENGINE)
# =====================================================================

SMART_BUNDLES = [
    {
        "bundle_id": "BND-01",
        "bundle_name": "Morning Chai-Nashta Super Saver",
        "occasion": "Daily Morning Peak (7 AM - 10 AM)",
        "items": [
            {"item": 231, "name": "Tata Tea Premium 250g", "mrp": 170.0},
            {"item": 215, "name": "Amul Taaza Toned Milk 500ml", "mrp": 31.0},
            {"item": 202, "name": "Britannia Good Day Cashew 200g", "mrp": 55.0},
        ],
        "discount_pct": 12.0,
        "rule_logic": "Anchor high-frequency daily milk & bread/tea buyers with high-margin biscuits (+34% attach rate).",
        "expected_volume_lift_pct": 28.5,
    },
    {
        "bundle_id": "BND-02",
        "bundle_name": "Weekend Match & Midnight Binge Pack",
        "occasion": "Fri-Sun Evenings & Cricket Match Nights",
        "items": [
            {"item": 218, "name": "Maggi 2-Minute Noodles 70g (Pack of 4)", "mrp": 72.0},
            {"item": 208, "name": "Coca-Cola 600ml", "mrp": 50.0},
            {"item": 226, "name": "Haldiram's Aloo Bhujia 200g", "mrp": 81.0},
            {"item": 238, "name": "Lay's Classic Salted 52g", "mrp": 25.0},
        ],
        "discount_pct": 15.0,
        "rule_logic": "Capitalizes on +45% weekend snack/beverage surge while clearing slow-moving snack packs.",
        "expected_volume_lift_pct": 42.0,
    },
    {
        "bundle_id": "BND-03",
        "bundle_name": "Shahi Festive Dry-Fruit & Halwa Box",
        "occasion": "Diwali / Raksha Bandhan / Festive Gifting",
        "items": [
            {"item": 219, "name": "Amul Ghee 500ml", "mrp": 385.0},
            {"item": 234, "name": "Almonds 250g", "mrp": 355.0},
            {"item": 227, "name": "Cashew Nuts 250g", "mrp": 355.0},
            {"item": 205, "name": "Kashmiri Saffron 1g", "mrp": 395.0},
        ],
        "discount_pct": 14.0,
        "rule_logic": "Moves high-MRP slow-turnover Saffron (3,013 zero-sales days) by bundling with fast-moving Ghee & Dry Fruits.",
        "expected_volume_lift_pct": 51.0,
    },
    {
        "bundle_id": "BND-04",
        "bundle_name": "Salary-Week Monthly Rasoi Staple Kit",
        "occasion": "Payday Week (1st - 7th of Every Month)",
        "items": [
            {"item": 214, "name": "Sona Masoori Rice 1kg", "mrp": 75.0},
            {"item": 248, "name": "Toor Dal 1kg", "mrp": 175.0},
            {"item": 243, "name": "Sunflower Oil 1L", "mrp": 195.0},
            {"item": 212, "name": "Wheat Atta 1kg", "mrp": 54.0},
            {"item": 203, "name": "Turmeric Powder 200g", "mrp": 115.0},
        ],
        "discount_pct": 10.0,
        "rule_logic": "Locks in household monthly staple wallet share during salary week (1st-7th) with cart-value threshold.",
        "expected_volume_lift_pct": 33.0,
    },
    {
        "bundle_id": "BND-05",
        "bundle_name": "Protein & Fitness Breakfast Combo",
        "occasion": "Monday-Friday Morning Metro Hub Promo",
        "items": [
            {"item": 249, "name": "Rolled Oats 1kg", "mrp": 255.0},
            {"item": 240, "name": "Peanut Butter 340g", "mrp": 270.0},
            {"item": 216, "name": "Honey 500g", "mrp": 365.0},
        ],
        "discount_pct": 12.0,
        "rule_logic": "Boosts Monday-Wednesday weekday trough sales among fitness-conscious metro shoppers.",
        "expected_volume_lift_pct": 29.0,
    },
]


@app.route("/api/discounts", methods=["GET"])
def api_discounts():
    store_id = int(request.args.get("store", 102))
    st_str = str(store_id)
    st_info = ARTIFACTS["stores_master"].get(st_str, {})
    items_master = ARTIFACTS["items_master"]
    pair_stats = ARTIFACTS["pair_stats"]

    tiered_discounts = []

    for it_str, it_info in sorted(items_master.items(), key=lambda x: int(x[0])):
        pair_key = f"{st_str}_{it_str}"
        st_data = pair_stats.get(pair_key)
        if not st_data:
            continue

        mrp = it_info["mrp_inr"]
        cat = it_info["item_category"]
        doi = st_data["days_of_stock"]
        shelf = st_data["shelf_life_days"]
        zero_days = st_data["zero_days"]
        stock_units = st_data["current_stock_units"]
        avg_units = st_data["avg_daily_units"]

        tier = None
        discount_pct = 0.0
        strategy_name = ""
        mechanic = ""
        reason = ""
        elasticity = 1.6

        # Rule 1: Perishable Overstock / Near-Expiry Clearance
        if shelf <= 7 and doi > shelf:
            excess_days = round(doi - shelf, 1)
            tier = "TIER_1_PERISHABLE_CLEARANCE"
            discount_pct = 25.0 if excess_days >= 2.0 else 20.0
            strategy_name = "Tier 1: Perishable Expiry Flash Clearance"
            mechanic = f"Flat {int(discount_pct)}% OFF Flash Deal (6 PM - 11 PM)"
            reason = f"Current stock ({stock_units} units = {doi} days cover) exceeds {shelf}-day perishable shelf life by {excess_days} days."
            elasticity = 2.2
        # Rule 2: Slow-Moving / High-MRP Dead-Stock Velocity Booster
        elif doi >= 15.0 or (zero_days > 400 and doi >= 10.0):
            tier = "TIER_2_SLOW_MOVER"
            discount_pct = 18.0 if mrp >= 350 else 15.0
            strategy_name = "Tier 2: Slow-Moving Capital Unlocker"
            mechanic = f"{int(discount_pct)}% OFF Tiered Slab or 'Buy 2 Save {int(discount_pct + 4)}%'"
            reason = f"High-MRP / slow velocity item ({doi} days inventory cover, {zero_days} historical zero-sale days). Unlocks working capital."
            elasticity = 1.85
        # Rule 3: Festive / High-Margin Category Promo
        elif cat in ("Dry Fruits & Nuts", "Biscuits & Chocolates", "Spices & Masalas", "Edible Oils & Ghee") and mrp >= 100:
            tier = "TIER_3_FESTIVE_PROMO"
            discount_pct = 10.0
            strategy_name = "Tier 3: Festive & Cart-Builder Promo"
            mechanic = "10% OFF on Orders above ₹499 (Festive / Weekend Special)"
            reason = f"High festive & weekend elasticity in {cat}; drives higher Average Order Value (AOV)."
            elasticity = 1.75
        # Rule 4: Weekday Trough / Salary-Week Traffic Driver
        elif doi >= 6.0:
            tier = "TIER_4_TRAFFIC_DRIVER"
            discount_pct = 6.0
            strategy_name = "Tier 4: Salary-Week / Mon-Wed Traffic Puller"
            mechanic = "6% Member Price / Bulk 2-Pack Saver"
            reason = f"Healthy stock cover ({doi} days); use modest 6% markdown on Mon-Wed to smooth weekday demand trough."
            elasticity = 1.5

        if tier:
            discounted_price = round(mrp * (1.0 - discount_pct / 100.0), 2)
            demand_lift_mult = 1.0 + (discount_pct / 100.0) * elasticity
            projected_daily_units = round(avg_units * demand_lift_mult, 1)
            new_doi = round(stock_units / max(0.5, projected_daily_units), 1)

            # Calculate spoilage/holding cost saved
            if tier == "TIER_1_PERISHABLE_CLEARANCE":
                at_risk_units = max(0.0, stock_units - (avg_units * shelf))
                spoilage_saved_inr = round(at_risk_units * discounted_price, 2)
            else:
                spoilage_saved_inr = round(stock_units * mrp * 0.04, 2)

            tiered_discounts.append(
                {
                    "item": it_info["item"],
                    "item_name": it_info["item_name"],
                    "category": cat,
                    "mrp_inr": mrp,
                    "discounted_price_inr": discounted_price,
                    "discount_pct": discount_pct,
                    "tier": tier,
                    "strategy_name": strategy_name,
                    "mechanic": mechanic,
                    "reason": reason,
                    "current_stock_units": stock_units,
                    "current_doi_days": doi,
                    "projected_doi_days": new_doi,
                    "baseline_daily_units": avg_units,
                    "projected_daily_units": projected_daily_units,
                    "expected_lift_pct": round((demand_lift_mult - 1.0) * 100.0, 1),
                    "estimated_value_recovered_inr": spoilage_saved_inr,
                }
            )

    # Sort so Tier 1 & Tier 2 appear first
    tier_order = {
        "TIER_1_PERISHABLE_CLEARANCE": 1,
        "TIER_2_SLOW_MOVER": 2,
        "TIER_3_FESTIVE_PROMO": 3,
        "TIER_4_TRAFFIC_DRIVER": 4,
    }
    tiered_discounts.sort(key=lambda x: (tier_order.get(x["tier"], 9), -x["discount_pct"]))

    # Enrich smart bundles with exact pricing
    bundles_enriched = []
    for b in SMART_BUNDLES:
        total_mrp = round(sum(i["mrp"] for i in b["items"]), 2)
        bundle_price = round(total_mrp * (1.0 - b["discount_pct"] / 100.0), 2)
        savings = round(total_mrp - bundle_price, 2)
        bundles_enriched.append(
            {
                **b,
                "total_mrp_inr": total_mrp,
                "bundle_price_inr": bundle_price,
                "customer_savings_inr": savings,
            }
        )

    return jsonify(
        {
            "store": st_info,
            "summary": {
                "total_recommendations": len(tiered_discounts),
                "tier1_perishable_count": sum(1 for d in tiered_discounts if d["tier"] == "TIER_1_PERISHABLE_CLEARANCE"),
                "tier2_slow_mover_count": sum(1 for d in tiered_discounts if d["tier"] == "TIER_2_SLOW_MOVER"),
                "tier3_festive_count": sum(1 for d in tiered_discounts if d["tier"] == "TIER_3_FESTIVE_PROMO"),
                "active_bundles_count": len(bundles_enriched),
                "total_value_protected_inr": round(sum(d["estimated_value_recovered_inr"] for d in tiered_discounts), 2),
            },
            "recommendations": tiered_discounts,
            "bundles": bundles_enriched,
        }
    )


@app.route("/api/simulate-discount", methods=["POST"])
def api_simulate_discount():
    data = request.get_json() or {}
    store_id = int(data.get("store", 102))
    item_id = int(data.get("item", 201))
    discount_pct = float(data.get("discount_pct", 15.0))
    duration_days = int(data.get("duration_days", 7))

    it_info = ARTIFACTS["items_master"].get(str(item_id), {})
    st_data = ARTIFACTS["pair_stats"].get(f"{store_id}_{item_id}", {})

    mrp = float(it_info.get("mrp_inr", 100.0))
    cat = it_info.get("item_category", "Staples & Grains")
    base_daily_units = float(st_data.get("avg_daily_units", 20.0))
    stock_units = int(st_data.get("current_stock_units", 100))
    shelf_life = int(st_data.get("shelf_life_days", 30))

    # Category-specific price elasticity & gross margin assumptions
    elasticity_map = {
        "Biscuits & Chocolates": 2.1,
        "Snacks & Namkeen": 2.0,
        "Beverages": 2.15,
        "Dry Fruits & Nuts": 1.95,
        "Dairy & Eggs": 1.75,
        "Fruits & Vegetables": 1.9,
        "Bakery & Breakfast": 1.85,
        "Edible Oils & Ghee": 1.65,
        "Staples & Grains": 1.55,
        "Spices & Masalas": 1.6,
        "Packaged Foods & Spreads": 1.85,
        "Tea & Coffee": 1.7,
    }
    elasticity = elasticity_map.get(cat, 1.8)
    wholesale_cost_ratio = 0.68  # 32% baseline retail gross margin
    unit_cost = round(mrp * wholesale_cost_ratio, 2)
    discounted_price = round(mrp * (1.0 - discount_pct / 100.0), 2)

    # Non-linear demand lift curve
    lift_multiplier = 1.0 + elasticity * (discount_pct / 100.0) * (1.0 - 0.006 * discount_pct)
    proj_daily_units = round(base_daily_units * lift_multiplier, 1)

    base_total_units = round(base_daily_units * duration_days, 1)
    proj_total_units = round(proj_daily_units * duration_days, 1)

    base_revenue = round(base_total_units * mrp, 2)
    proj_revenue = round(proj_total_units * discounted_price, 2)

    # Spoilage prevention if perishable
    spoilage_units_without_disc = max(0.0, stock_units - (base_daily_units * shelf_life)) if shelf_life <= 7 else 0.0
    spoilage_units_with_disc = max(0.0, stock_units - (proj_daily_units * shelf_life)) if shelf_life <= 7 else 0.0
    spoilage_saved_inr = round((spoilage_units_without_disc - spoilage_units_with_disc) * unit_cost, 2)

    base_profit = round(base_total_units * (mrp - unit_cost) - spoilage_units_without_disc * unit_cost, 2)
    proj_profit = round(proj_total_units * (discounted_price - unit_cost) - spoilage_units_with_disc * unit_cost, 2)

    verdict = "OPTIMAL_PROFIT_AND_VELOCITY"
    if discounted_price < unit_cost:
        verdict = "BELOW_COST_CLEARANCE_ONLY"
    elif proj_profit >= base_profit:
        verdict = "PROFIT_ACCRETIVE_SWEET_SPOT"
    else:
        verdict = "VOLUME_BOOSTER_MARGIN_TRADEOFF"

    return jsonify(
        {
            "item_name": it_info.get("item_name"),
            "category": cat,
            "mrp_inr": mrp,
            "unit_wholesale_cost_inr": unit_cost,
            "discounted_price_inr": discounted_price,
            "discount_pct": discount_pct,
            "duration_days": duration_days,
            "price_elasticity": elasticity,
            "baseline_units": base_total_units,
            "projected_units": proj_total_units,
            "volume_lift_pct": round((lift_multiplier - 1.0) * 100.0, 1),
            "baseline_revenue_inr": base_revenue,
            "projected_revenue_inr": proj_revenue,
            "baseline_net_profit_inr": base_profit,
            "projected_net_profit_inr": proj_profit,
            "spoilage_saved_inr": spoilage_saved_inr,
            "verdict": verdict,
        }
    )


# =====================================================================
# FEATURE 4: ITEM RECOMMENDER SYSTEM FOR A DATE RANGE
# =====================================================================

@app.route("/api/recommend-stock", methods=["POST"])
def api_recommend_stock():
    data = request.get_json() or {}
    store_id = int(data.get("store", 102))
    start_date = data.get("start_date", "2026-11-01")
    end_date = data.get("end_date", "2026-11-10")
    service_level = float(data.get("service_level", 0.95))
    category_filter = data.get("category", "all")

    # Z-score for chosen service level
    z_map = {0.90: 1.28, 0.95: 1.65, 0.99: 2.33}
    z_score = z_map.get(round(service_level, 2), 1.65)
    lead_time_days = 2.0  # Quick-commerce dark store replenishment lead time

    dates = get_dates_between(start_date, end_date)
    num_days = len(dates)
    st_str = str(store_id)
    st_info = ARTIFACTS["stores_master"].get(st_str, {})
    items_master = ARTIFACTS["items_master"]
    pair_stats = ARTIFACTS["pair_stats"]

    # Detect calendar highlights in the chosen date range
    active_festivals = []
    weekend_count = 0
    payday_count = 0
    for d_str in dates:
        dt = datetime.strptime(d_str, "%Y-%m-%d")
        if dt.weekday() >= 5:
            weekend_count += 1
        if 1 <= dt.day <= 7:
            payday_count += 1
        if d_str in INDIAN_FESTIVALS_BY_DATE:
            f_name, f_type = INDIAN_FESTIVALS_BY_DATE[d_str]
            active_festivals.append(f"{f_name} ({d_str})")

    recommendations = []
    total_order_units = 0
    total_procurement_cost = 0.0
    total_projected_revenue = 0.0
    critical_items_count = 0

    for it_str, it_info in sorted(items_master.items(), key=lambda x: int(x[0])):
        cat = it_info["item_category"]
        if category_filter != "all" and cat.lower() != category_filter.lower():
            continue

        it_id = it_info["item"]
        mrp = it_info["mrp_inr"]
        st_data = pair_stats.get(f"{st_str}_{it_str}", {})

        pred_sales_inr = 0.0
        base_sales_inr = 0.0
        for d_str in dates:
            bd = model.predict_single(store_id, it_id, d_str, include_breakdown=True)
            pred_sales_inr += bd["predicted_sales_inr"]
            base_sales_inr += bd["baseline_sales_inr"] * bd["month_multiplier"]

        pred_sales_inr = round(pred_sales_inr, 2)
        forecast_units = int(math.ceil(pred_sales_inr / max(1.0, mrp)))
        std_daily_units = float(st_data.get("std_daily_units", 5.0))

        # Safety stock scaled to dark store replenishment window & horizon
        safety_stock_units = int(math.ceil(z_score * std_daily_units * math.sqrt(lead_time_days)))
        total_required_units = forecast_units + safety_stock_units
        current_stock_units = int(st_data.get("current_stock_units", 0))
        recommended_order_units = max(0, total_required_units - current_stock_units)

        wholesale_unit_cost = round(mrp * 0.68, 2)
        est_procurement_cost = round(recommended_order_units * wholesale_unit_cost, 2)

        # Urgency classification
        daily_burn = max(0.5, forecast_units / max(1, num_days))
        days_cover = round(current_stock_units / daily_burn, 1)

        if current_stock_units < daily_burn * 2.2:
            priority = "CRITICAL_RESTOCK"
            priority_label = "Critical Restock (<48h Cover)"
            critical_items_count += 1
        elif current_stock_units < forecast_units:
            priority = "HIGH_PRIORITY"
            priority_label = "High Priority (Stock Deficit)"
        elif recommended_order_units > 0:
            priority = "SAFETY_REFILL"
            priority_label = "Safety Buffer Refill"
        else:
            priority = "SUFFICIENT"
            priority_label = "Sufficiently Stocked"

        cal_lift_pct = round(100.0 * (pred_sales_inr - base_sales_inr) / max(1.0, base_sales_inr), 1)
        driver_tags = []
        if active_festivals:
            driver_tags.append(f"Festive Surge ({len(active_festivals)} events)")
        if weekend_count > 0:
            driver_tags.append(f"{weekend_count} Weekend Days")
        if payday_count > 0 and cat in ("Staples & Grains", "Edible Oils & Ghee", "Spices & Masalas", "Tea & Coffee"):
            driver_tags.append(f"Salary Week ({payday_count}d)")
        if not driver_tags:
            driver_tags.append("Standard Seasonal Demand")

        total_order_units += recommended_order_units
        total_procurement_cost += est_procurement_cost
        total_projected_revenue += pred_sales_inr

        recommendations.append(
            {
                "item": it_id,
                "item_name": it_info["item_name"],
                "category": cat,
                "mrp_inr": mrp,
                "wholesale_cost_inr": wholesale_unit_cost,
                "forecast_revenue_inr": pred_sales_inr,
                "forecast_units": forecast_units,
                "safety_stock_units": safety_stock_units,
                "total_required_units": total_required_units,
                "current_stock_units": current_stock_units,
                "days_of_cover": days_cover,
                "recommended_order_units": recommended_order_units,
                "procurement_cost_inr": est_procurement_cost,
                "calendar_lift_pct": cal_lift_pct,
                "driver_summary": " + ".join(driver_tags),
                "priority": priority,
                "priority_label": priority_label,
            }
        )

    priority_rank = {
        "CRITICAL_RESTOCK": 1,
        "HIGH_PRIORITY": 2,
        "SAFETY_REFILL": 3,
        "SUFFICIENT": 4,
    }
    recommendations.sort(key=lambda r: (priority_rank.get(r["priority"], 9), -r["recommended_order_units"]))

    return jsonify(
        {
            "store": st_info,
            "date_range": {
                "start_date": start_date,
                "end_date": end_date,
                "num_days": num_days,
                "active_festivals": active_festivals,
                "weekend_days": weekend_count,
                "payday_days": payday_count,
            },
            "summary": {
                "total_skus_evaluated": len(recommendations),
                "skus_needing_restock": sum(1 for r in recommendations if r["recommended_order_units"] > 0),
                "critical_restock_count": critical_items_count,
                "total_recommended_order_units": total_order_units,
                "total_procurement_cost_inr": round(total_procurement_cost, 2),
                "total_projected_revenue_inr": round(total_projected_revenue, 2),
                "projected_gross_margin_inr": round(total_projected_revenue - total_procurement_cost, 2),
            },
            "recommendations": recommendations,
        }
    )


# =====================================================================
# FEATURE 5: UNMET USER QUERY TRACKER (>100 QUERIES AUTO-ALERT SYSTEM)
# =====================================================================

@app.route("/api/unmet-queries", methods=["GET"])
def api_get_unmet_queries():
    queries = load_unmet_queries()
    for q in queries:
        thresh = q.get("threshold", 100)
        if q.get("status") != "ADDED_TO_INVENTORY":
            if q["query_count"] > thresh:
                q["status"] = "ALERT_TRIGGERED"
            elif q["query_count"] >= thresh * 0.85:
                q["status"] = "APPROACHING_THRESHOLD"
            else:
                q["status"] = "TRACKING"
        # Calculate estimated monthly revenue opportunity
        # Assume ~35% daily search-to-order conversion on unmet intent
        est_monthly_units = int(round(q["query_count"] * 0.85))
        q["est_monthly_revenue_inr"] = round(est_monthly_units * float(q.get("estimated_mrp_inr", 100.0)), 2)

    queries.sort(key=lambda x: (0 if x["status"] == "ALERT_TRIGGERED" else (1 if x["status"] != "ADDED_TO_INVENTORY" else 2), -x["query_count"]))
    triggered = [q for q in queries if q["status"] == "ALERT_TRIGGERED"]

    return jsonify(
        {
            "threshold": 100,
            "total_tracked_unstocked_items": len(queries),
            "active_alerts_over_100": len(triggered),
            "total_unmet_revenue_opportunity_inr": round(sum(q["est_monthly_revenue_inr"] for q in triggered), 2),
            "queries": queries,
        }
    )


@app.route("/api/search-query", methods=["POST"])
def api_search_query():
    data = request.get_json() or {}
    raw_query = str(data.get("query", "")).strip()
    increment = int(data.get("increment", 1))
    store_id = int(data.get("store", 102))
    suggested_cat = data.get("category", "Packaged Foods & Spreads")
    estimated_mrp = float(data.get("estimated_mrp_inr", 120.0))

    if not raw_query:
        return jsonify({"error": "Please enter a product search query"}), 400

    increment = max(1, min(500, increment))
    q_lower = raw_query.lower()

    # Step 1: Check if product already exists in stocked items_master
    items_master = ARTIFACTS["items_master"]
    matched_stocked = []
    for it_str, it_info in items_master.items():
        if q_lower in it_info["item_name"].lower() or it_info["item_name"].lower() in q_lower:
            st_data = ARTIFACTS["pair_stats"].get(f"{store_id}_{it_str}", {})
            matched_stocked.append(
                {
                    **it_info,
                    "current_stock_units": st_data.get("current_stock_units", 50),
                }
            )

    if matched_stocked:
        return jsonify(
            {
                "in_inventory": True,
                "message": f"Product found in store catalog ({len(matched_stocked)} match).",
                "matched_items": matched_stocked,
            }
        )

    # Step 2: Not in inventory -> Log unmet customer query!
    queries = load_unmet_queries()
    st_info = ARTIFACTS["stores_master"].get(str(store_id), {"city": "New Delhi"})
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    found_entry = None
    for q in queries:
        if q["query_term"].lower() == q_lower or q_lower in q["query_term"].lower():
            found_entry = q
            break

    newly_crossed_100 = False
    if found_entry:
        prev_count = found_entry["query_count"]
        found_entry["query_count"] += increment
        found_entry["last_searched"] = now_str
        if prev_count <= 100 and found_entry["query_count"] > 100:
            newly_crossed_100 = True
        if found_entry.get("status") != "ADDED_TO_INVENTORY":
            found_entry["status"] = "ALERT_TRIGGERED" if found_entry["query_count"] > 100 else (
                "APPROACHING_THRESHOLD" if found_entry["query_count"] >= 85 else "TRACKING"
            )
    else:
        new_id = f"UQ-{len(queries) + 1:03d}"
        status = "ALERT_TRIGGERED" if increment > 100 else ("APPROACHING_THRESHOLD" if increment >= 85 else "TRACKING")
        if increment > 100:
            newly_crossed_100 = True
        found_entry = {
            "id": new_id,
            "query_term": raw_query,
            "suggested_category": suggested_cat,
            "estimated_mrp_inr": estimated_mrp,
            "query_count": increment,
            "threshold": 100,
            "top_store": store_id,
            "top_city": st_info.get("city", "New Delhi"),
            "trend_note": "Live customer search demand captured from Quick Commerce storefront",
            "recommended_initial_stock": max(45, int(increment * 0.8)),
            "status": status,
            "last_searched": now_str,
        }
        queries.append(found_entry)

    save_unmet_queries(queries)

    alert_triggered = found_entry["query_count"] > 100
    return jsonify(
        {
            "in_inventory": False,
            "alert_triggered": alert_triggered,
            "newly_crossed_100": newly_crossed_100,
            "entry": found_entry,
            "shopkeeper_notification": (
                f"URGENT SHOPKEEPER ALERT: '{found_entry['query_term']}' has reached {found_entry['query_count']} unmet customer queries "
                f"(exceeding the >100 query threshold)! Recommended Action: Add {found_entry['recommended_initial_stock']} units to {found_entry['top_city']} Dark Store inventory."
                if alert_triggered
                else f"Logged +{increment} unmet search(es) for '{found_entry['query_term']}' (Current count: {found_entry['query_count']}/100)."
            ),
        }
    )


@app.route("/api/add-to-inventory", methods=["POST"])
def api_add_to_inventory():
    data = request.get_json() or {}
    query_id = data.get("id")
    queries = load_unmet_queries()

    target = None
    for q in queries:
        if q["id"] == query_id:
            target = q
            break

    if not target:
        return jsonify({"error": "Unmet query ID not found"}), 404

    # Assign a new item ID in items_master
    items_master = ARTIFACTS["items_master"]
    next_item_id = max(int(k) for k in items_master.keys()) + 1
    new_item_obj = {
        "item": next_item_id,
        "item_name": target["query_term"],
        "item_category": target["suggested_category"],
        "mrp_inr": float(target["estimated_mrp_inr"]),
    }
    items_master[str(next_item_id)] = new_item_obj

    # Populate baseline stats across all stores so it appears in availability & recommender
    for st_str in ARTIFACTS["stores_master"].keys():
        pair_key = f"{st_str}_{next_item_id}"
        est_daily_units = round(max(8.0, target["query_count"] / 12.0), 1)
        est_daily_sales = round(est_daily_units * new_item_obj["mrp_inr"], 2)
        ARTIFACTS["pair_stats"][pair_key] = {
            "store": int(st_str),
            "item": next_item_id,
            "category": new_item_obj["item_category"],
            "mrp_inr": new_item_obj["mrp_inr"],
            "min_date": "2026-11-01",
            "max_date": "2026-11-01",
            "forecast_end_date": "2027-12-31",
            "total_days": 1,
            "active_days": 1,
            "zero_days": 0,
            "availability_pct": 100.0,
            "mean_all": est_daily_sales,
            "std_all": round(est_daily_sales * 0.22, 2),
            "mean_2020": est_daily_sales,
            "mean_2021": est_daily_sales,
            "mean_2022": est_daily_sales,
            "mean_2023": est_daily_sales,
            "mean_2024": est_daily_sales,
            "mean_2025_xgb": est_daily_sales,
            "yoy_growth": 0.12,
            "avg_daily_units": est_daily_units,
            "std_daily_units": round(est_daily_units * 0.22, 1),
            "current_stock_units": int(target.get("recommended_initial_stock", 60)),
            "days_of_stock": round(int(target.get("recommended_initial_stock", 60)) / est_daily_units, 1),
            "shelf_life_days": 60,
        }

    target["status"] = "ADDED_TO_INVENTORY"
    target["assigned_item_id"] = next_item_id
    save_unmet_queries(queries)

    return jsonify(
        {
            "success": True,
            "message": f"Successfully onboarded '{target['query_term']}' as SKU #{next_item_id} into store inventory with {target['recommended_initial_stock']} initial units!",
            "new_item": new_item_obj,
            "updated_query": target,
        }
    )


@app.errorhandler(405)
def method_not_allowed(error):
    return "Only POST method allowed for this endpoint\n", 405


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=3125)
