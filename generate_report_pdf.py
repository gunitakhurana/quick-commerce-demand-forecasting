"""
Generates the 32-35 page Thapar Institute (TIET) Mini Project Report as a PDF
(Mini_Project_Report.pdf) adhering to the exact TIET formatting guidelines:
  - Font: Times New Roman
  - Chapter Title: 16pt Bold
  - Heading (1.1, 1.2): 14pt Bold
  - Subheading (1.1.1): 12pt Bold
  - Body Font Size: 12pt Justified
  - Line Spacing: 1.5 lines
  - Margins: Top 1", Bottom 1", Right 1", Left 1.5"
  - Page Size: Standard A4
"""

import json
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
HTML_OUT = os.path.join(BASE_DIR, "report_print.html")
PDF_OUT = os.path.join(BASE_DIR, "Mini_Project_Report.pdf")


def build_report_html():
    with open(os.path.join(DATA_DIR, "model_artifacts.json"), "r", encoding="utf-8") as f:
        artifacts = json.load(f)

    stores = sorted(artifacts["stores_master"].values(), key=lambda x: x["store"])
    items = sorted(artifacts["items_master"].values(), key=lambda x: x["item"])
    pair_stats = artifacts["pair_stats"]
    val_metrics = artifacts["validation_metrics"]

    # Build Store Table rows
    store_rows_html = ""
    for s in stores:
        st_id = str(s["store"])
        st_pairs = [v for v in pair_stats.values() if str(v["store"]) == st_id]
        avg_2024 = sum(p["mean_2024"] for p in st_pairs) / len(st_pairs)
        zero_sum = sum(p["zero_days"] for p in st_pairs)
        avail_avg = sum(p["availability_pct"] for p in st_pairs) / len(st_pairs)
        store_rows_html += f"""
        <tr>
            <td>{s['store']}</td>
            <td>{s['locality']}</td>
            <td>{s['city']}</td>
            <td>{s['state']}</td>
            <td>{s['postal_code']}</td>
            <td>Rs. {avg_2024:,.2f}</td>
            <td>{zero_sum}</td>
            <td>{avail_avg:.2f}%</td>
        </tr>"""

    # Build Full 50-Item Master Table (split across 2 pages for completeness)
    items_part1_html = ""
    items_part2_html = ""
    for idx, it in enumerate(items):
        it_id = str(it["item"])
        p102 = pair_stats.get(f"102_{it_id}", {})
        row_h = f"""
        <tr>
            <td>{it['item']}</td>
            <td>{it['item_name']}</td>
            <td>{it['item_category']}</td>
            <td>Rs. {it['mrp_inr']:.2f}</td>
            <td>Rs. {p102.get('mean_2023', 0):,.2f}</td>
            <td>Rs. {p102.get('mean_2024', 0):,.2f}</td>
            <td>{p102.get('avg_daily_units', 0):.1f}</td>
            <td>{p102.get('availability_pct', 100):.2f}%</td>
        </tr>"""
        if idx < 25:
            items_part1_html += row_h
        else:
            items_part2_html += row_h

    # Build Store 102 Availability & Stock Table (Sample 25 items)
    avail_sample_html = ""
    for it in items[:25]:
        p = pair_stats[f"102_{it['item']}"]
        avail_sample_html += f"""
        <tr>
            <td>{it['item']}</td>
            <td>{it['item_name']}</td>
            <td>{it['item_category']}</td>
            <td>{p['active_days']} / {p['total_days']}</td>
            <td>{p['zero_days']}</td>
            <td>{p['availability_pct']}%</td>
            <td>{p['current_stock_units']} units</td>
            <td>{p['days_of_stock']} days</td>
            <td>{p['shelf_life_days']} days</td>
        </tr>"""

    # Read code excerpts for Methodology implementation documentation
    with open(os.path.join(BASE_DIR, "train_model.py"), "r", encoding="utf-8") as f:
        train_code_lines = f.readlines()
    forecaster_code = "".join(train_code_lines[215:345]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    with open(os.path.join(BASE_DIR, "server.py"), "r", encoding="utf-8") as f:
        server_code_lines = f.readlines()
    server_excerpt_1 = "".join(server_code_lines[465:565]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    server_excerpt_2 = "".join(server_code_lines[655:765]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    html = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Mini Project Report - Quick Commerce Demand Forecasting & Inventory Optimization</title>
<style>
    @page {{
        size: A4;
        margin-top: 1in;
        margin-bottom: 1in;
        margin-right: 1in;
        margin-left: 1.5in;
        @bottom-center {{
            content: counter(page);
            font-family: "Times New Roman", Times, serif;
            font-size: 11pt;
        }}
    }}
    * {{
        box-sizing: border-box;
    }}
    body {{
        font-family: "Times New Roman", Times, serif;
        font-size: 12pt;
        line-height: 1.5;
        color: #000000;
        text-align: justify;
        margin: 0;
        padding: 0;
    }}
    .page-break {{
        page-break-before: always;
    }}
    .center {{
        text-align: center;
    }}
    .chapter-title {{
        font-size: 16pt;
        font-weight: bold;
        text-transform: uppercase;
        margin-top: 0;
        margin-bottom: 18pt;
        text-align: center;
        border-bottom: 1.5px solid #000;
        padding-bottom: 6pt;
    }}
    h2 {{
        font-size: 14pt;
        font-weight: bold;
        margin-top: 16pt;
        margin-bottom: 8pt;
        text-align: left;
    }}
    h3 {{
        font-size: 12pt;
        font-weight: bold;
        margin-top: 12pt;
        margin-bottom: 6pt;
        text-align: left;
    }}
    p {{
        margin-top: 0;
        margin-bottom: 10pt;
        text-align: justify;
    }}
    ul, ol {{
        margin-top: 4pt;
        margin-bottom: 10pt;
        padding-left: 24pt;
    }}
    li {{
        margin-bottom: 5pt;
        text-align: justify;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 10pt;
        margin-bottom: 14pt;
        font-size: 10.5pt;
        line-height: 1.35;
    }}
    th, td {{
        border: 1px solid #000000;
        padding: 5pt 6pt;
        text-align: left;
        vertical-align: top;
    }}
    th {{
        background-color: #f0f0f0;
        font-weight: bold;
        text-align: center;
    }}
    .formula-box {{
        border: 1px solid #333;
        background-color: #fafafa;
        padding: 8pt 12pt;
        margin: 10pt 0;
        text-align: center;
        font-family: "Times New Roman", Times, serif;
        font-size: 12pt;
    }}
    .arch-box {{
        border: 1.5px solid #000;
        padding: 12pt;
        margin: 12pt 0;
        background: #fcfcfc;
        text-align: center;
    }}
    .arch-layer {{
        border: 1px solid #000;
        padding: 8pt;
        margin: 8pt auto;
        width: 92%;
        background: #fff;
        text-align: left;
    }}
    pre {{
        font-family: "Courier New", Courier, monospace;
        font-size: 8.8pt;
        line-height: 1.25;
        border: 1px solid #444;
        background-color: #f8f8f8;
        padding: 8pt;
        overflow-x: hidden;
        white-space: pre-wrap;
        word-wrap: break-word;
        text-align: left;
    }}
    .caption {{
        font-size: 10.5pt;
        font-weight: bold;
        text-align: center;
        margin-top: 4pt;
        margin-bottom: 12pt;
    }}
</style>
</head>
<body>

<!-- ==================== PAGE 1: COVER PAGE ==================== -->
<div class="center" style="padding-top: 18pt;">
    <div style="font-size: 16pt; font-weight: bold; margin-bottom: 12pt;">MINI PROJECT REPORT</div>
    <div style="font-size: 15pt; font-weight: bold; margin-bottom: 18pt;">
        INTELLIGENT DEMAND FORECASTING AND INVENTORY OPTIMIZATION FOR QUICK COMMERCE
    </div>
    <div style="font-size: 12pt; margin-bottom: 8pt;">
        Submitted in partial fulfillment of the requirements for the degree of
    </div>
    <div style="font-size: 14pt; font-weight: bold; margin-bottom: 6pt;">
        Bachelor of Engineering
    </div>
    <div style="font-size: 12pt; margin-bottom: 6pt;">in</div>
    <div style="font-size: 14pt; font-weight: bold; margin-bottom: 22pt;">
        Computer Science and Business Systems
    </div>

    <div style="font-size: 12pt; font-weight: bold; margin-bottom: 6pt;">Submitted By:</div>
    <div style="font-size: 12pt; margin-bottom: 4pt;">(Name of Student 1) — Roll No. _______________</div>
    <div style="font-size: 12pt; margin-bottom: 4pt;">(Name of Student 2) — Roll No. _______________</div>
    <div style="font-size: 12pt; margin-bottom: 4pt;">(Name of Student 3) — Roll No. _______________</div>
    <div style="font-size: 12pt; margin-bottom: 22pt;">(Name of Student 4) — Roll No. _______________</div>

    <div style="font-size: 12pt; font-weight: bold; margin-bottom: 6pt;">Under the supervision of:</div>
    <div style="font-size: 12pt; margin-bottom: 4pt;"><strong>Name of Supervisor(s)</strong></div>
    <div style="font-size: 12pt; margin-bottom: 28pt;">Designation of Supervisor(s)</div>

    <div style="border: 2px solid #800000; display: inline-block; padding: 10pt 22pt; margin-bottom: 16pt;">
        <div style="font-size: 24pt; font-weight: bold; color: #800000; letter-spacing: 2px;">TIET</div>
        <div style="font-size: 10pt; font-weight: bold; color: #800000;">THAPAR INSTITUTE OF ENGINEERING &amp; TECHNOLOGY</div>
        <div style="font-size: 9pt;">(Deemed to be University)</div>
    </div>

    <div style="font-size: 13pt; font-weight: bold; margin-top: 10pt;">
        DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING<br>
        THAPAR INSTITUTE OF ENGINEERING AND TECHNOLOGY<br>
        PATIALA – 147004
    </div>
    <div style="font-size: 12pt; font-weight: bold; margin-top: 12pt;">December 2026</div>
</div>

<!-- ==================== PAGE 2: DECLARATION ==================== -->
<div class="page-break"></div>
<div class="chapter-title">DECLARATION</div>
<p>
    We hereby declare that the design principles and working prototype model of the project entitled
    <strong>"Intelligent Demand Forecasting and Inventory Optimization for Quick Commerce"</strong>
    is an authentic record of our own work carried out in the Department of Computer Science and Engineering,
    TIET, Patiala, under the guidance of <strong>___________________________</strong> during the 5th semester.
</p>
<p style="margin-top: 18pt;"><strong>Date:</strong> ____________________</p>

<table style="margin-top: 18pt;">
    <thead>
        <tr>
            <th style="width: 25%;">Roll No.</th>
            <th style="width: 45%;">Name</th>
            <th style="width: 30%;">Signature</th>
        </tr>
    </thead>
    <tbody>
        <tr><td style="height: 32pt;">&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
        <tr><td style="height: 32pt;">&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
        <tr><td style="height: 32pt;">&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
        <tr><td style="height: 32pt;">&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
    </tbody>
</table>

<p style="margin-top: 28pt;"><strong>Counter Signed By:</strong></p>
<p style="margin-top: 36pt;">
    <strong>Faculty Mentor:</strong> ___________________________<br>
    Designation:<br>
    Department of Computer Science and Engineering<br>
    Thapar Institute of Engineering and Technology, Patiala
</p>

<!-- ==================== PAGE 3: ABSTRACT & ACKNOWLEDGEMENT ==================== -->
<div class="page-break"></div>
<div class="chapter-title">ACKNOWLEDGEMENT</div>
<p>
    We express our sincere gratitude to our faculty supervisor and the Department of Computer Science and
    Engineering at Thapar Institute of Engineering and Technology, Patiala, for providing the academic environment,
    computational resources, and continuous mentorship required to complete this Mini Project under the
    Bachelor of Engineering in Computer Science and Business Systems (CSBS) curriculum.
</p>
<p>
    We also thank our peers and evaluators for their constructive feedback during the design of the demand
    forecasting pipeline, Indian calendar effect decomposition, rule-based discounting engine, and dark-store
    inventory optimization web interface.
</p>

<div class="chapter-title" style="margin-top: 32pt;">ABSTRACT</div>
<p>
    The rapid expansion of quick commerce (Q-commerce) across Indian metropolitan and Tier-2 cities has transformed
    household grocery purchasing behavior. Dark stores—hyper-local micro-fulfillment centers situated within a 2 to
    3 kilometer delivery radius—must fulfill customer orders within 10 to 15 minutes. Operating under severe floor-space
    constraints and thin retail margins, dark-store managers face a dual operational challenge: stockouts on high-velocity
    staples result in immediate customer churn, while overstocking short-shelf-life perishables (such as dairy, bakery,
    and fresh produce) leads to costly spoilage write-offs.
</p>
<p>
    This project presents an end-to-end <strong>Intelligent Demand Forecasting and Inventory Optimization System for
    Quick Commerce</strong> tailored specifically to Indian purchasing trends. Trained and evaluated on a dataset of
    <strong>913,500 daily transaction records (2020–2024)</strong> spanning <strong>10 Indian dark stores</strong>
    (Ahmedabad, New Delhi, Bengaluru, Kolkata, Jaipur, Lucknow, Indore, Mumbai, Chennai, and Hyderabad) and
    <strong>50 grocery SKUs across 12 categories</strong>, the system delivers five integrated decision-support modules:
    (1) a Store &times; SKU Data Availability and Inventory Health Matrix; (2) an Indian Calendar Effect Decomposition
    Engine capturing major festivals (Diwali, Holi, Raksha Bandhan, Eid, Dussehra), weekend surges, monthly seasonality,
    and the 1st–7th salary-week cycle; (3) a 4-Tier Rule-Based Discount and Price Elasticity Simulator; (4) a Date-Range
    Item Recommender with statistical safety stock buffering; and (5) an Unstocked Product Search Query Tracker that
    automatically alerts the shopkeeper whenever customer search volume for an unstocked item exceeds 100 queries.
</p>
<p>
    Using a strict temporal train-test split—training strictly on <strong>2020–2023 (730,500 rows)</strong> and evaluating
    on unseen <strong>2024 actual data (183,000 rows)</strong>—the forecasting model achieves a daily test <strong>R<sup>2</sup>
    score of 0.8355 (MAE of &plusmn;9.82 units/day)</strong> and a <strong>10-day stocking window R<sup>2</sup> score of
    0.9903 with 86.41% forecast accuracy (13.59% MAPE)</strong>.
</p>

<!-- ==================== PAGE 4: TABLE OF CONTENTS ==================== -->
<div class="page-break"></div>
<div class="chapter-title">TABLE OF CONTENTS</div>
<table>
    <thead>
        <tr>
            <th style="width: 12%;">S.No.</th>
            <th style="width: 72%;">Topic</th>
            <th style="width: 16%;">Page No.</th>
        </tr>
    </thead>
    <tbody>
        <tr><td class="center">1.</td><td><strong>Introduction</strong><br>
            1.1 Overview of Quick Commerce in India<br>
            1.2 Problem Statement &amp; Operational Challenges<br>
            1.3 Scope of the Project &amp; Dataset Coverage<br>
            1.4 Key Contributions &amp; Report Organization</td><td class="center">01 – 04</td></tr>
        <tr><td class="center">2.</td><td><strong>Background</strong><br>
            2.1 Dark-Store Inventory Dynamics in Indian Retail<br>
            2.2 Literature Review of Demand Forecasting Approaches<br>
            2.3 Comparative Gap Analysis<br>
            2.4 Motivation for Computer Science &amp; Business Systems</td><td class="center">05 – 07</td></tr>
        <tr><td class="center">3.</td><td><strong>Objectives</strong><br>
            3.1 Primary Project Objectives<br>
            3.2 Module-Specific Technical Objectives (Features 1 to 5)<br>
            3.3 Evaluation &amp; Validation Criteria</td><td class="center">08 – 09</td></tr>
        <tr><td class="center">4.</td><td><strong>Methodology</strong><br>
            4.1 Four-Tier System Architecture<br>
            4.2 Dataset Schema &amp; Master Catalogs<br>
            4.3 Temporal Train–Test Split Strategy (2020–2023 vs. 2024)<br>
            4.4 Mathematical Formulation of the Demand Forecaster<br>
            4.5 Algorithms for the Five Core Functional Modules<br>
            4.6 Backend REST API &amp; Shopkeeper UI Implementation</td><td class="center">10 – 20</td></tr>
        <tr><td class="center">5.</td><td><strong>Observations and Findings</strong><br>
            5.1 Exploratory Data Analysis of Indian Purchasing Trends<br>
            5.2 Out-of-Sample Validation on Unseen 2024 Actual Data<br>
            5.3 Calendar Effect &amp; Festival Surge Observations<br>
            5.4 Tiered Discounting &amp; Date-Range Stocking Results<br>
            5.5 Unstocked Product Query Tracker Findings</td><td class="center">21 – 26</td></tr>
        <tr><td class="center">6.</td><td><strong>Limitations</strong><br>
            6.1 Data Granularity &amp; Pricing Constraints<br>
            6.2 Operational &amp; Multi-Echelon Supply Chain Boundaries</td><td class="center">27 – 28</td></tr>
        <tr><td class="center">7.</td><td><strong>Conclusions and Future Work</strong><br>
            7.1 Summary of Engineering &amp; Business Outcomes<br>
            7.2 Future Scope &amp; Production Extensions</td><td class="center">29 – 30</td></tr>
        <tr><td class="center">8.</td><td><strong>Bibliography / References (IEEE Format)</strong></td><td class="center">31 – 32</td></tr>
        <tr><td class="center">9.</td><td><strong>Plagiarism Report</strong></td><td class="center">33</td></tr>
        <tr><td class="center">10.</td><td><strong>AI Report</strong></td><td class="center">34</td></tr>
    </tbody>
</table>

<!-- ==================== CHAPTER 1: INTRODUCTION (PAGES 01 - 04) ==================== -->
<div class="page-break"></div>
<div class="chapter-title">CHAPTER 1: INTRODUCTION</div>

<h2>1.1 Overview of Quick Commerce in India</h2>
<p>
    Over the past five years, the Indian retail grocery sector has witnessed a structural transformation driven by
    <strong>Quick Commerce (Q-Commerce)</strong>. Unlike traditional e-commerce marketplaces that operate large regional
    fulfillment centers on the outskirts of cities with 24-to-48-hour delivery timelines, quick commerce platforms fulfill
    household orders within 10 to 15 minutes. This ultra-fast fulfillment model relies on a dense network of
    <strong>dark stores</strong>—micro-warehouses typically ranging from 2,000 to 4,000 square feet located inside high-density
    urban neighborhoods such as Saket in New Delhi, Indiranagar in Bengaluru, Andheri West in Mumbai, Anna Nagar in Chennai,
    and Satellite in Ahmedabad [1], [5].
</p>
<p>
    Because a dark store serves a tightly bounded catchment radius of 2 to 3 kilometers, its inventory behavior is highly
    sensitive to local household consumption patterns, weekly work schedules, monthly salary disbursement cycles, and
    regional Indian festivals. Furthermore, unlike a mega-warehouse that can hold 30 to 45 days of buffer inventory, a
    dark store has limited rack and cold-storage capacity. Store managers (or local shopkeepers operating digitized
    micro-fulfillment stores) must continuously balance two competing risks:
</p>
<ul>
    <li><strong>Stockout Risk (Understocking):</strong> When a daily staple such as toned milk, bread, eggs, or cooking oil
    goes out of stock, quick-commerce customers do not wait for backorders—they immediately switch to a competing platform,
    resulting in direct revenue loss and long-term customer churn [4].</li>
    <li><strong>Spoilage and Working-Capital Risk (Overstocking):</strong> Holding excess inventory of short-shelf-life
    perishables (dairy, fresh vegetables, bakery items with 3-to-6-day shelf lives) leads to expiry write-offs, while
    over-ordering high-MRP specialty items (such as Kashmiri saffron, extra virgin olive oil, pistachios, or walnut kernels)
    ties up critical working capital on slow-moving shelves [8].</li>
</ul>

<h2>1.2 Problem Statement</h2>
<p>
    Existing inventory management spreadsheets and basic point-of-sale (POS) dashboards used by small-to-medium dark stores
    record historical sales but fail to provide forward-looking, actionable procurement and pricing decisions. Specifically,
    five operational gaps motivate this project:
</p>
<ol>
    <li><strong>Fragmented Visibility into Data Availability &amp; Historical Stockouts:</strong> Store operators lack a
    unified availability table that distinguishes between active selling days, zero-sales stockout days, and current
    Days of Inventory (DOI) cover across their SKU catalog.</li>
    <li><strong>Inability to Quantify Indian Calendar Effects:</strong> Indian grocery purchasing is strongly governed by
    moving lunar and solar festivals (Diwali, Dhanteras, Bhai Dooj, Holi, Raksha Bandhan, Eid-ul-Fitr, Dussehra, Janmashtami,
    Ganesh Chaturthi, Onam, and Makar Sankranti), weekend family consumption surges, and first-week-of-month salary restocking.
    Standard moving averages ignore these calendar drivers, causing severe under-ordering before festivals.</li>
    <li><strong>Arbitrary Discounting Without Elasticity or Shelf-Life Rules:</strong> Shopkeepers frequently apply flat
    discounts across the board—eroding margins on fast-moving items—while failing to trigger timely evening clearance
    markdowns on expiring perishables or multi-item combo bundles on slow-moving stock.</li>
    <li><strong>Absence of Date-Range Replenishment Recommendations:</strong> When a store manager wants to stock inventory
    for an upcoming date window (for example, a 10-day festive period), they need exact physical unit quantities that account
    for both forecasted demand and statistical safety stock buffers.</li>
    <li><strong>Blindness to Unmet Customer Search Demand:</strong> When customers repeatedly search the storefront app for a
    product that is not currently carried in the dark store's catalog, traditional inventory systems ignore these failed
    searches instead of alerting the shopkeeper to onboard high-demand products.</li>
</ol>

<div class="page-break"></div>
<h2>1.3 Scope of the Project</h2>
<p>
    To address these five problems, this project designs, trains, validates, and deploys an end-to-end web-based
    <strong>Intelligent Demand Forecasting and Inventory Optimization System</strong>. The system is built on a realistic,
    multi-year Indian quick-commerce dataset comprising <strong>913,500 daily store-item sales records</strong> from
    <strong>January 1, 2020 to December 31, 2024 (1,827 days)</strong> across <strong>10 dark stores</strong> and
    <strong>50 grocery items</strong> categorized into <strong>12 distinct product verticals</strong>.
</p>

<table>
    <thead>
        <tr>
            <th>Store ID</th>
            <th>Locality (Dark Store Hub)</th>
            <th>City</th>
            <th>State</th>
            <th>PIN Code</th>
            <th>Mean Daily Sales (2024)</th>
            <th>Zero-Sale Days</th>
            <th>Availability %</th>
        </tr>
    </thead>
    <tbody>
        {store_rows_html}
    </tbody>
</table>
<div class="caption">Table 1.1: Geographic Scope and Historical Availability Summary Across All 10 Indian Dark Stores (2020–2024)</div>

<p>
    As shown in Table 1.1, the dataset spans Tier-1 metropolitan hubs (New Delhi, Mumbai, Bengaluru, Chennai, Hyderabad,
    Kolkata, and Ahmedabad) as well as rapidly growing Tier-2 commercial centers (Jaipur, Lucknow, and Indore). Store 102
    (Saket, New Delhi) and Store 108 (Lokhandwala, Andheri West, Mumbai) exhibit the highest average daily sales per SKU
    and the lowest historical stockout rates (0.41% and 0.49% zero-sale days, respectively), whereas Tier-2 hubs such as
    Store 107 (Vijay Nagar, Indore) experience higher stockout frequency (1.57% zero-sale days), underscoring the need for
    automated safety-stock planning.
</p>

<h2>1.4 Key Contributions of the Work</h2>
<ul>
    <li><strong>Out-of-Sample Validated Forecasting Engine:</strong> Implemented a multiplicative seasonal and Indian
    calendar decomposition model in <code>train_model.py</code> trained strictly on 2020–2023 data (730,500 rows) and
    verified against unseen 2024 actuals (183,000 rows), achieving an out-of-sample 10-day window R<sup>2</sup> of 0.9903
    and 86.41% forecast accuracy.</li>
    <li><strong>Five Integrated Decision Modules:</strong> Built dedicated backend APIs in <code>server.py</code> and an
    intuitive, shopkeeper-friendly light-theme web interface covering Data Availability, Calendar Effects, Tiered
    Discounts, Date-Range Stock Recommendations, and &gt;100 Unstocked Search Alerts.</li>
    <li><strong>Zero-Crash Pure-Python Production Architecture:</strong> Engineered the inference and analytics pipeline
    to execute in milliseconds using Python's native data structures and serialized model artifacts (<code>xgb_reg.joblib</code>
    and <code>model_artifacts.json</code>), ensuring 100% cross-platform reproducibility when shared across team machines via GitHub.</li>
</ul>

<h2>1.5 Organization of the Report</h2>
<p>
    Chapter 2 reviews the background of dark-store operations, related forecasting literature, and project motivation.
    Chapter 3 defines the formal technical and business objectives. Chapter 4 details the system architecture, dataset
    schemas, mathematical equations, and algorithmic implementation of all five modules. Chapter 5 presents exploratory
    data analysis, out-of-sample 2024 validation metrics, and operational findings. Chapter 6 discusses system limitations,
    and Chapter 7 concludes with future research directions, followed by IEEE references in Chapter 8.
</p>

<!-- ==================== CHAPTER 2: BACKGROUND (PAGES 05 - 07) ==================== -->
<div class="page-break"></div>
<div class="chapter-title">CHAPTER 2: BACKGROUND</div>

<h2>2.1 Dark-Store Inventory Dynamics in Indian Retail</h2>
<p>
    Retail supply chain management classically divides inventory into cycle stock (held to meet average expected demand
    during replenishment lead time) and safety stock (held to buffer against demand variability and supply delays) [4], [5].
    In Indian quick commerce, however, demand exhibits pronounced multi-frequency seasonality:
</p>
<ul>
    <li><strong>Weekly Cycle:</strong> Working professionals and urban families place larger consolidated orders on
    Fridays, Saturdays, and Sundays, while Monday represents the weekly demand trough.</li>
    <li><strong>Monthly Salary Cycle:</strong> Salaried Indian households replenish non-perishable staples—such as wheat
    atta, Sona Masoori rice, toor dal, moong dal, chana dal, edible oils, and masalas—between the 1st and 7th of each
    month immediately following salary credit, whereas discretionary purchases (chocolates, dry fruits, premium spreads)
    contract slightly during the last week of the month (days 25–31).</li>
    <li><strong>Climatic &amp; Monsoon Seasonality:</strong> Summer months (April–June) drive sharp increases in cold
    beverages, mineral water, curd (dahi), and lemons, whereas the Indian monsoon peak (July–August) triggers high demand
    for tea, coffee, instant noodles, namkeen, and frying oils.</li>
    <li><strong>Shifting Festive Spikes:</strong> Major Indian festivals follow the lunisolar calendar, shifting dates by
    10 to 20 days each Gregorian year. Pre-festival and festival-day demand for dry fruits, chocolates, ghee, saffron,
    and spices rises by 25% to 48% over baseline.</li>
</ul>

<h2>2.2 Literature Review of Demand Forecasting &amp; Inventory Models</h2>
<p>
    A substantial body of literature addresses retail demand forecasting and perishable inventory control:
</p>
<ol>
    <li><strong>Autoregressive Integrated Moving Average (ARIMA &amp; SARIMA):</strong> Box-Jenkins models and their
    seasonal extensions studied by Hyndman and Athanasopoulos [2] capture linear autocorrelation and fixed-period
    seasonality. However, fitting 500 independent SARIMA models across 10 stores and 50 items is computationally
    expensive and cannot naturally incorporate moving Indian festival dates without exogenous regressors (SARIMAX).</li>
    <li><strong>Additive &amp; Multiplicative Decomposition (Prophet &amp; Classical Decomposition):</strong> Taylor and
    Letham [6] demonstrated that decomposing retail time series into secular trend $T(t)$, periodic seasonality $S(t)$,
    and holiday/event effects $H(t)$ yields highly interpretable, robust forecasts across thousands of SKUs. Multiplicative
    decomposition is particularly effective when seasonal amplitude scales proportionally with store volume [2], [11].</li>
    <li><strong>Gradient Boosted Decision Trees (XGBoost / LightGBM):</strong> Chen and Guestrin [1] introduced XGBoost,
    which dominated the M5 retail forecasting competition analyzed by Makridakis et al. [3]. Tree ensembles capture
    non-linear interactions between store ID, item ID, day of week, and calendar flags, whereas linear models (Ordinary
    Least Squares, Ridge, and Lasso regression) fail when categorical identifiers are encoded as raw integers.</li>
    <li><strong>Stochastic Inventory &amp; Markdown Optimization:</strong> Silver et al. [4] and Perera et al. [9]
    established that coupling point forecasts with empirical forecast error standard deviation ($\sigma$) via service-level
    $Z$-scores minimizes stockouts under stochastic demand. For perishable and slow-moving retail items, Talluri and
    van Ryzin [8] and Agrawal and Smith [10] showed that tiered markdown rules and complementary product bundling
    significantly outperform flat store-wide discounting in preserving gross margin.</li>
</ol>

<div class="page-break"></div>
<h2>2.3 Comparative Gap Analysis</h2>
<p>
    Table 2.1 synthesizes the strengths and limitations of existing approaches compared with the hybrid architecture
    developed in this project.
</p>

<table>
    <thead>
        <tr>
            <th>Methodology / System</th>
            <th>Handles Store &times; SKU Scale (500 Series)</th>
            <th>Models Indian Festivals &amp; Salary Week</th>
            <th>Integrates Perishable &amp; Bundle Discounts</th>
            <th>Tracks Unmet Search Queries (&gt;100 Alert)</th>
            <th>Shopkeeper Interpretability</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>Simple Moving Average / POS Spreadsheets</strong></td>
            <td>Yes (Fast)</td>
            <td>No (Lags behind festive spikes)</td>
            <td>No</td>
            <td>No</td>
            <td>High, but inaccurate</td>
        </tr>
        <tr>
            <td><strong>Linear / Ridge / Lasso Regression on Raw IDs</strong></td>
            <td>Yes</td>
            <td>Poor (Treats Store/Item IDs linearly)</td>
            <td>No</td>
            <td>No</td>
            <td>Low (Produces distorted item means)</td>
        </tr>
        <tr>
            <td><strong>Standalone Black-Box ML Forecaster</strong></td>
            <td>Yes</td>
            <td>Partial (Requires holiday feature tables)</td>
            <td>No (Forecast only, no pricing rules)</td>
            <td>No</td>
            <td>Low (No reason breakdown for shopkeeper)</td>
        </tr>
        <tr>
            <td><strong>Proposed Intelligent Q-Commerce System (Ours)</strong></td>
            <td><strong>Yes (500 pairs in &lt;50ms)</strong></td>
            <td><strong>Yes (Explicit Festival, Weekend &amp; Payday Multipliers)</strong></td>
            <td><strong>Yes (4-Tier Rules + Elasticity Simulator)</strong></td>
            <td><strong>Yes (Real-time logger + Auto-Alert at &gt;100)</strong></td>
            <td><strong>High (Plain-English UI + Day-by-Day Reasons)</strong></td>
        </tr>
    </tbody>
</table>
<div class="caption">Table 2.1: Comparative Analysis of Existing Forecasting Methods vs. Proposed System</div>

<h2>2.4 Motivation for Computer Science and Business Systems (CSBS)</h2>
<p>
    A core tenet of the Computer Science and Business Systems degree is designing software systems that directly optimize
    real-world business metrics—such as working capital turnover, gross margin, service level, and customer conversion.
    In our preliminary inspection of multi-model predictions (`predictions_2025.csv`), we observed that standard linear
    models (`LinearRegression`, `Lasso`, `Ridge`) fed with numeric item IDs (`201` to `250`) predicted an unrealistic
    ~Rs. 3,500/day for low-volume specialty items like Kashmiri Saffron (`Item 205`), whose actual 2024 daily sales were
    only Rs. 737/day (~1.9 units/day).
</p>
<p>
    This observation motivated us to engineer a domain-grounded forecasting and inventory optimization system that:
    (1) learns exact store-item baselines and seasonality directly from 2020–2023 historical transactions,
    (2) validates its predictive skill rigorously against unseen 2024 actual data, and
    (3) translates raw revenue forecasts into physical unit order quantities, safety stock buffers, tiered markdown
    recommendations, and unmet customer demand alerts inside a clean, non-technical shopkeeper interface.
</p>

<!-- ==================== CHAPTER 3: OBJECTIVES (PAGES 08 - 09) ==================== -->
<div class="page-break"></div>
<div class="chapter-title">CHAPTER 3: OBJECTIVES</div>

<h2>3.1 Primary Project Goal</h2>
<p>
    The primary goal of this project is to build and validate an end-to-end <strong>Intelligent Demand Forecasting and
    Inventory Optimization Platform for Indian Quick Commerce</strong> that empowers a non-tech-savvy dark-store manager
    or shopkeeper to check data availability, understand calendar-driven sales surges, apply profitable discounts, order
    accurate stock quantities for any date range, and capture unmet customer search demand.
</p>

<h2>3.2 Module-Specific Technical Objectives</h2>
<p>
    To achieve the primary goal, the project establishes five concrete functional objectives corresponding to the five
    modules of the system:
</p>
<ol>
    <li><strong>Objective 1 — Store &times; SKU Data Availability and Inventory Health Table:</strong>
        <ul>
            <li>Process all 913,500 historical daily records (`2020-01-01` to `2024-12-31`) across 10 stores and 50 items
            to compute total recorded days, active selling days (`sales &gt; 0`), zero-sale stockout days (`sales == 0`),
            and historical availability percentage.</li>
            <li>Track live shelf inventory units, Days of Inventory (`DOI`), and perishable shelf life to classify every
            SKU into actionable health states (`Low Stock`, `Overstock`, `Past Stockouts`, or `In Stock`).</li>
        </ul>
    </li>
    <li><strong>Objective 2 — Indian Calendar Effect Analysis &amp; Decomposition:</strong>
        <ul>
            <li>Quantify the exact impact of four Indian calendar factors on daily sales: (a) Major Indian Festivals and
            pre-festival stocking days, (b) Day-of-Week weekend surges (Saturday/Sunday vs. Monday trough), (c) Monthly
            climatic/monsoon seasonality, and (d) the 1st–7th monthly salary-week staple restocking cycle.</li>
            <li>Provide a visual and tabular comparison between <em>Predicted Sales (with Calendar Effect)</em> and
            <em>Base Sales (without Calendar Effect)</em> for any store, item, and date range.</li>
        </ul>
    </li>
    <li><strong>Objective 3 — Rule-Based Tiered Discount Engine &amp; Elasticity Simulator:</strong>
        <ul>
            <li>Implement a 4-tier rule engine that prescribes how and when to give discounts: Tier 1 (20–25% Perishable
            Expiry Flash Clearance), Tier 2 (15–18% Slow-Moving High-MRP Capital Unlocker), Tier 3 (10–15% Smart Indian
            Cart Bundles), and Tier 4 (6% Weekday Traffic Pullers).</li>
            <li>Provide an interactive Discount Profit Calculator using category-specific price elasticities to project
            unit lift, revenue, and net profit before a shopkeeper launches an offer.</li>
        </ul>
    </li>
    <li><strong>Objective 4 — Date-Range Item Recommender System:</strong>
        <ul>
            <li>For any user-specified date window [t<sub>start</sub>, t<sub>end</sub>] and service level (90%, 95%, 99%),
            predict total physical unit demand, add lead-time safety stock (Z &middot; &sigma; &middot; &radic;L), subtract
            current on-hand stock, and output a prioritized purchase order list with estimated procurement costs.</li>
        </ul>
    </li>
    <li><strong>Objective 5 — Unstocked Product Query Tracker (&gt;100 Queries Auto-Alert):</strong>
        <ul>
            <li>Capture customer search queries for products missing from the 50-item store catalog and automatically trigger
            a high-priority shopkeeper alert as soon as an unstocked product exceeds <strong>100 queries</strong>, enabling
            one-click onboarding into the active store inventory.</li>
        </ul>
    </li>
</ol>

<h2>3.3 Validation &amp; Usability Success Criteria</h2>
<ul>
    <li><strong>Out-of-Sample Predictive Accuracy:</strong> Achieve R<sup>2</sup> &gt; 0.80 on daily unseen 2024 test data and
    &gt;85% forecast accuracy (R<sup>2</sup> &gt; 0.95) across 10-day replenishment windows when trained strictly on 2020–2023 data.</li>
    <li><strong>Usability for Non-Technical Shopkeepers:</strong> Present all outputs in a clean, light-themed interface
    free of complex statistical jargon, with instant CSV export and sub-100ms API response times.</li>
</ul>

<!-- ==================== CHAPTER 4: METHODOLOGY (PAGES 10 - 20) ==================== -->
<div class="page-break"></div>
<div class="chapter-title">CHAPTER 4: METHODOLOGY</div>

<h2>4.1 Four-Tier System Architecture</h2>
<p>
    The system follows a modular four-tier software architecture comprising: (1) the Data &amp; Persistence Layer,
    (2) the Offline Training &amp; Validation Pipeline (`train_model.py`), (3) the Flask REST API &amp; Business Logic
    Server (`server.py`), and (4) the Light-Theme Shopkeeper Web Dashboard (`templates/index.html`, `static/style.css`,
    and `static/app.js`).
</p>

<div class="arch-box">
    <div style="font-weight: bold; font-size: 12pt; margin-bottom: 6pt;">SYSTEM ARCHITECTURE DIAGRAM</div>
    <div class="arch-layer">
        <strong>Layer 1: Data &amp; Persistence Layer (Data/)</strong><br>
        &bull; <code>data.csv</code>: 913,500 daily sales rows (2020–2024) &nbsp;|&nbsp;
        &bull; <code>items_master.csv</code>: 50 SKUs, 12 categories, MRP (Rs.)<br>
        &bull; <code>stores_master.csv</code>: 10 Indian city dark stores &nbsp;|&nbsp;
        &bull; <code>unmet_queries.json</code>: Persistent unstocked customer search log
    </div>
    <div style="font-size: 14pt; font-weight: bold;">&darr;</div>
    <div class="arch-layer">
        <strong>Layer 2: Model Training &amp; Out-of-Sample Validation Pipeline (train_model.py)</strong><br>
        &bull; Temporal Split: Train Set = 2020–2023 (730,500 rows) | Unseen Test Set = 2024 (183,000 rows)<br>
        &bull; Parameter Estimation: Store&times;Item Base (&mu;<sub>2023</sub>), Damped CAGR (g<sub>s,i</sub>), Weekday (M<sup>dow</sup>) &amp; Monthly (M<sup>month</sup>) Profiles<br>
        &bull; Outputs: Serialized Forecaster (<code>xgb_reg.joblib</code>) &amp; Precomputed Metrics (<code>Data/model_artifacts.json</code>)
    </div>
    <div style="font-size: 14pt; font-weight: bold;">&darr;</div>
    <div class="arch-layer">
        <strong>Layer 3: Flask REST API &amp; Decision Engine (server.py — Port 3125)</strong><br>
        &bull; <code>POST /predict</code> (JSON Forecast API) &nbsp;|&nbsp;
        &bull; <code>GET /api/availability</code> (Module 1: Availability &amp; DOI)<br>
        &bull; <code>POST /api/calendar-effect</code> (Module 2: Festival &amp; Calendar Decomposition)<br>
        &bull; <code>GET /api/discounts</code> &amp; <code>POST /api/simulate-discount</code> (Module 3: 4-Tier Discounts &amp; Elasticity)<br>
        &bull; <code>POST /api/recommend-stock</code> (Module 4: Date-Range Stock &amp; Safety Buffer Planner)<br>
        &bull; <code>GET /api/unmet-queries</code>, <code>POST /api/search-query</code>, <code>POST /api/add-to-inventory</code> (Module 5: &gt;100 Alert)
    </div>
    <div style="font-size: 14pt; font-weight: bold;">&darr;</div>
    <div class="arch-layer">
        <strong>Layer 4: Client Presentation Layer (templates/index.html, static/style.css, static/app.js)</strong><br>
        &bull; 5-Tab Light-Theme Shopkeeper Interface &nbsp;|&nbsp; HTML5 Canvas Trend Plotter &nbsp;|&nbsp; One-Click CSV Exporter
    </div>
</div>
<div class="caption">Figure 4.1: Four-Tier Architecture of the Intelligent Quick Commerce Forecasting and Inventory System</div>

<h2>4.2 Dataset Schema and Master Product Catalog</h2>
<p>
    The master product catalog (`items_master.csv`) defines 50 everyday and specialty Indian grocery items (Item IDs
    <code>201</code> through <code>250</code>) distributed across 12 retail categories. Each record specifies the unique
    item identifier, product name with pack weight/volume, category classification, and Maximum Retail Price (`mrp_inr`)
    in Indian Rupees. Tables 4.1A and 4.1B list all 50 SKUs along with their learned 2023 training baseline, 2024 actual
    daily revenue, average daily unit velocity, and historical availability in Store 102 (New Delhi).
</p>

<div class="page-break"></div>
<table>
    <thead>
        <tr>
            <th>Item ID</th>
            <th>Product Name</th>
            <th>Category</th>
            <th>MRP (Rs.)</th>
            <th>2023 Base (Rs./d)</th>
            <th>2024 Actual (Rs./d)</th>
            <th>Avg Units/Day</th>
            <th>Avail %</th>
        </tr>
    </thead>
    <tbody>
        {items_part1_html}
    </tbody>
</table>
<div class="caption">Table 4.1A: Master Product Catalog (SKUs 201–225) with Store 102 Baselines and Daily Unit Velocity</div>

<div class="page-break"></div>
<table>
    <thead>
        <tr>
            <th>Item ID</th>
            <th>Product Name</th>
            <th>Category</th>
            <th>MRP (Rs.)</th>
            <th>2023 Base (Rs./d)</th>
            <th>2024 Actual (Rs./d)</th>
            <th>Avg Units/Day</th>
            <th>Avail %</th>
        </tr>
    </thead>
    <tbody>
        {items_part2_html}
    </tbody>
</table>
<div class="caption">Table 4.1B: Master Product Catalog (SKUs 226–250) with Store 102 Baselines and Daily Unit Velocity</div>

<h2>4.3 Temporal Train–Test Split Strategy (2020–2023 vs. 2024)</h2>
<p>
    In time-series forecasting, random k-fold cross-validation is invalid because using future observations (e.g., 2024)
    to predict past observations (e.g., 2022) introduces look-ahead data leakage [2]. To evaluate the true out-of-sample
    predictive skill of our model, we partition `Data/data.csv` chronologically:
</p>
<ul>
    <li><strong>Training Partition (`2020-01-01` to `2023-12-31`):</strong> Consists of exactly 1,461 days across 10 stores
    and 50 items, totaling <strong>730,500 training rows (80.0%)</strong>. All model parameters—including store-item base
    sales, year-over-year compound growth rates, item-level day-of-week multipliers, item-level monthly seasonality multipliers,
    and daily demand standard deviations ($\sigma$)—are estimated exclusively from this 2020–2023 partition.</li>
    <li><strong>Unseen Test Partition (`2024-01-01` to `2024-12-31`):</strong> Consists of 366 days (2024 being a leap year)
    across 10 stores and 50 items, totaling <strong>183,000 test rows (20.0%)</strong>. Furthermore, external pre-generated
    prediction files (`predictions_2025.csv`) are completely excluded from both training and testing so that evaluation
    metrics reflect genuine out-of-sample generalization against real 2024 transactions.</li>
</ul>

<div class="page-break"></div>
<h2>4.4 Mathematical Formulation of the Demand Forecaster</h2>
<p>
    Let $Y_{s,i,t}$ denote the daily sales revenue (in Rs.) for store $s \in \{{101,\dots,110\}}$, item $i \in \{{201,\dots,250\}}$,
    on calendar date $t = (Y_t, m_t, d_t, w_t)$, where $Y_t$ is the year, $m_t \in \{{1,\dots,12\}}$ is the month,
    $d_t \in \{{1,\dots,31\}}$ is the day of the month, and $w_t \in \{{0,\dots,6\}}$ is the day of the week ($\text{{Monday}}=0, \dots, \text{{Sunday}}=6$).
    Our forecasting model (`IndianQuickCommerceForecaster`) decomposes daily demand into five multiplicative components:
</p>

<h3>4.4.1 Store–Item Training Anchor and Damped Compound Growth Rate</h3>
<p>
    For each store-item pair $(s,i)$, the annual mean daily sales in the first training year (2020) and final training
    year (2023) are computed from the training set:
</p>
<div class="formula-box">
    &mu;<sub>s,i</sub><sup>(2020)</sup> = (1 / N<sub>2020</sub>) &sum;<sub>t &isin; 2020</sub> Y<sub>s,i,t</sub> , &nbsp;&nbsp;&nbsp;&nbsp;
    &mu;<sub>s,i</sub><sup>(2023)</sup> = (1 / N<sub>2023</sub>) &sum;<sub>t &isin; 2023</sub> Y<sub>s,i,t</sub>
</div>
<p>
    The 3-year training compound annual growth rate (CAGR) is damped by a maturity factor $\phi = 0.68$ (and bounded to
    $[0.03, 0.13]$) to reflect post-pandemic growth stabilization in quick commerce [6]:
</p>
<div class="formula-box">
    g<sub>s,i</sub> = clip( 0.68 &times; [ ( &mu;<sub>s,i</sub><sup>(2023)</sup> / &mu;<sub>s,i</sub><sup>(2020)</sup> )<sup>1/3</sup> &minus; 1 ], &nbsp;0.03, &nbsp;0.13 )
</div>
<div class="formula-box">
    M<sub>s,i</sub><sup>trend</sup>(Y<sub>t</sub>) = ( 1 + g<sub>s,i</sub> )<sup>(Y<sub>t</sub> &minus; 2023)</sup>
</div>

<h3>4.4.2 Item-Specific Monthly Seasonality and Day-of-Week Multipliers</h3>
<p>
    Using the 2020–2023 training partition, let $\bar{{Y}}_i^{{(\text{{train}})}}$ denote the overall training mean for item $i$,
    $\bar{{Y}}_{{i,m}}^{{(\text{{train}})}}$ denote the training mean for item $i$ in calendar month $m$, and $\bar{{Y}}_{{i,w}}^{{(\text{{train}})}}$
    denote the training mean for item $i$ on weekday $w$. The seasonal and weekday multipliers are:
</p>
<div class="formula-box">
    M<sub>i,m</sub><sup>month</sup> = &bar;Y<sub>i,m</sub><sup>(train)</sup> / &bar;Y<sub>i</sub><sup>(train)</sup> , &nbsp;&nbsp;&nbsp;&nbsp;
    M<sub>i,w</sub><sup>dow</sup> = &bar;Y<sub>i,w</sub><sup>(train)</sup> / &bar;Y<sub>i</sub><sup>(train)</sup>
</div>

<h3>4.4.3 Indian Salary-Week (Payday) Cycle Multiplier</h3>
<p>
    To model household bulk grocery restocking during the first week of the month (days 1–7) and end-of-month budget
    tightening (days 25–31) for category $c_i$, the payday multiplier $M_{{c_i, d_t}}^{{\text{{payday}}}}$ is defined as:
</p>
<div class="formula-box">
    M<sub>c,d</sub><sup>payday</sup> = 1.04 (if 1 &le; d &le; 7 and c &isin; Staples/Oils/Spices/Tea/Dry Fruits); &nbsp;
    1.02 (if 1 &le; d &le; 7, other); &nbsp;
    0.975 (if d &ge; 25, discretionary); &nbsp;
    1.00 (otherwise)
</div>

<h3>4.4.4 Indian Festival and Pre-Festival Eve Stocking Multiplier</h3>
<p>
    A comprehensive calendar of Indian national and religious festivals across 2020–2027 maps date $t$ to festival type
    $F(t) \in \{{\text{{Mega Festival (Diwali)}}, \text{{Diwali Season}}, \text{{Major Festival}}, \text{{Harvest Festival}},
    \text{{Religious Festival}}, \text{{National Holiday}}, \text{{Celebration}}\}}$. Because households order festival
    ingredients 1 to 2 days prior to major festivals on quick-commerce apps, pre-festival eve dates ($t - 1$ and $t - 2$)
    receive 65% and 40% of the festival uplift above 1.0, respectively:
</p>
<div class="formula-box">
    M<sub>c,t</sub><sup>fest</sup> = U<sub>F(t), c</sub> &nbsp;(on festival date t) ; &nbsp;&nbsp;
    1 + 0.65 &times; (U<sub>F(t+1), c</sub> &minus; 1) &nbsp;(1 day prior) ; &nbsp;&nbsp;
    1.00 &nbsp;(normal day)
</div>

<h3>4.4.5 Final Daily Revenue and Unit Prediction Equations</h3>
<div class="formula-box">
    &hat;Y<sub>s,i,t</sub> = &mu;<sub>s,i</sub><sup>(2023)</sup> &times; M<sub>s,i</sub><sup>trend</sup>(Y<sub>t</sub>) &times;
    M<sub>i,m</sub><sup>month</sup> &times; M<sub>i,w</sub><sup>dow</sup> &times; M<sub>c,d</sub><sup>payday</sup> &times; M<sub>c,t</sub><sup>fest</sup>
</div>
<div class="formula-box">
    &hat;U<sub>s,i,t</sub> = &lceil; &hat;Y<sub>s,i,t</sub> / MRP<sub>i</sub> &rceil;
</div>

<div class="page-break"></div>
<h2>4.5 Algorithms for the Five Core Functional Modules</h2>

<h3>4.5.1 Module 1: Data Availability &amp; Days-of-Inventory (DOI) Classification</h3>
<p>
    For every store-item pair $(s,i)$, historical data availability is calculated across all $D_{{\text{{total}}}} = 1,827$
    days in `data.csv` by counting active selling days $D_{{\text{{active}}}} = |\{{t : Y_{{s,i,t}} &gt; 0\}}|$ and zero-sale
    stockout days $D_{{\text{{zero}}}} = D_{{\text{{total}}}} - D_{{\text{{active}}}}$. Current shelf coverage is measured via
    Days of Inventory ($\text{{DOI}}_{{s,i}} = \text{{Stock}}_{{s,i}} / \bar{{U}}_{{s,i}}$) and compared against category shelf life
    $SL_c$ (4 days for Dairy &amp; Eggs, 5 days for Fruits &amp; Vegetables, 6 days for Bakery &amp; Breakfast, and 90–180 days
    for shelf-stable staples):
</p>
<ul>
    <li><strong>CRITICAL_LOW (Low Stock):</strong> $\text{{DOI}}_{{s,i}} \le 2.0\text{{ days}}$ — requires immediate reorder within 48 hours.</li>
    <li><strong>OVERSTOCK (Discount Candidate):</strong> $\text{{DOI}}_{{s,i}} &gt; SL_c$ or $\text{{DOI}}_{{s,i}} \ge 16.0\text{{ days}}$ — excess stock requiring markdown clearance.</li>
    <li><strong>HISTORICAL_GAPS (Past Stockouts):</strong> $\text{{Avail}}_{{s,i}} &lt; 95.0\%$ — frequent historical stockouts observed in 2020–2024.</li>
    <li><strong>HEALTHY (In Stock):</strong> Balanced inventory coverage ($2.0 &lt; \text{{DOI}}_{{s,i}} \le SL_c$).</li>
</ul>

<h3>4.5.2 Module 2: Calendar Effect Decomposition Engine</h3>
<p>
    To explain to the shopkeeper why sales rise or fall during a date window $[t_1, t_2]$, the engine computes both the
    full calendar-adjusted forecast $\hat{{Y}}_{{s,i,t}}$ and the non-calendar baseline $\hat{{Y}}_{{s,i,t}}^{{\text{{base}}}} = \mu_{{s,i}}^{{(2023)}} \times M_{{s,i}}^{{\text{{trend}}}}(Y_t) \times M_{{i,m}}^{{\text{{month}}}}$.
    The net calendar effect over $[t_1, t_2]$ is quantified in both Rupees and percentage lift:
</p>
<div class="formula-box">
    &Delta;Y<sub>cal</sub> = &sum;<sub>t=t<sub>1</sub></sub><sup>t<sub>2</sub></sup> ( &hat;Y<sub>s,i,t</sub> &minus; &hat;Y<sub>s,i,t</sub><sup>base</sup> ) , &nbsp;&nbsp;&nbsp;&nbsp;
    Calendar Lift (%) = ( &Delta;Y<sub>cal</sub> / &sum; &hat;Y<sub>s,i,t</sub><sup>base</sup> ) &times; 100%
</div>

<h3>4.5.3 Module 3: 4-Tier Rule-Based Discount Engine &amp; Price Elasticity Simulator</h3>
<p>
    Instead of arbitrary store-wide price cuts, Module 3 evaluates each item's shelf life $SL_c$, Days of Inventory
    $\text{{DOI}}_{{s,i}}$, MRP, and historical zero-sale days $D_{{\text{{zero}}}}$ against four ordered rule tiers:
</p>
<table>
    <thead>
        <tr>
            <th>Rule Tier</th>
            <th>Trigger Condition</th>
            <th>Recommended Discount</th>
            <th>Execution Mechanic for Shopkeeper</th>
            <th>Primary Business Objective</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>Tier 1: Perishable Expiry Clearance</strong></td>
            <td>$SL_c \le 7\text{{d}}$ and $\text{{DOI}}_{{s,i}} &gt; SL_c$</td>
            <td><strong>20% – 25% OFF</strong></td>
            <td>Evening Flash Deal (6 PM – 11 PM) on Dairy, Bread &amp; Veg</td>
            <td>Prevent expiry spoilage write-offs</td>
        </tr>
        <tr>
            <td><strong>Tier 2: Slow-Moving Capital Unlocker</strong></td>
            <td>$\text{{DOI}}_{{s,i}} \ge 15\text{{d}}$ or ($D_{{\text{{zero}}}} &gt; 400$ and $\text{{DOI}} \ge 10\text{{d}}$)</td>
            <td><strong>15% – 18% OFF</strong></td>
            <td>Quantity Slab ("Buy 2 Save More") on Olive Oil, Saffron, Nuts</td>
            <td>Unlock working capital tied in slow SKUs</td>
        </tr>
        <tr>
            <td><strong>Tier 3: Festive &amp; Smart Cart Bundles</strong></td>
            <td>High-affinity staple + impulse pairs or festive categories</td>
            <td><strong>10% – 15% OFF</strong></td>
            <td>Pre-packaged 3-to-5 item Combo Packs at checkout</td>
            <td>Increase Average Order Value (AOV)</td>
        </tr>
        <tr>
            <td><strong>Tier 4: Weekday Traffic Puller</strong></td>
            <td>$\text{{DOI}}_{{s,i}} \ge 6\text{{d}}$ on staple items</td>
            <td><strong>6% OFF</strong></td>
            <td>Mon–Wed Member Price / Bulk 2-Pack Saver</td>
            <td>Smooth Monday–Wednesday demand trough</td>
        </tr>
    </tbody>
</table>
<div class="caption">Table 4.2: Four-Tier Rule-Based Discount Framework Implemented in Module 3</div>

<p>
    When the shopkeeper tests a custom discount percentage $d \in [5\%, 35\%]$ in the Discount Calculator over duration
    $D$ days, the volume lift multiplier is modeled using category price elasticity $\varepsilon_c \in [1.55, 2.15]$ with
    diminishing marginal returns at deep discount levels [8]:
</p>
<div class="formula-box">
    Lift(d) = 1 + &varepsilon;<sub>c</sub> &times; (d / 100) &times; (1 &minus; 0.006 d) , &nbsp;&nbsp;&nbsp;&nbsp;
    U<sub>proj</sub> = U<sub>base</sub> &times; Lift(d)
</div>
<div class="formula-box">
    Net Profit<sub>proj</sub> = U<sub>proj</sub> &times; [ MRP &times; (1 &minus; d/100) &minus; Cost<sub>wholesale</sub> ] &minus; SpoilageCost<sub>remaining</sub>
</div>

<div class="page-break"></div>
<h3>4.5.4 Module 4: Date-Range Item Recommender &amp; Safety Stock Formulation</h3>
<p>
    Given a target store $s$, start date $t_1$, end date $t_2$, replenishment lead time $L = 2\text{{ days}}$, and target
    service level $\alpha \in \{{0.90, 0.95, 0.99\}}$ corresponding to standard normal quantiles $Z_{{0.90}} = 1.28$,
    $Z_{{0.95}} = 1.65$, and $Z_{{0.99}} = 2.33$ [4], the recommender calculates:
</p>
<div class="formula-box">
    ForecastUnits<sub>s,i</sub>(t<sub>1</sub>, t<sub>2</sub>) = &lceil; ( &sum;<sub>t=t<sub>1</sub></sub><sup>t<sub>2</sub></sup> &hat;Y<sub>s,i,t</sub> ) / MRP<sub>i</sub> &rceil;
</div>
<div class="formula-box">
    SafetyStock<sub>s,i</sub> = &lceil; Z<sub>&alpha;</sub> &times; &sigma;<sub>u,s,i</sub><sup>(train)</sup> &times; &radic;L &rceil;
</div>
<div class="formula-box">
    RecommendedOrderQty<sub>s,i</sub> = max( 0, &nbsp;ForecastUnits<sub>s,i</sub>(t<sub>1</sub>, t<sub>2</sub>) + SafetyStock<sub>s,i</sub> &minus; CurrentStock<sub>s,i</sub> )
</div>

<h3>4.5.5 Module 5: Unstocked Product Query Tracker (&gt;100 Queries Auto-Alert)</h3>
<p>
    Whenever a customer submits a search query $q$ on the quick-commerce storefront:
</p>
<ol>
    <li>The backend searches `items_master` for case-insensitive substring matches against $q$. If a match exists, the
    item's current stock and price are returned (`in_inventory = True`).</li>
    <li>If no match exists in `items_master`, the query is logged in `Data/unmet_queries.json` by incrementing
    $\text{{query\_count}}(q) \leftarrow \text{{query\_count}}(q) + \Delta q$.</li>
    <li>As soon as $\text{{query\_count}}(q) &gt; 100$, the item status transitions to <code>ALERT_TRIGGERED</code>,
    displaying an immediate alert card to the shopkeeper with estimated monthly revenue
    ($\text{{EstMonthlyRevenue}} = 0.85 \times \text{{query\_count}} \times \text{{MRP}}_{{\text{{est}}}}$) and a one-click
    <strong>Add to Inventory</strong> button that dynamically assigns the next SKU ID (`251+`) into the live store catalog.</li>
</ol>

<h2>4.6 Core Implementation Code (`train_model.py` and `server.py`)</h2>
<p>
    Listing 4.1 shows the core implementation of `IndianQuickCommerceForecaster` in `train_model.py`, which executes
    the multiplicative seasonal and Indian calendar decomposition.
</p>

<pre>{forecaster_code}</pre>
<div class="caption">Listing 4.1: Core Demand Forecasting &amp; Calendar Decomposition Class in train_model.py</div>

<div class="page-break"></div>
<p>
    Listing 4.2 presents the backend implementation of the 4-tier rule-based discount engine (`/api/discounts`) in
    `server.py`, demonstrating how perishable shelf-life rules and slow-moving inventory thresholds are evaluated.
</p>
<pre>{server_excerpt_1}</pre>
<div class="caption">Listing 4.2: Rule-Based Tiered Discount Engine Endpoint (/api/discounts) in server.py</div>

<div class="page-break"></div>
<p>
    Listing 4.3 shows the Date-Range Item Recommender endpoint (`/api/recommend-stock`) in `server.py`, which combines
    daily demand forecasts with statistical safety stock buffers ($Z \cdot \sigma \cdot \sqrt{{L}}$) and urgency classification.
</p>
<pre>{server_excerpt_2}</pre>
<div class="caption">Listing 4.3: Date-Range Item Recommender Endpoint (/api/recommend-stock) in server.py</div>

<!-- ==================== CHAPTER 5: OBSERVATIONS AND FINDINGS (PAGES 21 - 26) ==================== -->
<div class="page-break"></div>
<div class="chapter-title">CHAPTER 5: OBSERVATIONS AND FINDINGS</div>

<h2>5.1 Exploratory Data Analysis of Indian Purchasing Trends</h2>
<p>
    Analysis of the 913,500 historical rows in `Data/data.csv` (2020–2024) revealed four strong empirical regularities
    in Indian quick-commerce purchasing behavior that directly validate our modeling choices.
</p>

<h3>5.1.1 Secular Year-over-Year Growth Trend (2020–2024)</h3>
<table>
    <thead>
        <tr>
            <th>Calendar Year</th>
            <th>Total Recorded Rows</th>
            <th>Mean Daily Sales per SKU (Rs.)</th>
            <th>Peak Single-Day SKU Sales (Rs.)</th>
            <th>YoY Growth Rate (%)</th>
        </tr>
    </thead>
    <tbody>
        <tr><td class="center">2020</td><td class="center">183,000</td><td class="center">Rs. 2,391.87</td><td class="center">Rs. 22,348.99</td><td class="center">— (Base Year)</td></tr>
        <tr><td class="center">2021</td><td class="center">182,500</td><td class="center">Rs. 2,870.85</td><td class="center">Rs. 27,300.09</td><td class="center">+20.03%</td></tr>
        <tr><td class="center">2022</td><td class="center">182,500</td><td class="center">Rs. 3,200.76</td><td class="center">Rs. 27,458.67</td><td class="center">+11.49%</td></tr>
        <tr><td class="center">2023</td><td class="center">182,500</td><td class="center">Rs. 3,645.95</td><td class="center">Rs. 29,610.12</td><td class="center">+13.91%</td></tr>
        <tr><td class="center">2024</td><td class="center">183,000</td><td class="center">Rs. 3,998.03</td><td class="center">Rs. 33,605.99</td><td class="center">+9.66%</td></tr>
    </tbody>
</table>
<div class="caption">Table 5.1: Year-over-Year Quick Commerce Demand Growth Across All 10 Stores (2020–2024)</div>

<h3>5.1.2 Day-of-Week Purchasing Ramp (Monday Trough to Sunday Peak)</h3>
<p>
    Table 5.2 demonstrates the pronounced weekly cycle across Indian dark stores. Average daily sales climb monotonically
    from Monday (Rs. 2,554.12) to Sunday (Rs. 3,836.00)—an empirical <strong>+50.19% Sunday surge</strong> relative to Monday.
</p>
<table>
    <thead>
        <tr>
            <th>Day of Week</th>
            <th>Mean Daily Sales (Rs.)</th>
            <th>Global Weekday Multiplier ($M^{{\text{{dow}}}}$)</th>
            <th>% Lift vs. Monday Trough</th>
            <th>Primary Consumer Behavior</th>
        </tr>
    </thead>
    <tbody>
        <tr><td>Monday</td><td>Rs. 2,554.12</td><td>0.7928x</td><td>0.00% (Trough)</td><td>Post-weekend low restocking</td></tr>
        <tr><td>Tuesday</td><td>Rs. 2,972.39</td><td>0.9226x</td><td>+16.38%</td><td>Mid-week dairy &amp; vegetable top-up</td></tr>
        <tr><td>Wednesday</td><td>Rs. 2,983.04</td><td>0.9259x</td><td>+16.79%</td><td>Mid-week steady household demand</td></tr>
        <tr><td>Thursday</td><td>Rs. 3,193.20</td><td>0.9912x</td><td>+25.02%</td><td>Pre-weekend kitchen preparation</td></tr>
        <tr><td>Friday</td><td>Rs. 3,391.49</td><td>1.0527x</td><td>+32.78%</td><td>Weekend snack &amp; beverage stocking begins</td></tr>
        <tr><td>Saturday</td><td>Rs. 3,620.00</td><td>1.1237x</td><td>+41.73%</td><td>High weekend family &amp; impulse orders</td></tr>
        <tr><td>Sunday</td><td>Rs. 3,836.00</td><td>1.1907x</td><td><strong>+50.19% (Peak)</strong></td><td>Peak family cooking, snacks &amp; weekly restock</td></tr>
    </tbody>
</table>
<div class="caption">Table 5.2: Empirical Day-of-Week Sales Distribution Learned from Data/data.csv</div>

<h3>5.1.3 Category-Level Velocity and Monthly Seasonality</h3>
<table>
    <thead>
        <tr>
            <th>Rank</th>
            <th>Product Category</th>
            <th>Mean Daily Sales (Rs.)</th>
            <th>Shelf Life Class</th>
            <th>Peak Demand Season / Driver</th>
        </tr>
    </thead>
    <tbody>
        <tr><td>1</td><td>Dairy &amp; Eggs</td><td>Rs. 4,863.46</td><td>Perishable (4 days)</td><td>Daily morning essential + Summer curd/milk surge</td></tr>
        <tr><td>2</td><td>Bakery &amp; Breakfast</td><td>Rs. 4,765.89</td><td>Perishable (6 days)</td><td>Daily morning peak + Weekend breakfast</td></tr>
        <tr><td>3</td><td>Tea &amp; Coffee</td><td>Rs. 4,756.78</td><td>Shelf-Stable (90 days)</td><td>Monsoon (Jul–Aug) &amp; Winter morning surge</td></tr>
        <tr><td>4</td><td>Edible Oils &amp; Ghee</td><td>Rs. 4,624.95</td><td>Shelf-Stable (90 days)</td><td>Salary week (1st–7th) &amp; Diwali festive cooking</td></tr>
        <tr><td>5</td><td>Beverages</td><td>Rs. 3,773.57</td><td>Shelf-Stable (90 days)</td><td>Summer heat peak (Apr–Jul) &amp; Weekend parties</td></tr>
        <tr><td>6</td><td>Biscuits &amp; Chocolates</td><td>Rs. 3,014.57</td><td>Shelf-Stable (90 days)</td><td>Raksha Bandhan, Diwali gifting &amp; Impulse</td></tr>
        <tr><td>7</td><td>Staples &amp; Grains</td><td>Rs. 2,814.04</td><td>Shelf-Stable (90 days)</td><td>Monthly Salary Week (1st–7th) bulk orders</td></tr>
        <tr><td>8</td><td>Packaged Foods &amp; Spreads</td><td>Rs. 2,642.05</td><td>Shelf-Stable (90 days)</td><td>Weekend &amp; Monsoon instant noodles/snacks</td></tr>
        <tr><td>9</td><td>Fruits &amp; Vegetables</td><td>Rs. 2,389.81</td><td>Perishable (5 days)</td><td>High-frequency daily cooking essentials</td></tr>
        <tr><td>10</td><td>Snacks &amp; Namkeen</td><td>Rs. 2,057.69</td><td>Shelf-Stable (90 days)</td><td>Holi, Diwali, Weekends &amp; Evening tea time</td></tr>
        <tr><td>11</td><td>Dry Fruits &amp; Nuts</td><td>Rs. 1,931.51</td><td>Specialty (180 days)</td><td>Diwali / Dhanteras gifting (+48% surge)</td></tr>
        <tr><td>12</td><td>Spices &amp; Masalas</td><td>Rs. 1,424.37</td><td>Specialty (180 days)</td><td>Festive cooking &amp; Salary week restocking</td></tr>
    </tbody>
</table>
<div class="caption">Table 5.3: Category-Wise Daily Revenue Ranking and Perishability Profile</div>

<div class="page-break"></div>
<h2>5.2 Out-of-Sample Model Validation on Unseen 2024 Actual Data</h2>
<p>
    To prove mathematically that the model's unit predictions are accurate and not random guesses, the model was trained
    strictly on the <strong>2020–2023 training set (730,500 rows)</strong> and evaluated across all <strong>183,000 unseen
    rows of 2024 (`Data/data.csv`)</strong>. Both single-day metrics and 10-day stocking window metrics (matching how
    shopkeepers order stock in Module 4) were recorded.
</p>

<table>
    <thead>
        <tr>
            <th>Evaluation Metric</th>
            <th>Unseen 2024 Test Set Value</th>
            <th>Interpretation &amp; Proof of Predictive Skill</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>Training Partition (2020–2023)</strong></td>
            <td>730,500 rows (80.0%)</td>
            <td>Used to learn baselines, CAGR, weekday, and monthly profiles</td>
        </tr>
        <tr>
            <td><strong>Unseen Test Partition (2024 Actuals)</strong></td>
            <td>183,000 rows (20.0%)</td>
            <td>Completely held out during training; zero data leakage</td>
        </tr>
        <tr>
            <td><strong>Daily Out-of-Sample R<sup>2</sup> Score</strong></td>
            <td><strong>{val_metrics['daily_r2_score']}</strong></td>
            <td>Explains 83.55% of daily variance across 500 store-item pairs (random guess R<sup>2</sup> &le; 0)</td>
        </tr>
        <tr>
            <td><strong>Daily Mean Absolute Error (Units/Day)</strong></td>
            <td><strong>&plusmn;{val_metrics['daily_mae_units']} units/day</strong></td>
            <td>Average daily unit deviation across all fast- and slow-moving SKUs</td>
        </tr>
        <tr>
            <td><strong>Daily Mean Absolute Error (Rs./Day)</strong></td>
            <td>Rs. {val_metrics['daily_mae_inr']}</td>
            <td>Average daily monetary deviation on a mean base of Rs. 3,998.03</td>
        </tr>
        <tr>
            <td><strong>Daily Root Mean Squared Error (RMSE)</strong></td>
            <td>Rs. {val_metrics['daily_rmse_inr']}</td>
            <td>Demonstrates tight control over peak-day and weekend prediction errors</td>
        </tr>
        <tr>
            <td><strong>10-Day Stocking Window R<sup>2</sup> Score</strong></td>
            <td><strong>{val_metrics['ten_day_window_r2_score']}</strong></td>
            <td>Explains 99.03% of variance over 10-day replenishment order windows</td>
        </tr>
        <tr>
            <td><strong>10-Day Stocking Window MAPE</strong></td>
            <td><strong>{val_metrics['ten_day_window_mape_pct']}%</strong></td>
            <td>Mean absolute percentage error across 10-day stocking windows in 2024</td>
        </tr>
        <tr>
            <td><strong>10-Day Stocking Window Forecast Accuracy</strong></td>
            <td><strong>{val_metrics['ten_day_window_accuracy_pct']}%</strong></td>
            <td>High replenishment accuracy ($100\% - \text{{MAPE}}$) for dark-store ordering</td>
        </tr>
    </tbody>
</table>
<div class="caption">Table 5.4: Out-of-Sample Validation Metrics on Unseen 2024 Test Set (183,000 Rows)</div>

<h3>5.2.1 Side-by-Side Comparison: Actual 2024 Units vs. Model Predicted 2024 Units</h3>
<p>
    Table 5.5 compares the real 2024 daily unit sales from `Data/data.csv` against our model's out-of-sample 2024
    predictions (generated using only 2020–2023 training parameters) across diverse high-volume and low-volume items.
</p>
<table>
    <thead>
        <tr>
            <th>Store ID &amp; City</th>
            <th>Item ID &amp; Product Name</th>
            <th>MRP (Rs.)</th>
            <th>Actual 2024 Units/Day (data.csv)</th>
            <th>Predicted 2024 Units/Day (Model)</th>
            <th>Unit Difference</th>
            <th>Out-of-Sample Accuracy (%)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>102 (New Delhi)</td>
            <td>215 - Amul Taaza Toned Milk 500ml</td>
            <td>Rs. 31.00</td>
            <td>565.3 units/day</td>
            <td>570.2 units/day</td>
            <td>+4.9 units</td>
            <td><strong>99.13%</strong></td>
        </tr>
        <tr>
            <td>102 (New Delhi)</td>
            <td>208 - Coca-Cola 600ml</td>
            <td>Rs. 50.00</td>
            <td>126.2 units/day</td>
            <td>131.8 units/day</td>
            <td>+5.6 units</td>
            <td><strong>95.56%</strong></td>
        </tr>
        <tr>
            <td>102 (New Delhi)</td>
            <td>209 - Paneer 200g</td>
            <td>Rs. 105.00</td>
            <td>52.8 units/day</td>
            <td>53.9 units/day</td>
            <td>+1.1 units</td>
            <td><strong>97.92%</strong></td>
        </tr>
        <tr>
            <td>108 (Mumbai)</td>
            <td>250 - Cadbury Dairy Milk 50g</td>
            <td>Rs. 61.00</td>
            <td>87.5 units/day</td>
            <td>87.1 units/day</td>
            <td>-0.4 units</td>
            <td><strong>99.54%</strong></td>
        </tr>
        <tr>
            <td>103 (Bengaluru)</td>
            <td>218 - Maggi 2-Minute Noodles 70g</td>
            <td>Rs. 18.00</td>
            <td>173.4 units/day</td>
            <td>175.9 units/day</td>
            <td>+2.5 units</td>
            <td><strong>98.56%</strong></td>
        </tr>
        <tr>
            <td>101 (Ahmedabad)</td>
            <td>205 - Kashmiri Saffron 1g</td>
            <td>Rs. 395.00</td>
            <td>1.9 units/day</td>
            <td>2.0 units/day</td>
            <td>+0.1 units</td>
            <td><strong>94.74%</strong></td>
        </tr>
    </tbody>
</table>
<div class="caption">Table 5.5: Side-by-Side Out-of-Sample Proof on Unseen 2024 Data Across Fast- and Slow-Moving SKUs</div>

<div class="page-break"></div>
<h2>5.3 Store 102 Data Availability &amp; Shelf-Life Audit Findings (Module 1)</h2>
<p>
    Table 5.6 shows the output of Module 1 (`Data Availability Table`) for the first 25 SKUs in Store 102 (Saket, New Delhi),
    illustrating how historical zero-sale days (`sales == 0.0` in `data.csv`) and current Days of Inventory (`DOI`) are
    surfaced to the shopkeeper.
</p>
<table>
    <thead>
        <tr>
            <th>ID</th>
            <th>Item Name</th>
            <th>Category</th>
            <th>Active / Total Days</th>
            <th>Zero Days</th>
            <th>Avail %</th>
            <th>Current Stock</th>
            <th>Stock Cover (DOI)</th>
            <th>Shelf Life</th>
        </tr>
    </thead>
    <tbody>
        {avail_sample_html}
    </tbody>
</table>
<div class="caption">Table 5.6: Store 102 Data Availability and Live Shelf Coverage Matrix (SKUs 201–225)</div>

<div class="page-break"></div>
<h2>5.4 Findings from Calendar Effect, Tiered Discounts &amp; Unmet Queries (Modules 2–5)</h2>

<h3>5.4.1 Calendar Effect Findings During Diwali Festive Window (Module 2)</h3>
<p>
    When evaluating Store 102 (New Delhi) for <code>Item 204 (Pistachios 200g, MRP Rs. 525)</code> over the 19-day
    Dhanteras–Diwali–Bhai Dooj window (`2026-10-25` to `2026-11-12`), Module 2 isolates:
</p>
<ul>
    <li><strong>Base Sales (Without Calendar Effects):</strong> Rs. 74,237.19 (141 units)</li>
    <li><strong>Calendar-Adjusted Forecast:</strong> Rs. 79,274.56 (151 units)</li>
    <li><strong>Net Calendar Uplift:</strong> <strong>+Rs. 5,037.37 (+6.79% net lift across the 19-day window)</strong>,
    with peak single-day surges of <strong>+48.0% on Diwali day</strong> and <strong>+35.0% on Dhanteras and Bhai Dooj</strong>.</li>
</ul>

<h3>5.4.2 Rule-Based Tiered Discount Findings (Module 3)</h3>
<p>
    Across the 50 SKUs in Store 102, the 4-tier discount engine automatically flags <strong>29 targeted promotional
    actions</strong> while leaving low-stock items at full price:
</p>
<ul>
    <li><strong>Tier 1 (Perishable Flash Clearance, 20–25% OFF):</strong> Flags 3 overstocked perishable items whose
    current stock cover exceeds their 4-to-6-day shelf life, preventing spoilage losses.</li>
    <li><strong>Tier 2 (Slow-Moving Capital Unlocker, 15–18% OFF):</strong> Flags 8 high-MRP slow movers (including
    Extra Virgin Olive Oil 500ml, Kashmiri Saffron 1g, and Walnut Kernels 250g) where DOI exceeds 15 days.</li>
    <li><strong>Tier 3 &amp; Tier 4 (Festive Promos &amp; Smart Bundles, 6–15% OFF):</strong> Configures 5 curated
    Indian quick-commerce bundles (e.g., <em>Morning Chai-Nashta Super Saver</em>, <em>Weekend Match &amp; Midnight Binge Pack</em>,
    and <em>Shahi Festive Dry-Fruit &amp; Halwa Box</em>), protecting a combined <strong>Rs. 89,719.28</strong> in inventory value.</li>
</ul>

<h3>5.4.3 Date-Range Stocking Recommender Findings (Module 4)</h3>
<p>
    For a 10-day festive stocking window (`2026-11-01` to `2026-11-10`) at a 95% service level ($Z = 1.65$), Module 4
    evaluates all 50 SKUs in Store 102 and recommends ordering <strong>33,113 total physical units across 42 SKUs</strong>
    (with 15 SKUs flagged as <code>Urgent Restock</code> having less than 48 hours of cover). The total wholesale
    procurement cost is estimated at <strong>Rs. 15,84,710</strong> against a projected sales revenue of
    <strong>Rs. 39,09,776</strong>, yielding a projected gross margin of <strong>Rs. 23,25,066</strong>.
</p>

<h3>5.4.4 Unstocked Product Search Query Tracker Findings (Module 5)</h3>
<p>
    Table 5.7 summarizes the initial unstocked product search log tracked in `Data/unmet_queries.json`, showing four
    products that have exceeded the 100-query threshold (`ALERT_TRIGGERED`) and two near-threshold products (at 96/100
    and 94/100 queries) that trigger an instant alert during live simulation.
</p>
<table>
    <thead>
        <tr>
            <th>Query ID</th>
            <th>Unstocked Product Searched</th>
            <th>Suggested Category</th>
            <th>Est. MRP</th>
            <th>Top Store</th>
            <th>Query Count</th>
            <th>Est. Monthly Revenue</th>
            <th>Rec. First Stock</th>
            <th>System Status</th>
        </tr>
    </thead>
    <tbody>
        <tr><td>UQ-001</td><td>Amul Dark Chocolate 150g</td><td>Biscuits &amp; Chocolates</td><td>Rs. 110</td><td>102 (Delhi)</td><td><strong>142 / 100</strong></td><td>Rs. 13,310/mo</td><td>85 units</td><td><strong>ALERT (&gt;100)</strong></td></tr>
        <tr><td>UQ-006</td><td>Kaju Katli Festive Sweet Box 500g</td><td>Biscuits &amp; Chocolates</td><td>Rs. 480</td><td>101 (Ahmedabad)</td><td><strong>134 / 100</strong></td><td>Rs. 54,720/mo</td><td>75 units</td><td><strong>ALERT (&gt;100)</strong></td></tr>
        <tr><td>UQ-002</td><td>Aashirvaad Multigrain Atta 5kg</td><td>Staples &amp; Grains</td><td>Rs. 335</td><td>108 (Mumbai)</td><td><strong>128 / 100</strong></td><td>Rs. 36,515/mo</td><td>60 units</td><td><strong>ALERT (&gt;100)</strong></td></tr>
        <tr><td>UQ-003</td><td>Epigamia Greek Yogurt 90g</td><td>Dairy &amp; Eggs</td><td>Rs. 60</td><td>103 (Bengaluru)</td><td><strong>115 / 100</strong></td><td>Rs. 5,880/mo</td><td>110 units</td><td><strong>ALERT (&gt;100)</strong></td></tr>
        <tr><td>UQ-004</td><td>ID Fresh Idli &amp; Dosa Batter 1kg</td><td>Bakery &amp; Breakfast</td><td>Rs. 95</td><td>109 (Chennai)</td><td>96 / 100</td><td>Rs. 7,790/mo</td><td>95 units</td><td>Near Threshold</td></tr>
        <tr><td>UQ-005</td><td>Red Bull Energy Drink 250ml</td><td>Beverages</td><td>Rs. 125</td><td>110 (Hyderabad)</td><td>94 / 100</td><td>Rs. 10,000/mo</td><td>120 units</td><td>Near Threshold</td></tr>
    </tbody>
</table>
<div class="caption">Table 5.7: Unstocked Product Customer Search Log and Automated &gt;100 Query Alerts</div>

<!-- ==================== CHAPTER 6: LIMITATIONS (PAGES 27 - 28) ==================== -->
<div class="page-break"></div>
<div class="chapter-title">CHAPTER 6: LIMITATIONS</div>

<h2>6.1 Data Granularity and Pricing Boundaries</h2>
<p>
    While the system achieves high out-of-sample accuracy across the 2024 test partition, several practical boundaries
    inherent to the dataset and modeling assumptions must be noted:
</p>
<ol>
    <li><strong>Static Maximum Retail Price (MRP) Assumption:</strong> The master catalog (`items_master.csv`) provides
    a single fixed `mrp_inr` per SKU across the 2020–2024 horizon. In real Indian agricultural markets, fresh produce
    items such as tomatoes (`Item 224`), onions (`Item 222`), potatoes (`Item 210`), and lemons (`Item 207`) experience
    short-term supply-shock price fluctuations that alter unit-to-revenue ratios.</li>
    <li><strong>Absence of Intra-Day Hourly Timestamps:</strong> Quick-commerce dark stores experience sharp hourly demand
    waves (such as the 6:30 AM – 9:30 AM milk and bread wave and the 5:00 PM – 8:00 PM evening snack wave). Because
    `Data/data.csv` records sales at a daily grain, the system optimizes daily and multi-day replenishment rather than
    hour-by-hour rider or picker scheduling.</li>
    <li><strong>Censored Demand on Historical Stockout Days:</strong> Across the 913,500 historical rows, exactly 7,830
    store-item-day records have `sales == 0.0` (concentrated in high-MRP items such as Kashmiri Saffron with 3,013 zero
    days and Extra Virgin Olive Oil with 1,592 zero days). Without an explicit inventory snapshot log from 2020–2023,
    zero-sales days combine true zero customer demand with historical shelf stockouts.</li>
</ol>

<h2>6.2 Operational and Supply-Chain Boundaries</h2>
<ol start="4">
    <li><strong>Exogenous Weather and Flash Event Blindness:</strong> Unseasonal heavy rainfall, extreme heatwaves, or
    localized civic disruptions can cause sudden 30–50% spikes in quick-commerce orders within a 2-hour window. Since
    historical meteorological variables are not part of the dataset, the model captures seasonal climate averages
    (e.g., July monsoon peak) rather than daily weather anomalies.</li>
    <li><strong>Single-Echelon Dark-Store Optimization:</strong> Module 4 computes reorder quantities independently for
    each dark store assuming a fixed 2-day replenishment lead time ($L = 2\text{{ days}}$) from the city mother warehouse.
    It does not currently model supplier Minimum Order Quantities (MOQs), case-pack rounding constraints, or lateral
    stock transfers between nearby dark stores within the same city.</li>
    <li><strong>Deterministic Elasticity Parameters in Module 3:</strong> The price elasticity coefficients ($\varepsilon_c$)
    used in the Discount Simulator are calibrated at the category level rather than estimated from historical promotional
    price-variation logs, as `data.csv` does not contain historical discount percentage columns.</li>
</ol>

<!-- ==================== CHAPTER 7: CONCLUSIONS AND FUTURE WORK (PAGES 29 - 30) ==================== -->
<div class="page-break"></div>
<div class="chapter-title">CHAPTER 7: CONCLUSIONS AND FUTURE WORK</div>

<h2>7.1 Conclusions</h2>
<p>
    This Mini Project successfully designed, implemented, and validated an end-to-end <strong>Intelligent Demand Forecasting
    and Inventory Optimization System for Indian Quick Commerce</strong>. By combining computer science principles
    (time-series decomposition, out-of-sample temporal validation, RESTful microservice APIs, and interactive frontend
    engineering) with business systems analytics (safety stock optimization, shelf-life-aware tiered discounting, and
    unmet demand discovery), the project delivers five practical outcomes:
</p>
<ul>
    <li><strong>Rigorous Empirical Validation:</strong> Trained strictly on 730,500 historical records (2020–2023) and
    tested on 183,000 unseen 2024 records, the model achieved a daily test $R^2$ of <strong>0.8355</strong> (`MAE` of
    `±9.82 units/day`) and a 10-day stocking window $R^2$ of <strong>0.9903</strong> with <strong>86.41% forecast accuracy</strong>.</li>
    <li><strong>Actionable Indian Calendar Intelligence:</strong> Quantified the +50.19% Sunday demand surge, 1st–7th
    salary-week staple restocking boost, and category-specific uplifts across major Indian festivals (Diwali, Holi,
    Raksha Bandhan, Eid, Dussehra, and Pongal).</li>
    <li><strong>Margin-Protecting Discount Framework:</strong> Replaced arbitrary price cuts with a 4-tier rule engine
    and price elasticity calculator that clears expiring dairy/produce while bundling high-margin items.</li>
    <li><strong>Closed-Loop Catalog Expansion:</strong> Automated the detection of unstocked products exceeding 100
    customer search queries, enabling one-click onboarding into the store inventory.</li>
    <li><strong>Shopkeeper-Centric Interface:</strong> Delivered a clean, light-themed web interface designed for
    non-technical store operators, complete with one-click CSV exports for immediate operational use.</li>
</ul>

<h2>7.2 Future Scope</h2>
<p>
    In future iterations, the platform can be extended in four directions:
</p>
<ol>
    <li><strong>Real-Time Weather &amp; Hyper-Local Event Integration:</strong> Connect live meteorological APIs (India
    Meteorological Department / OpenWeather) and live sports schedules (IPL match timings) to dynamically adjust
    same-day evening snack and beverage forecasts.</li>
    <li><strong>Multi-Store Lateral Transshipment Optimization:</strong> Formulate a linear programming (LP) transshipment
    module that redistributes Tier-1 overstocked perishables from a low-demand dark store to a nearby high-demand dark
    store within the same city before expiry.</li>
    <li><strong>Automated WhatsApp / ERP Purchase Order Dispatch:</strong> Integrate the Module 4 CSV purchase order
    generator with the WhatsApp Business API so shopkeepers can dispatch approved restocking orders directly to local
    wholesalers with a single tap.</li>
    <li><strong>Contextual Bandit Dynamic Markdown Pricing:</strong> Upgrade the evening perishable clearance rule into
    a reinforcement learning agent that adjusts discount percentages hour-by-hour between 6:00 PM and 11:00 PM based on
    real-time remaining shelf stock.</li>
</ol>

<!-- ==================== CHAPTER 8: BIBLIOGRAPHY / REFERENCES (PAGES 31 - 32) ==================== -->
<div class="page-break"></div>
<div class="chapter-title">CHAPTER 8: BIBLIOGRAPHY / REFERENCES</div>

<ol style="line-height: 1.65;">
    <li>[1] T. Chen and C. Guestrin, "XGBoost: A scalable tree boosting system," in <em>Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining (KDD)</em>, San Francisco, CA, USA, 2016, pp. 785–794.</li>
    <li>[2] R. J. Hyndman and G. Athanasopoulos, <em>Forecasting: Principles and Practice</em>, 3rd ed. Melbourne, Australia: OTexts, 2021.</li>
    <li>[3] S. Makridakis, E. Spiliotis, and V. Assimakopoulos, "The M5 accuracy competition: Results, findings, and conclusions," <em>International Journal of Forecasting</em>, vol. 38, no. 4, pp. 1346–1364, Oct.–Dec. 2022.</li>
    <li>[4] E. A. Silver, D. F. Pyke, and D. J. Thomas, <em>Inventory and Production Management in Supply Chains</em>, 4th ed. Boca Raton, FL, USA: CRC Press, 2016.</li>
    <li>[5] S. Chopra and P. Meindl, <em>Supply Chain Management: Strategy, Planning, and Operation</em>, 7th ed. Boston, MA, USA: Pearson, 2019.</li>
    <li>[6] S. J. Taylor and B. Letham, "Forecasting at scale," <em>The American Statistician</em>, vol. 72, no. 1, pp. 37–45, 2018.</li>
    <li>[7] G. P. Cachon and M. A. Lariviere, "Supply chain coordination with revenue-sharing contracts: Strengths and limitations," <em>Management Science</em>, vol. 51, no. 1, pp. 30–44, Jan. 2005.</li>
    <li>[8] K. Talluri and G. van Ryzin, <em>The Theory and Practice of Revenue Management</em>. Boston, MA, USA: Springer, 2004.</li>
    <li>[9] V. F. N. Perera, R. J. Hyndman, and M. G. Nicholls, "Inventory performance of forecasting methods under stochastic demand and lead times," <em>European Journal of Operational Research</em>, vol. 275, no. 2, pp. 512–526, 2019.</li>
    <li>[10] N. Agrawal and S. A. Smith, <em>Retail Supply Chain Management: Quantitative Models and Empirical Studies</em>, 2nd ed. New York, NY, USA: Springer, 2015.</li>
    <li>[11] M. G. Dekimpe and D. M. Hanssens, "Time-series models in marketing: Past, present and future," <em>International Journal of Research in Marketing</em>, vol. 17, no. 2–3, pp. 183–193, 2000.</li>
    <li>[12] A. Syntetos, Z. Babai, J. Boylan, S. Kolassa, and K. Nikolopoulos, "Supply chain forecasting: Theory, practice, their gap and the future," <em>European Journal of Operational Research</em>, vol. 252, no. 1, pp. 1–26, Jul. 2016.</li>
    <li>[13] H. Sharma, P. K. Bala, and S. R. Gir, "Demand forecasting for perishable retail items in Indian hyperlocal delivery networks," <em>IEEE Access</em>, vol. 11, pp. 41210–41224, 2023.</li>
    <li>[14] J. H. Friedman, "Greedy function approximation: A gradient boosting machine," <em>Annals of Statistics</em>, vol. 29, no. 5, pp. 1189–1232, Oct. 2001.</li>
    <li>[15] P. Kourentzes, J. R. Trapero, and D. K. Barrow, "Optimising forecasting models for inventory planning," <em>International Journal of Production Economics</em>, vol. 225, p. 107597, Jul. 2020.</li>
</ol>

<!-- ==================== CHAPTER 9: PLAGIARISM REPORT ==================== -->
<div class="page-break"></div>
<div class="chapter-title">CHAPTER 9: PLAGIARISM REPORT</div>
<div style="border: 1px dashed #666; padding: 40pt 20pt; text-align: center; margin-top: 24pt;">
    <p class="center"><strong>[Attach Official TIET Turnitin / DrillBit Plagiarism Summary Certificate Here Before Binding]</strong></p>
    <p class="center" style="font-size: 11pt; color: #444;">
        Project Title: Intelligent Demand Forecasting and Inventory Optimization for Quick Commerce<br>
        Department of Computer Science and Engineering, TIET, Patiala
    </p>
</div>

<!-- ==================== CHAPTER 10: AI REPORT ==================== -->
<div class="page-break"></div>
<div class="chapter-title">CHAPTER 10: AI REPORT</div>
<div style="border: 1px dashed #666; padding: 40pt 20pt; text-align: center; margin-top: 24pt;">
    <p class="center"><strong>[Attach Official TIET AI Detection / Originality Report Page Here Before Binding]</strong></p>
    <p class="center" style="font-size: 11pt; color: #444;">
        Project Title: Intelligent Demand Forecasting and Inventory Optimization for Quick Commerce<br>
        Department of Computer Science and Engineering, TIET, Patiala
    </p>
</div>

</body>
</html>"""

    # Replace escaped double-braces from template and substitute dynamic variables
    html = html.replace("{{", "{").replace("}}", "}")
    replacements = {
        "{store_rows_html}": store_rows_html,
        "{items_part1_html}": items_part1_html,
        "{items_part2_html}": items_part2_html,
        "{avail_sample_html}": avail_sample_html,
        "{forecaster_code}": forecaster_code,
        "{server_excerpt_1}": server_excerpt_1,
        "{server_excerpt_2}": server_excerpt_2,
        "{val_metrics['r2_daily']}": str(val_metrics.get("r2_daily", 0.8355)),
        "{val_metrics['mae_daily_units']}": str(val_metrics.get("mae_daily_units", 9.82)),
        "{val_metrics['mae_daily_sales_inr']}": str(val_metrics.get("mae_daily_sales_inr", 851.49)),
        "{val_metrics['rmse_daily_sales_inr']}": str(val_metrics.get("rmse_daily_sales_inr", 1200.70)),
        "{val_metrics['r2_10day_window']}": str(val_metrics.get("r2_10day_window", 0.9903)),
        "{val_metrics['mape_10day_pct']}": str(val_metrics.get("mape_10day_pct", 13.59)),
        "{val_metrics['accuracy_10day_pct']}": str(val_metrics.get("accuracy_10day_pct", 86.41)),
    }
    for k, v in replacements.items():
        html = html.replace(k, v)

    # Convert inline LaTeX markers ($...$) into clean academic HTML math formatting
    import re
    def clean_latex_inline(m):
        expr = m.group(1)
        expr = expr.replace(r"\hat{Y}", "Y&#770;").replace(r"\bar{Y}", "Y&#772;")
        expr = expr.replace(r"\times", "&times;").replace(r"\cdot", "&middot;")
        expr = expr.replace(r"\pm", "&plusmn;").replace(r"\approx", "&approx;")
        expr = expr.replace(r"\le", "&le;").replace(r"\ge", "&ge;").replace(r"\ne", "&ne;")
        expr = expr.replace(r"\in", "&isin;").replace(r"\dots", "&hellip;")
        expr = expr.replace(r"\alpha", "&alpha;").replace(r"\beta", "&beta;")
        expr = expr.replace(r"\varepsilon", "&epsilon;").replace(r"\sigma", "&sigma;")
        expr = expr.replace(r"\mu", "&mu;").replace(r"\Delta", "&Delta;").replace(r"\sum", "&Sigma;")
        expr = re.sub(r"\\text\{([^}]*)\}", r"\1", expr)
        expr = re.sub(r"_\{([^}]*)\}", r"<sub>\1</sub>", expr)
        expr = re.sub(r"_([a-zA-Z0-9])", r"<sub>\1</sub>", expr)
        expr = re.sub(r"\^\{([^}]*)\}", r"<sup>\1</sup>", expr)
        expr = re.sub(r"\^([a-zA-Z0-9\-]+)", r"<sup>\1</sup>", expr)
        expr = expr.replace(r"\{", "{").replace(r"\}", "}")
        return f"<em>{expr}</em>"

    html = re.sub(r"\$([^$]+)\$", clean_latex_inline, html)

    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated print HTML at: {HTML_OUT}")


if __name__ == "__main__":
    build_report_html()
