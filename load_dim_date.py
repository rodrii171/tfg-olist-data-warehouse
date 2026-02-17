import pandas as pd
import mysql.connector
from datetime import datetime
import os

# =========================
# CONFIGURACIÓN
# =========================
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
    # 1) LEER CSV DE PEDIDOS
    # =========================
    # Se carga el dataset de pedidos para extraer el rango de fechas
    orders = pd.read_csv(ORDERS_CSV)

    # =========================
    # 2) CONVERTIR A DATETIME
    # =========================
    # Se convierte el timestamp de compra a tipo fecha/hora real
    # errors="coerce" convierte valores inválidos en NaT sin romper el script
    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )

    # =========================
    # 3) RANGO DE FECHAS
    # =========================
    # Se obtiene la fecha mínima y máxima del dataset
    # Esto permite generar un calendario completo solo para el periodo necesario
    min_date = orders["order_purchase_timestamp"].min().date()
    max_date = orders["order_purchase_timestamp"].max().date()

    print("Rango fechas (compra):", min_date, "->", max_date)

    # =========================
    # 4) GENERAR CALENDARIO
    # =========================
    # Se crea una fila por cada día entre min_date y max_date
    dim_date = pd.DataFrame({
        "full_date": pd.date_range(start=min_date, end=max_date, freq="D")
    })

    dim_date["date_sk"] = dim_date["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["full_date"].dt.year
    dim_date["month"] = dim_date["full_date"].dt.month
    dim_date["day"] = dim_date["full_date"].dt.day
    dim_date["quarter"] = dim_date["full_date"].dt.quarter
    dim_date["week_of_year"] = dim_date["full_date"].dt.isocalendar().week.astype(int)
    dim_date["day_of_week"] = dim_date["full_date"].dt.dayofweek + 1  

    
    dim_date["full_date"] = dim_date["full_date"].dt.date

    print("Filas dim_date generadas:", len(dim_date))
    print(dim_date.head())

    # =========================
    # 5) CONEXIÓN MYSQL
    # =========================
    # Se establece conexión con la base de datos del Data Warehouse
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    # =========================
    # 6) RECARGA COMPLETA
    # =========================
    # Se eliminan los datos anteriores antes de insertar los nuevos
    cur.execute("DELETE FROM dim_date;")
    conn.commit()

    # =========================
    # 7) INSERT MASIVO
    # =========================
    # Se define la sentencia SQL de inserción
    insert_sql = """
        INSERT INTO dim_date
        (date_sk, full_date, year, month, day, quarter, week_of_year, day_of_week)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    data = list(dim_date[[
        "date_sk", "full_date", "year", "month", "day", "quarter", "week_of_year", "day_of_week"
    ]].itertuples(index=False, name=None))

    cur.executemany(insert_sql, data)
    conn.commit()

    print("dim_date cargada en MySQL:", cur.rowcount, "filas")
    
    # =========================
    # 9) CERRAR CONEXIÓN
    # =========================
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()