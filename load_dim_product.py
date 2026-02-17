import pandas as pd
import mysql.connector
import os

# =========================
# CONFIGURACIÓN
# =========================
PRODUCTS_CSV = "olist_products_dataset.csv"
CATEGORIES_CSV = "product_category_name_translation.csv"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": os.getenv("MYSQL_PASSWORD"),  
    "database": "tfg_olist_dw",
    "port": 3306
}

def main():

    # =========================
    # 1) LEER LOS CSV
    # =========================
    # Se cargan los datasets de productos y traducción de categorías
    products = pd.read_csv(PRODUCTS_CSV)
    categories = pd.read_csv(CATEGORIES_CSV)

    # =========================
    # 2) CORREGIR COLUMNAS MAL ESCRITAS
    # =========================
    # En el dataset original algunas columnas están mal escritas ("lenght")
    # Se renombran para mantener consistencia en el Data Warehouse
    products = products.rename(columns={
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length"
    })

    # =========================
    # 3) LIMPIEZA DE CAMPOS CLAVE
    # =========================
    # Se convierten a string y se eliminan espacios en blanco
    # Esto evita errores en joins y posibles duplicados invisibles
    products["product_id"] = products["product_id"].astype("string").str.strip()
    products["product_category_name"] = products["product_category_name"].astype("string").str.strip()

    categories["product_category_name"] = categories["product_category_name"].astype("string").str.strip()
    categories["product_category_name_english"] = categories["product_category_name_english"].astype("string").str.strip()

    # =========================
    # 4) TRANSFORM → JOIN PARA AÑADIR TRADUCCIÓN
    # =========================
    # Se realiza un LEFT JOIN para añadir la traducción al inglés
    # Se mantienen todos los productos aunque no tengan traducción
    df = products.merge(
        categories,
        on="product_category_name",
        how="left"
    )

    # =========================
    # 5) ELIMINAR DUPLICADOS
    # =========================
    # Se garantiza que exista una única fila por product_id
    df_dim = df.drop_duplicates(subset=["product_id"], keep="first").copy()

    # =========================
    # 6) SELECCIONAR COLUMNAS DEL DATA WAREHOUSE
    # =========================
    # Se seleccionan únicamente los atributos relevantes para dim_product
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

    # =========================
    # 7) CONVERTIR NaN A None
    # =========================
    # MySQL no reconoce NaN, necesita NULL (None en Python)
    df_dim = df_dim.astype(object).where(df_dim.notna(), None)
    

    # =========================
    # 8) LOGS DE VALIDACIÓN
    # =========================
    # Se muestran estadísticas para comprobar que el proceso es correcto
    print("Filas CSV productos:", len(products))
    print("Filas dim_product:", len(df_dim))
    print("Categorias sin traducción (NULL):", pd.isna(df_dim["product_category_name_english"]).sum())
    print(df_dim.head())

    # =========================
    # 9) CONEXIÓN A MYSQL
    # =========================
    # Se establece conexión con la base de datos del Data Warehouse
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    # =========================
    # 10) RECARGA COMPLETA DE LA DIMENSIÓN
    # =========================
    # Se eliminan los datos anteriores antes de insertar los nuevos
    cur.execute("DELETE FROM dim_product;")
    conn.commit()

    # =========================
    # 11) SENTENCIA SQL DE INSERCIÓN
    # =========================
    # Se define la sentencia SQL para insertar los registros
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

    # =========================
    # 12) CONVERTIR DATAFRAME EN TUPLAS PARA INSERT MASIVO
    # =========================
    # Se convierten las filas en tuplas para inserción eficiente
    data = list(df_dim.itertuples(index=False, name=None))
    cur.executemany(insert_sql, data)
    conn.commit()

    print("dim_product cargada en MySQL:", cur.rowcount, "filas")
    
    # =========================
    # 13) CERRAR CONEXIÓN
    # =========================
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()