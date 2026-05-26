-- ClickZetta Lakehouse SQL
-- 对应原始：script/gold/gold_dim_customers.ipynb
-- Gold 层：客户维度表
--
-- 迁移说明：
--   PySpark 的多表 join 直接翻译为 SQL JOIN，逻辑完全一致
--   COALESCE 处理 NULL 值，与 PySpark 的 coalesce() 函数对应

CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE IF NOT EXISTS gold.dim_customers AS
SELECT
    ROW_NUMBER() OVER (ORDER BY c.cst_id)   AS customer_key,
    c.cst_id                                 AS customer_id,
    c.cst_key                                AS customer_number,
    c.cst_firstname                          AS first_name,
    c.cst_lastname                           AS last_name,
    l.cntry                                  AS country,
    c.cst_marital_status                     AS marital_status,
    CASE
        WHEN c.cst_gndr != 'n/a' THEN c.cst_gndr
        ELSE COALESCE(e.gen, 'n/a')
    END                                      AS gender,
    e.bdate                                  AS birthdate,
    c.cst_create_date                        AS create_date
FROM silver.crm_cust_info       c
LEFT JOIN silver.erp_cust_az12  e ON c.cst_id = CAST(e.cid AS INT)
LEFT JOIN silver.erp_loc_a101   l ON e.cid    = l.cid;