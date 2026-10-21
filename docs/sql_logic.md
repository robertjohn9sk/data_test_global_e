# SQL logic guide

All four reports read `fact_sales`, which is one row per order line. Each report filters to `status = 'Delivered'`, so returned, cancelled, and processing rows remain available for audit but do not inflate dashboard revenue.

## Q1 — Monthly revenue trend

`STRFTIME(date_key, '%Y-%m')` creates a stable month label. The query groups fact rows by that label and sums `line_revenue_usd`, then orders chronologically.

## Q2 — Top products and revenue share

The CTE first aggregates delivered revenue by product through `dim_product`. The outer query uses `SUM(revenue_usd) OVER ()` as the grand total, so each product’s share is calculated as product revenue divided by total delivered product revenue.

## Q3 — Segment and channel revenue

The fact joins to `dim_customer` through `customer_key`, then groups by the customer segment and sales channel. This keeps the business dimensions in the star schema instead of repeating descriptive attributes in the fact.

## Q4 — Customer revenue rank

The query counts distinct orders and sums line revenue per customer. `RANK() OVER (ORDER BY SUM(...) DESC)` ranks customers by revenue while preserving ties with the same rank.

## Reconciliation checkpoint

The pipeline validates 12 orders and 20 lines and asserts delivered revenue of `9994.624060` USD before completing.
