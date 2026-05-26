#!/usr/bin/env python3
"""
spark2lakehouse-medallion 一键初始化脚本

执行顺序：
  1. 连接 ClickZetta Lakehouse
  2. 创建 bronze / silver / gold schema
  3. 创建 Volume（<schema>.medallion_vol）
  4. 上传 datasets/engineering/ 下的 CSV 文件到 Volume（保留子目录结构）

完成后按顺序运行 03_lakehouse/ 下的 notebooks：
  init_lakehouse.ipynb          ← 可跳过（本脚本已完成相同工作）
  01_bronze/bronze.ipynb
  02_silver/silver_orchestration.ipynb
  03_gold/gold_orchestration.ipynb
  04_validate.ipynb

用法：
  pip install clickzetta_zettapark_python python-dotenv
  cp .env.sample .env  # 填写连接信息
  python setup.py
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    import clickzetta
except ImportError:
    print("请先安装依赖: pip install clickzetta_zettapark_python python-dotenv")
    sys.exit(1)

# ── 配置 ────────────────────────────────────────────────────────────────────

SCHEMA_NAME   = os.environ.get("CLICKZETTA_SCHEMA", "public")
VOLUME_NAME   = os.environ.get("CLICKZETTA_VOLUME", "medallion_vol")
VOLUME_ID     = f"{SCHEMA_NAME}.{VOLUME_NAME}"

DATASETS_DIR  = Path(__file__).parent / "datasets" / "engineering"

# ── 连接 ────────────────────────────────────────────────────────────────────

def get_conn():
    required = ["CLICKZETTA_SERVICE", "CLICKZETTA_INSTANCE", "CLICKZETTA_WORKSPACE",
                "CLICKZETTA_USERNAME", "CLICKZETTA_PASSWORD", "CLICKZETTA_SCHEMA"]
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
        schema=SCHEMA_NAME,
        vcluster=os.environ.get("CLICKZETTA_VCLUSTER", "default_ap"),
    )

# ── Schema & Volume ──────────────────────────────────────────────────────────

def create_schemas(cur):
    print("\n[1/3] 创建 Schema")
    for schema in ["bronze", "silver", "gold"]:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        print(f"      {schema}  OK")


def create_volume(cur):
    print(f"\n[2/3] 创建 Volume: {VOLUME_ID}")
    cur.execute(f"USE SCHEMA {SCHEMA_NAME}")
    cur.execute(f"CREATE VOLUME IF NOT EXISTS {VOLUME_ID}")
    print(f"      OK")

# ── 上传数据集 ───────────────────────────────────────────────────────────────

def upload_datasets(cur):
    print(f"\n[3/3] 上传数据集到 Volume（{DATASETS_DIR.relative_to(Path(__file__).parent)}）")
    cur.execute(f"USE SCHEMA {SCHEMA_NAME}")

    if not DATASETS_DIR.exists():
        print(f"      [WARN] {DATASETS_DIR} 不存在，跳过上传")
        return

    files = sorted(DATASETS_DIR.rglob("*.csv"))
    if not files:
        print(f"      [WARN] 未找到 CSV 文件")
        return

    for f in files:
        rel    = f.relative_to(DATASETS_DIR)
        dest   = str(rel).replace("\\", "/")   # Windows 兼容
        subdir = str(rel.parent) if str(rel.parent) != "." else ""
        print(f"      PUT {dest} ...", end=" ", flush=True)
        if subdir:
            cur.execute(f"PUT '{f.resolve()}' TO VOLUME {VOLUME_NAME} SUBDIRECTORY '{subdir}'")
        else:
            cur.execute(f"PUT '{f.resolve()}' TO VOLUME {VOLUME_NAME} FILE '{f.name}'")
        print("OK")

# ── 主流程 ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("spark2lakehouse-medallion 初始化")
    print(f"  Service  : {os.environ.get('CLICKZETTA_SERVICE', '(未设置)')}")
    print(f"  Instance : {os.environ.get('CLICKZETTA_INSTANCE', '(未设置)')}")
    print(f"  Workspace: {os.environ.get('CLICKZETTA_WORKSPACE', '(未设置)')}")
    print(f"  Schema   : {SCHEMA_NAME}")
    print(f"  Volume   : {VOLUME_ID}")
    print("=" * 60)

    print("\n连接 Lakehouse ...", end=" ", flush=True)
    conn = get_conn()
    cur = conn.cursor()
    print("OK")

    try:
        create_schemas(cur)
        create_volume(cur)
        upload_datasets(cur)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        cur.close()
        conn.close()
        sys.exit(1)

    cur.close()
    conn.close()

    print("\n" + "=" * 60)
    print("初始化完成！接下来按顺序运行 notebooks：")
    print()
    print("  jupyter notebook  # 或 jupyter lab")
    print()
    print("  1. 03_lakehouse/01_bronze/bronze.ipynb")
    print("  2. 03_lakehouse/02_silver/silver_orchestration.ipynb")
    print("  3. 03_lakehouse/03_gold/gold_orchestration.ipynb")
    print("  4. 04_validate.ipynb")
    print("=" * 60)


if __name__ == "__main__":
    main()
