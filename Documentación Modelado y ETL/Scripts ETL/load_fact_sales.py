import pandas as pd
import mysql.connector
import os

# =========================
# CONFIGURACIÓN
# =========================
ORDER_ITEMS_CSV = "olist_order_items_dataset.csv"
ORDERS_CSV = "olist_orders_dataset.csv"
CUSTOMERS_CSV = "olist_customers_dataset.csv"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": os.getenv("MYSQL_PASSWORD"),  
    "database": "tfg_olist_dw",
    "port": 3306
}

def main():

    # =========================
    # 1) LEER CSVs
    # =========================
    # Se cargan los datasets necesarios para construir la fact table
    order_items = pd.read_csv(ORDER_ITEMS_CSV)
    orders = pd.read_csv(ORDERS_CSV)
    customers = pd.read_csv(CUSTOMERS_CSV)

    # =========================
    # 2) CONVERTIR COLUMNAS DE FECHA A DATETIME
    # =========================
    # Se transforman todas las fechas relevantes del pedido
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

    # =========================
    # 3) JOIN order_items + orders
    # =========================
    # Se añaden datos del pedido a cada línea de producto
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

    # =========================
    # 4) JOIN CON CLIENTES
    # =========================
    # Se añade el customer_unique_id necesario para enlazar con dim_customer
    df = df.merge(
        customers[["customer_id", "customer_unique_id"]],
        on="customer_id",
        how="left",
    )

    # =========================
    # 5) OBTENER CLAVES SUSTITUTAS DE DIMENSIONES
    # =========================
    # Se conecta a la base de datos para leer las dimensiones
    conn = mysql.connector.connect(**DB_CONFIG)

    dim_customer = pd.read_sql(
        "SELECT customer_sk, customer_unique_id FROM dim_customer",
        conn
    )
    dim_product = pd.read_sql(
        "SELECT product_sk, product_id FROM dim_product",
        conn
    )

    # =========================
    # 6) JOIN CON DIMENSIONES
    # =========================
    # Se reemplazan claves naturales por claves sustitutas (SK)
    df = df.merge(dim_customer, on="customer_unique_id", how="left")
    df = df.merge(dim_product, on="product_id", how="left")

    # =========================
    # 7) CREAR date_sk
    # =========================
    # Se genera la clave de fecha (YYYYMMDD) para enlazar con dim_date
    df["date_sk"] = pd.to_numeric(
        df["order_purchase_timestamp"].dt.strftime("%Y%m%d"),
        errors="coerce"
    )

    # =========================
    # 8) CONSTRUIR FACT TABLE
    # =========================
    # Grano: 1 fila = 1 producto dentro de un pedido (order_item_id)
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

    # =========================
    # 9) CONVERTIR NaN A None
    # =========================
    # MySQL necesita NULL en lugar de NaN
    fact = fact.astype(object).where(fact.notna(), None)

    # =========================
    # 10) VACIAR TABLA (RECARGA COMPLETA)
    # =========================
    cur = conn.cursor()
    cur.execute("DELETE FROM fact_sales;")
    conn.commit()

    # =========================
    # 11) INSERT MASIVO
    # =========================
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

    # =========================
    # 12) CERRAR CONEXIONES
    # =========================
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()