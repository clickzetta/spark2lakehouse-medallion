-- ClickZetta Lakehouse SQL
-- Bronze 层：ERP 数据摄取
-- 对应原始：script/bronze/bronze_layer(basic).ipynb（ERP 部分）

CREATE SCHEMA IF NOT EXISTS bronze;

-- ERP 客户信息
CREATE TABLE IF NOT EXISTS bronze.erp_cust_az12 (
    cid     STRING,
    bdate   STRING,
    gen     STRING,
    ingestion_date TIMESTAMP
);

COPY INTO bronze.erp_cust_az12 (cid, bdate, gen, ingestion_date)
FROM (
    SELECT $1, $2, $3, CURRENT_TIMESTAMP()
    FROM '<volume_path>/source_erp/CUST_AZ12.csv'
)
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true');

-- ERP 地区信息
CREATE TABLE IF NOT EXISTS bronze.erp_loc_a101 (
    cid     STRING,
    cntry   STRING,
    ingestion_date TIMESTAMP
);

COPY INTO bronze.erp_loc_a101 (cid, cntry, ingestion_date)
FROM (
    SELECT $1, $2, CURRENT_TIMESTAMP()
    FROM '<volume_path>/source_erp/LOC_A101.csv'
)
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true');

-- ERP 产品分类
CREATE TABLE IF NOT EXISTS bronze.erp_px_cat_g1v2 (
    id          STRING,
    cat         STRING,
    subcat      STRING,
    maintenance STRING,
    ingestion_date TIMESTAMP
);

COPY INTO bronze.erp_px_cat_g1v2 (id, cat, subcat, maintenance, ingestion_date)
FROM (
    SELECT $1, $2, $3, $4, CURRENT_TIMESTAMP()
    FROM '<volume_path>/source_erp/PX_CAT_G1V2.csv'
)
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true');
