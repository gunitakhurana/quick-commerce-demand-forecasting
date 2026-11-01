let METADATA = { stores: [], items: [], categories: [] };
let CURRENT_AVAIL_ROWS = [];
let CURRENT_DISCOUNTS = [];
let CURRENT_RECOMMENDATIONS = [];

function formatRs(val) {
    return "Rs. " + Math.round(Number(val || 0)).toLocaleString("en-IN");
}

document.addEventListener("DOMContentLoaded", async function () {
    initTabs();
    await fetchMetadata();
    await loadAvailabilityData();
    await loadCalendarEffect();
    await loadDiscountsData();
    await runDiscountSimulator();
    await loadRecommenderData();
    await loadUnmetQueries();
    setupEventListeners();
});

function initTabs() {
    const buttons = document.querySelectorAll(".tab-btn");
    const panels = document.querySelectorAll(".tab-panel");

    buttons.forEach((btn) => {
        btn.addEventListener("click", () => {
            buttons.forEach((b) => b.classList.remove("active"));
            panels.forEach((p) => p.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById(btn.dataset.tab).classList.add("active");
        });
    });
}

async function fetchMetadata() {
    const res = await fetch("/api/metadata");
    METADATA = await res.json();

    const globalSelect = document.getElementById("globalStoreSelect");
    globalSelect.innerHTML = METADATA.stores
        .map((s) => `<option value="${s.store}" ${s.store === 102 ? "selected" : ""}>${s.store} - ${s.city} (${s.locality})</option>`)
        .join("");

    const availStore = document.getElementById("availStoreFilter");
    availStore.innerHTML =
        `<option value="102" selected>Current Store</option>` +
        `<option value="all">All Stores</option>` +
        METADATA.stores.map((s) => `<option value="${s.store}">${s.city}</option>`).join("");

    ["availCategoryFilter", "recCategoryFilter"].forEach((id) => {
        const el = document.getElementById(id);
        el.innerHTML =
            `<option value="all">All Categories</option>` +
            METADATA.categories.map((c) => `<option value="${c}">${c}</option>`).join("");
    });

    ["calItemSelect", "simItemSelect"].forEach((id) => {
        const el = document.getElementById(id);
        el.innerHTML = METADATA.items
            .map((it) => `<option value="${it.item}" ${it.item === 204 && id === "calItemSelect" ? "selected" : ""}>${it.item} - ${it.item_name} (Rs. ${it.mrp_inr})</option>`)
            .join("");
    });

    document.getElementById("navAlertBadge").textContent = METADATA.unmet_alerts_count || 0;
}

// 1. Data Availability
async function loadAvailabilityData() {
    const store = document.getElementById("availStoreFilter").value;
    const category = document.getElementById("availCategoryFilter").value;
    const status = document.getElementById("availStatusFilter").value;
    const search = document.getElementById("availSearchInput").value;

    const params = new URLSearchParams({ store, category, status, sort_by: "store_item", search });
    const res = await fetch(`/api/availability?${params.toString()}`);
    const data = await res.json();

    CURRENT_AVAIL_ROWS = data.rows || [];

    document.getElementById("kpiAvailRecords").textContent = data.summary.total_records;
    document.getElementById("kpiAvailPct").textContent = data.summary.avg_availability_pct + "%";
    document.getElementById("kpiCriticalLow").textContent = data.summary.critical_low_stock_count;
    document.getElementById("kpiOverstock").textContent = data.summary.overstock_count;

    const tbody = document.getElementById("availTableBody");
    if (!CURRENT_AVAIL_ROWS.length) {
        tbody.innerHTML = `<tr><td colspan="10">No records found.</td></tr>`;
        return;
    }

    tbody.innerHTML = CURRENT_AVAIL_ROWS.map((r) => {
        let badge = `<span class="badge badge-success">In Stock</span>`;
        if (r.stock_status === "CRITICAL_LOW") badge = `<span class="badge badge-danger">Low Stock</span>`;
        else if (r.stock_status === "OVERSTOCK") badge = `<span class="badge badge-warning">Overstock</span>`;
        else if (r.stock_status === "HISTORICAL_GAPS") badge = `<span class="badge badge-warning">Past Stockouts</span>`;

        return `<tr>
            <td>${r.item}</td>
            <td><strong>${r.item_name}</strong></td>
            <td>${r.category}</td>
            <td>${r.mrp_inr}</td>
            <td>${r.active_days} / ${r.total_days}</td>
            <td>${r.zero_days}</td>
            <td>${r.availability_pct}%</td>
            <td>${Math.round(r.avg_daily_units)}</td>
            <td>${r.current_stock_units} (${r.days_of_stock}d)</td>
            <td>${badge}</td>
        </tr>`;
    }).join("");
}

// 2. Calendar Effect
async function loadCalendarEffect() {
    const store = Number(document.getElementById("globalStoreSelect").value || 102);
    const item = Number(document.getElementById("calItemSelect").value || 204);
    const start_date = document.getElementById("calStartDate").value;
    const end_date = document.getElementById("calEndDate").value;

    const res = await fetch("/api/calendar-effect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ store, item, start_date, end_date }),
    });
    const data = await res.json();
    const s = data.summary;

    document.getElementById("calPredInr").textContent = formatRs(s.total_predicted_inr);
    document.getElementById("calPredUnits").textContent = `${s.total_predicted_units} units (${s.days_analyzed} days)`;
    document.getElementById("calBaseInr").textContent = formatRs(s.total_baseline_inr);

    const sign = s.net_calendar_lift_pct >= 0 ? "+" : "";
    document.getElementById("calLiftPct").textContent = `${sign}${s.net_calendar_lift_pct}%`;
    document.getElementById("calLiftInr").textContent = `${sign}${formatRs(s.net_calendar_lift_inr)}`;
    document.getElementById("calFestDays").textContent = `${s.festival_days_count} Festivals`;
    document.getElementById("calWeekendPayday").textContent = `${s.weekend_days_count} Weekends, ${s.payday_days_count} Salary Days`;

    drawChart(data.daily_series || []);

    const tbody = document.getElementById("calDailyTableBody");
    tbody.innerHTML = (data.daily_series || [])
        .map((d) => {
            let factor = d.reasons[0];
            if (d.festival_name) factor = `<span class="badge badge-warning">${d.festival_name}</span>`;
            else if (d.is_weekend) factor = `<span class="badge badge-info">Weekend</span>`;
            return `<tr>
                <td>${d.date}</td>
                <td>${d.weekday.slice(0, 3)}</td>
                <td>${factor}</td>
                <td>${formatRs(d.baseline_sales_inr)}</td>
                <td><strong>${formatRs(d.predicted_sales_inr)}</strong></td>
                <td>${Math.ceil(d.predicted_units)}</td>
            </tr>`;
        })
        .join("");
}

