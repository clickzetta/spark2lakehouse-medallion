# spark2lakehouse-medallion

> **Spark SQL → ClickZetta Lakehouse 迁移示例**

本项目 fork 自 [DataWithBaraa/databricks_bootcamp_2026](https://github.com/DataWithBaraa/databricks_bootcamp_2026)（MIT License），在保留原始 Databricks Notebook 代码的基础上，新增了对应的 **ClickZetta ZettaPark Python 实现**和**迁移说明文档**。原始代码使用 PySpark DataFrame API，迁移后使用 ZettaPark（ClickZetta 的 Python DataFrame 框架），API 几乎一一对应。

## 项目结构

```
├── 01_spark/           # 📦 原始 Databricks Notebooks（PySpark，只读参考）
│   ├── 01_bronze/      #   Bronze 层：spark.read.csv() → Delta 写入
│   ├── 02_silver/      #   Silver 层：DataFrame filter/withColumn/dropDuplicates
│   └── 03_gold/        #   Gold 层：DataFrame join + 聚合
│
├── 02_migration/       # 📖 迁移说明文档
│   ├── 01_overview.md          迁移策略与关键差异
│   └── 02_medallion_mapping.md 逐层语法对照
│
├── 03_lakehouse/       # ✅ 迁移后的 ClickZetta ZettaPark Python
│   ├── 01_bronze/      #   bronze.py：从 Volume 读取 CSV → 写入 bronze 表
│   ├── 02_silver/      #   silver_crm.py / silver_erp.py：清洗 + 标准化
│   └── 03_gold/        #   gold.py：dim_customers / dim_products / fact_sales
│
├── datasets/           # 原始数据集（CRM + ERP CSV 文件）
├── setup.py            # 🚀 一键初始化（创建 Volume、上传数据、执行全流程）
├── validate.py         # ✔️  迁移验证（22 项数据质量检查）
└── .env.sample         # 连接配置模板
```

## 数据架构

| 层次 | 说明 | 原始实现 | Lakehouse 实现 |
|------|------|---------|---------------|
| Bronze | 原始数据，不做转换 | PySpark 读 CSV → 写 Delta | ZettaPark `session.read.csv()` → `save_as_table()` |
| Silver | 清洗、去重、标准化 | PySpark DataFrame 转换 | ZettaPark `with_column()` + `F.when()` |
| Gold | 维度建模（dim/fact） | PySpark join + 聚合 | ZettaPark `df.join()` + `F.row_number()` |

## 数据源

- **CRM 系统**：客户信息（cust_info）、产品信息（prd_info）、销售明细（sales_details）
- **ERP 系统**：客户补充信息（CUST_AZ12）、地区信息（LOC_A101）、产品分类（PX_CAT_G1V2）

## 快速开始

1. 安装依赖：`pip install clickzetta_zettapark_python python-dotenv`
2. 复制配置：`cp .env.sample .env`，填写 ClickZetta 连接信息
3. 一键初始化：`python setup.py`
   - 自动创建 Volume、上传数据集、执行 Bronze → Silver → Gold 全流程
4. 验证迁移结果：`python validate.py`

或按层单独运行：`python run_lakehouse.py [bronze|silver|gold]`

阅读 [迁移概述](02_migration/01_overview.md) 和 [Medallion 架构映射](02_migration/02_medallion_mapping.md) 了解迁移细节。

## 迁移验证

`validate.py` 对迁移结果执行 22 项自动化检查：

| 检查类别 | 内容 |
|---------|------|
| 行数合理性 | 各层表有数据，行数符合预期 |
| Bronze → Silver 一致性 | Silver 不丢行，销售明细完整 |
| 关键列无空值 | 主键、外键均不为 NULL |
| 数据清洗效果 | gender / marital_status / country 标准化正确 |
| 维度完整性 | surrogate key 无重复 |
| 外键完整性 | fact_sales 所有外键均能关联到 dim 表 |
| 业务指标合理性 | 数量 > 0，country 覆盖率 > 50% |

实际运行结果：**20/22 通过，迁移逻辑全部正确**。2 项警告为源数据本身的质量问题（非迁移引入）：
- `crm_cust_info` 原始数据存在 5 组重复 `customer_id`
- `crm_sales_details` 存在 3 条负销售额（退货/冲销单）

## 原始项目

- 原始作者：[DataWithBaraa](https://github.com/DataWithBaraa)
- 原始 Repo：[databricks_bootcamp_2026](https://github.com/DataWithBaraa/databricks_bootcamp_2026)
- License：MIT
- 技术栈：Databricks、PySpark、Delta Lake、Unity Catalog