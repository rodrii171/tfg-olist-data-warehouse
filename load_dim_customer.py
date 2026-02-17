import pandas as pd
import mysql.connector

CUSTOMERS_CSV = "olist_customers_dataset.csv"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "PASSWORD",
    "database": "tfg_olist_dw",
    "port": 3306
}

def main():
    
    df = pd.read_csv(CUSTOMERS_CSV)

    
    for col in ["customer_id", "customer_unique_id", "customer_city", "customer_state"]:
        df[col] = df[col].astype(str).str.strip()

   
    df_dim = df.drop_duplicates(subset=["customer_unique_id"], keep="first").copy()

    
    df_dim = df_dim[[
        "customer_unique_id",
        "customer_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state"
    ]]

    print("Filas CSV originales:", len(df))
    print("Filas dim_customer (deduplicadas):", len(df_dim))
    print(df_dim.head())

    
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    
    cur.execute("DELETE FROM dim_customer;")
    conn.commit()

    insert_sql = """
        INSERT INTO dim_customer
        (customer_unique_id, customer_id, customer_zip_code_prefix, customer_city, customer_state)
        VALUES (%s, %s, %s, %s, %s)
    """

    data = list(df_dim.itertuples(index=False, name=None))

    cur.executemany(insert_sql, data)
    conn.commit()

    print("dim_customer cargada en MySQL:", cur.rowcount, "filas")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()