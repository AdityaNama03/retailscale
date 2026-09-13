<p align="center">
  <h1 align="center">🏬 RetailScale</h1>
  <p align="center">
    <strong>End-to-end data engineering &amp; analytics platform for e-commerce intelligence</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Snowflake-29B5E8?style=for-the-badge&logo=snowflake&logoColor=white" alt="Snowflake"/>
    <img src="https://img.shields.io/badge/dbt-FF694B?style=for-the-badge&logo=dbt&logoColor=white" alt="dbt"/>
    <img src="https://img.shields.io/badge/Airflow-017CEE?style=for-the-badge&logo=apache-airflow&logoColor=white" alt="Airflow"/>
    <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"/>
    <img src="https://img.shields.io/badge/AWS_S3-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white" alt="AWS S3"/>
    <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  </p>
</p>

---

RetailScale is a production-grade data pipeline that ingests raw e-commerce data from the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), transforms it through a **medallion architecture** (Bronze → Silver → Gold) using **Snowflake** and **dbt**, orchestrates daily refreshes with **Apache Airflow**, and surfaces insights through a 7-page **Streamlit** analytics dashboard.

Built to demonstrate real-world data engineering patterns — not toy examples.

---

## 📐 Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────────────────────┐     ┌──────────────┐
│              │     │                  │     │         Snowflake              │     │              │
│  Olist CSVs  │────▶│    Amazon S3     │────▶│                                │────▶│  Streamlit   │
│  (Kaggle)    │     │  Landing Zone    │     │  Bronze ──▶ Silver ──▶ Gold    │     │  Dashboard   │
│              │     │                  │     │  (raw)     (dbt)     (dbt)     │     │  (7 pages)   │
└──────────────┘     └──────────────────┘     └────────────────────────────────┘     └──────────────┘
       │                     │                              │                              │
       │                     │                              │                              │
       ▼                     ▼                              ▼                              ▼
   9 CSV files        Date-partitioned          8 staging views              Executive Overview
   ~99K orders        bronze/ prefixes          2 intermediate models        Revenue Analytics
   ~100K customers    Idempotent uploads        4 fact tables                Product Analytics
   ~33K products      Retry w/ backoff          4 dimension tables           Customer Analytics
   ~3K sellers                                  1 SCD Type 2 snapshot        Delivery & Logistics
                                                4 singular tests             Seller Performance
                                                                             Data Quality Monitor
```

### Pipeline Flow (Airflow DAG)

```
upload_to_s3  ──▶  snowflake_copy_into  ──▶  dbt_run  ──▶  dbt_test
     │                    │                     │              │
     ▼                    ▼                     ▼              ▼
  Python script       COPY INTO             Builds all      Runs schema +
  with idempotent     bronze tables         Silver & Gold   singular tests.
  S3 uploads +        with ON_ERROR=        models via      Blocks pipeline
  retry backoff       'CONTINUE'            ref() graph     if tests fail