function drawChart(series) {
    const canvas = document.getElementById("calendarChartCanvas");
    if (!canvas || !series.length) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width;
    const H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const padL = 60, padR = 20, padT = 20, padB = 30;
    const plotW = W - padL - padR;
    const plotH = H - padT - padB;

    const vals = series.flatMap((d) => [d.predicted_sales_inr, d.baseline_sales_inr]);
    const maxVal = Math.max(...vals, 100) * 1.1;
    const minVal = Math.min(...vals, 0) * 0.85;

    ctx.strokeStyle = "#e5e7eb";
    ctx.fillStyle = "#555";
    ctx.font = "11px Arial";

    for (let i = 0; i <= 3; i++) {
        const y = padT + (plotH * i) / 3;
        const v = maxVal - ((maxVal - minVal) * i) / 3;
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(W - padR, y);
        ctx.stroke();
        ctx.fillText(Math.round(v), 8, y + 4);
    }

    const getX = (idx) => padL + (plotW * idx) / Math.max(1, series.length - 1);
    const getY = (v) => padT + plotH - ((v - minVal) / Math.max(1, maxVal - minVal)) * plotH;

    // Base line
    ctx.strokeStyle = "#9ca3af";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    series.forEach((d, i) => {
        const x = getX(i), y = getY(d.baseline_sales_inr);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Predicted line
    ctx.strokeStyle = "#2563eb";
    ctx.lineWidth = 2;
    ctx.beginPath();
    series.forEach((d, i) => {
        const x = getX(i), y = getY(d.predicted_sales_inr);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();

    series.forEach((d, i) => {
        const x = getX(i), y = getY(d.predicted_sales_inr);
        if (d.festival_name) {
            ctx.fillStyle = "#dc2626";
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        }
        const step = Math.max(1, Math.floor(series.length / 7));
        if (i % step === 0 || i === series.length - 1) {
            ctx.fillStyle = "#555";
            ctx.fillText(d.date.slice(5), x - 14, H - 8);
        }
    });
}

// 3. Discounts
async function loadDiscountsData() {
    const store = Number(document.getElementById("globalStoreSelect").value || 102);
    const res = await fetch(`/api/discounts?store=${store}`);
    const data = await res.json();

    CURRENT_DISCOUNTS = data.recommendations || [];

    document.getElementById("bundlesContainer").innerHTML = (data.bundles || [])
        .map(
            (b) => `<div class="bundle-row">
                <div class="controls-row justify-between" style="margin-bottom:4px;">
                    <strong>${b.bundle_name}</strong>
                    <span class="badge badge-success">${b.discount_pct}% OFF (Rs. ${b.bundle_price_inr})</span>
                </div>
                <div style="font-size:12px; color:#555;">
                    ${b.items.map((i) => i.name).join(" + ")}
                </div>
            </div>`
        )
        .join("");

    renderDiscountTable();
}

function renderDiscountTable() {
    const tierFilter = document.getElementById("discTierFilter").value;
    const tbody = document.getElementById("discTableBody");
    const filtered =
        tierFilter === "all"
            ? CURRENT_DISCOUNTS
            : CURRENT_DISCOUNTS.filter((d) => d.tier === tierFilter);

    tbody.innerHTML = filtered
        .map((d) => {
            let badge = `<span class="badge badge-info">Tier 4</span>`;
            if (d.tier === "TIER_1_PERISHABLE_CLEARANCE") badge = `<span class="badge badge-danger">Tier 1</span>`;
            else if (d.tier === "TIER_2_SLOW_MOVER") badge = `<span class="badge badge-warning">Tier 2</span>`;
            else if (d.tier === "TIER_3_FESTIVE_PROMO") badge = `<span class="badge badge-success">Tier 3</span>`;

            return `<tr>
                <td>${badge}</td>
                <td><strong>${d.item_name}</strong></td>
                <td>Rs. ${d.mrp_inr}</td>
                <td><strong>Rs. ${d.discounted_price_inr}</strong></td>
                <td>${d.discount_pct}%</td>
                <td>${d.mechanic}</td>
                <td>+${d.expected_lift_pct}% (${Math.round(d.projected_daily_units)} units/d)</td>
            </tr>`;
        })
        .join("");
}

async function runDiscountSimulator() {
    const store = Number(document.getElementById("globalStoreSelect").value || 102);
    const item = Number(document.getElementById("simItemSelect").value || 201);
    const discount_pct = Number(document.getElementById("simDiscRange").value || 15);
    const duration_days = Number(document.getElementById("simDurationSelect").value || 7);

    document.getElementById("simDiscLabel").textContent = discount_pct + "%";

    const res = await fetch("/api/simulate-discount", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ store, item, discount_pct, duration_days }),
    });
    const d = await res.json();

    document.getElementById("simResultBox").innerHTML = `
        <p><strong>Offer Price:</strong> Rs. ${d.discounted_price_inr} (MRP: Rs. ${d.mrp_inr})</p>
        <p><strong>Expected Units:</strong> ${Math.round(d.projected_units)} units (+${d.volume_lift_pct}%)</p>
        <p><strong>Expected Revenue:</strong> ${formatRs(d.projected_revenue_inr)} | <strong>Net Profit:</strong> ${formatRs(d.projected_net_profit_inr)}</p>
    `;
}

// 4. Item Recommender
async function loadRecommenderData() {
    const store = Number(document.getElementById("globalStoreSelect").value || 102);
    const start_date = document.getElementById("recStartDate").value;
    const end_date = document.getElementById("recEndDate").value;
    const service_level = Number(document.getElementById("recServiceLevel").value || 0.95);
    const category = document.getElementById("recCategoryFilter").value;

    const res = await fetch("/api/recommend-stock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ store, start_date, end_date, service_level, category }),
    });
    const data = await res.json();

    CURRENT_RECOMMENDATIONS = data.recommendations || [];
    const s = data.summary;
    const dr = data.date_range;

    document.getElementById("recCriticalCount").textContent = s.critical_restock_count;
    document.getElementById("recSkusNeed").textContent = `${s.skus_needing_restock} / ${s.total_skus_evaluated}`;
    document.getElementById("recTotalUnits").textContent = s.total_recommended_order_units;
    document.getElementById("recProcCost").textContent = "Cost: " + formatRs(s.total_procurement_cost_inr);
    document.getElementById("recProjRev").textContent = formatRs(s.total_projected_revenue_inr);
    document.getElementById("recProjMargin").textContent = "Margin: " + formatRs(s.projected_gross_margin_inr);

    const fests = dr.active_festivals.length ? dr.active_festivals.join(", ") : "None";
    document.getElementById("recCalendarBanner").innerHTML =
        `<strong>Period:</strong> ${dr.start_date} to ${dr.end_date} (${dr.num_days} days) | <strong>Festivals:</strong> ${fests} | <strong>Weekends:</strong> ${dr.weekend_days}`;

    renderRecommenderTable();
}

