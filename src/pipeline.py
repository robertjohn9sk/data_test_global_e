"""Build the RetailPro warehouse and execute the four assessment reports."""
from __future__ import annotations
import csv, json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW, OUTPUT = ROOT / "data/raw/orders_raw.json", ROOT / "data/output"
DB, REPORTS = ROOT / "data/warehouse/retail_bi.duckdb", OUTPUT / "reports"
FX = {"USD": Decimal("1.00"), "EUR": Decimal("1.08")}

def money(v): return Decimal(v).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

def category(v):
    key = v.strip().lower().replace(" & ", " and ")
    if key in {"sports", "sports and fitness"}: return "Sports & Fitness"
    if key == "home appliances": return "Home Appliances"
    return v.strip().title()

def flatten():
    source = json.loads(RAW.read_text(encoding="utf-8"))
    assert source["export_metadata"]["record_count"] == len(source["orders"])
    orders, lines = [], []
    for order in source["orders"]:
        c, r = order["customer"], order["sales_rep"]
        orders.append((order["order_id"], order["order_date"], order["status"], order["channel"], c["customer_id"], c["full_name"], c["segment"], c["region"], c["city"], c["country"], r["rep_id"], r["name"], order.get("shipping_cost"), order["currency"], order.get("payment_method")))
        for n, item in enumerate(order.get("line_items", []), 1):
            discount = Decimal(str(item.get("discount_pct") or 0)); qty = Decimal(str(item["quantity"])); price = Decimal(str(item["unit_price"]))
            local = money(qty * price * (1 - discount / 100)); rate = FX[order["currency"]]
            lines.append((order["order_id"], n, item["product_id"], item["product_name"], item["category"], category(item["category"]), int(qty), price, discount, order["currency"], rate, local, money(local * rate)))
    assert len(orders) == 12 and len(lines) == 20
    return orders, lines

def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerows(rows)