```

---

## 🗄️ Data Model

### Medallion Architecture

| Layer | Schema | Purpose | Implementation |
|-------|--------|---------|----------------|
| **🥉 Bronze** | `BRONZE` | Raw landing — all `VARCHAR`, no rejects | `COPY INTO` from S3 external stage, `ON_ERROR='CONTINUE'` |
| **🥈 Silver** | `SILVER` | Cleaned, typed, deduplicated | dbt views: 8 staging models + 2 intermediate models |
| **🥇 Gold** | `GOLD` | Business-ready dimensional model | dbt tables: 4 fact tables + 4 dimension tables |

### Gold Layer Star Schema

```
                         ┌───────────────┐
                         │  dim_dates    │
                         │  DATE_DAY     │
                         │  YEAR/QUARTER │
                         │  MONTH        │
                         │  IS_WEEKEND   │
                         └───────┬───────┘
                                 │
  ┌───────────────┐              │              ┌────────────────┐
  │ dim_customers │              │              │  dim_products  │
  │ CUSTOMER_ID   │              │              │  PRODUCT_ID    │
  │ UNIQUE_ID     │              │              │  CATEGORY_NAME │
  │ STATE / CITY  │              │              │  WEIGHT / DIMS │
  │ (SCD Type 2)  │              │              └───────┬────────┘
  └───────┬───────┘              │                      │
          │           ┌──────────┴──────────┐           │
          └──────────▶│    fct_orders       │           │
                      │  ORDER_ID           │           │
                      │  CUSTOMER_ID (FK)   │           │
                      │  PURCHASE_DATE      │           │
                      │  TOTAL_PAYMENT_VALUE│           │
                      │  IS_LATE_DELIVERY   │           │
                      └──────────┬──────────┘           │
                                 │                      │
            ┌────────────────────┼──────────────┐       │
            │                    │              │       │
  ┌─────────┴──────┐  ┌─────────┴─────┐  ┌─────┴──────┴──────┐
  │ fct_payments   │  │ fct_delivery  │  │  fct_order_items  │
  │ PAYMENT_TYPE   │  │  _performance │  │  PRODUCT_ID (FK)  │
  │ PAYMENT_VALUE  │  │  IS_LATE      │  │  SELLER_ID (FK)   │
  │ INSTALLMENTS   │  │  DELAY_DAYS   │  │  PRICE / FREIGHT  │
  └────────────────┘  └───────────────┘  └─────────┬─────────┘
                                                    │
                                          ┌─────────┴─────────┐
                                          │   dim_sellers     │
                                          │   SELLER_ID       │
                                          │   CITY / STATE    │
                                          └───────────────────┘
```

### dbt Model Lineage

```
Sources (Bronze)          Staging (Silver)           Intermediate (Silver)        Marts (Gold)
─────────────────         ────────────────           ─────────────────────        ────────────
bronze.orders        ──▶  stg_orders            ──▶  int_orders_enriched    ──▶  fct_orders
bronze.customers     ──▶  stg_customers         ──▶  ├── (joins customers,       fct_order_items
bronze.order_items   ──▶  stg_order_items       ──▶  │    payments)              fct_payments
bronze.payments      ──▶  stg_payments          ──▶  │                           fct_delivery_performance
bronze.products      ──▶  stg_products               │
bronze.sellers       ──▶  stg_sellers                 └── int_delivery_      ──▶  dim_customers (via snapshot)
bronze.reviews       ──▶  stg_reviews                     performance             dim_products
bronze.geolocation   ──▶  stg_geolocation                                         dim_sellers
                                                                                  dim_dates (generator)
Snapshot:
stg_customers ──▶ snap_customers (SCD2) ──▶ dim_customers
```

---

## 📊 Dashboard Pages

The Streamlit dashboard has **7 enterprise-grade pages** — all querying from the Gold schema.

| # | Page | KPIs | Charts | What It Answers |
|---|------|------|--------|-----------------|
| 1 | **Executive Overview** | Revenue, Orders, AOV, On-Time % | Area trend, Stacked bar, Donut, Horizontal bar | *"How is the business doing today?"* |
| 2 | **Revenue Analytics** | GMV, Freight, Avg Installments, Rev/Customer | Dual-axis, Stacked area, Histogram, Heatmap | *"Where does revenue come from?"* |
| 3 | **Product Analytics** | Categories, Products Sold, Top Category, Avg Price | Treemap, Bar charts, Scatter, Box plot | *"Which categories drive the business?"* |
| 4 | **Customer Analytics** | Unique Customers, Orders/Customer, Top State, CLV | Geo bars, Donut (repeat rate), Histogram | *"Who are our customers?"* |
| 5 | **Delivery & Logistics** | On-Time Rate, Avg Days, Late Count, Worst Delay | SLA trend line, Delay histogram, Box plot | *"Are we hitting delivery targets?"* |
| 6 | **Seller Performance** | Active Sellers, Top State, Rev/Seller, Items/Seller | Seller density, Revenue bars, Freight analysis | *"Who are our top sellers?"* |
| 7 | **Data Quality Monitor** | Tables Monitored, Total Rows, Null Rate, Orphans | Row counts, Null analysis, dbt test status | *"Is the data trustworthy?"* |

### Design System — "Midnight Commerce"

| Element | Value |
|---------|-------|
| Theme | Dark (`#0E1117` background) |
| Primary Accent | Electric Blue `#58A6FF` |
| Positive | Emerald Green `#3FB950` |
| Warning | Amber Gold `#D29922` |
| Negative | Coral Red `#F85149` |
| Charts | Plotly with `plotly_dark` template |
| Font | Inter (Google Fonts) |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Source Data** | [Olist Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle) | 9 CSV files — real Brazilian e-commerce data |
| **Object Storage** | Amazon S3 | Landing zone with date-partitioned bronze prefixes |
| **Data Warehouse** | Snowflake | Bronze/Silver/Gold schemas, external stage, compute |
| **Transformation** | dbt (dbt-snowflake) | Staging, intermediate, mart models + tests + snapshots |
| **Orchestration** | Apache Airflow (Docker) | Daily DAG: S3 upload → Snowflake load → dbt run → dbt test |
| **Containerization** | Docker Compose | Airflow webserver, scheduler, Postgres metadata DB |
| **Dashboard** | Streamlit + Plotly | 7-page enterprise analytics dashboard |
| **Language** | Python 3.x | Upload scripts, Airflow DAGs, Streamlit app |

