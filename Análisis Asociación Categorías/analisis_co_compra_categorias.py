import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# =========================
# 1) CARGAR CSV
# =========================
order_items = pd.read_csv("olist_order_items_dataset.csv")
products = pd.read_csv("olist_products_dataset.csv")
translations = pd.read_csv("product_category_name_translation.csv")

# =========================
# 2) UNIR PRODUCTOS CON LA TRADUCCIÓN DE CATEGORÍAS
# =========================
products_cat = products.merge(
    translations,
    on="product_category_name",
    how="left"
)

# Si no hay traducción, usamos la categoría original
products_cat["category_final"] = products_cat["product_category_name_english"].fillna(
    products_cat["product_category_name"]
)

# =========================
# 3) UNIR ORDER ITEMS CON CATEGORÍAS
# =========================
df = order_items.merge(
    products_cat[["product_id", "category_final"]],
    on="product_id",
    how="left"
)

# Eliminar filas sin categoría
df = df.dropna(subset=["category_final"])

# =========================
# 4) DEJAR SOLO UNA VEZ CADA CATEGORÍA POR PEDIDO
# =========================
# Si un pedido tiene varios productos de la misma categoría,
# contamos esa categoría solo una vez dentro del pedido
basket = df[["order_id", "category_final"]].drop_duplicates()

# =========================
# 5) CREAR MATRIZ PEDIDO x CATEGORÍA
# =========================
basket_matrix = pd.crosstab(
    basket["order_id"],
    basket["category_final"]
)

# Convertir a 0/1
basket_matrix = (basket_matrix > 0).astype(int)

# =========================
# 6) CREAR MATRIZ DE CO-COMPRA
# =========================
co_purchase_matrix = basket_matrix.T.dot(basket_matrix)

# Poner la diagonal a 0 para que no cuente la categoría consigo misma
for cat in co_purchase_matrix.index:
    co_purchase_matrix.loc[cat, cat] = 0

# =========================
# 7) GUARDAR MATRIZ COMPLETA
# =========================
co_purchase_matrix.to_csv("co_purchase_matrix_categories.csv", encoding="utf-8-sig")
print("Matriz completa guardada en: co_purchase_matrix_categories.csv")

# =========================
# 8) SACAR TOP PARES DE CATEGORÍAS
# =========================
pairs = []
categories = co_purchase_matrix.index.tolist()

for i in range(len(categories)):
    for j in range(i + 1, len(categories)):
        cat1 = categories[i]
        cat2 = categories[j]
        count = co_purchase_matrix.loc[cat1, cat2]
        if count > 0:
            pairs.append((cat1, cat2, count))

pairs_df = pd.DataFrame(
    pairs,
    columns=["category_1", "category_2", "times_bought_together"]
).sort_values(by="times_bought_together", ascending=False)

pairs_df.to_csv("top_category_pairs.csv", index=False, encoding="utf-8-sig")
print("Top pares guardados en: top_category_pairs.csv")

print("\nTop 20 pares de categorías que más se compran juntas:")
print(pairs_df.head(20).to_string(index=False))

# =========================
# 9) QUEDARSE CON LAS CATEGORÍAS MÁS RELEVANTES
# =========================
# Para que el heatmap no salga enorme, elegimos las categorías
# con mayor número total de co-compras
top_n = 15

top_categories = co_purchase_matrix.sum(axis=1).sort_values(ascending=False).head(top_n).index
matrix_top = co_purchase_matrix.loc[top_categories, top_categories]

# =========================
# 10) DIBUJAR MAPA DE CALOR
# =========================
plt.figure(figsize=(12, 10))
sns.heatmap(
    matrix_top,
    annot=True,
    fmt="d",
    cmap="Blues",
    linewidths=0.5
)

plt.title("Mapa de calor de categorías que suelen comprarse juntas")
plt.xticks(rotation=45, ha="right")
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()

# =========================
# 11) GUARDAR HEATMAP COMO IMAGEN
# =========================
plt.figure(figsize=(12, 10))
sns.heatmap(
    matrix_top,
    annot=True,
    fmt="d",
    cmap="Blues",
    linewidths=0.5
)

plt.title("Mapa de calor de categorías que suelen comprarse juntas")
plt.xticks(rotation=45, ha="right")
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig("heatmap_categories_bought_together.png", dpi=300, bbox_inches="tight")
plt.close()

print("\nHeatmap guardado en: heatmap_categories_bought_together.png")
