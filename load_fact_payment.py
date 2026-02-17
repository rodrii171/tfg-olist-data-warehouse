import pandas as pd
import mysql.connector

PAYMENTS_CSV = "olist_order_payments_dataset.csv"
ORDERS_CSV = "olist_orders_dataset.csv"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "PASSWORD", 
    "database": "tfg_olist_dw",
    "port": 3306
}

def main():
    payments = pd.read_csv(PAYMENTS_CSV)
    orders = pd.read_csv(ORDERS_CSV)

    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )

    df = payments.merge(
        orders[["order_id", "order_purchase_timestamp"]],
        on="order_id",
        how="left"
    )

    df["date_sk"] = pd.to_numeric(
        df["order_purchase_timestamp"].dt.strftime("%Y%m%d"),
        errors="coerce"
    )

    fact = df[[
        "date_sk",
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value"
    ]].copy()

  
    fact = fact.astype(object).where(fact.notna(), None)

    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

   
    cur.execute("DELETE FROM fact_payment;")
    conn.commit()

    insert_sql = """
        INSERT INTO fact_payment
        (
            date_sk,
            order_id,
            payment_sequential,
            payment_type,
            payment_installments,
            payment_value
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    data = list(fact.itertuples(index=False, name=None))
    cur.executemany(insert_sql, data)
    conn.commit()

    print("fact_payment cargada en MySQL:", cur.rowcount, "filas")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()