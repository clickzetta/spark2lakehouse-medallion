#!/usr/bin/env python3
"""
spark2lakehouse-medallion 一键初始化脚本

执行顺序：
  1. 连接 ClickZetta Lakehouse（ZettaPark Session）
  2. 创建 Volume（mcp_demo.medallion_vol）
  3. 上传 datasets/engineering/ 所有 CSV 到 Volume
  4. Bronze：从 Volume 读取 CSV → 写入 bronze 表
  5. Silver：清洗 CRM + ERP 数据
  6. Gold：构建维度表 + 事实表

用法：
  pip install clickzetta_zettapark_python python-dotenv
  cp .env.sample .env  # 填写连接信息
  python setup.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    import clickzetta
    from clickzetta.zettapark.session import Session
except ImportError:
    print("请先安装依赖: pip install clickzetta_zettapark_python python-dotenv")
    sys.exit(1)

# ── 配置 ────────────────────────────────────────────────────────────────────

SCHEMA_NAME      = "mcp_demo"
VOLUME_NAME      = "medallion_vol"
VOLUME_ID        = f"{SCHEMA_NAME}.{VOLUME_NAME}"   # used for DDL (CREATE/DROP)
VOLUME_REF       = VOLUME_NAME                      # used for PUT (no schema prefix)
VOLUME_PATH      = f"/Volumes/quick_start/{SCHEMA_NAME}/{VOLUME_NAME}"
VOLUME_URI_BASE  = f"vol://{SCHEMA_NAME}.{VOLUME_NAME}"  # ZettaPark read path

DATASETS_DIR = Path(__file__).parent / "datasets" / "engineering"

# ── 连接 ────────────────────────────────────────────────────────────────────

def get_session() -> Session:
    required = ["CLICKZETTA_SERVICE", "CLICKZETTA_INSTANCE", "CLICKZETTA_WORKSPACE",
                "CLICKZETTA_USERNAME", "CLICKZETTA_PASSWORD"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"[ERROR] .env 缺少必填项: {', '.join(missing)}")
        sys.exit(1)

    params = {
        "service":   os.environ["CLICKZETTA_SERVICE"],
        "instance":  os.environ["CLICKZETTA_INSTANCE"],
        "workspace": os.environ["CLICKZETTA_WORKSPACE"],
        "username":  os.environ["CLICKZETTA_USERNAME"],
        "password":  os.environ["CLICKZETTA_PASSWORD"],
        "schema":    os.environ.get("CLICKZETTA_SCHEMA", SCHEMA_NAME),
        "vcluster":  os.environ.get("CLICKZETTA_VCLUSTER", "default_ap"),
    }
    return Session.builder.configs(params).create()


# ── Volume 操作（需要 connector cursor，ZettaPark 不直接支持 DDL/PUT） ──────

def get_cursor():
    import clickzetta as cz
    return cz.connect(
        service=os.environ["CLICKZETTA_SERVICE"],
        instance=os.environ["CLICKZETTA_INSTANCE"],
        workspace=os.environ["CLICKZETTA_WORKSPACE"],
        username=os.environ["CLICKZETTA_USERNAME"],
        password=os.environ["CLICKZETTA_PASSWORD"],
        schema=os.environ.get("CLICKZETTA_SCHEMA", SCHEMA_NAME),
        vcluster=os.environ.get("CLICKZETTA_VCLUSTER", "default_ap"),
    ).cursor()


def create_volume(cur):
    print(f"\n[1/4] 创建 Volume: {VOLUME_ID}")
    cur.execute(f"CREATE VOLUME IF NOT EXISTS {VOLUME_ID}")
    print(f"      OK → {VOLUME_PATH}")


def upload_datasets(cur):
    print(f"\n[2/4] 上传数据集到 Volume")
    csv_files = sorted(DATASETS_DIR.rglob("*.csv"))
    if not csv_files:
        print(f"      [WARN] {DATASETS_DIR} 下没有找到 CSV 文件")
        return

    for csv_path in csv_files:
        rel = csv_path.relative_to(DATASETS_DIR)
        subdir = str(rel.parent) if str(rel.parent) != "." else ""
        abs_path = str(csv_path.resolve())

        if subdir:
            sql = f"PUT '{abs_path}' TO VOLUME {VOLUME_REF} SUBDIRECTORY '{subdir}'"
        else:
            sql = f"PUT '{abs_path}' TO VOLUME {VOLUME_REF}"

        print(f"      PUT {rel} ...", end=" ", flush=True)
        cur.execute(sql)
        print("OK")


# ── ZettaPark 层执行 ─────────────────────────────────────────────────────────

def run_bronze(session: Session):
    print(f"\n[3/4] Bronze 层")
    sys.path.insert(0, str(Path(__file__).parent / "03_lakehouse" / "01_bronze"))
    import bronze
    bronze.run(session, VOLUME_URI_BASE, SCHEMA_NAME)


def run_silver(session: Session):
    print(f"\n[4/4] Silver 层")
    sys.path.insert(0, str(Path(__file__).parent / "03_lakehouse" / "02_silver"))
    import silver_crm, silver_erp
    silver_crm.run(session, SCHEMA_NAME, SCHEMA_NAME)
    silver_erp.run(session, SCHEMA_NAME, SCHEMA_NAME)


def run_gold(session: Session):
    print(f"\n[5/5] Gold 层")
    sys.path.insert(0, str(Path(__file__).parent / "03_lakehouse" / "03_gold"))
    import gold
    gold.run(session, SCHEMA_NAME)


# ── 主流程 ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("spark2lakehouse-medallion 初始化")
    print(f"  Service  : {os.environ.get('CLICKZETTA_SERVICE', '(未设置)')}")
    print(f"  Instance : {os.environ.get('CLICKZETTA_INSTANCE', '(未设置)')}")
    print(f"  Workspace: {os.environ.get('CLICKZETTA_WORKSPACE', '(未设置)')}")
    print(f"  Schema   : {SCHEMA_NAME}")
    print(f"  Volume   : {VOLUME_ID}  →  {VOLUME_PATH}")
    print("=" * 60)

    # Volume 操作用 connector cursor
    print("\n连接 Lakehouse (connector) ...", end=" ", flush=True)
    cur = get_cursor()
    print("OK")

    try:
        create_volume(cur)
        upload_datasets(cur)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        cur.close()
        sys.exit(1)
    cur.close()

    # ZettaPark Session 执行数据转换
    print("\n连接 Lakehouse (ZettaPark) ...", end=" ", flush=True)
    session = get_session()
    print("OK")

    try:
        run_bronze(session)
        run_silver(session)
        run_gold(session)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        session.close()
        sys.exit(1)

    session.close()
    print("\n" + "=" * 60)
    print("初始化完成！")
    print(f"  Bronze: crm_cust_info / crm_prd_info / crm_sales_details")
    print(f"          erp_cust_az12 / erp_loc_a101 / erp_px_cat_g1v2")
    print(f"  Silver: crm_customers / crm_products / crm_sales")
    print(f"          erp_customers / erp_customer_location / erp_product_category")
    print(f"  Gold  : dim_customers / dim_products / fact_sales")
    print("=" * 60)


if __name__ == "__main__":
    main()
