# Retail BI Technical Assessment

An end-to-end, reproducible BI engineering solution for the RetailPro ERP JSON export. Python handles extraction and validation, DuckDB provides the analytical warehouse, SQL provides the reporting layer, and Streamlit provides a lightweight dashboard.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/pipeline.py
streamlit run src/dashboard.py
```

The pipeline rebuilds `data/warehouse/retail_bi.duckdb`, exports target tables to `data/output/`, and executes the four required reports to `data/output/reports/`.

## Deliverables

- `data/raw/orders_raw.json` — preserved source export, unchanged.
- `src/pipeline.py` — validation, flattening, dimensional modelling, loading, CSV export, and report execution.
- `data/output/orders.csv` and `order_lines.csv` — Task 1 target tables.
- `data/output/dim_*.csv` and `fact_sales.csv` — star-schema tables.
- `data/output/data_quality_log.csv` — affected records and handling decisions.
- `sql/reporting_queries.sql` — the four dashboard queries.
- `data/output/reports/*.csv` — executed query results.
- `docs/star_schema.md` — Mermaid diagram and grain definitions.
- `docs/dashboard.svg` — static dashboard preview; the live version is `src/dashboard.py`.
- `public/` — Netlify-hosted online report explorer.

## Online testing

The Netlify version is a read-only presentation layer over the same CSV outputs produced by the local DuckDB run; it is not a hosted DuckDB server. Open the public site, switch between the four report tabs, and use **Download CSV** to inspect each result. To reproduce or change the model, run `python src/pipeline.py` locally and use the generated DuckDB file; Netlify’s managed database product is Postgres, not DuckDB, so it is intentionally not presented as an equivalent replacement.

The Netlify site is configured by `netlify.toml` with `public/` as its publish directory. The repository is connected to the assessment site: https://bitestgloabe.netlify.app/. Successful pipeline runs refresh the published CSV copies; pushing the updated files to the production branch triggers deployment.

## Modelling decisions

`fact_sales` is at source line-item grain, with `(order_id, line_number)` as its natural key. Delivered revenue is the dashboard scope; returned, cancelled, and processing rows remain in the fact for auditability but are excluded from revenue reports. EUR is converted at the fixed assessment rate of 1.08 USD/EUR, USD uses 1.00, and shipping remains at order grain so it cannot be multiplied by line joins.

### Q-A — customer history / SCD Type 2

Sarah Mitchell’s segment changes from Premium to VIP on order `ORD-2024-012`. I would use a Type 2 customer dimension keyed by `customer_key`, preserving the earlier Premium version and adding a VIP version whose effective date is the first observed VIP order date; the source does not provide a change timestamp. This preserves historical reporting but adds version-management and lookup complexity.

### Q-B — incremental loading

For daily appended files, land each file immutably, validate it, and upsert only unseen `order_id` values using a control table or watermark keyed by source export date. A production implementation would also use a deterministic line hash for late-arriving corrections, load new dimension versions when tracked attributes change, and make the fact load idempotent with a unique `(order_id, line_number)` key.

## Data quality findings

1. Category casing differs for `PROD-416` on `ORD-2024-006`; the pipeline preserves the raw category in staging and canonicalizes it to `Home Appliances` in `dim_product`.
2. `PROD-207` is labelled `Sports & Fitness` in `ORD-2024-003` and `Sports` in `ORD-2024-009` and `ORD-2024-011`; the product dimension maps both to `Sports & Fitness`.
3. `PROD-207` has a materially different supplied unit price in `ORD-2024-009` (€149.99 vs $59.99 elsewhere). The pipeline flags the record and retains the supplied value because currency and price history do not prove it is erroneous.

Discounts of zero are valid, and null discounts would be treated as zero. Cancelled and returned orders are retained but excluded from delivered revenue; no refund transactions are invented.

## AI usage declaration

ChatGPT/Codex was used as a senior BI and data-engineering mentor for requirement extraction, schema and quality-rule design, implementation review, query design, and documentation. The prompts asked for a time-boxed, reproducible Python + DuckDB solution and required actual validation rather than unverified claims. Add the final ChatGPT shared-link URL here before hand-in.

## Dashboard and review notes

The public dashboard visualizes all four required reports: monthly revenue, product revenue and share, historical segment/channel revenue, and customer rank. It includes the underlying report tables and CSV downloads. Months with no delivered sales display zero; the seven-row SQL result remains unchanged. KPIs use unrounded fact revenue and display two decimal places.

The supplied prompts align with the assessment. Separate hosting is an optional presentation convenience; no additional hosted database is required. “Production-quality” is interpreted here as a reproducible assessment, not a claim that this small batch pipeline implements production operations. Customer SCD logic supports the observed Premium-to-VIP change; repeated segment reversions and changes to other attributes require a more general change-detection implementation. Q4 intentionally includes delivered customers only; total orders means delivered orders. The source customer ID should be included in grouping if extending to customers with duplicate names.

During this review, ChatGPT/Codex inspected the repository, reran the pipeline, checked standalone SQL results, and added browser charts over the exported data. The workflow was: compare requirements to code, validate actual outputs, then add the smallest dashboard presentation layer. The conversation shared-link field above remains a manual submission step.

Review verification: the pipeline completed successfully with 12 orders, 20 lines and delivered revenue 9994.624060 USD. All four standalone SQL queries matched their CSV outputs (7, 8, 5 and 6 rows). JavaScript syntax and dashboard rendering logic were checked against the actual CSVs. Full browser visual verification and a new screenshot remain pending because the browser binary download failed in this environment.