function renderRecommenderTable() {
    const prioFilter = document.getElementById("recPriorityFilter").value;
    const tbody = document.getElementById("recTableBody");
    const rows =
        prioFilter === "all"
            ? CURRENT_RECOMMENDATIONS
            : CURRENT_RECOMMENDATIONS.filter((r) => r.priority === prioFilter);

    tbody.innerHTML = rows
        .map((r) => {
            let badge = `<span class="badge badge-success">Sufficient</span>`;
            if (r.priority === "CRITICAL_RESTOCK") badge = `<span class="badge badge-danger">Urgent</span>`;
            else if (r.priority === "HIGH_PRIORITY") badge = `<span class="badge badge-warning">High</span>`;
            else if (r.priority === "SAFETY_REFILL") badge = `<span class="badge badge-info">Refill</span>`;

            return `<tr>
                <td>${badge}</td>
                <td><strong>${r.item_name}</strong></td>
                <td>${r.category}</td>
                <td>${r.mrp_inr}</td>
                <td>${r.forecast_units}</td>
                <td>${r.safety_stock_units}</td>
                <td>${r.current_stock_units}</td>
                <td><strong>${r.recommended_order_units}</strong></td>
                <td>${formatRs(r.procurement_cost_inr)}</td>
            </tr>`;
        })
        .join("");
}

