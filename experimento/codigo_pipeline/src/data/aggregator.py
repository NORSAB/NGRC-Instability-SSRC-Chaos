"""
Data Aggregator
"""
import pandas as pd
from config.topology import SYNTHETIC_HUB_NAME, TIME_COL, ENTITY_COL, FEATURE_COLS

def aggregate_data(df_clean):
    required = {
        "anio_aprobacion", "pais", "tipo_socio",
        "monto_bruto_usd", "cantidad_aprobaciones"
    }
    missing = required.difference(df_clean.columns)
    if missing:
        raise ValueError(f"Missing columns before aggregation: {sorted(missing)}")

    df_clean = df_clean.copy()
    for col in ["anio_aprobacion", "monto_bruto_usd", "cantidad_aprobaciones"]:
        df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")
    if df_clean[list(required)].isna().any().any():
        bad = df_clean[list(required)].isna().sum()
        raise ValueError(f"Null or non-numeric values in BCIE input: {bad[bad > 0].to_dict()}")
    if (df_clean[["monto_bruto_usd", "cantidad_aprobaciones"]] < 0).any().any():
        raise ValueError("Negative approvals or amounts are not admissible")

    # Aggregation
    df_agg = df_clean.groupby(["anio_aprobacion", "pais", "tipo_socio"], as_index=False).agg(
        monto_total_usd_aprobados=("monto_bruto_usd", "sum"),
        cantidad_total_aprobados=("cantidad_aprobaciones", "sum")
    )

    df_agg["anio_aprobacion"] = pd.to_numeric(df_agg["anio_aprobacion"], errors='coerce').fillna(0).astype(int)
    df_agg = df_agg[df_agg["anio_aprobacion"] > 1900]

    df_agg = df_agg.rename(columns={
        "anio_aprobacion": TIME_COL,
        "pais": ENTITY_COL,
        "monto_total_usd_aprobados": FEATURE_COLS[0], 
        "cantidad_total_aprobados": FEATURE_COLS[1]
    })

    # Synthetic Hub Creation
    df_hub = df_agg.groupby(TIME_COL, as_index=False)[[FEATURE_COLS[0], FEATURE_COLS[1]]].sum()
    df_hub[ENTITY_COL] = SYNTHETIC_HUB_NAME 
    df_hub["tipo_socio"] = "Hub"

    df_final = pd.concat([df_agg, df_hub], ignore_index=True)
    return df_final
