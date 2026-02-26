import pandas as pd
import mysql.connector
import os
# =========================
# CONFIGURACIÓN
# =========================

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
    # 1) LEER CSV
    # =========================
    # Se carga el dataset de clientes en un DataFrame
    
    df = pd.read_csv(CUSTOMERS_CSV)

    # =========================
    # 2) LIMPIEZA BÁSICA
    # =========================
    # Convertimos a texto y quitamos espacios
    # Evita problemas con IDs/campos con espacios "invisibles"
    for col in ["customer_id", "customer_unique_id", "customer_city", "customer_state"]:
        df[col] = df[col].astype(str).str.strip()

    # =========================
    # 3) DEDUPLICAR PARA DIMENSIÓN
    # =========================
    # Nos quedamos con 1 fila por customer_unique_id (cliente real)
    # Si hay varias filas para el mismo cliente, usamos la primera
    df_dim = df.drop_duplicates(subset=["customer_unique_id"], keep="first").copy()

    # =========================
    # 4) SELECCIONAR COLUMNAS QUE CARGAMOS EN dim_customer
    # =========================
    # Se seleccionan únicamente los atributos relevantes para la dimensión
    df_dim = df_dim[[
        "customer_unique_id",
        "customer_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state"
    ]]

    # =========================
    # 5) LOGS PARA COMPROBAR
    # =========================
    # Se muestran estadísticas básicas para validar el proceso
    print("Filas CSV originales:", len(df))
    print("Filas dim_customer (deduplicadas):", len(df_dim))
    print(df_dim.head())

    # =========================
    # 6) CONECTAR A MYSQL
    # =========================
    # Se establece conexión con la base de datos del Data Warehouse
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    # =========================
    # 7) VACIAR TABLA (RECARGA COMPLETA)
    # =========================
    # Se eliminan los datos anteriores antes de insertar los nuevos
    cur.execute("DELETE FROM dim_customer;")
    conn.commit()

    # =========================
    # 8) INSERT MASIVO
    # =========================
    # Se define la sentencia SQL de inserción
    insert_sql = """
        INSERT INTO dim_customer
        (customer_unique_id, customer_id, customer_zip_code_prefix, customer_city, customer_state)
        VALUES (%s, %s, %s, %s, %s)
    """

    data = list(df_dim.itertuples(index=False, name=None))

    cur.executemany(insert_sql, data)
    conn.commit()

    print("dim_customer cargada en MySQL:", cur.rowcount, "filas")

    # =========================
    # 9) CERRAR CONEXIONES
    # =========================
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()