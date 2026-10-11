# RetailScale Dashboard Documentation

Reference for the 7-page Streamlit dashboard in `streamlit/`. Every page reads from the **Gold** schema in Snowflake (`fct_*` and `dim_*` tables built by dbt) through `run_query()` in `streamlit/connection.py`, which caches results with `@st.cache_data`.

Conventions used across pages:

- Currency is Brazilian real (R$), formatted by `format_currency()` in `config.py`.
- "Revenue" means `fct_orders.TOTAL_PAYMENT_VALUE` unless stated otherwise. Where a page excludes cancelled orders it filters `ORDER_STATUS != 'canceled'`.
- "GMV" means `SUM(fct_order_items.PRICE)` (item price, excluding freight).
- Customer metrics join `dim_customers` with `IS_CURRENT = true`, so only the current SCD2 version of each customer is counted.
- `IS_LATE` is `NULL` for undelivered or cancelled orders by design, so it is never counted as on-time.

---

## 1. Executive Overview

**Question answered:** how is the business doing overall?

| KPI | Definition | Source |
|-----|-----------|--------|
| Total Revenue | Sum of `TOTAL_PAYMENT_VALUE`, non-cancelled orders | `fct_orders` |
| Total Orders | Count of non-cancelled orders | `fct_orders` |
| Avg Order Value | Total revenue / total orders | `fct_orders` |
| On-Time Delivery % | Orders with `IS_LATE = false` / delivered orders | `fct_delivery_performance` |

| Chart | Type | Data |
|-------|------|------|
| Monthly Revenue Trend | Area plus dashed 3-month rolling average | Monthly sum of revenue, non-cancelled |
| Order Status Distribution | Stacked bar by month | Order count by `ORDER_STATUS` |
| Payment Method Breakdown | Donut | `SUM(PAYMENT_VALUE)` by `PAYMENT_TYPE` from `fct_payments` |
| Top 10 Categories by Revenue | Horizontal bar | `SUM(PRICE)` by category, `fct_order_items` joined to `dim_products` |

---

## 2. Revenue Analytics

**Question answered:** where does revenue come from?

| KPI | Definition | Source |
|-----|-----------|--------|
| GMV | `SUM(PRICE)` | `fct_order_items` |
| Total Freight Revenue | `SUM(FREIGHT_VALUE)` | `fct_order_items` |
| Avg Installments | `AVG(PAYMENT_INSTALLMENTS)` | `fct_payments` |
| Revenue per Customer | Non-cancelled revenue / distinct `CUSTOMER_ID` | `fct_orders` |

| Chart | Type | Data |
|-------|------|------|
| GMV vs AOV Trend | Dual-axis: GMV bars, AOV line | Monthly GMV (`fct_order_items`) joined to monthly AOV (`fct_orders`) |
| Revenue by Payment Type Over Time | Stacked area | Monthly `PAYMENT_VALUE` by type |
| Installment Distribution | Bar | Payment count by installment number |
| Revenue Heatmap | Heatmap | Revenue by day of week and month, joined to `dim_dates` |
| Monthly Revenue Table | Table | Month, GMV, orders, AOV, MoM growth % (via `LAG`) |

---

## 3. Product Analytics

**Question answered:** which categories drive the business?

| KPI | Definition | Source |
|-----|-----------|--------|
| Active Categories | Distinct `PRODUCT_CATEGORY_NAME` | `dim_products` |
| Products Sold | Distinct `PRODUCT_ID` | `fct_order_items` |
| Top Category | Highest `SUM(PRICE)`, with its revenue | `fct_order_items` + `dim_products` |
| Avg Item Price | `AVG(PRICE)` | `fct_order_items` |

Charts: category revenue treemap (top 20, coloured by units), top 15 categories by units, top 15 by average price, price vs freight scatter (bubble size = units), price box plot for the top 10 categories by volume, and a full category breakdown table. Rows with a null category are excluded.

---

## 4. Customer Analytics

**Question answered:** who are our customers?

| KPI | Definition | Source |
|-----|-----------|--------|
| Unique Customers | Distinct `CUSTOMER_UNIQUE_ID`, current rows | `dim_customers` |
| Avg Orders per Customer | All orders / unique customers | `fct_orders`, `dim_customers` |
| Top State | State with most orders | `fct_orders` + `dim_customers` |
| Avg Customer Value | Mean of per-customer total spend | `fct_orders` + `dim_customers` |

Charts: top 15 states by customers, top 10 states by customers, top 10 cities by revenue, order frequency donut (1 order / 2 orders / 3+ orders), order value histogram (orders under R$ 2,000), and a state performance table (customers, orders, revenue).

---

## 5. Delivery & Logistics

**Question answered:** are we hitting delivery targets?

| KPI | Definition | Source |
|-----|-----------|--------|
| On-Time Rate | `IS_LATE = false` / delivered orders | `fct_delivery_performance` |
| Avg Delivery Days | `DATEDIFF('day', purchase, delivered)` | `fct_delivery_performance` |
| Late Deliveries | Count where `IS_LATE = true` | `fct_delivery_performance` |
| Worst Delay | `MAX(DELIVERY_DELAY_DAYS)` | `fct_delivery_performance` |

Charts: monthly on-time rate line, delivery delay histogram, late % by state (top 15), delivery breakdown donut (On-Time / Late / Undelivered), delivery time by month box plot, and a state SLA table (total deliveries, on-time %, average and worst delay).

---

## 6. Seller Performance

**Question answered:** who are our top sellers?

| KPI | Definition | Source |
|-----|-----------|--------|
| Active Sellers | Distinct `SELLER_ID` with items sold | `fct_order_items` |
| Top Seller State | State with most sellers | `dim_sellers` |
| Avg Revenue / Seller | `SUM(PRICE)` / distinct sellers | `fct_order_items` |
| Avg Items / Seller | Item rows / distinct sellers | `fct_order_items` |

Charts: seller distribution by state, top 15 sellers by revenue, top 15 by order count, revenue-per-seller histogram, average freight by seller state, and a seller directory table (top 100 by revenue, seller ID truncated to 12 characters).

---

## 7. Data Quality Monitor

**Question answered:** is the data trustworthy?

| KPI | Definition | Source |
|-----|-----------|--------|
| Tables Monitored | Gold tables in the row-count check (8) | `fct_*`, `dim_*` |
| Total Gold Rows | Sum of row counts | all Gold tables |
| Null Rate (Orders) | % of `fct_orders` rows with null `TOTAL_PAYMENT_VALUE` | `fct_orders` |
| Orphan Items | `fct_order_items` rows with no matching order | `fct_order_items` LEFT JOIN `fct_orders` |

Panels: Gold table row counts, column null analysis for `fct_orders` (purchase, approved and delivery dates, payment value, `IS_LATE_DELIVERY`), order status distribution, a data quality checks summary, and a pipeline architecture diagram.

---

## Caveats found while documenting

These come from reading the SQL, not from running it against Snowflake:

1. **State-level delivery metrics include undelivered orders in the denominator.** The state SLA table and "Late Delivery % by State" use `COUNT(*)` without the `ORDER_DELIVERED_DATE IS NOT NULL` filter that the KPI queries use. Because `IS_LATE` is `NULL` for those orders, state on-time % reads lower than the headline On-Time Rate.
2. **Avg Orders per Customer counts cancelled orders**, while Revenue and AOV on pages 1 and 2 exclude them.
3. **Average delivery days uses purchase-to-delivered**, so it measures total fulfilment time rather than carrier transit time.
