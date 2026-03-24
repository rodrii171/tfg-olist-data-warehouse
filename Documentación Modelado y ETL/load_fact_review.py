import pandas as pd
import mysql.connector
import os

REVIEWS_CSV = "olist_order_reviews_dataset.csv"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": "tfg_olist_dw",
    "port": 3306
}

def main():
    # EXTRACT
    reviews = pd.read_csv(REVIEWS_CSV)

    print("Filas CSV reviews:", len(reviews))
    print("Columnas:", list(reviews.columns))

    # TRANSFORM
    reviews["review_creation_date"] = pd.to_datetime(
        reviews["review_creation_date"], errors="coerce"
    )
    reviews["review_answer_timestamp"] = pd.to_datetime(
        reviews["review_answer_timestamp"], errors="coerce"
    )

    reviews["date_sk"] = pd.to_numeric(
        reviews["review_creation_date"].dt.strftime("%Y%m%d"),
        errors="coerce"
    )

    reviews["has_comment"] = reviews["review_comment_message"].notna().astype(int)

    fact = reviews[[
        "date_sk",
        "order_id",
        "review_id",
        "review_score",
        "review_creation_date",
        "review_answer_timestamp",
        "has_comment"
    ]].copy()

    fact = fact.astype(object).where(fact.notna(), None)

    print("Filas preparadas para fact_review:", len(fact))
    print(fact.head())

    # LOAD
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("DELETE FROM fact_review;")
    conn.commit()

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

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()