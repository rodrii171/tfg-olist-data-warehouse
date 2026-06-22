import pandas as pd
import mysql.connector
import os

# =========================
# CONFIGURACIÓN
# =========================
REVIEWS_CSV = "olist_order_reviews_dataset.csv"

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
    # Se carga el dataset de reviews de pedidos
    reviews = pd.read_csv(REVIEWS_CSV)

    print("Filas CSV reviews:", len(reviews))
    print("Columnas:", list(reviews.columns))

    # =========================
    # 2) CONVERTIR COLUMNAS DE FECHA A DATETIME
    # =========================
    # Se transforman las fechas asociadas a la creación y respuesta de la review
    reviews["review_creation_date"] = pd.to_datetime(
        reviews["review_creation_date"], errors="coerce"
    )

    reviews["review_answer_timestamp"] = pd.to_datetime(
        reviews["review_answer_timestamp"], errors="coerce"
    )

    # =========================
    # 3) CREAR date_sk
    # =========================
    # Se genera la clave de fecha en formato YYYYMMDD a partir de la fecha de creación
    reviews["date_sk"] = pd.to_numeric(
        reviews["review_creation_date"].dt.strftime("%Y%m%d"),
        errors="coerce"
    )

    # =========================
    # 4) CREAR INDICADOR has_comment
    # =========================
    # Se indica si la review contiene comentario escrito
    reviews["has_comment"] = reviews["review_comment_message"].notna().astype(int)

    # =========================
    # 5) CONSTRUIR FACT TABLE
    # =========================
    # Se seleccionan los campos necesarios para la tabla fact_review
    fact = reviews[
        [
            "date_sk",
            "order_id",
            "review_id",
            "review_score",
            "review_creation_date",
            "review_answer_timestamp",
            "has_comment"
        ]
    ].copy()

    # =========================
    # 6) CONVERTIR NaN A None
    # =========================
    # Se adaptan los valores nulos para poder insertarlos correctamente en MySQL
    fact = fact.astype(object).where(fact.notna(), None)

    print("Filas preparadas para fact_review:", len(fact))
    print(fact.head())

    # =========================
    # 7) CONECTAR CON MYSQL
    # =========================
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    # =========================
    # 8) VACIAR TABLA (RECARGA COMPLETA)
    # =========================
    cur.execute("DELETE FROM fact_review;")
    conn.commit()

    # =========================
    # 9) INSERT MASIVO
    # =========================
    insert_sql = """
        INSERT INTO fact_review
        (
            date_sk,
            order_id,
            review_id,
            review_score,
            review_creation_date,
            review_answer_timestamp,
            has_comment
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    data = list(fact.itertuples(index=False, name=None))
    cur.executemany(insert_sql, data)
    conn.commit()

    print("fact_review cargada en MySQL:", cur.rowcount, "filas")

    # =========================
    # 10) CERRAR CONEXIONES
    # =========================
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()