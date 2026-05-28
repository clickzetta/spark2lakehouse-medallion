#!/usr/bin/env python3
"""
reset.py — drop all Lakehouse objects created by setup.py and the notebooks

Use this to start fresh or clean up after testing.

Usage:
    python reset.py
    python reset.py --dry-run   # preview without executing
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DRY_RUN = "--dry-run" in sys.argv

SCHEMA_NAME = os.environ.get("CLICKZETTA_SCHEMA", "public")
VOLUME_NAME = os.environ.get("CLICKZETTA_VOLUME", "medallion_vol")
VOLUME_ID   = f"{SCHEMA_NAME}.{VOLUME_NAME}"

try:
    import clickzetta
except ImportError:
    print("请先安装依赖: pip install clickzetta_zettapark_python python-dotenv")
    sys.exit(1)


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


def execute(cur, stmt):
    if DRY_RUN:
        print(f"  [DRY] {stmt}")
        return
    try:
        cur.execute(stmt)
        print(f"  OK: {stmt[:80]}")
    except Exception as e:
        print(f"  WARN: {e}")


def main():
    if DRY_RUN:
        print("=== DRY RUN — 不会实际删除任何对象 ===\n")

    conn = get_conn()
    cur = conn.cursor()

    try:
        print(f"删除 Volume {VOLUME_ID} ...")
        execute(cur, f"DROP VOLUME IF EXISTS {VOLUME_ID}")

        for schema in ["bronze", "silver", "gold"]:
            print(f"删除 schema {schema} (CASCADE) ...")
            execute(cur, f"DROP SCHEMA IF EXISTS {schema} CASCADE")
    finally:
        cur.close()
        conn.close()

    if DRY_RUN:
        print("\n=== DRY RUN 完成，未执行任何删除 ===")
    else:
        print("\n清理完成。重新初始化请运行: python setup.py")


if __name__ == "__main__":
    main()
