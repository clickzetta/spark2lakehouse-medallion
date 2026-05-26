#!/usr/bin/env python3
"""Gold layer: build dimensional model (dim_customers, dim_products, fact_sales).

Uses session.sql() — mirrors the original spark.sql() pattern in the PySpark notebooks.
"""

from clickzetta.zettapark.session import Session


def gold_dim_customers(session: Session, schema: str):
    print("  gold.dim_customers ...", end=" ", flush=True)
    df = session.sql(f"""
        SELECT
            ROW_NUMBER() OVER (ORDER BY ci.customer_id) AS customer_key,
            ci.customer_id,
            ci.customer_number,
            ci.first_name,
            ci.last_name,
            la.country,
            ci.marital_status,
            CASE WHEN ci.gender <> 'n/a' THEN ci.gender
                 ELSE COALESCE(ca.gender, 'n/a')
            END AS gender,
            ca.birth_date AS birthdate,
            ci.created_date AS create_date
        FROM {schema}.crm_customers ci
        LEFT JOIN {schema}.erp_customers ca
            ON ci.customer_number = ca.customer_number
        LEFT JOIN {schema}.erp_customer_location la
            ON ci.customer_number = la.customer_number
    """)
    df.write.save_as_table(f"{schema}.dim_customers", mode="overwrite")
    print("OK")


def gold_dim_products(session: Session, schema: str):
    print("  gold.dim_products ...", end=" ", flush=True)
    df = session.sql(f"""
        SELECT
            ROW_NUMBER() OVER (ORDER BY pn.start_date, pn.product_number) AS product_key,
            pn.product_id,
            pn.product_number,
            pn.product_name,
            pn.category_id,
            pc.category,
            pc.subcategory,
            pc.maintenance_flag,
            pn.product_line,
            pn.start_date
        FROM {schema}.crm_products pn
        LEFT JOIN {schema}.erp_product_category pc
            ON pn.category_id = pc.category_id
    """)
    df.write.save_as_table(f"{schema}.dim_products", mode="overwrite")
    print("OK")


def gold_fact_sales(session: Session, schema: str):
    print("  gold.fact_sales ...", end=" ", flush=True)
    df = session.sql(f"""
        SELECT
            sd.order_number,
            pr.product_key,
            cu.customer_key,
            sd.order_date,
            sd.ship_date,
            sd.due_date,
            sd.sales_amount,
            sd.quantity,
            sd.price
        FROM {schema}.crm_sales sd
        LEFT JOIN {schema}.dim_products pr
            ON sd.product_number = pr.product_number
        LEFT JOIN {schema}.dim_customers cu
            ON sd.customer_id = cu.customer_id
    """)
    df.write.save_as_table(f"{schema}.fact_sales", mode="overwrite")
    print("OK")


def run(session: Session, schema: str = "mcp_demo"):
    gold_dim_customers(session, schema)
    gold_dim_products(session, schema)
    gold_fact_sales(session, schema)
