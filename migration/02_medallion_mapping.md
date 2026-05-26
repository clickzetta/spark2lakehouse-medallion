# Medallion 架构层次映射

## Bronze 层

| 原始 Notebook | Lakehouse 文件 | 说明 |
|--------------|---------------|------|
| `script/bronze/bronze_layer(basic).ipynb` | `lakehouse/bronze/01_load_crm.sql` | CRM 数据摄取 |
| `script/bronze/bronze_layer_(improved).ipynb` | `lakehouse/bronze/02_load_erp.sql` | ERP 数据摄取（改进版，含 schema 校验） |

## Silver 层

| 原始 Notebook | Lakehouse 文件 | 说明 |
|--------------|---------------|------|
| `script/silver/crm/silver_crm_cust_info.ipynb` | `lakehouse/silver/01_crm_cust_info.sql` | 客户信息清洗 |
| `script/silver/crm/silver_crm_prd_info.ipynb` | `lakehouse/silver/02_crm_prd_info.sql` | 产品信息清洗 |
| `script/silver/crm/silver_crm_sales_details.ipynb` | `lakehouse/silver/03_crm_sales_details.sql` | 销售明细清洗 |
| `script/silver/erp/silver_erp_cust_az12.ipynb` | `lakehouse/silver/04_erp_cust_az12.sql` | ERP 客户补充信息 |
| `script/silver/erp/silver_erp_loc_a101.ipynb` | `lakehouse/silver/05_erp_loc_a101.sql` | 地区信息 |
| `script/silver/erp/silver_erp_px_cat_g1v2.ipynb` | `lakehouse/silver/06_erp_px_cat.sql` | 产品分类 |

## Gold 层

| 原始 Notebook | Lakehouse 文件 | 说明 |
|--------------|---------------|------|
| `script/gold/gold_dim_customers.ipynb` | `lakehouse/gold/01_dim_customers.sql` | 客户维度表 |
| `script/gold/gold_dim_products.ipynb` | `lakehouse/gold/02_dim_products.sql` | 产品维度表 |
| `script/gold/gold_fact_sales.ipynb` | `lakehouse/gold/03_fact_sales.sql` | 销售事实表 |
| `script/gold/gold_orchestration.ipynb` | `lakehouse/gold/00_orchestration.sql` | 编排脚本 |

## 常见 PySpark → SQL 转换模式

### 去重（QUALIFY + ROW_NUMBER）

```python
# PySpark
df.dropDuplicates(["cid"])
```

```sql
-- Lakehouse SQL
SELECT * FROM t
QUALIFY ROW_NUMBER() OVER (PARTITION BY cid ORDER BY ingestion_date DESC) = 1
```

### 条件转换（CASE WHEN）

```python
# PySpark
df.withColumn("gender", when(col("gen") == "F", "Female")
                        .when(col("gen") == "M", "Male")
                        .otherwise("n/a"))
```

```sql
-- Lakehouse SQL
CASE gen WHEN 'F' THEN 'Female' WHEN 'M' THEN 'Male' ELSE 'n/a' END AS gender
```

### 日期解析（TRY_TO_DATE）

```python
# PySpark
df.withColumn("bdate", to_date(col("BDATE"), "M/d/yyyy"))
```

```sql
-- Lakehouse SQL
TRY_TO_DATE(bdate, 'M/d/yyyy') AS bdate
```

### NULL 处理（COALESCE）

```python
# PySpark
df.withColumn("country", coalesce(col("country"), lit("n/a")))
```

```sql
-- Lakehouse SQL
COALESCE(country, 'n/a') AS country
```