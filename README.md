# spark2lakehouse-medallion

> **Spark SQL → ClickZetta Lakehouse 迁移示例**

本项目 fork 自 [DataWithBaraa/databricks_bootcamp_2026](https://github.com/DataWithBaraa/databricks_bootcamp_2026)（MIT License），在保留原始 Databricks Notebook 代码的基础上，新增了对应的 **ClickZetta Lakehouse SQL 实现**和**迁移说明文档**。

## 项目结构

```
├── datasets/           # 原始数据集（CRM + ERP CSV 文件）
├── script/             # 原始 Databricks Notebooks（PySpark）
│   ├── bronze/         #   Bronze 层：原始数据摄取
│   ├── silver/         #   Silver 层：数据清洗与标准化
│   └── gold/           #   Gold 层：维度建模
├── lakehouse/          # ✅ Lakehouse 实现（ClickZetta SQL）
│   ├── bronze/         #   Bronze 层 SQL
│   ├── silver/         #   Silver 层 SQL
│   └── gold/           #   Gold 层 SQL
└── migration/          # ✅ 迁移说明文档
    ├── 01_overview.md
    ├── 02_medallion_mapping.md
    └── 03_step_by_step.md
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