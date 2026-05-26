-- ClickZetta Lakehouse SQL
-- Silver 层：CRM 产品信息 + 销售明细清洗
-- 对应原始：script/silver/crm/silver_crm_prd_info.ipynb, silver_crm_sales_details.ipynb

CREATE SCHEMA IF NOT EXISTS silver;

-- CRM 产品信息清洗
CREATE TABLE IF NOT EXISTS silver.crm_prd_info (
    prd_id       INT,
    prd_key      STRING,
    prd_nm       STRING,
    prd_cost     DECIMAL(18,2),
    prd_line     STRING,
    prd_start_dt DATE,
    prd_end_dt   DATE,
    ingestion_date TIMESTAMP
);

INSERT OVERWRITE silver.crm_prd_info
SELECT
    CAST(REPLACE(prd_id, 'PRD-', '') AS INT)                AS prd_id,
    REPLACE(SUBSTRING(prd_key, 4), '-', '_')                AS prd_key,
    prd_nm,
    CASE WHEN prd_cost IS NULL OR prd_cost = '' THEN 0
         ELSE CAST(prd_cost AS DECIMAL(18,2))
    END                                                      AS prd_cost,
    CASE
        WHEN UPPER(TRIM(prd_line)) = 'M' THEN 'Mountain'
        WHEN UPPER(TRIM(prd_line)) = 'R' THEN 'Road'
        WHEN UPPER(TRIM(prd_line)) = 'S' THEN 'Other Sales'
        WHEN UPPER(TRIM(prd_line)) = 'T' THEN 'Touring'
        ELSE 'n/a'
    END                                                      AS prd_line,
    TRY_TO_DATE(prd_start_dt, 'M/d/yyyy')                   AS prd_start_dt,
    DATEADD(DAY, -1,
        LEAD(TRY_TO_DATE(prd_start_dt, 'M/d/yyyy'))
            OVER (PARTITION BY REPLACE(SUBSTRING(prd_key, 4), '-', '_')
                  ORDER BY TRY_TO_DATE(prd_start_dt, 'M/d/yyyy'))
    )                                                        AS prd_end_dt,
    CURRENT_TIMESTAMP()                                      AS ingestion_date
FROM bronze.crm_prd_info
WHERE prd_id IS NOT NULL;

-- CRM 销售明细清洗
CREATE TABLE IF NOT EXISTS silver.crm_sales_details (
    sls_ord_num  STRING,
    sls_prd_key  STRING,
    sls_cust_id  STRING,
    sls_order_dt STRING,
    sls_ship_dt  STRING,
    sls_due_dt   STRING,
    sls_sales    DECIMAL(18,2),
    sls_quantity INT,
    sls_price    DECIMAL(18,2),
    ingestion_date TIMESTAMP
);

INSERT OVERWRITE silver.crm_sales_details
SELECT
    sls_ord_num,
    sls_prd_key,
    sls_cust_id,
    CASE WHEN LENGTH(sls_order_dt) != 8 OR CAST(sls_order_dt AS INT) <= 0
         THEN NULL ELSE sls_order_dt END                     AS sls_order_dt,
    CASE WHEN LENGTH(sls_ship_dt)  != 8 OR CAST(sls_ship_dt  AS INT) <= 0
         THEN NULL ELSE sls_ship_dt  END                     AS sls_ship_dt,
    CASE WHEN LENGTH(sls_due_dt)   != 8 OR CAST(sls_due_dt   AS INT) <= 0
         THEN NULL ELSE sls_due_dt   END                     AS sls_due_dt,
    CASE WHEN sls_sales IS NULL OR CAST(sls_sales AS DECIMAL(18,2)) <= 0
         THEN CAST(sls_quantity AS INT) * ABS(CAST(sls_price AS DECIMAL(18,2)))
         ELSE CAST(sls_sales AS DECIMAL(18,2))
    END                                                      AS sls_sales,
    CAST(sls_quantity AS INT)                                AS sls_quantity,
    CASE WHEN sls_price IS NULL OR CAST(sls_price AS DECIMAL(18,2)) <= 0
         THEN CAST(sls_sales AS DECIMAL(18,2)) / NULLIF(CAST(sls_quantity AS INT), 0)
         ELSE CAST(sls_price AS DECIMAL(18,2))
    END                                                      AS sls_price,
    CURRENT_TIMESTAMP()                                      AS ingestion_date
FROM bronze.crm_sales_details
WHERE sls_ord_num IS NOT NULL;
