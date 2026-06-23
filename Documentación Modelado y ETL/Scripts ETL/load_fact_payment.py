import pandas as pd
import mysql.connector
import os

# =========================
# CONFIGURACIÓN
# =========================
PAYMENTS_CSV = "olist_order_payments_dataset.csv"
ORDERS_CSV = "olist_orders_dataset.csv"

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
    # Se cargan los datasets de pagos y pedidos
    payments = pd.read_csv(PAYMENTS_CSV)
    orders = pd.read_csv(ORDERS_CSV)

    # =========================
    # 2) CONVERTIR FECHA DE COMPRA A DATETIME
    # =========================
    # Se transforma el timestamp para poder calcular date_sk
    # errors="coerce" convierte valores inválidos en NaT (nulo) sin romper el script
    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )

    # =========================
    # 3) JOIN PAYMENTS + ORDERS
    # =========================
    # Se hace un LEFT JOIN para añadir la fecha de compra (order_purchase_timestamp)
    # a cada registro de pago usando order_id como clave
    df = payments.merge(
        orders[["order_id", "order_purchase_timestamp"]],
        on="order_id",
        how="left"
    )

    # =========================
    # 4) CREAR date_sk (YYYYMMDD)
    # =========================
    # Se crea la clave de fecha para conectar con dim_date
    # Ejemplo: 2018-01-05 -> 20180105
    df["date_sk"] = pd.to_numeric(
        df["order_purchase_timestamp"].dt.strftime("%Y%m%d"),
        errors="coerce"
    )

    # =========================
    # 5) CONSTRUIR FACT TABLE
    # =========================
    # Se seleccionan los campos necesarios para fact_payment
    # Grano: 1 fila = 1 pago de un pedido (payment_sequential)
    fact = df[[
        "date_sk",
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value"
    ]].copy()

    # =========================
    # 6) CONVERTIR NaN A None
    # =========================
    # MySQL necesita NULL, no NaN
    fact = fact.astype(object).where(fact.notna(), None)

    # =========================
    # 7) CONECTAR A MYSQL
    # =========================
    # Se establece conexión con la base de datos del Data Warehouse
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    # =========================
    # 8) VACIAR TABLA (RECARGA COMPLETA)
    # =========================
    # Se eliminan los datos anteriores antes de insertar los nuevos
    cur.execute("DELETE FROM fact_payment;")
    conn.commit()

    # =========================
    # 9) INSERT MASIVO
    # =========================
    # Se define la sentencia SQL de inserción
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

    # =========================
    # 10) CERRAR CONEXIONES
    # =========================
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()