-- ClickZetta Lakehouse SQL
-- 对应原始：script/silver/crm/silver_crm_cust_info.ipynb
-- Silver 层：CRM 客户信息清洗
--
-- 迁移说明：
--   PySpark 的 filter/withColumn/dropDuplicates 全部用 SQL 表达
--   去重使用 QUALIFY + ROW_NUMBER() 替代 dropDuplicates()
--   日期解析使用 TRY_TO_DATE() 替代 to_date()

CREATE SCHEMA IF NOT EXISTS silver;

CREATE TABLE IF NOT EXISTS silver.crm_cust_info (
    cst_id          INT,
    cst_key         STRING,
    cst_firstname   STRING,
    cst_lastname    STRING,
    cst_marital_status STRING,
    cst_gndr        STRING,
    cst_create_date DATE,
    ingestion_date  TIMESTAMP
);

INSERT OVERWRITE silver.crm_cust_info
SELECT
    CAST(REPLACE(cid, 'NAS', '') AS INT)    AS cst_id,
    cid                                      AS cst_key,
    TRIM(SPLIT_PART(cid, '-', 1))           AS cst_firstname,
    TRIM(SPLIT_PART(cid, '-', 2))           AS cst_lastname,
    CASE
        WHEN UPPER(TRIM(gen)) = 'S' THEN 'Single'
        WHEN UPPER(TRIM(gen)) = 'M' THEN 'Married'
        ELSE 'n/a'
    END                                      AS cst_marital_status,
    CASE
        WHEN UPPER(TRIM(gen)) = 'F' THEN 'Female'
        WHEN UPPER(TRIM(gen)) = 'M' THEN 'Male'
        ELSE 'n/a'
    END                                      AS cst_gndr,
    TRY_TO_DATE(bdate, 'M/d/yyyy')          AS cst_create_date,
    CURRENT_TIMESTAMP()                      AS ingestion_date
FROM bronze.crm_cust_info
WHERE cid IS NOT NULL
  AND cid LIKE 'NAS%'
QUALIFY ROW_NUMBER() OVER (PARTITION BY cid ORDER BY ingestion_date DESC) = 1;