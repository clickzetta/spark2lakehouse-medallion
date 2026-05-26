# 迁移概述

## Medallion Architecture 迁移思路

Medallion Architecture（铜/银/金三层架构）与 ClickZetta Lakehouse 的分层数仓设计天然对齐：

| Medallion 层 | Lakehouse 对应层 | 主要工作 |
|-------------|----------------|---------|
| Bronze | ODS（原始数据层） | 从 Volume 读取 CSV → 写入 bronze 表 |
| Silver | DWD（明细数据层） | DataFrame 清洗、去重、标准化 |
| Gold | DWS/ADS（汇总/应用层） | DataFrame join + 维度建模 |

## 迁移工作量评估

| 层次 | 原始代码量 | 迁移难度 | 主要改动 |
|------|-----------|---------|---------|
| Bronze | 2 个 Notebook | 低 | `spark.read.csv(path)` → `session.read.csv("vol://...")`，路径格式不同，schema 自动推断 |
| Silver | 6 个 Notebook | 低 | `withColumn` → `with_column`，其余逻辑完全一致 |
| Gold | 3 个 Notebook + 1 个编排 | 低 | `Window` 需从独立模块导入，其余一致 |

**结论：本项目涉及的 PySpark DataFrame API 全部可迁移到 ZettaPark，无需改写任何业务逻辑，全程使用 DataFrame API（无 SQL 回退）。两侧代码结构完全对称，差异仅限于：连接方式（SparkSession → ZettaPark Session）、CSV 路径格式（本地/DBFS → `vol://`）、Window 模块导入路径，以及方法命名风格（camelCase → snake_case）。**

## 关键迁移模式

### 1. Bronze 层：数据摄取

```python
# 原始 PySpark
df = spark.read.format("csv").option("header", True).load(path)
df.write.format("delta").mode("overwrite").saveAsTable("bronze.cust_info")
```

```python
# ZettaPark（路径格式不同，支持自动推断 schema，其余一致）
df = session.read.option("header", "true").csv("vol://public.medallion_vol/source_crm/cust_info.csv")
df.write.save_as_table("bronze.crm_cust_info", mode="overwrite")
```

### 2. Silver 层：数据清洗

```python
# 原始 PySpark
cleaned = (
    df.withColumn("gender", F.when(F.col("cst_gndr") == "M", "Male")
                              .when(F.col("cst_gndr") == "F", "Female")
                              .otherwise("n/a"))
      .dropDuplicates(["cst_id"])
)
```

```python
# ZettaPark（仅命名风格差异，逻辑完全一致）
cleaned = (
    df.with_column("gender", F.when(F.col("cst_gndr") == "M", "Male")
                               .when(F.col("cst_gndr") == "F", "Female")
                               .otherwise("n/a"))
      .drop_duplicates(["cst_id"])
)
```

### 3. Gold 层：维度建模

```python
# 原始 PySpark
from pyspark.sql.window import Window
window = Window.partitionBy("cst_id").orderBy(F.col("cst_create_date").desc())
deduped = df.withColumn("flag", F.row_number().over(window)).filter(F.col("flag") == 1)
```

```python
# ZettaPark（Window 导入路径不同，其余一致）
from clickzetta.zettapark.window import Window
window = Window.partition_by("cst_id").order_by(F.col("cst_create_date").desc())
deduped = df.with_column("flag", F.row_number().over(window)).filter(F.col("flag") == 1)
```

## API 兼容性速查

| PySpark 用法 | ZettaPark 等价写法 | 兼容性 |
|-------------|------------------|--------|
| `spark.read.csv(path)` | `session.read.csv("vol://schema.vol/path")` | ✅ 路径格式不同 |
| `df.withColumn(name, expr)` | `df.with_column(name, expr)` | ✅ 下划线命名风格 |
| `df.withColumnRenamed(old, new)` | `df.with_column_renamed(old, new)` | ✅ 同上 |
| `df.dropDuplicates(cols)` | `df.drop_duplicates(cols)` | ✅ 同上 |
| `df.write.mode("overwrite").saveAsTable(t)` | `df.write.save_as_table(t, mode="overwrite")` | ✅ 参数位置略有调整 |
| `F.when().otherwise()` | `F.when().otherwise()` | ✅ 完全一致 |
| `F.col() / F.lit() / F.trim()` 等 | 同名函数 | ✅ 完全一致 |
| `df.filter() / select() / join()` | 同名方法 | ✅ 完全一致 |
| `spark.sql(query)` | `session.sql(query)` | ✅ 完全一致（本项目全程 DataFrame API） |
| `from pyspark.sql.window import Window` | `from clickzetta.zettapark.window import Window` | ✅ 导入路径不同 |
| `schema.inferSchema = True` | `session.read.option("header","true").csv(path)` | ✅ 支持自动推断，无需显式声明 |