---

## 📁 Project Structure

```
retailscale/
│
├── .env                              # Secrets (gitignored): AWS, Snowflake creds
├── .gitignore
├── Dockerfile                        # Custom Airflow image with dbt baked in
├── docker-compose.yml                # Airflow services: webserver, scheduler, postgres
├── README.md
├── LEARNING.md                       # Daily engineering journal
│
├── data/
│   └── raw/                          # Olist CSVs (gitignored, ~130MB)
│       ├── olist_orders_dataset.csv
│       ├── olist_customers_dataset.csv
│       ├── olist_order_items_dataset.csv
│       ├── olist_order_payments_dataset.csv
│       ├── olist_order_reviews_dataset.csv
│       ├── olist_products_dataset.csv
│       ├── olist_sellers_dataset.csv
│       ├── olist_geolocation_dataset.csv
│       └── product_category_name_translation.csv
│
├── scripts/
│   └── upload_to_s3.py               # Idempotent S3 uploader with retry backoff
│
├── snowflake/
│   └── setup/
│       ├── 01_create_databases.sql
│       ├── 02_create_schemas.sql
│       ├── 03_create_stages.sql
│       ├── 04_create_file_formats.sql
│       ├── 05_create_bronze_tables.sql   # 9 tables, all VARCHAR
│       └── 06_copy_into_bronze.sql       # COPY INTO + row count sanity check
│
├── dbt_retailscale/
│   ├── dbt_project.yml
│   ├── macros/
│   │   └── generate_schema_name.sql      # Custom schema routing (no prefix)
│   ├── models/
│   │   ├── staging/                      # 8 staging views (Silver)
│   │   │   ├── _staging__sources.yml
│   │   │   ├── stg_orders.sql
│   │   │   ├── stg_customers.sql
│   │   │   ├── stg_order_items.sql
│   │   │   ├── stg_payments.sql
│   │   │   ├── stg_products.sql
│   │   │   ├── stg_sellers.sql
│   │   │   ├── stg_reviews.sql
│   │   │   └── stg_geolocation.sql
│   │   ├── intermediate/                 # 2 intermediate models (Silver)
│   │   │   ├── int_orders_enriched.sql
│   │   │   └── int_delivery_performance.sql
│   │   └── marts/                        # 8 Gold mart tables
│   │       ├── _marts__models.yml        # Schema tests
│   │       ├── fct_orders.sql
│   │       ├── fct_order_items.sql
│   │       ├── fct_payments.sql
│   │       ├── fct_delivery_performance.sql
│   │       ├── dim_customers.sql         # Built from SCD2 snapshot
│   │       ├── dim_products.sql
│   │       ├── dim_sellers.sql
│   │       └── dim_dates.sql             # Date spine via generator
│   ├── snapshots/
│   │   └── snap_customers.sql            # SCD Type 2 (check strategy)
│   ├── tests/                            # 4 singular data quality tests
│   │   ├── assert_delivery_date_after_purchase.sql
│   │   ├── assert_no_orphan_order_items.sql
│   │   ├── assert_payment_totals_match_order_totals.sql
│   │   └── assert_positive_order_values.sql
│   └── seeds/
│       └── product_category_name_translation.csv
│
├── airflow/
│   ├── dags/
│   │   └── retailscale_daily_pipeline.py   # Daily DAG
│   ├── logs/                               # (gitignored)
│   └── plugins/
│
├── streamlit/
│   ├── .streamlit/
│   │   └── config.toml                     # Dark theme config
│   ├── app.py                              # Landing page + navigation
│   ├── config.py                           # Colour palette, chart helpers
│   ├── connection.py                       # Snowflake connector + @st.cache_data
│   ├── assets/
│   │   └── style.css                       # Midnight Commerce dark theme
│   ├── components/
│   │   ├── kpi_card.py                     # Reusable KPI card component
│   │   ├── header.py                       # Page header component
│   │   └── filters.py                      # Sidebar filter controls
│   ├── pages/
│   │   ├── 1_executive_overview.py
│   │   ├── 2_revenue_analytics.py
│   │   ├── 3_product_analytics.py
│   │   ├── 4_customer_analytics.py
│   │   ├── 5_delivery_logistics.py
│   │   ├── 6_seller_performance.py
│   │   └── 7_data_quality.py
│   └── utils/
│       └── snowflake_connector.py
│
└── docs/
    └── RetailScale_Dashboard_Documentation.md
```

