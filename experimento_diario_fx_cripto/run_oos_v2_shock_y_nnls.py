"""Deriva los anexos de shocks y NNLS desde la corrida causal principal.

Debe ejecutarse despues de ``run_oos_univariado.py``. Ya no reimplementa lectores ni
descarga de datos: esa duplicacion era la causa de que el supuesto reservorio recurrente
se corrigiera en un archivo y siguiera siendo feed-forward en otro.
"""
from pathlib import Path

import pandas as pd


OUTPUT = Path(__file__).resolve().parent / "output"
SOURCE = OUTPUT / "oos_univariado.csv"

if not SOURCE.exists():
    raise FileNotFoundError("Ejecute primero run_oos_univariado.py")

frame = pd.read_csv(SOURCE)
required = {
    "entity", "t0", "mode", "test_es_shock", "train_tuvo_shock", "categoria",
    "mase", "qlike", "error_signed", "raw_pred", "yhat", "y_test",
    "pred_negativa_cruda", "positive_by_construction",
}
missing = required.difference(frame.columns)
if missing:
    raise ValueError(f"La salida principal no tiene columnas requeridas: {sorted(missing)}")

# Tarea 1: conserva todos los metodos, pero las dos banderas ya se calcularon con sigma de
# la ventana de entrenamiento, no con la serie completa.
task1 = frame[[
    "entity", "t0", "mode", "test_es_shock", "train_tuvo_shock", "categoria",
    "mase", "qlike", "error_signed", "fit_status",
]].copy()
task1.to_csv(OUTPUT / "oos_test_vs_train_shock.csv", index=False)
summary1 = (task1.groupby(["mode", "categoria"])
            .agg(mase_mediana=("mase", "median"), qlike_mediana=("qlike", "median"),
                 error_signed_mediano=("error_signed", "median"), n=("mase", "count"))
            .reset_index())

# Tarea 2: compara la especificacion heredada con signo contra la base no negativa real.
mapping = {
    "nnls_signed_clip_legacy": "nnls_original_legacy",
    "nnls_nonneg": "nnls_nonneg",
}
task2 = frame[frame["mode"].isin(mapping)].copy()
task2["variant"] = task2["mode"].map(mapping)
task2 = task2.rename(columns={
    "pred_negativa_cruda": "pred_negativa",
    "yhat": "yhat_clipped",
})
task2 = task2[[
    "entity", "t0", "variant", "raw_pred", "pred_negativa", "yhat_clipped",
    "y_test", "mase", "qlike", "positive_by_construction",
]]
task2.to_csv(OUTPUT / "oos_nnls_features_noneg.csv", index=False)
summary2 = (task2.groupby("variant")
            .agg(pct_negativas=("pred_negativa", "mean"),
                 qlike_mediana=("qlike", "median"), mase_mediana=("mase", "median"),
                 n=("variant", "count"))
            .reset_index())
summary2["pct_negativas"] = (100 * summary2["pct_negativas"]).round(2)

with (OUTPUT / "oos_test_vs_train_shock_resumen.md").open("w", encoding="utf-8") as file:
    file.write("# Test shock frente a shock en entrenamiento (clasificacion causal)\n\n")
    file.write(summary1.to_markdown(index=False))
    file.write("\n")

with (OUTPUT / "oos_nnls_features_noneg_resumen.md").open("w", encoding="utf-8") as file:
    file.write("# NNLS heredado frente a NNLS con base no negativa\n\n")
    file.write(summary2.to_markdown(index=False))
    file.write("\n")

print(summary1.to_string(index=False))
print("\n", summary2.to_string(index=False))
