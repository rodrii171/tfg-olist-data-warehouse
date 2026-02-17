import pandas as pd
import mysql.connector

PRODUCTS_CSV = "olist_products_dataset.csv"
CATEGORIES_CSV = "product_category_name_translation.csv"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "PASSWORD",  
    "database": "tfg_olist_dw",
    "port": 3306
}

def main():
    
    products = pd.read_csv(PRODUCTS_CSV)
    categories = pd.read_csv(CATEGORIES_CSV)

    
    products = products.rename(columns={
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length"
    })

    
    products["product_id"] = products["product_id"].astype("string").str.strip()
    products["product_category_name"] = products["product_category_name"].astype("string").str.strip()

    categories["product_category_name"] = categories["product_category_name"].astype("string").str.strip()
    categories["product_category_name_english"] = categories["product_category_name_english"].astype("string").str.strip()

   
    df = products.merge(
        categories,
        on="product_category_name",
        how="left"
    )

    
    df_dim = df.drop_duplicates(subset=["product_id"], keep="first").copy()

    
    df_dim = df_dim[[
        "product_id",
        "product_category_name",
        "product_category_name_english",
        "product_name_length",
        "product_description_length",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm"
    ]]

    
    df_dim = df_dim.astype(object).where(df_dim.notna(), None)
    

   
    print("Filas CSV productos:", len(products))
    print("Filas dim_product:", len(df_dim))
    print("Categorias sin traducción (NULL):", pd.isna(df_dim["product_category_name_english"]).sum())
    print(df_dim.head())

    
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    
    cur.execute("DELETE FROM dim_product;")
    conn.commit()

    
    insert_sql = """
        INSERT INTO dim_product
        (
            product_id,
            product_category_name,
            product_category_name_english,
            product_name_length,
            product_description_length,
            product_photos_qty,
            product_weight_g,
            product_length_cm,
            product_height_cm,
            product_width_cm
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    data = list(df_dim.itertuples(index=False, name=None))
    cur.executemany(insert_sql, data)
    conn.commit()

    print("dim_product cargada en MySQL:", cur.rowcount, "filas")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()