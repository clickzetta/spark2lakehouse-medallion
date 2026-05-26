#!/usr/bin/env python3
"""Bronze layer: load raw CSVs from Volume into bronze schema tables.

Volume path format for ZettaPark: vol://schema.volume_name/subpath/file.csv
All columns loaded as STRING — Silver layer handles type casting.
"""

from clickzetta.zettapark.session import Session
from clickzetta.zettapark.types import StructType, StructField, StringType


def _str(*cols):
    return StructType([StructField(c, StringType()) for c in cols])


SCHEMAS = {
    "source_crm/cust_info.csv": _str(
        "cst_id", "cst_key", "cst_firstname", "cst_lastname",
        "cst_marital_status", "cst_gndr", "cst_create_date",
    ),
    "source_crm/prd_info.csv": _str(
        "prd_id", "prd_key", "prd_nm", "prd_cost", "prd_line",
        "prd_start_dt", "prd_end_dt",
    ),
    "source_crm/sales_details.csv": _str(
        "sls_ord_num", "sls_prd_key", "sls_cust_id",
        "sls_order_dt", "sls_ship_dt", "sls_due_dt",
        "sls_sales", "sls_quantity", "sls_price",
    ),
    "source_erp/CUST_AZ12.csv": _str("cid", "bdate", "gen"),
    "source_erp/LOC_A101.csv":  _str("cid", "cntry"),
    "source_erp/PX_CAT_G1V2.csv": _str("id", "cat", "subcat", "maintenance"),
}

TABLES = {
    "source_crm/cust_info.csv":     "crm_cust_info",
    "source_crm/prd_info.csv":      "crm_prd_info",
    "source_crm/sales_details.csv": "crm_sales_details",
    "source_erp/CUST_AZ12.csv":     "erp_cust_az12",
    "source_erp/LOC_A101.csv":      "erp_loc_a101",
    "source_erp/PX_CAT_G1V2.csv":   "erp_px_cat_g1v2",
}


def run(session: Session, volume_uri_base: str, schema: str):
    """
    volume_uri_base: e.g. "vol://your_schema.medallion_vol"
    """
    for csv_rel, table_name in TABLES.items():
        csv_path = f"{volume_uri_base}/{csv_rel}"
        target = f"{schema}.{table_name}"
        print(f"  Loading {csv_rel} → {target} ...", end=" ", flush=True)
        df = (session.read
              .option("header", "true")
              .schema(SCHEMAS[csv_rel])
              .csv(csv_path))
        df.write.save_as_table(target, mode="overwrite")
        print("OK")