// 5. Unmet Queries (>100 Alert)
async function loadUnmetQueries() {
    const res = await fetch("/api/unmet-queries");
    const data = await res.json();

    document.getElementById("navAlertBadge").textContent = data.active_alerts_over_100;
    document.getElementById("activeAlertsHeaderBadge").textContent = data.active_alerts_over_100 + " Alerts";

    const queries = data.queries || [];
    const triggered = queries.filter((q) => q.status === "ALERT_TRIGGERED");

    const grid = document.getElementById("triggeredAlertsGrid");
    grid.innerHTML = triggered.length
        ? triggered
              .map(
                  (q) => `<div class="alert-item">
                    <div>
                        <strong>${q.query_term}</strong> (${q.query_count} queries)<br>
                        <span style="font-size:12px; color:#555;">Suggested Stock: ${q.recommended_initial_stock} units | MRP: Rs. ${q.estimated_mrp_inr}</span>
                    </div>
                    <button class="btn-success" onclick="onboardUnmetProduct('${q.id}')">Add to Inventory</button>
                </div>`
              )
              .join("")
        : `<p>No unstocked items above 100 queries.</p>`;

    const tbody = document.getElementById("unmetQueriesTableBody");
    tbody.innerHTML = queries
        .map((q) => {
            let badge = `<span class="badge badge-info">Tracking (${q.query_count}/100)</span>`;
            let actionHtml = `<button class="btn-sm" onclick="quickBoostQuery('${q.query_term.replace(/'/g, "\\'")}', '${q.suggested_category}', ${q.estimated_mrp_inr})">+10 Queries</button>`;

            if (q.status === "ADDED_TO_INVENTORY") {
                badge = `<span class="badge badge-success">Added</span>`;
                actionHtml = `In Stock`;
            } else if (q.query_count > 100) {
                badge = `<span class="badge badge-danger">Alert (&gt;100)</span>`;
                actionHtml = `<button class="btn-success" onclick="onboardUnmetProduct('${q.id}')">Add to Inventory</button>`;
            } else if (q.query_count >= 85) {
                badge = `<span class="badge badge-warning">Near Threshold</span>`;
            }

            return `<tr>
                <td><strong>${q.query_term}</strong></td>
                <td>${q.suggested_category}</td>
                <td>${q.estimated_mrp_inr}</td>
                <td><strong>${q.query_count}</strong> / 100</td>
                <td>${formatRs(q.est_monthly_revenue_inr)}</td>
                <td>${q.recommended_initial_stock}</td>
                <td>${badge}</td>
                <td>${actionHtml}</td>
            </tr>`;
        })
        .join("");
}

