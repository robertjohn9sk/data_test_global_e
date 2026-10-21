"""Small Streamlit dashboard backed by the generated DuckDB warehouse."""
from pathlib import Path
import duckdb
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
st.set_page_config(page_title="RetailPro BI", layout="wide")
st.title("RetailPro Sales Performance")
st.caption("Delivered revenue only • fixed EUR→USD rate 1.08 • line-item fact grain")
con = duckdb.connect(str(ROOT / "data/warehouse/retail_bi.duckdb"), read_only=True)
total = con.sql("SELECT SUM(line_revenue_usd) FROM fact_sales WHERE status='Delivered'").fetchone()[0]
orders = con.sql("SELECT COUNT(DISTINCT order_id) FROM fact_sales WHERE status='Delivered'").fetchone()[0]
products = con.sql("SELECT COUNT(DISTINCT product_key) FROM fact_sales WHERE status='Delivered'").fetchone()[0]
a, b, c = st.columns(3)
a.metric("Delivered revenue", f"${total:,.2f}"); b.metric("Delivered orders", orders); c.metric("Products sold", products)
st.subheader("Monthly revenue trend")
st.line_chart(con.sql("SELECT date_key AS month, SUM(line_revenue_usd) revenue_usd FROM fact_sales WHERE status='Delivered' GROUP BY 1 ORDER BY 1").df().set_index("month"))
st.subheader("Top products")
st.dataframe(con.sql("SELECT p.product_name, ROUND(SUM(f.line_revenue_usd),2) revenue_usd FROM fact_sales f JOIN dim_product p USING(product_key) WHERE f.status='Delivered' GROUP BY 1 ORDER BY 2 DESC").df(), use_container_width=True)
con.close()
