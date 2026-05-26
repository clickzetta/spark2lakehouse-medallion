-- ClickZetta Lakehouse SQL
-- 对应原始：script/bronze/bronze_layer(basic).ipynb
-- Bronze 层：CRM 数据摄取
--
-- 迁移说明：
--   原始使用 spark.read.csv() 读取文件，写入 Delta 表
--   Lakehouse 使用 COPY INTO 或 CREATE TABLE AS SELECT 摄取 CSV
--   替换 <volume_path> 为实际的 External Volume 路径

CREATE SCHEMA IF NOT EXISTS bronze;

-- 客户信息
CREATE TABLE IF NOT EXISTS bronze.crm_cust_info (
    cid         STRING,
    bdate       STRING,
    gen         STRING,
    ingestion_date TIMESTAMP
);

COPY INTO bronze.crm_cust_info (cid, bdate, gen, ingestion_date)
FROM (
    SELECT $1, $2, $3, CURRENT_TIMESTAMP()
    FROM '<volume_path>/source_crm/cust_info.csv'
)
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true', 'delimiter' = ',');

-- 产品信息
CREATE TABLE IF NOT EXISTS bronze.crm_prd_info (
    prd_id      STRING,
    prd_key     STRING,
    prd_nm      STRING,
    prd_cost    STRING,
    prd_line    STRING,
    prd_start_dt STRING,
    prd_end_dt  STRING,
    ingestion_date TIMESTAMP
);

COPY INTO bronze.crm_prd_info
FROM (
    SELECT $1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP()
    FROM '<volume_path>/source_crm/prd_info.csv'
)
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true');

-- 销售明细
CREATE TABLE IF NOT EXISTS bronze.crm_sales_details (
    sls_ord_num  STRING,
    sls_prd_key  STRING,
    sls_cust_id  STRING,
    sls_order_dt STRING,
    sls_ship_dt  STRING,
    sls_due_dt   STRING,
    sls_sales    STRING,
    sls_quantity STRING,
    sls_price    STRING,
    ingestion_date TIMESTAMP
);

COPY INTO bronze.crm_sales_details
FROM (
    SELECT $1, $2, $3, $4, $5, $6, $7, $8, $9, CURRENT_TIMESTAMP()
    FROM '<volume_path>/source_crm/sales_details.csv'
)
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true');