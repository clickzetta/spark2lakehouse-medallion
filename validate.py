#!/usr/bin/env python3
"""
迁移验证脚本：验证 ZettaPark 迁移后的数据质量和业务逻辑正确性。

检查项：
  1. 行数合理性（各层行数符合预期）
  2. Bronze → Silver 行数一致性（Silver 不应无故丢行）
  3. 关键列无空值（主键、外键）
  4. Silver 数据清洗效果（gender/marital_status 标准化）
  5. Gold 维度完整性（dim 表无重复 surrogate key）
  6. Gold 事实表关联完整性（fact_sales 外键均能关联到 dim）
  7. 业务指标合理性（销售额 > 0，数量 > 0）

用法：
  python validate.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from clickzetta.zettapark.session import Session
except ImportError:
    print("Install: pip install clickzetta_zettapark_python python-dotenv")
    sys.exit(1)

SCHEMA = os.environ.get("CLICKZETTA_SCHEMA", "")

if not SCHEMA:
    print("[ERROR] .env 缺少 CLICKZETTA_SCHEMA，请填写目标 schema 名称")
    sys.exit(1)

PASS = "✓"
FAIL = "✗"

results = []


def get_session() -> Session:
    params = {
        "service":   os.environ["CLICKZETTA_SERVICE"],
        "instance":  os.environ["CLICKZETTA_INSTANCE"],
        "workspace": os.environ["CLICKZETTA_WORKSPACE"],
        "username":  os.environ["CLICKZETTA_USERNAME"],
        "password":  os.environ["CLICKZETTA_PASSWORD"],
        "schema":    SCHEMA,
        "vcluster":  os.environ.get("CLICKZETTA_VCLUSTER", "default_ap"),
    }
    return Session.builder.configs(params).create()


def check(session, name: str, sql: str, expect_zero: bool = True, desc: str = "", warn_only: bool = False):
    """Run a validation query. Pass if result is 0 (expect_zero=True) or >0 (expect_zero=False).
    warn_only=True: report as warning (WARN) instead of failure — for known source data issues.
    """
    rows = session.sql(sql).collect()
    val = rows[0][0] if rows else 0
    passed = (val == 0) if expect_zero else (val > 0)
    if passed:
        status = PASS
    elif warn_only:
        status = "⚠"
    else:
        status = FAIL
    results.append((status, name, val, desc))
    print(f"  {status}  {name:<55} {val}")
    return passed


def run_checks(session):
    s = SCHEMA

    print("\n── 1. 行数合理性 ──────────────────────────────────────────")
    check(session, "Bronze crm_cust_info 有数据",
          f"SELECT COUNT(*) FROM {s}.crm_cust_info",
          expect_zero=False, desc="应 > 0")
    check(session, "Bronze crm_sales_details 有数据",
          f"SELECT COUNT(*) FROM {s}.crm_sales_details",
          expect_zero=False)
    check(session, "Gold fact_sales 有数据",
          f"SELECT COUNT(*) FROM {s}.fact_sales",
          expect_zero=False)

    print("\n── 2. Bronze → Silver 行数一致性 ──────────────────────────")
    check(session, "Silver crm_customers 行数 ≤ Bronze crm_cust_info",
          f"""SELECT CASE WHEN
              (SELECT COUNT(*) FROM {s}.crm_customers) >
              (SELECT COUNT(*) FROM {s}.crm_cust_info)
          THEN 1 ELSE 0 END""",
          expect_zero=True, desc="Silver 不应多于 Bronze")
    check(session, "Silver crm_sales 行数 = Bronze crm_sales_details",
          f"""SELECT ABS(
              (SELECT COUNT(*) FROM {s}.crm_sales) -
              (SELECT COUNT(*) FROM {s}.crm_sales_details))""",
          expect_zero=True, desc="销售明细不应丢行")

    print("\n── 3. 关键列无空值 ────────────────────────────────────────")
    check(session, "Silver crm_customers.customer_id 无空值",
          f"SELECT COUNT(*) FROM {s}.crm_customers WHERE customer_id IS NULL")
    check(session, "Silver crm_customers.customer_number 无空值",
          f"SELECT COUNT(*) FROM {s}.crm_customers WHERE customer_number IS NULL")
    check(session, "Silver crm_sales.order_number 无空值",
          f"SELECT COUNT(*) FROM {s}.crm_sales WHERE order_number IS NULL")
    check(session, "Gold dim_customers.customer_key 无空值",
          f"SELECT COUNT(*) FROM {s}.dim_customers WHERE customer_key IS NULL")
    check(session, "Gold dim_products.product_key 无空值",
          f"SELECT COUNT(*) FROM {s}.dim_products WHERE product_key IS NULL")

    print("\n── 4. Silver 数据清洗效果 ─────────────────────────────────")
    check(session, "crm_customers.gender 只含标准值",
          f"""SELECT COUNT(*) FROM {s}.crm_customers
              WHERE gender NOT IN ('Male','Female','n/a')""")
    check(session, "crm_customers.marital_status 只含标准值",
          f"""SELECT COUNT(*) FROM {s}.crm_customers
              WHERE marital_status NOT IN ('Single','Married','n/a')""")
    check(session, "erp_customers.gender 只含标准值",
          f"""SELECT COUNT(*) FROM {s}.erp_customers
              WHERE gender NOT IN ('Male','Female','n/a')""")
    check(session, "erp_customer_location.country 无空字符串",
          f"SELECT COUNT(*) FROM {s}.erp_customer_location WHERE country = ''")

    print("\n── 5. Gold 维度完整性 ─────────────────────────────────────")
    check(session, "dim_customers.customer_key 无重复",
          f"""SELECT COUNT(*) FROM (
              SELECT customer_key, COUNT(*) AS n FROM {s}.dim_customers
              GROUP BY customer_key HAVING n > 1)""")
    check(session, "dim_products.product_key 无重复",
          f"""SELECT COUNT(*) FROM (
              SELECT product_key, COUNT(*) AS n FROM {s}.dim_products
              GROUP BY product_key HAVING n > 1)""")
    check(session, "dim_customers.customer_id 无重复",
          f"""SELECT COUNT(*) FROM (
              SELECT customer_id, COUNT(*) AS n FROM {s}.dim_customers
              GROUP BY customer_id HAVING n > 1)""",
          warn_only=True, desc="源数据 crm_cust_info 本身存在重复 customer_id")

    print("\n── 6. fact_sales 外键关联完整性 ───────────────────────────")
    check(session, "fact_sales 中 product_key 均存在于 dim_products",
          f"""SELECT COUNT(*) FROM {s}.fact_sales f
              LEFT JOIN {s}.dim_products p ON f.product_key = p.product_key
              WHERE f.product_key IS NOT NULL AND p.product_key IS NULL""")
    check(session, "fact_sales 中 customer_key 均存在于 dim_customers",
          f"""SELECT COUNT(*) FROM {s}.fact_sales f
              LEFT JOIN {s}.dim_customers c ON f.customer_key = c.customer_key
              WHERE f.customer_key IS NOT NULL AND c.customer_key IS NULL""")

    print("\n── 7. 业务指标合理性 ──────────────────────────────────────")
    check(session, "crm_sales.sales_amount 无负值",
          f"SELECT COUNT(*) FROM {s}.crm_sales WHERE sales_amount < 0",
          warn_only=True, desc="源数据存在负值（退货/冲销单），非迁移问题")
    check(session, "crm_sales.quantity 无零或负值",
          f"SELECT COUNT(*) FROM {s}.crm_sales WHERE quantity <= 0")
    check(session, "dim_customers 有 country 信息的比例 > 50%",
          f"""SELECT CASE WHEN
              (SELECT COUNT(*) FROM {s}.dim_customers WHERE country IS NOT NULL AND country <> 'n/a') * 100.0 /
              NULLIF((SELECT COUNT(*) FROM {s}.dim_customers), 0) < 50
          THEN 1 ELSE 0 END""",
          expect_zero=True, desc="超过 50% 客户应有国家信息")


def main():
    print("=" * 65)
    print("spark2lakehouse-medallion 迁移验证")
    print(f"  Schema: {SCHEMA}")
    print("=" * 65)

    print("\n连接 Lakehouse ...", end=" ", flush=True)
    session = get_session()
    print("OK\n")

    try:
        run_checks(session)
    finally:
        session.close()

    passed = sum(1 for r in results if r[0] == PASS)
    warned = sum(1 for r in results if r[0] == "⚠")
    failed = sum(1 for r in results if r[0] == FAIL)
    total = len(results)

    print("\n" + "=" * 65)
    print(f"验证结果: {passed}/{total} 通过", end="")
    if warned:
        print(f"  {warned} 项源数据质量警告", end="")
    if failed:
        print(f"  {failed} 项失败")
        print("\n失败项：")
        for status, name, val, desc in results:
            if status == FAIL:
                print(f"  {FAIL}  {name}  (值={val}  {desc})")
    else:
        print("  — 迁移验证全部通过")
    if warned:
        print("\n源数据质量警告（非迁移问题）：")
        for status, name, val, desc in results:
            if status == "⚠":
                print(f"  ⚠  {name}  (值={val})  {desc}")
    print("=" * 65)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