---

## 🚀 Getting Started

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Scripts, dbt, Streamlit |
| Docker & Docker Compose | Latest | Airflow runtime |
| AWS Account | — | S3 bucket for landing zone |
| Snowflake Account | — | Data warehouse (free trial works) |
| Kaggle Account | — | Download the Olist dataset |

### 1. Clone & Setup

```bash
git clone https://github.com/AdityaNama03/retailscale.git
cd retailscale

# Create virtual environment
python -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

# Install dependencies
pip install dbt-snowflake snowflake-connector-python streamlit plotly pandas boto3 python-dotenv millify
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
# AWS
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=ap-south-1
S3_BUCKET=your-s3-bucket-name

# Snowflake
SNOWFLAKE_ACCOUNT=your_account_id
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=RETAILSCALE_WH
SNOWFLAKE_DATABASE=RETAILSCALE_DEV
SNOWFLAKE_SCHEMA=GOLD
SNOWFLAKE_ROLE=ACCOUNTADMIN
```

### 3. Download the Dataset

Download the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) from Kaggle and place all 9 CSV files in `data/raw/`.

### 4. Setup Snowflake

Run the SQL scripts in order inside your Snowflake worksheet:

```bash
# Run in Snowflake UI or via SnowSQL
snowflake/setup/01_create_databases.sql
snowflake/setup/02_create_schemas.sql
snowflake/setup/03_create_stages.sql
snowflake/setup/04_create_file_formats.sql
snowflake/setup/05_create_bronze_tables.sql
```

### 5. Upload Data to S3

```bash
python scripts/upload_to_s3.py
# Uploads 9 CSVs to s3://your-bucket/bronze/{table}/ingestion_date=YYYY-MM-DD/
# Idempotent — safe to re-run
```

### 6. Load into Snowflake Bronze

Run the COPY INTO statements:

```bash
snowflake/setup/06_copy_into_bronze.sql
```

### 7. Run dbt Models

```bash
cd dbt_retailscale

# Configure dbt profile (~/.dbt/profiles.yml)
dbt debug          # Verify connection
dbt snapshot       # Build SCD Type 2 customer snapshot
dbt run            # Build all Silver + Gold models
dbt test           # Run schema + singular tests
```

### 8. Start Airflow (for scheduled runs)

```bash
cd ..   # back to project root
docker compose up -d

# Access Airflow UI at http://localhost:8090
# Login: admin / admin
# Enable the 'retailscale_daily_pipeline' DAG
```

### 9. Launch the Dashboard

```bash
cd streamlit
streamlit run app.py

# Opens at http://localhost:8501
```

---

## 🧪 Data Quality

RetailScale has multiple layers of data quality enforcement:

### dbt Schema Tests (`_marts__models.yml`)

| Model | Column | Test |
|-------|--------|------|
| `fct_orders` | `order_id` | `not_null`, `unique` |
| `fct_orders` | `customer_id` | `not_null` |
| `fct_orders` | `order_status` | `accepted_values` (8 valid statuses) |
| `dim_customers` | `customer_id` | `not_null` |

