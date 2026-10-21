-- Q1: Monthly delivered revenue trend
SELECT STRFTIME(date_key, '%Y-%m') AS month_label, ROUND(SUM(line_revenue_usd), 2) AS revenue_usd
FROM fact_sales WHERE status = 'Delivered' GROUP BY 1 ORDER BY 1;

-- Q2: Top products and share of delivered revenue
WITH product_revenue AS (
  SELECT p.product_name, SUM(f.line_revenue_usd) AS revenue_usd
  FROM fact_sales f JOIN dim_product p USING (product_key)
  WHERE f.status = 'Delivered' GROUP BY p.product_name
)
SELECT product_name, ROUND(revenue_usd, 2) AS revenue_usd,
       ROUND(100 * revenue_usd / SUM(revenue_usd) OVER (), 2) AS pct_total
FROM product_revenue ORDER BY revenue_usd DESC;

-- Q3: Revenue by customer segment and channel
SELECT c.customer_segment, f.channel, ROUND(SUM(f.line_revenue_usd), 2) AS revenue_usd
FROM fact_sales f JOIN dim_customer c USING (customer_key)
WHERE f.status = 'Delivered'
GROUP BY 1, 2 ORDER BY 1, 2;

-- Q4: Customer order count, revenue, and revenue rank
SELECT c.customer_name, COUNT(DISTINCT f.order_id) AS total_orders,
       ROUND(SUM(f.line_revenue_usd), 2) AS revenue_usd,
       RANK() OVER (ORDER BY SUM(f.line_revenue_usd) DESC) AS revenue_rank
FROM fact_sales f JOIN dim_customer c USING (customer_key)
WHERE f.status = 'Delivered'
GROUP BY c.customer_name ORDER BY revenue_rank;
