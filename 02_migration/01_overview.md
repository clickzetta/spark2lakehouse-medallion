# 迁移概述

## Medallion Architecture 迁移思路

Medallion Architecture（铜/银/金三层架构）与 ClickZetta Lakehouse 的分层数仓设计天然对齐：

| Medallion 层 | Lakehouse 对应层 | 主要工作 |
|-------------|----------------|---------|
| Bronze | ODS（原始数据层） | 建外部表或 COPY INTO 摄取 |
| Silver | DWD（明细数据层） | SQL 清洗、去重、标准化 |
| Gold | DWS/ADS（汇总/应用层） | SQL 维度建模、聚合 |

## 迁移工作量评估

| 层次 | 原始代码量 | 迁移难度 | 主要改动 |
|------|-----------|---------|---------|
| Bronze | 2 个 Notebook | 低 | `spark.read.csv()` → `COPY INTO` |
| Silver | 6 个 Notebook | 中 | PySpark 清洗逻辑 → SQL CASE WHEN、COALESCE |
| Gold | 3 个 Notebook + 1 个编排 | 低 | PySpark join → SQL JOIN，逻辑几乎不变 |

## 关键迁移模式

### 1. Bronze 层：数据摄取

```python
# 原始 PySpark
df = spark.read.format("csv").option("header", True).load(path)
df.write.format("delta").mode("overwrite").saveAsTable("bronze.cust_info")
```

```sql
-- Lakehouse SQL
COPY INTO bronze.cust_info
FROM '<volume_path>/cust_info.csv'
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true');
```

### 2. Silver 层：数据清洗

```python
# 原始 PySpark
df = df.withColumn("bdate", to_date(col("BDATE"), "M/d/yyyy")) \
       .filter(col("cid").startswith("NAS")) \
       .dropDuplicates(["cid"])
```

```sql
-- Lakehouse SQL
INSERT INTO silver.crm_cust_info
SELECT
    cid,
    TRY_TO_DATE(bdate, 'M/d/yyyy') AS bdate,
    ...
FROM bronze.cust_info
WHERE cid LIKE 'NAS%'
QUALIFY ROW_NUMBER() OVER (PARTITION BY cid ORDER BY ingestion_date DESC) = 1;
```

### 3. Gold 层：维度建模

```python
# 原始 PySpark
dim_customers = crm_cust.join(erp_cust, crm_cust.cid == erp_cust.cid, "left") \
                         .join(erp_loc, ...)
```

```sql
-- Lakehouse SQL
CREATE TABLE gold.dim_customers AS
SELECT ...
FROM silver.crm_cust_info c
LEFT JOIN silver.erp_cust_az12 e ON c.cid = e.cid
LEFT JOIN silver.erp_loc_a101 l ON ...;
```