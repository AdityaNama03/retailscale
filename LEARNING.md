# RetailScale — Learning Log

This file tracks what I actually learned each day building RetailScale — concepts understood, mistakes made, and how real debugging works. Updated after each work session.

---

## Day 1 — 2026-09-06

### What got built
- S3 landing zone (`retailscale-landing`) with date-partitioned bronze prefixes
- Snowflake: warehouse, database, `BRONZE`/`SILVER`/`GOLD` schemas, storage integration + external stage, 8 bronze tables, all loaded via `COPY INTO`
- dbt project connected to Snowflake, with custom schema routing so models build into clean `SILVER`/`GOLD` schemas instead of dbt's default prefixed names
- 4 staging models (`stg_orders`, `stg_customers`, `stg_order_items`, `stg_payments`)
- 1 intermediate model (`int_orders_enriched`) joining orders + customers + aggregated payments
- SCD Type 2 snapshot (`snap_customers`) — validated end-to-end with a real city-change simulation
- `dim_customers` (built on the snapshot) and `fct_orders` (fact table with a late-delivery flag)
- dbt schema + custom tests
- A working Airflow DAG (Docker Compose), orchestrating: S3 upload → Snowflake copy → dbt run → dbt test

---

### Core concepts learned

**Medallion architecture (Bronze/Silver/Gold)**
Bronze = raw, untyped, never rejects data (`VARCHAR` everywhere, `ON_ERROR = 'CONTINUE'`). Silver = cleaned, typed, deduplicated — this is where casting and null-filtering actually happen. Gold = business-ready marts people actually query. Each layer has a distinct job; don't blend them.

**Idempotency**
S3 uploads check `head_object` before writing, so re-running the same day's upload doesn't duplicate work. The principle: a pipeline should be safe to re-run without side effects.

**`ON_ERROR = 'CONTINUE'` trade-off**
Lets bad rows get skipped instead of failing the whole file load — correct for bronze's "land everything" philosophy, but it means silent data loss unless you also check `VALIDATE(table, JOB_ID => '_last')` after loads.

**dbt schema routing isn't automatic**
By default dbt prefixes custom schemas with the target schema (e.g. `dev_silver`), not just `silver`. Needed a custom `generate_schema_name` macro to override that and get exact `SILVER`/`GOLD` schema names matching what we manually created in Snowflake.

**Fan-out**
Joining a "one" table (orders) to a "many" table (payments, due to installments) without aggregating first silently multiplies rows. Fixed by aggregating `stg_payments` down to one row per `order_id` *before* joining. This is one of the most common real-world dbt bugs — it doesn't error, it just quietly inflates numbers.

**SCD Type 2**
Never `UPDATE` a dimension in place — that destroys history. Instead, close out the old row (`dbt_valid_to` gets set) and insert a new one (`dbt_valid_to = null`) when tracked columns change. Implemented via dbt snapshots with `strategy='check'` (since Olist has no `updated_at` column to use the `timestamp` strategy). Proved it actually works by manually updating a customer's city in bronze, re-running `dbt snapshot`, and confirming 2 rows existed for that customer afterward — one closed, one current.

**Always alias transformed columns**
Any time you `CAST`/`::` a column, it needs an explicit `as` alias — otherwise the resulting column gets an auto-generated name and breaks downstream references silently rather than loudly.

**dbt tests as automated data quality gates**
`not_null`/`unique` protect structural integrity (no missing/duplicate keys — this is literally what would catch a fan-out bug). `accepted_values` protects against unexpected values sneaking into a column. This replaces manually eyeballing query results.

**Airflow's actual job**
Not to do new work — it automates and governs work that could otherwise be run manually. What it adds: scheduling (runs itself daily), enforced task dependencies (`>>` operator — downstream literally cannot start early), automatic retries, visible failure state, and a history of what ran and when. The DAG shape (`upload_to_s3 >> snowflake_copy_into >> dbt_run >> dbt_test`) enforces that tests failing blocks nothing further from running on bad data.

---

### Debugging lessons (the "how real engineering feels" section)

- **Unsaved files look identical to broken files.** Several `dbt run` "Nothing to do" errors today were just an unsaved `.sql` file — dbt reads from disk, so it doesn't exist until you hit save. Always check the tab's unsaved-dot before assuming there's a real bug.
- **Missing commas between CTEs are a very common SQL error** — every `with x as (...),` needs the trailing comma except the last CTE. This alone caused multiple failed runs today.
- **`pip`'s dependency resolver can effectively hang.** Installing two packages together (`dbt-snowflake` + `apache-airflow-providers-snowflake`) in one command triggered `ResolutionTooDeep` — pip searching an enormous combination space for compatible versions. Fix: don't force unrelated packages to resolve together; install only what's actually needed (we didn't need the Airflow Snowflake provider since we used `BashOperator`, not a native hook).
- **`_PIP_ADDITIONAL_REQUIREMENTS` reinstalls on every container start** — fine for a quick test, terrible for iteration speed. Building a custom image via a `Dockerfile` (`pip install` baked in at build time) fixes this — pay the cost once, not on every `docker compose up`.
- **Docker Compose can silently run a stale container** after you edit `docker-compose.yml`, if it doesn't recreate from scratch. `docker compose up -d --force-recreate <service>` or a full `down` + `up` avoids chasing a ghost config.
- **YAML is indentation-sensitive in a way that fails unpredictably.** Pasting a `volumes:` block one level too deep (nested inside `environment:` instead of as a sibling) produced a confusing schema-validation error, not an obvious "wrong indentation" message. When Compose validation errors look bizarre, check indentation first.
- **dbt's partial-parse cache can go stale** when a project directory is shared between two different execution contexts (host venv vs. container) — `rm -rf target` before running clears it and forces a fresh parse.
- **Read the actual error class name.** `ResolutionTooDeep`, `KeyError`, "port is already allocated" — each pointed at a specific, fixable cause once actually read, rather than just retried blindly.

---

*Next session: remaining staging/mart models, Streamlit dashboard, second DAG, Slack alerting, full architecture docs, GitHub remote push.*