def main():
    orders, lines = flatten(); OUTPUT.mkdir(parents=True, exist_ok=True); REPORTS.mkdir(exist_ok=True); DB.parent.mkdir(exist_ok=True)
    if DB.exists(): DB.unlink()
    con = duckdb.connect(str(DB))
    con.execute("CREATE TABLE orders (order_id VARCHAR, order_date TIMESTAMPTZ, status VARCHAR, channel VARCHAR, customer_id VARCHAR, customer_name VARCHAR, customer_segment VARCHAR, region VARCHAR, city VARCHAR, country VARCHAR, rep_id VARCHAR, rep_name VARCHAR, shipping_cost DECIMAL(18,6), currency VARCHAR, payment_method VARCHAR)")
    con.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", orders)
    con.execute("CREATE TABLE order_lines (order_id VARCHAR, line_number INTEGER, product_id VARCHAR, product_name VARCHAR, category_raw VARCHAR, category VARCHAR, quantity INTEGER, unit_price DECIMAL(18,6), discount_pct DECIMAL(9,4), currency VARCHAR, fx_rate_to_usd DECIMAL(9,4), line_revenue_local DECIMAL(18,6), line_revenue_usd DECIMAL(18,6))")
    con.executemany("INSERT INTO order_lines VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", lines)
    con.execute("CREATE TABLE dim_date AS SELECT DISTINCT CAST(order_date AS DATE) date_key, EXTRACT(year FROM order_date)::INTEGER year_num, EXTRACT(month FROM order_date)::INTEGER month_num, STRFTIME(order_date, '%B') month_name FROM orders")
    con.execute("CREATE TABLE dim_product AS SELECT row_number() OVER (ORDER BY product_id)::INTEGER product_key, product_id, MIN(product_name) product_name, MIN(category) category FROM order_lines GROUP BY product_id")
    con.execute("CREATE TABLE dim_customer AS SELECT row_number() OVER (ORDER BY customer_id, effective_from)::INTEGER customer_key, customer_id, customer_name, customer_segment, region, city, country, effective_from, COALESCE(LEAD(effective_from) OVER (PARTITION BY customer_id ORDER BY effective_from), DATE '9999-12-31') effective_to, LEAD(effective_from) OVER (PARTITION BY customer_id ORDER BY effective_from) IS NULL is_current FROM (SELECT customer_id, MIN(customer_name) customer_name, customer_segment, MIN(region) region, MIN(city) city, MIN(country) country, CAST(MIN(order_date) AS DATE) effective_from FROM orders GROUP BY customer_id, customer_segment) x")
    con.execute("CREATE TABLE fact_sales AS SELECT o.order_id, l.line_number, d.date_key, c.customer_key, p.product_key, o.status, o.channel, o.currency, l.quantity, l.unit_price*l.fx_rate_to_usd unit_price_usd, l.discount_pct, l.line_revenue_usd FROM orders o JOIN order_lines l USING(order_id) JOIN dim_date d ON CAST(o.order_date AS DATE)=d.date_key JOIN dim_product p USING(product_id) JOIN dim_customer c ON o.customer_id=c.customer_id AND CAST(o.order_date AS DATE)>=c.effective_from AND CAST(o.order_date AS DATE)<c.effective_to")
    quality = [("DQ-001", "ORD-2024-006 / PROD-416", "Category casing differs", "Canonicalized to Home Appliances; raw value retained."), ("DQ-002", "PROD-207 and PROD-214", "Product categories vary by order", "Mapped Sports and Sports & Fitness to Sports & Fitness."), ("DQ-003", "ORD-2024-009 / PROD-207", "Materially different supplied price", "Flagged for review; retained supplied EUR price.")]
    write_csv(OUTPUT / "data_quality_log.csv", [("issue_id","records","issue","decision"), *quality])
    for table in ("orders", "order_lines", "dim_customer", "dim_product", "dim_date", "fact_sales"): con.execute(f"COPY {table} TO ? (HEADER, DELIMITER ',')", [str(OUTPUT / f"{table}.csv")])
    queries = {"q1_monthly_revenue":"SELECT STRFTIME(date_key, '%Y-%m') month_label, ROUND(SUM(line_revenue_usd),2) revenue_usd FROM fact_sales WHERE status='Delivered' GROUP BY 1 ORDER BY 1", "q2_top_products":"WITH x AS (SELECT p.product_name, SUM(f.line_revenue_usd) revenue_usd FROM fact_sales f JOIN dim_product p USING(product_key) WHERE status='Delivered' GROUP BY 1) SELECT product_name, ROUND(revenue_usd,2) revenue_usd, ROUND(100*revenue_usd/SUM(revenue_usd) OVER(),2) pct_total FROM x ORDER BY revenue_usd DESC", "q3_segment_channel":"SELECT c.customer_segment, f.channel, ROUND(SUM(f.line_revenue_usd),2) revenue_usd FROM fact_sales f JOIN dim_customer c USING(customer_key) WHERE f.status='Delivered' GROUP BY 1,2 ORDER BY 1,2", "q4_customer_rank":"SELECT c.customer_name, COUNT(DISTINCT f.order_id) total_orders, ROUND(SUM(f.line_revenue_usd),2) revenue_usd, RANK() OVER(ORDER BY SUM(f.line_revenue_usd) DESC) revenue_rank FROM fact_sales f JOIN dim_customer c USING(customer_key) WHERE f.status='Delivered' GROUP BY 1 ORDER BY revenue_rank"}
    for name, sql in queries.items(): con.execute(f"COPY ({sql}) TO ? (HEADER, DELIMITER ',')", [str(REPORTS / f"{name}.csv")])
    delivered = con.sql("SELECT ROUND(SUM(line_revenue_usd),6) FROM fact_sales WHERE status='Delivered'").fetchone()[0]
    assert str(delivered) == "9994.624060", delivered
    print(f"validated orders={len(orders)} lines={len(lines)} delivered_revenue_usd={delivered}")
    con.close()

if __name__ == "__main__": main()
