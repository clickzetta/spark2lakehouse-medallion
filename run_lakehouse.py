#!/usr/bin/env python3
"""Run individual Lakehouse ZettaPark layers against ClickZetta Lakehouse.

Usage:
  python run_lakehouse.py [bronze|silver|gold]   # run one layer
  python run_lakehouse.py                         # run all layers
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from clickzetta.zettapark.session import Session
except ImportError:
    print("Install: pip install clickzetta_zettapark_python python-dotenv")
    sys.exit(1)

SCHEMA_NAME = "mcp_demo"
VOLUME_URI_BASE = f"vol://{SCHEMA_NAME}.medallion_vol"

BASE = Path(__file__).parent / "03_lakehouse"


def get_session() -> Session:
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


def run_bronze(session):
    sys.path.insert(0, str(BASE / "01_bronze"))
    import bronze
    bronze.run(session, VOLUME_URI_BASE, SCHEMA_NAME)


def run_silver(session):
    sys.path.insert(0, str(BASE / "02_silver"))
    import silver_crm, silver_erp
    silver_crm.run(session, SCHEMA_NAME, SCHEMA_NAME)
    silver_erp.run(session, SCHEMA_NAME, SCHEMA_NAME)


def run_gold(session):
    sys.path.insert(0, str(BASE / "03_gold"))
    import gold
    gold.run(session, SCHEMA_NAME)


LAYERS = {
    "bronze": run_bronze,
    "silver": run_silver,
    "gold":   run_gold,
}


def main():
    layer = sys.argv[1] if len(sys.argv) > 1 else None
    if layer and layer not in LAYERS:
        print(f"Unknown layer '{layer}'. Choose from: {', '.join(LAYERS)}")
        sys.exit(1)

    print(f"Connecting to {os.environ['CLICKZETTA_SERVICE']} ...")
    session = get_session()

    try:
        if layer:
            print(f"\n── {layer.upper()} ──")
            LAYERS[layer](session)
        else:
            for name, fn in LAYERS.items():
                print(f"\n── {name.upper()} ──")
                fn(session)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        session.close()
        sys.exit(1)

    session.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
