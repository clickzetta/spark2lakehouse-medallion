# Medallion 架构层次映射

## Bronze 层

| 原始 Spark Notebook | Lakehouse Notebook | 说明 |
|--------------------|-------------------|------|
| `01_spark/01_bronze/bronze_layer(basic).ipynb` | `03_lakehouse/01_bronze/bronze.ipynb` | 全部 6 张源表一次性摄取 |
| `01_spark/01_bronze/bronze_layer_(improved).ipynb` | （同上，已合并） | 改进版逻辑已内联到同一 notebook |

## Silver 层

| 原始 Spark Notebook | Lakehouse Notebook | 说明 |
|--------------------|-------------------|------|
| `01_spark/02_silver/crm/silver_crm_cust_info.ipynb` | `03_lakehouse/02_silver/crm/silver_crm_cust_info.ipynb` | 客户信息清洗 |
| `01_spark/02_silver/crm/silver_crm_prd_info.ipynb` | `03_lakehouse/02_silver/crm/silver_crm_prd_info.ipynb` | 产品信息清洗 |
| `01_spark/02_silver/crm/silver_crm_sales_details.ipynb` | `03_lakehouse/02_silver/crm/silver_crm_sales_details.ipynb` | 销售明细清洗 |
| `01_spark/02_silver/erp/silver_erp_cust_az12.ipynb` | `03_lakehouse/02_silver/erp/silver_erp_cust_az12.ipynb` | ERP 客户补充信息 |
| `01_spark/02_silver/erp/silver_erp_loc_a101.ipynb` | `03_lakehouse/02_silver/erp/silver_erp_loc_a101.ipynb` | 地区信息 |
| `01_spark/02_silver/erp/silver_erp_px_cat_g1v2.ipynb` | `03_lakehouse/02_silver/erp/silver_erp_px_cat_g1v2.ipynb` | 产品分类 |
| `01_spark/02_silver/silver_orchestration.ipynb` | `03_lakehouse/02_silver/silver_orchestration.ipynb` | 编排脚本（按序运行全部 silver） |

## Gold 层

| 原始 Spark Notebook | Lakehouse Notebook | 说明 |
|--------------------|-------------------|------|
| `01_spark/03_gold/gold_dim_customers.ipynb` | `03_lakehouse/03_gold/gold_dim_customers.ipynb` | 客户维度表 |
| `01_spark/03_gold/gold_dim_products.ipynb` | `03_lakehouse/03_gold/gold_dim_products.ipynb` | 产品维度表 |
| `01_spark/03_gold/gold_fact_sales.ipynb` | `03_lakehouse/03_gold/gold_fact_sales.ipynb` | 销售事实表 |
| `01_spark/03_gold/gold_orchestration.ipynb` | `03_lakehouse/03_gold/gold_orchestration.ipynb` | 编排脚本（按序运行全部 gold） |

## 常见 PySpark → ZettaPark 转换模式

### 去重（drop_duplicates + row_number）

```python
# PySpark
df.dropDuplicates(["cid"])

# ZettaPark
df.drop_duplicates(["cid"])
```

对于需要按优先级保留最新记录的场景：

```python
# PySpark
window = Window.partitionBy("cid").orderBy(F.col("cst_create_date").desc())
df.withColumn("flag", F.row_number().over(window)).filter(F.col("flag") == 1)

# ZettaPark
from clickzetta.zettapark.window import Window
window = Window.partition_by("cid").order_by(F.col("cst_create_date").desc())
df.with_column("flag", F.row_number().over(window)).filter(F.col("flag") == 1)
```

### 条件转换（F.when / otherwise）

```python
# PySpark
df.withColumn("gender", F.when(F.col("gen") == "F", "Female")
                          .when(F.col("gen") == "M", "Male")
                          .otherwise("n/a"))

# ZettaPark（逻辑完全一致，仅方法名加下划线）
df.with_column("gender", F.when(F.col("gen") == "F", "Female")
                           .when(F.col("gen") == "M", "Male")
                           .otherwise("n/a"))
```

### 日期解析

```python
# PySpark
df.withColumn("bdate", F.to_date(F.col("BDATE"), "M/d/yyyy"))

# ZettaPark
df.with_column("bdate", F.to_date(F.col("BDATE"), "M/d/yyyy"))
```

### NULL 处理

```python
# PySpark
df.withColumn("country", F.coalesce(F.col("country"), F.lit("n/a")))

# ZettaPark
df.with_column("country", F.coalesce(F.col("country"), F.lit("n/a")))
```

### 类型转换

```python
# PySpark
df.withColumn("price", F.col("price").cast("DECIMAL(10,2)"))

# ZettaPark
df.with_column("price", F.col("price").cast("DECIMAL(10,2)"))
```
