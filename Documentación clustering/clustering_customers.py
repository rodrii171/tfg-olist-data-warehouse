import pandas as pd
import mysql.connector
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import os

# CONFIGURACIÓN DE LA CONEXIÓN
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": "tfg_olist_dw"
}

def main():

    # Conexión a MySQL
    conn = mysql.connector.connect(**DB_CONFIG)

    # 1) EXTRAER DATOS DESDE MYSQL

    query = """
    SELECT 
        c.customer_unique_id,
        COUNT(DISTINCT s.order_id) AS num_orders,
        SUM(s.price) AS total_spent,
        AVG(s.freight_value) AS avg_freight,
        AVG(DATEDIFF(s.order_delivered_customer_date, s.order_estimated_delivery_date)) AS avg_delay,
        AVG(r.review_score) AS avg_review
    FROM fact_sales s
    JOIN dim_customer c ON s.customer_sk = c.customer_sk
    LEFT JOIN fact_review r ON s.order_id = r.order_id
    GROUP BY c.customer_unique_id
    """

    df = pd.read_sql(query, conn)

    print("Número de clientes en el dataset de clustering:", len(df))

    # 2) LIMPIEZA
    df = df.fillna(0)

    # 3) VARIABLES PARA EL CLUSTERING
    features = df[[
        "num_orders",
        "total_spent",
        "avg_freight",
        "avg_delay",
        "avg_review"
    ]]

    # 4) ESCALADO
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)

    # 5) APLICAR K-MEANS
    kmeans = KMeans(n_clusters=3, random_state=42)
    df["cluster"] = kmeans.fit_predict(X_scaled)

    # 6) MOSTRAR RESULTADOS EN CONSOLA
    print("\nPrimeras filas con cluster asignado:")
    print(df.head())

    print("\nNúmero de clientes por cluster:")
    print(df["cluster"].value_counts().sort_index())

    print("\nPerfil medio de cada cluster:")
    print(
        df.groupby("cluster")[[
            "num_orders",
            "total_spent",
            "avg_freight",
            "avg_delay",
            "avg_review"
        ]].mean()
    )

    # 7) GUARDAR RESULTADOS EN CSV
    df.to_csv("customer_clusters.csv", index=False)
    print("\n CSV generado: customer_clusters.csv")

    conn.close()

if __name__ == "__main__":
    main()