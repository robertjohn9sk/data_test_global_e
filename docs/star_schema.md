# Star schema

```mermaid
erDiagram
    DIM_DATE ||--o{ FACT_SALES : date_key
    DIM_CUSTOMER ||--o{ FACT_SALES : customer_key
    DIM_PRODUCT ||--o{ FACT_SALES : product_key
    DIM_DATE { DATE date_key PK INTEGER year INTEGER month }
    DIM_CUSTOMER { INTEGER customer_key PK VARCHAR customer_id VARCHAR customer_segment DATE effective_from DATE effective_to BOOLEAN is_current }
    DIM_PRODUCT { INTEGER product_key PK VARCHAR product_id VARCHAR product_name VARCHAR category }
    FACT_SALES { VARCHAR order_id PK INTEGER line_number PK DATE date_key FK INTEGER customer_key FK INTEGER product_key FK VARCHAR status VARCHAR channel INTEGER quantity DECIMAL line_revenue_usd }
```

`fact_sales` has one row per source order line. `orders` and `order_lines` are the auditable flattened Task 1 tables; shipping stays at order grain and is intentionally not joined into the line-grain revenue fact.