### dbt Singular Tests (`tests/`)

| Test | What It Validates |
|------|-------------------|
| `assert_delivery_date_after_purchase` | Delivery never happens before purchase |
| `assert_no_orphan_order_items` | Every line item belongs to a valid order |
| `assert_payment_totals_match_order_totals` | Payment sums match order totals (±R$0.01) |
| `assert_positive_order_values` | Non-cancelled orders have positive revenue |

### Bronze Layer Safeguards

- `ON_ERROR = 'CONTINUE'` — never reject data at bronze, skip bad rows silently
- `_loaded_at` timestamp on every row — full auditability
- `_source_file` metadata — trace any row back to its source file

---

## 📈 Key Dataset Statistics

| Entity | Records | Source File |
|--------|---------|------------|
| Orders | 99,441 | `olist_orders_dataset.csv` |
| Customers | 99,441 | `olist_customers_dataset.csv` |
| Order Items | 112,650 | `olist_order_items_dataset.csv` |
| Payments | 103,886 | `olist_order_payments_dataset.csv` |
| Reviews | 99,224 | `olist_order_reviews_dataset.csv` |
| Products | 32,951 | `olist_products_dataset.csv` |
| Sellers | 3,095 | `olist_sellers_dataset.csv` |
| Geolocation | 1,000,163 | `olist_geolocation_dataset.csv` |

---

## 🔑 Key Engineering Decisions

| Decision | Why |
|----------|-----|
| **All Bronze columns are VARCHAR** | Bronze mirrors the source exactly — type casting belongs in Silver |
| **Custom `generate_schema_name` macro** | dbt defaults prefix custom schemas with target (`dev_silver`). We override to get clean `SILVER`/`GOLD` |
| **SCD Type 2 via `dbt snapshot`** | Customer city/state can change. Never update in place — close old row, insert new one |
| **Pre-aggregate payments before joining** | Joining orders (one) to payments (many) without aggregating first causes fan-out — silently inflates row counts |
| **`@st.cache_data(ttl=900)` on all queries** | 15-minute cache — balance between freshness and Snowflake compute cost |
| **Airflow DAG with strict task ordering** | `>>` operator enforces: upload → load → transform → test. Tests failing blocks bad data from propagating |
| **`BashOperator` for dbt, not Snowflake provider** | Simpler, avoids pip dependency hell between dbt-snowflake and airflow-providers-snowflake |
| **Docker image with dbt baked in** | `_PIP_ADDITIONAL_REQUIREMENTS` reinstalls on every container start. Custom `Dockerfile` pays the cost once |

---

## 🗺️ Roadmap

- [x] S3 landing zone with idempotent uploads
- [x] Snowflake Bronze/Silver/Gold schemas
- [x] dbt staging, intermediate, and mart models
- [x] SCD Type 2 customer snapshot
- [x] 4 singular data quality tests
- [x] Airflow DAG (Docker Compose)
- [x] 7-page Streamlit dashboard
- [ ] Slack alerting on pipeline failures
- [ ] Full CI/CD with GitHub Actions
- [ ] dbt docs generation + hosting
- [ ] Cost monitoring (Snowflake credit tracking)
- [ ] Row-level security for multi-tenant access

---

## 📄 Documentation

| Document | Description |
|----------|-------------|
| [`README.md`](README.md) | This file — project overview and setup guide |
| [`LEARNING.md`](LEARNING.md) | Daily engineering journal — what was learned, mistakes made, debugging stories |
| [`docs/RetailScale_Dashboard_Documentation.md`](docs/RetailScale_Dashboard_Documentation.md) | Complete dashboard reference — every KPI, SQL query, chart, and data source |

---

## 🤝 Contributing

This is a personal portfolio project, but feedback is welcome! Feel free to:

1. Open an issue for bugs or suggestions
2. Fork and submit a PR
3. Star the repo if you found it useful ⭐

---

## 📜 License

This project is for educational and portfolio purposes. The Olist dataset is public and available under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

---

<p align="center">
  <sub>Built with ☕ and SQL by <a href="https://github.com/AdityaNama03">Aditya Nama</a></sub>
</p>