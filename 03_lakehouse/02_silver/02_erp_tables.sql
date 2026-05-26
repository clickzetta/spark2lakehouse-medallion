-- ClickZetta Lakehouse SQL
-- Silver 层：ERP 数据清洗
-- 对应原始：script/silver/erp/silver_erp_*.ipynb

CREATE SCHEMA IF NOT EXISTS silver;

-- ERP 客户信息清洗
CREATE TABLE IF NOT EXISTS silver.erp_cust_az12 (
    cid     STRING,
    bdate   DATE,
    gen     STRING,
    ingestion_date TIMESTAMP
);

INSERT OVERWRITE silver.erp_cust_az12
SELECT
    CASE WHEN cid LIKE 'NAS%' THEN REPLACE(cid, 'NAS', '') ELSE cid END AS cid,
    CASE
        WHEN TRY_TO_DATE(bdate, 'M/d/yyyy') > CURRENT_DATE() THEN NULL
        ELSE TRY_TO_DATE(bdate, 'M/d/yyyy')
    END                                                                   AS bdate,
    CASE
        WHEN UPPER(TRIM(gen)) IN ('F', 'FEMALE') THEN 'Female'
        WHEN UPPER(TRIM(gen)) IN ('M', 'MALE')   THEN 'Male'
        ELSE 'n/a'
    END                                                                   AS gen,
    CURRENT_TIMESTAMP()                                                   AS ingestion_date
FROM bronze.erp_cust_az12
WHERE cid IS NOT NULL;

-- ERP 地区信息清洗
CREATE TABLE IF NOT EXISTS silver.erp_loc_a101 (
    cid     STRING,
    cntry   STRING,
    ingestion_date TIMESTAMP
);

INSERT OVERWRITE silver.erp_loc_a101
SELECT
    REPLACE(cid, '-', '')                                                 AS cid,
    CASE
        WHEN TRIM(cntry) = 'DE'  THEN 'Germany'
        WHEN TRIM(cntry) = 'US'  THEN 'United States'
        WHEN TRIM(cntry) = 'US ' THEN 'United States'
        WHEN TRIM(cntry) = ''    THEN 'n/a'
        WHEN cntry IS NULL       THEN 'n/a'
        ELSE TRIM(cntry)
    END                                                                   AS cntry,
    CURRENT_TIMESTAMP()                                                   AS ingestion_date
FROM bronze.erp_loc_a101;

-- ERP 产品分类清洗
CREATE TABLE IF NOT EXISTS silver.erp_px_cat_g1v2 (
    id          STRING,
    cat         STRING,
    subcat      STRING,
    maintenance STRING,
    ingestion_date TIMESTAMP
);

INSERT OVERWRITE silver.erp_px_cat_g1v2
SELECT
    id,
    cat,
    subcat,
    maintenance,
    CURRENT_TIMESTAMP() AS ingestion_date
FROM bronze.erp_px_cat_g1v2
WHERE id IS NOT NULL;
