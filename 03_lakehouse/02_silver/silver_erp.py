#!/usr/bin/env python3
"""Silver layer (ERP): clean and normalize ERP bronze tables."""

from clickzetta.zettapark.session import Session
from clickzetta.zettapark import functions as F


def _trim_strings(df):
    from clickzetta.zettapark.types import StringType
    for field in df.schema.fields:
        if isinstance(field.datatype, StringType):
            df = df.with_column(field.name, F.trim(F.col(field.name)))
    return df


def silver_erp_cust_az12(session: Session, src_schema: str, tgt_schema: str):
    print("  silver.erp_customers ...", end=" ", flush=True)
    df = session.table(f"{src_schema}.erp_cust_az12")
    df = _trim_strings(df)

    df = (df
        .with_column("cid",
            F.when(F.col("cid").startswith("NAS"),
                   F.substring(F.col("cid"), 4, F.length(F.col("cid"))))
             .otherwise(F.col("cid")))
        .with_column("bdate",
            F.when(F.col("bdate") > F.current_date(), F.lit(None))
             .otherwise(F.col("bdate")))
        .with_column("gen",
            F.when(F.upper(F.col("gen")).isin("F", "FEMALE"), F.lit("Female"))
             .when(F.upper(F.col("gen")).isin("M", "MALE"), F.lit("Male"))
             .otherwise(F.lit("n/a")))
    )

    rename_map = {
        "cid":   "customer_number",
        "bdate": "birth_date",
        "gen":   "gender",
    }
    for old, new in rename_map.items():
        df = df.with_column_renamed(old, new)

    df.write.save_as_table(f"{tgt_schema}.erp_customers", mode="overwrite")
    print("OK")


def silver_erp_loc_a101(session: Session, src_schema: str, tgt_schema: str):
    print("  silver.erp_customer_location ...", end=" ", flush=True)
    df = session.table(f"{src_schema}.erp_loc_a101")
    df = _trim_strings(df)

    df = (df
        .with_column("cid",
            F.regexp_replace(F.col("cid"), F.lit("-"), F.lit("")))
        .with_column("cntry",
            F.when(F.col("cntry") == "DE", F.lit("Germany"))
             .when(F.col("cntry").isin("US", "USA"), F.lit("United States"))
             .when(F.col("cntry").is_null() | (F.col("cntry") == ""), F.lit("n/a"))
             .otherwise(F.col("cntry")))
    )

    rename_map = {
        "cid":   "customer_number",
        "cntry": "country",
    }
    for old, new in rename_map.items():
        df = df.with_column_renamed(old, new)

    df.write.save_as_table(f"{tgt_schema}.erp_customer_location", mode="overwrite")
    print("OK")


def silver_erp_px_cat_g1v2(session: Session, src_schema: str, tgt_schema: str):
    print("  silver.erp_product_category ...", end=" ", flush=True)
    df = session.table(f"{src_schema}.erp_px_cat_g1v2")
    df = _trim_strings(df)

    df = df.with_column("maintenance",
        F.when(F.upper(F.col("maintenance")) == "YES", F.lit(True))
         .when(F.upper(F.col("maintenance")) == "NO", F.lit(False))
         .otherwise(F.lit(None)))

    rename_map = {
        "id":          "category_id",
        "cat":         "category",
        "subcat":      "subcategory",
        "maintenance": "maintenance_flag",
    }
    for old, new in rename_map.items():
        df = df.with_column_renamed(old, new)

    df.write.save_as_table(f"{tgt_schema}.erp_product_category", mode="overwrite")
    print("OK")


def run(session: Session, src_schema: str = "mcp_demo", tgt_schema: str = "mcp_demo"):
    silver_erp_cust_az12(session, src_schema, tgt_schema)
    silver_erp_loc_a101(session, src_schema, tgt_schema)
    silver_erp_px_cat_g1v2(session, src_schema, tgt_schema)
