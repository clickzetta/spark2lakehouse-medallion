#!/usr/bin/env python3
"""
spark2lakehouse-medallion 一键初始化脚本

执行顺序：
  1. 连接 ClickZetta Lakehouse
  2. 创建 Volume（mcp_demo.medallion_vol）
  3. 上传 datasets/engineering/ 所有 CSV 到 Volume
  4. 执行 lakehouse/bronze/*.sql
  5. 执行 lakehouse/silver/*.sql
  6. 执行 lakehouse/gold/*.sql

用法：
  pip install clickzetta-connector-python python-dotenv
  cp .env.sample .env  # 填写连接信息
  python setup.py
"""

import os
import sys
import glob
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    import clickzetta
except ImportError:
    print("请先安装依赖: pip install clickzetta-connector-python python-dotenv")
    sys.exit(1)

# ── 配置 ────────────────────────────────────────────────────────────────────

SCHEMA_NAME   = "mcp_demo"
VOLUME_NAME   = "medallion_vol"
VOLUME_ID     = f"{SCHEMA_NAME}.{VOLUME_NAME}"
VOLUME_PATH   = f"/Volumes/quick_start/{SCHEMA_NAME}/{VOLUME_NAME}"

DATASETS_DIR  = Path(__file__).parent / "datasets" / "engineering"
LAKEHOUSE_DIR = Path(__file__).parent / "lakehouse"

SQL_LAYERS = ["01_bronze", "02_silver", "03_gold"]

# ── 连接 ────────────────────────────────────────────────────────────────────

def get_conn():
    required = ["CLICKZETTA_SERVICE", "CLICKZETTA_INSTANCE", "CLICKZETTA_WORKSPACE",
                "CLICKZETTA_USERNAME", "CLICKZETTA_PASSWORD"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"[ERROR] .env 缺少必填项: {', '.join(missing)}")
        sys.exit(1)

    return clickzetta.connect(
        service=os.environ["CLICKZETTA_SERVICE"],
        instance=os.environ["CLICKZETTA_INSTANCE"],
        workspace=os.environ["CLICKZETTA_WORKSPACE"],
        username=os.environ["CLICKZETTA_USERNAME"],
        password=os.environ["CLICKZETTA_PASSWORD"],
        schema=os.environ.get("CLICKZETTA_SCHEMA", SCHEMA_NAME),
        vcluster=os.environ.get("CLICKZETTA_VCLUSTER", "default_ap"),
    )

# ── Volume 操作 ──────────────────────────────────────────────────────────────

def create_volume(cur):
    print(f"\n[1/3] 创建 Volume: {VOLUME_ID}")
    cur.execute(f"CREATE VOLUME IF NOT EXISTS {VOLUME_ID}")
    print(f"      OK → {VOLUME_PATH}")


def upload_datasets(cur):
    print(f"\n[2/3] 上传数据集到 Volume")
    csv_files = sorted(DATASETS_DIR.rglob("*.csv"))
    if not csv_files:
        print(f"      [WARN] {DATASETS_DIR} 下没有找到 CSV 文件")
        return

    for csv_path in csv_files:
        # 保留相对于 datasets/engineering/ 的子目录结构
        rel = csv_path.relative_to(DATASETS_DIR)
        subdir = str(rel.parent) if str(rel.parent) != "." else ""
        abs_path = str(csv_path.resolve())

        if subdir:
            sql = f"PUT '{abs_path}' TO {VOLUME_ID} SUBDIRECTORY '{subdir}'"
        else:
            sql = f"PUT '{abs_path}' TO {VOLUME_ID}"

        print(f"      PUT {rel} ...", end=" ", flush=True)
        cur.execute(sql)
        print("OK")

# ── SQL 执行 ─────────────────────────────────────────────────────────────────

def run_sql_file(cur, path: Path):
    sql = path.read_text()
    # 替换 volume 路径占位符
    sql = sql.replace("<volume_path>", VOLUME_PATH)
    sql = sql.replace("<your_volume_path>", VOLUME_PATH)

    statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
    for stmt in statements:
        preview = stmt.replace("\n", " ")[:72]
        print(f"      SQL: {preview}...", end=" ", flush=True)
        cur.execute(stmt)
        print("OK")


def run_layers(cur):
    print(f"\n[3/3] 执行 Lakehouse SQL")
    for layer in SQL_LAYERS:
        sql_files = sorted((LAKEHOUSE_DIR / layer).glob("*.sql"))
        if not sql_files:
            print(f"      [SKIP] {layer}/ 下没有 SQL 文件")
            continue
        print(f"\n  ── {layer.upper()} ──")
        for f in sql_files:
            print(f"  {f.name}")
            run_sql_file(cur, f)

# ── 主流程 ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("spark2lakehouse-medallion 初始化")
    print(f"  Service  : {os.environ.get('CLICKZETTA_SERVICE', '(未设置)')}")
    print(f"  Instance : {os.environ.get('CLICKZETTA_INSTANCE', '(未设置)')}")
    print(f"  Workspace: {os.environ.get('CLICKZETTA_WORKSPACE', '(未设置)')}")
    print(f"  Volume   : {VOLUME_ID}  →  {VOLUME_PATH}")
    print("=" * 60)

    print("\n连接 Lakehouse ...", end=" ", flush=True)
    conn = get_conn()
    cur = conn.cursor()
    print("OK")

    try:
        create_volume(cur)
        upload_datasets(cur)
        run_layers(cur)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        cur.close()
        conn.close()
        sys.exit(1)

    cur.close()
    conn.close()
    print("\n" + "=" * 60)
    print("初始化完成！")
    print(f"  Bronze 表: bronze.crm_cust_info / crm_prd_info / crm_sales_details")
    print(f"  Silver 表: silver.crm_cust_info / erp_cust_az12 / erp_loc_a101")
    print(f"  Gold   表: gold.dim_customers")
    print("=" * 60)


if __name__ == "__main__":
    main()
