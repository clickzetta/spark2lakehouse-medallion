-- ClickZetta Lakehouse SQL
-- Gold 层：产品维度表 + 销售事实表
-- 对应原始：script/gold/gold_dim_products.ipynb, gold_fact_sales.ipynb

CREATE SCHEMA IF NOT EXISTS gold;

-- 产品维度表
CREATE TABLE IF NOT EXISTS gold.dim_products AS
SELECT
    ROW_NUMBER() OVER (ORDER BY p.prd_start_dt, p.prd_key) AS product_key,
    p.prd_id                                                AS product_id,
    p.prd_key                                               AS product_number,
    p.prd_nm                                                AS product_name,
    p.prd_cost                                              AS product_cost,
    p.prd_line                                              AS product_line,
    c.cat                                                   AS category,
    c.subcat                                                AS subcategory,
    c.maintenance                                           AS maintenance,
    p.prd_start_dt                                          AS start_date
FROM silver.crm_prd_info    p
LEFT JOIN silver.erp_px_cat_g1v2 c
    ON p.prd_key = REPLACE(c.id, '-', '_')
WHERE p.prd_end_dt IS NULL
   OR p.prd_end_dt > CURRENT_DATE();

-- 销售事实表
CREATE TABLE IF NOT EXISTS gold.fact_sales AS
SELECT
    s.sls_ord_num                                           AS order_number,
    p.product_key,
    c.customer_key,
    TRY_TO_DATE(s.sls_order_dt, 'yyyyMMdd')                AS order_date,
    TRY_TO_DATE(s.sls_ship_dt,  'yyyyMMdd')                AS ship_date,
    TRY_TO_DATE(s.sls_due_dt,   'yyyyMMdd')                AS due_date,
    CAST(s.sls_sales    AS DECIMAL(18,2))                   AS sales_amount,
    CAST(s.sls_quantity AS INT)                             AS quantity,
    CAST(s.sls_price    AS DECIMAL(18,2))                   AS unit_price
FROM silver.crm_sales_details s
LEFT JOIN gold.dim_products  p ON s.sls_prd_key  = p.product_number
LEFT JOIN gold.dim_customers c ON CAST(s.sls_cust_id AS INT) = c.customer_id
WHERE s.sls_ord_num IS NOT NULL;
