# spark2lakehouse-medallion

> **Spark SQL → ClickZetta Lakehouse 迁移示例**

本项目 fork 自 [DataWithBaraa/databricks_bootcamp_2026](https://github.com/DataWithBaraa/databricks_bootcamp_2026)（MIT License），在保留原始 Databricks Notebook 代码的基础上，新增了对应的 **ClickZetta Lakehouse SQL 实现**和**迁移说明文档**。

## 项目结构

```
├── spark/              # 📦 原始 Databricks Notebooks（PySpark，只读参考）
│   ├── 01_bronze/      #   Bronze 层：spark.read.csv() → Delta 写入
│   ├── 02_silver/      #   Silver 层：DataFrame filter/withColumn/dropDuplicates
│   └── 03_gold/        #   Gold 层：DataFrame join + 聚合
│
├── lakehouse/          # ✅ 迁移后的 ClickZetta Lakehouse SQL
│   ├── 01_bronze/      #   COPY INTO 替代 spark.read.csv()
│   ├── 02_silver/      #   INSERT OVERWRITE + QUALIFY 替代 dropDuplicates()
│   └── 03_gold/        #   纯 SQL 维度表 + 事实表
│
├── migration/          # 📖 迁移说明文档
│   ├── 01_overview.md          迁移策略与关键差异
│   └── 02_medallion_mapping.md 逐层语法对照
│
├── datasets/           # 原始数据集（CRM + ERP CSV 文件）
├── setup.py            # 🚀 一键初始化（创建 Volume、上传数据、执行 SQL）
└── .env.sample         # 连接配置模板
```

## 数据架构

| 层次 | 说明 | 原始实现 | Lakehouse 实现 |
|------|------|---------|---------------|
| Bronze | 原始数据，不做转换 | PySpark 读 CSV → 写 Delta | `COPY INTO` 或 `CREATE TABLE AS SELECT` |
| Silver | 清洗、去重、标准化 | PySpark DataFrame 转换 | 纯 SQL `INSERT INTO SELECT` |
| Gold | 维度建模（dim/fact） | PySpark join + 聚合 | 纯 SQL 维度表 + 事实表 |

## 数据源

- **CRM 系统**：客户信息（cust_info）、产品信息（prd_info）、销售明细（sales_details）
- **ERP 系统**：客户补充信息（CUST_AZ12）、地区信息（LOC_A101）、产品分类（PX_CAT_G1V2）

## 快速开始

1. 阅读 [迁移概述](migration/01_overview.md)
2. 参考 [Medallion 架构映射](migration/02_medallion_mapping.md)
3. 按照 [逐步迁移指南](migration/03_step_by_step.md) 执行

## 原始项目

- 原始作者：[DataWithBaraa](https://github.com/DataWithBaraa)
- 原始 Repo：[databricks_bootcamp_2026](https://github.com/DataWithBaraa/databricks_bootcamp_2026)
- License：MIT
- 技术栈：Databricks、PySpark、Delta Lake、Unity Catalog