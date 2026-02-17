# TFG - Data Warehouse Olist

## Descripción
Diseño e implementación de un Data Warehouse basado en modelo en estrella sobre el dataset Olist (e-commerce brasileño).

## Tecnologías
- Python (Pandas)
- MySQL
- MySQL Workbench

## Estructura del proyecto
- Scripts ETL:
  - load_dim_date.py
  - load_dim_customer.py
  - load_dim_product.py
  - load_fact_sales.py
  - load_fact_payment.py

- Esquema SQL del Data Warehouse

## Modelo
Modelo dimensional en estrella con:
- Dimensiones: dim_customer, dim_product, dim_date
- Hechos: fact_sales, fact_payment

## Autor
Rodrigo García Arroyo
