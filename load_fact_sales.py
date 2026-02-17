import pandas as pd
import mysql.connector

ORDER_ITEMS_CSV = "olist_order_items_dataset.csv"
ORDERS_CSV = "olist_orders_dataset.csv"
CUSTOMERS_CSV = "olist_customers_dataset.csv"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "PASSWORD",  
    "database": "tfg_olist_dw",
    "port": 3306
}

def main():
   
    order_items = pd.read_csv(ORDER_ITEMS_CSV)
    orders = pd.read_csv(ORDERS_CSV)
    customers = pd.read_csv(CUSTOMERS_CSV)

  
    order_date_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for c in order_date_cols:
        orders[c] = pd.to_datetime(orders[c], errors="coerce")

    order_items["shipping_limit_date"] = pd.to_datetime(
        order_items["shipping_limit_date"], errors="coerce"
    )

    
    df = order_items.merge(
        orders[
            [
                "order_id",
                "customer_id",
                "order_status",
                "order_purchase_timestamp",
                "order_approved_at",
                "order_delivered_carrier_date",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ]
        ],
        on="order_id",
        how="left",
    )

  
    df = df.merge(
        customers[["customer_id", "customer_unique_id"]],
        on="customer_id",
        how="left",
    )

    
    conn = mysql.connector.connect(**DB_CONFIG)

    dim_customer = pd.read_sql(
        "SELECT customer_sk, customer_unique_id FROM dim_customer",
        conn
    )
    dim_product = pd.read_sql(
        "SELECT product_sk, product_id FROM dim_product",
        conn
    )

   
    df = df.merge(dim_customer, on="customer_unique_id", how="left")
    df = df.merge(dim_product, on="product_id", how="left")

   
    df["date_sk"] = pd.to_numeric(
        df["order_purchase_timestamp"].dt.strftime("%Y%m%d"),
        errors="coerce"
    )

    
    fact = df[
        [
            "customer_sk",
            "product_sk",
            "date_sk",
            "order_id",
            "order_item_id",
            "seller_id",
            "shipping_limit_date",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
            "price",
            "freight_value",
        ]
    ].copy()

    
    fact = fact.astype(object).where(fact.notna(), None)

  
    cur = conn.cursor()
    cur.execute("DELETE FROM fact_sales;")
    conn.commit()

    
    insert_sql = """
        INSERT INTO fact_sales
        (
            customer_sk,
            product_sk,
            date_sk,
            order_id,
            order_item_id,
            seller_id,
            shipping_limit_date,
            order_status,
            order_purchase_timestamp,
            order_approved_at,
            order_delivered_carrier_date,
            order_delivered_customer_date,
            order_estimated_delivery_date,
            price,
            freight_value
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    data = list(fact.itertuples(index=False, name=None))
    cur.executemany(insert_sql, data)
    conn.commit()

    print("fact_sales cargada en MySQL:", cur.rowcount, "filas")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()