# Intelligent Demand Forecasting & Inventory Optimization for Quick Commerce

Mini Project (B.E. Computer Science and Business Systems, Thapar Institute of Engineering & Technology, Patiala)

## Features Implemented
1. **Data Availability Table**: Store x SKU historical availability matrix (2020-2024), stockout tracking, and live inventory health across 10 Indian cities and 50 SKUs.
2. **Calendar Effect Engine**: Quantifies Indian festivals (Diwali, Holi, Raksha Bandhan, Eid, Dussehra), weekend surges (+50.2% Sunday peak), monthly seasonality, and the 1st-7th salary week.
3. **Rule-Based Tiered Discount Engine**: 4-tier markdown framework (Perishable Expiry Clearance, Slow-Moving Stock Booster, Combo Bundles, Weekday Promos) + interactive price elasticity & profit calculator.
4. **Date-Range Item Recommender**: Predicts unit demand over any chosen date window, adds volatility-based safety stock ($Z \cdot \sigma \cdot \sqrt{L}$), and outputs exact reorder quantities.
5. **Unstocked Product Query Tracker (>100 Queries Alert)**: Tracks customer searches for unstocked products and automatically triggers a shopkeeper inventory onboarding alert once queries exceed 100.

## Train / Test Evaluation Summary
- **Training Set**: `2020-01-01` to `2023-12-31` (`730,500` rows, 80%)
- **Unseen Test Set**: `2024-01-01` to `2024-12-31` (`183,000` rows, 20% actuals)
- **Daily Test $R^2$**: `0.8355` | **Daily MAE**: `+/- 9.82 units/day`
- **10-Day Stocking Window $R^2$**: `0.9903` | **10-Day Forecast Accuracy**: `86.41%` (`13.59%` MAPE)

## How Any Team Member Can Run the Project

1. **Clone the repository**:
   ```bash
   git clone <YOUR_GITHUB_REPO_URL>
   cd "Mini Project"
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Re-run model training & 2024 test evaluation**:
   ```bash
   python train_model.py
   ```

4. **Start the server**:
   ```bash
   python server.py
   ```

5. **Open the Dashboard**:
   Open `http://localhost:3125` in any web browser.
