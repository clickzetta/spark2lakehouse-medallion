#!/usr/bin/env python3
"""Silver layer (CRM): clean and normalize CRM bronze tables."""

from clickzetta.zettapark.session import Session
from clickzetta.zettapark import functions as F
from clickzetta.zettapark.types import DateType


def _trim_strings(df, session):
    """Trim all string columns."""
    from clickzetta.zettapark.types import StringType
    for field in df.schema.fields:
        if isinstance(field.datatype, StringType):
            df = df.with_column(field.name, F.trim(F.col(field.name)))
    return df


def silver_crm_cust_info(session: Session, src_schema: str, tgt_schema: str):
    print("  silver.crm_customers ...", end=" ", flush=True)
    df = session.table(f"{src_schema}.crm_cust_info")
    df = _trim_strings(df, session)

    df = (df
        .with_column("cst_marital_status",
            F.when(F.upper(F.col("cst_marital_status")) == "S", F.lit("Single"))
             .when(F.upper(F.col("cst_marital_status")) == "M", F.lit("Married"))
             .otherwise(F.lit("n/a")))
        .with_column("cst_gndr",
            F.when(F.upper(F.col("cst_gndr")) == "F", F.lit("Female"))
             .when(F.upper(F.col("cst_gndr")) == "M", F.lit("Male"))
             .otherwise(F.lit("n/a")))
        .filter(F.col("cst_id").is_not_null())
    )

    rename_map = {
        "cst_id":           "customer_id",
        "cst_key":          "customer_number",
        "cst_firstname":    "first_name",
        "cst_lastname":     "last_name",
        "cst_marital_status": "marital_status",
        "cst_gndr":         "gender",
        "cst_create_date":  "created_date",
    }
    for old, new in rename_map.items():
        df = df.with_column_renamed(old, new)

    df.write.save_as_table(f"{tgt_schema}.crm_customers", mode="overwrite")
    print("OK")


def silver_crm_prd_info(session: Session, src_schema: str, tgt_schema: str):
    print("  silver.crm_products ...", end=" ", flush=True)
    df = session.table(f"{src_schema}.crm_prd_info")
    df = _trim_strings(df, session)

    df = (df
        .with_column("cat_id",
            F.regexp_replace(F.substring(F.col("prd_key"), 1, 5), F.lit("-"), F.lit("_")))
        .with_column("prd_key",
            F.substring(F.col("prd_key"), 7, F.length(F.col("prd_key"))))
        .with_column("prd_cost",
            F.coalesce(F.col("prd_cost"), F.lit(0)))
        .with_column("prd_line",
            F.when(F.upper(F.col("prd_line")) == "M", F.lit("Mountain"))
             .when(F.upper(F.col("prd_line")) == "R", F.lit("Road"))
             .when(F.upper(F.col("prd_line")) == "S", F.lit("Other Sales"))
             .when(F.upper(F.col("prd_line")) == "T", F.lit("Touring"))
             .otherwise(F.lit("n/a")))
        .with_column("prd_start_dt", F.col("prd_start_dt").cast(DateType()))
    )

    rename_map = {
        "prd_id":       "product_id",
        "cat_id":       "category_id",
        "prd_key":      "product_number",
        "prd_nm":       "product_name",
        "prd_cost":     "product_cost",
        "prd_line":     "product_line",
        "prd_start_dt": "start_date",
        "prd_end_dt":   "end_date",
    }
    for old, new in rename_map.items():
        df = df.with_column_renamed(old, new)

    df.write.save_as_table(f"{tgt_schema}.crm_products", mode="overwrite")
    print("OK")


def silver_crm_sales_details(session: Session, src_schema: str, tgt_schema: str):
    print("  silver.crm_sales ...", end=" ", flush=True)
    df = session.table(f"{src_schema}.crm_sales_details")
    df = _trim_strings(df, session)

    df = (df
        .with_column("sls_order_dt",
            F.when(
                (F.col("sls_order_dt") == 0) | (F.length(F.col("sls_order_dt").cast("string")) != 8),
                F.lit(None).cast(DateType())
            ).otherwise(F.to_date(F.col("sls_order_dt").cast("string"), "yyyyMMdd")))
        .with_column("sls_ship_dt",
            F.when(
                (F.col("sls_ship_dt") == 0) | (F.length(F.col("sls_ship_dt").cast("string")) != 8),
                F.lit(None).cast(DateType())
            ).otherwise(F.to_date(F.col("sls_ship_dt").cast("string"), "yyyyMMdd")))
        .with_column("sls_due_dt",
            F.when(
                (F.col("sls_due_dt") == 0) | (F.length(F.col("sls_due_dt").cast("string")) != 8),
                F.lit(None).cast(DateType())
            ).otherwise(F.to_date(F.col("sls_due_dt").cast("string"), "yyyyMMdd")))
        .with_column("sls_price",
            F.when(
                F.col("sls_price").is_null() | (F.col("sls_price") <= 0),
                F.when(F.col("sls_quantity") != 0,
                       F.col("sls_sales") / F.col("sls_quantity"))
                 .otherwise(F.lit(None))
            ).otherwise(F.col("sls_price")))
    )

    rename_map = {
        "sls_ord_num":  "order_number",
        "sls_prd_key":  "product_number",
        "sls_cust_id":  "customer_id",
        "sls_order_dt": "order_date",
        "sls_ship_dt":  "ship_date",
        "sls_due_dt":   "due_date",
        "sls_sales":    "sales_amount",
        "sls_quantity": "quantity",
        "sls_price":    "price",
    }
    for old, new in rename_map.items():
        df = df.with_column_renamed(old, new)

    df.write.save_as_table(f"{tgt_schema}.crm_sales", mode="overwrite")
    print("OK")


def run(session: Session, src_schema: str = "mcp_demo", tgt_schema: str = "mcp_demo"):
    silver_crm_cust_info(session, src_schema, tgt_schema)
    silver_crm_prd_info(session, src_schema, tgt_schema)
    silver_crm_sales_details(session, src_schema, tgt_schema)
