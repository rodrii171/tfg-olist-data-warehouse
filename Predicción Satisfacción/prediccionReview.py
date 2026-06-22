import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score


# 1) Cargar datos
df = pd.read_csv("customer_clusters.csv")

# 2) Variables de entrada y variable objetivo
X = df[["num_orders", "total_spent", "avg_freight", "avg_delay"]]
y = df["avg_review"]

# 3) Dividir en entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# =========================
# MODELO 1: REGRESIÓN LINEAL
# =========================
modelo_lr = LinearRegression()
modelo_lr.fit(X_train, y_train)
y_pred_lr = modelo_lr.predict(X_test)

mae_lr = mean_absolute_error(y_test, y_pred_lr)
r2_lr = r2_score(y_test, y_pred_lr)

# Tabla real vs predicho - Regresión Lineal
resultados_lr = pd.DataFrame({
    "Review real": y_test.reset_index(drop=True),
    "Review predicha": pd.Series(y_pred_lr).round(2)
})
resultados_lr["Diferencia"] = (
    resultados_lr["Review real"] - resultados_lr["Review predicha"]
).round(2)

# =========================
# MODELO 2: RANDOM FOREST
# =========================
modelo_rf = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)
modelo_rf.fit(X_train, y_train)
y_pred_rf = modelo_rf.predict(X_test)

mae_rf = mean_absolute_error(y_test, y_pred_rf)
r2_rf = r2_score(y_test, y_pred_rf)

# Tabla real vs predicho - Random Forest
resultados_rf = pd.DataFrame({
    "Review real": y_test.reset_index(drop=True),
    "Review predicha": pd.Series(y_pred_rf).round(2)
})
resultados_rf["Diferencia"] = (
    resultados_rf["Review real"] - resultados_rf["Review predicha"]
).round(2)

# =========================
# RESULTADOS POR PANTALLA
# =========================
print("=== COMPARATIVA DE MODELOS ===")
print(f"Regresión Lineal -> MAE: {mae_lr:.4f} | R2: {r2_lr:.4f}")
print(f"Random Forest    -> MAE: {mae_rf:.4f} | R2: {r2_rf:.4f}")

print("\n=== COEFICIENTES REGRESIÓN LINEAL ===")
coeficientes_lr = pd.DataFrame({
    "Variable": X.columns,
    "Coeficiente": modelo_lr.coef_
})
print(coeficientes_lr.to_string(index=False))
print(f"\nIntercepto: {modelo_lr.intercept_:.4f}")

print("\n=== IMPORTANCIA DE VARIABLES RANDOM FOREST ===")
importancias_rf = pd.DataFrame({
    "Variable": X.columns,
    "Importancia": modelo_rf.feature_importances_
}).sort_values(by="Importancia", ascending=False)
print(importancias_rf.to_string(index=False))

print("\n=== PRIMERAS 20 FILAS - REGRESIÓN LINEAL ===")
print(resultados_lr.head(20).to_string(index=False))

print("\n=== PRIMERAS 20 FILAS - RANDOM FOREST ===")
print(resultados_rf.head(20).to_string(index=False))

# =========================
# TABLA RESUMEN COMPARATIVA
# =========================
comparativa = pd.DataFrame({
    "Modelo": ["Regresión Lineal", "Random Forest"],
    "MAE": [round(mae_lr, 4), round(mae_rf, 4)],
    "R2": [round(r2_lr, 4), round(r2_rf, 4)]
})

print("\n=== RESUMEN FINAL ===")
print(comparativa.to_string(index=False))
# =========================
# GUARDAR ARCHIVOS CSV
# =========================
resultados_lr.to_csv(
    "predicciones_regresion_lineal.csv",
    index=False,
    sep=";",
    decimal=","
)

resultados_rf.to_csv(
    "predicciones_random_forest.csv",
    index=False,
    sep=";",
    decimal=","
)

comparativa.to_csv(
    "comparativa_modelos.csv",
    index=False,
    sep=";",
    decimal=","
)
resultados_lr["Modelo"] = "Regresión Lineal"
resultados_rf["Modelo"] = "Random Forest"

predicciones_modelos = pd.concat(
    [resultados_lr, resultados_rf],
    ignore_index=True
)

predicciones_modelos.to_csv(
    "predicciones_modelos.csv",
    index=False,
    sep=";",
    decimal=","
)
importancias_rf.to_csv(
    "importancia_variables.csv",
    index=False,
    sep=";",
    decimal=","
)
coeficientes_lr.to_csv(
    "coeficientes_regresion_lineal.csv",
    index=False,
    sep=";",
    decimal=","
)
print("\nArchivos guardados:")
print("- predicciones_regresion_lineal.csv")
print("- predicciones_random_forest.csv")
print("- comparativa_modelos.csv")