async function simulateCustomerSearch() {
    const query = document.getElementById("simSearchInput").value.trim();
    const category = document.getElementById("simSearchCategory").value;
    const estimated_mrp_inr = Number(document.getElementById("simSearchMrp").value || 100);
    const increment = Number(document.getElementById("simSearchBurst").value || 5);
    const store = Number(document.getElementById("globalStoreSelect").value || 102);

    if (!query) return;

    const res = await fetch("/api/search-query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, category, estimated_mrp_inr, increment, store }),
    });
    const data = await res.json();

    const fb = document.getElementById("searchSimFeedback");
    fb.classList.remove("hidden", "badge-danger", "badge-warning", "badge-success");

    if (data.in_inventory) {
        fb.classList.add("badge-success");
        const m = data.matched_items[0];
        fb.textContent = `Item "${m.item_name}" is already in inventory (Current stock: ${m.current_stock_units} units).`;
    } else if (data.alert_triggered) {
        fb.classList.add("badge-danger");
        fb.textContent = `Alert Triggered: "${data.entry.query_term}" reached ${data.entry.query_count} queries (>100). Recommended: Add ${data.entry.recommended_initial_stock} units to inventory.`;
    } else {
        fb.classList.add("badge-warning");
        fb.textContent = `Logged query for "${data.entry.query_term}". Total count: ${data.entry.query_count}/100.`;
    }

    await loadUnmetQueries();
}

window.quickBoostQuery = async function (query, category, mrp) {
    document.getElementById("simSearchInput").value = query;
    document.getElementById("simSearchCategory").value = category;
    document.getElementById("simSearchMrp").value = mrp;
    document.getElementById("simSearchBurst").value = "15";
    await simulateCustomerSearch();
};

window.onboardUnmetProduct = async function (id) {
    const res = await fetch("/api/add-to-inventory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id }),
    });
    const data = await res.json();
    if (data.success) {
        const fb = document.getElementById("searchSimFeedback");
        fb.classList.remove("hidden", "badge-danger", "badge-warning");
        fb.classList.add("badge-success");
        fb.textContent = `Added "${data.new_item.item_name}" to store inventory.`;
        await fetchMetadata();
        await loadUnmetQueries();
        await loadAvailabilityData();
        await loadRecommenderData();
    }
};

function setupEventListeners() {
    document.getElementById("globalStoreSelect").addEventListener("change", (e) => {
        document.getElementById("availStoreFilter").value = e.target.value;
        loadAvailabilityData();
        loadCalendarEffect();
        loadDiscountsData();
        runDiscountSimulator();
        loadRecommenderData();
    });

    ["availStoreFilter", "availCategoryFilter", "availStatusFilter"].forEach((id) => {
        document.getElementById(id).addEventListener("change", loadAvailabilityData);
    });
    document.getElementById("availSearchInput").addEventListener("input", loadAvailabilityData);

    document.getElementById("runCalendarBtn").addEventListener("click", loadCalendarEffect);
    document.querySelectorAll(".preset-row .btn-sm[data-start]").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.getElementById("calStartDate").value = btn.dataset.start;
            document.getElementById("calEndDate").value = btn.dataset.end;
            if (btn.dataset.item) document.getElementById("calItemSelect").value = btn.dataset.item;
            loadCalendarEffect();
        });
    });

    document.getElementById("discTierFilter").addEventListener("change", renderDiscountTable);
    ["simItemSelect", "simDiscRange", "simDurationSelect"].forEach((id) => {
        document.getElementById(id).addEventListener("input", runDiscountSimulator);
    });

    document.getElementById("runRecommenderBtn").addEventListener("click", loadRecommenderData);
    document.getElementById("recPriorityFilter").addEventListener("change", renderRecommenderTable);

    document.getElementById("runSearchSimBtn").addEventListener("click", simulateCustomerSearch);
    document.querySelectorAll(".query-preset").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.getElementById("simSearchInput").value = btn.dataset.q;
            document.getElementById("simSearchCategory").value = btn.dataset.cat;
            document.getElementById("simSearchMrp").value = btn.dataset.mrp;
        });
    });

    document.getElementById("exportAvailCsvBtn").addEventListener("click", () => {
        exportCsv("availability_table.csv", CURRENT_AVAIL_ROWS);
    });
    document.getElementById("exportPoCsvBtn").addEventListener("click", () => {
        exportCsv("recommended_stock.csv", CURRENT_RECOMMENDATIONS);
    });
}

function exportCsv(filename, rows) {
    if (!rows || !rows.length) return;
    const keys = Object.keys(rows[0]);
    const csvContent = [
        keys.join(","),
        ...rows.map((r) => keys.map((k) => `"${String(r[k] ?? "").replace(/"/g, '""')}"`).join(",")),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
}
