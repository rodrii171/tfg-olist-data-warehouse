# TFG — Arquitectura de Business Intelligence para e-commerce

**Autor:** Rodrigo García Arroyo  
**Tutor:** Carlos Camacho Gómez  
**ETSISI · Universidad Politécnica de Madrid · 2026**

---

## Descripción

Diseño e implementación de una arquitectura de Business Intelligence completa aplicada al dataset público de e-commerce brasileño Olist (~100.000 pedidos, 2016–2018).

El proyecto incluye:
- Modelo dimensional Galaxy Schema (metodología Kimball) en MySQL
- Procesos ETL desarrollados en Python
- Dashboards interactivos en Power BI
- Segmentación de clientes con K-means y predicción de satisfacción

---

## Tecnologías

- **Python** — pandas, mysql-connector-python, scikit-learn
- **MySQL** — almacenamiento del Data Warehouse
- **Power BI Desktop** — visualización e informes

---

## Estructura

```
├── etl/
│   ├── load_dim_date.py
│   ├── load_dim_customer.py
│   ├── load_dim_product.py
│   ├── load_fact_sales.py
│   ├── load_fact_payment.py
│   └── load_fact_review.py
├── sql/
│   └── schema.sql
├── analysis/
│   ├── clustering.py
│   └── prediction.py
└── powerbi/
    └── tfg_olist.pbix
```

---

## Modelo dimensional

3 tablas de hechos (`fact_sales`, `fact_payment`, `fact_review`) que comparten 3 dimensiones (`dim_date`, `dim_customer`, `dim_product`).

---

## Ejecución

### 1. Instalar dependencias

```bash
pip install pandas mysql-connector-python scikit-learn
```

### 2. Crear el esquema en MySQL

```bash
mysql -u root -p < sql/schema.sql
```

### 3. Configurar credenciales

```bash
export MYSQL_PASSWORD=tu_contraseña   # Linux/macOS
set MYSQL_PASSWORD=tu_contraseña      # Windows
```

### 4. Ejecutar ETL (en este orden)

```bash
python etl/load_dim_date.py
python etl/load_dim_customer.py
python etl/load_dim_product.py
python etl/load_fact_sales.py
python etl/load_fact_payment.py
python etl/load_fact_review.py
```

### 5. Análisis avanzado

```bash
python analysis/clustering.py    # genera customer_clusters.csv
python analysis/prediction.py    # requiere customer_clusters.csv
```

---

## Dataset

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — descargar desde Kaggle y colocar los CSV en el directorio raíz antes de ejecutar el ETL.

---

## Resultados

| Segmento | Clientes | Gasto medio | Review medio |
|---|---|---|---|
| Satisfechos | 74.082 (77,6 %) | 110,95 € | 4,65 |
| Insatisfechos | 17.036 (17,9 %) | 126,27 € | 1,58 |
| Premium | 4.302 (4,5 %) | 762,85 € | 4,06 |

| Modelo | MAE | R² |
|---|---|---|
| Regresión Lineal | 1,0137 | 0,0935 |
| Random Forest | 0,9813 | 0,0771 |
