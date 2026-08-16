"""Validacion semanal secundaria del Articulo 4 con protocolo causal.

El guion no modifica ni descarga los datos. Compara lectores NG-RC con enlaces
positivos, un SSRC realmente recurrente y referencias EWMA/GARCH/GJR-GARCH.
La seleccion de lambda del Ridge se hace dentro de cada ventana mediante una
particion temporal interna. Combustibles se conserva como validacion secundaria,
no como evidencia principal del mecanismo sintetico.

Salidas:
  output/kappa_vs_T_combustibles.csv
  output/oos_combustibles.csv
  output/sensibilidad_piso_combustibles.csv
  output/resumen_combustibles.md
"""
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf

from eventos import EVENTOS, categoria, tipo_categoria
from modelos_volatilidad import (
    DesignScaler,
    causal_window,
    ewma_forecast,
    fit_garch_forecast,
    fit_nnls_nonnegative,
    fit_ridge_temporal,
    fit_softplus_temporal,
    fit_ssrc_log_temporal,
    make_reservoir,
    predict_ridge,
    predict_softplus,
    predict_ssrc_log,
    qlike,
)

warnings.filterwarnings("ignore")

REPO = Path(r"D:\2026\Tesis2026\Datos_Combustibles_Honduras\repositorio_combustibles_honduras.csv")
OUT = Path(__file__).resolve().parent / "output"
FUELS = ["Súper", "Regular", "Diesel", "Kerosene"]
K = 3
T_TRAIN = 150
STEP = 4
RES_DIM = 50
SEED = 7
FLOOR_MULTIPLIERS = (1e-6, 1e-4, 1e-2)


def ngrc_matrix(x, k):
    """Matriz NG-RC para el diagnostico kappa, ajustada a su propia ventana."""
    x = np.asarray(x, dtype=float)
    z = (x - np.mean(x)) / (np.std(x) + 1e-12)
    rows = []
    for t in range(k, len(z)):
        lags = z[t - k:t]
        quad = [lags[i] * lags[j] for i in range(k) for j in range(i, k)]
        rows.append(np.concatenate((lags, quad)))
    return np.asarray(rows)


def kappa_diag(f_window):
    cov = np.cov(f_window, rowvar=False)
    raw = float(np.linalg.cond(cov))
    try:
        lw = float(np.linalg.cond(LedoitWolf().fit(f_window).covariance_))
    except Exception:
        lw = np.nan
    return raw, lw


def fit_ols(x, y):
    scaler = DesignScaler.fit(x)
    xs = scaler.transform(x)
    w, *_ = np.linalg.lstsq(xs, y, rcond=None)
    return scaler, w


def add_prediction(store, sensitivity, metadata, mode, y_true, yhat_raw,
                   y_train, parameter=np.nan):
    reference_scale = max(float(np.median(y_train)), 1e-12)
    reference_floor = reference_scale * 1e-4
    yhat = max(float(yhat_raw), reference_floor)
    naive_mae = float(np.mean(np.abs(np.diff(y_train))))
    row = dict(metadata)
    row.update(
        mode=mode,
        y_true=float(y_true),
        yhat_raw=float(yhat_raw),
        yhat=float(yhat),
        prediccion_cruda_negativa=bool(yhat_raw < 0),
        mase=abs(float(y_true) - yhat) / (naive_mae + 1e-12),
        qlike=float(qlike(y_true, yhat_raw, reference_floor)),
        piso_referencia=reference_floor,
        parametro_regularizacion=parameter,
    )
    store.append(row)
    for multiplier in FLOOR_MULTIPLIERS:
        floor = reference_scale * multiplier
        sensitivity.append({
            **metadata,
            "mode": mode,
            "multiplicador_piso": multiplier,
            "piso": floor,
            "qlike": float(qlike(y_true, yhat_raw, floor)),
        })


def main():
    if not REPO.exists():
        raise FileNotFoundError(f"No existe el snapshot de combustibles: {REPO}")
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(REPO, encoding="utf-8-sig")
    df["FechaInicioISO"] = pd.to_datetime(df["FechaInicioISO"], errors="coerce")
    df = df.sort_values("Índice").reset_index(drop=True)
    print(f"Snapshot: {len(df)} semanas, {df['FechaInicioISO'].min().date()} a "
          f"{df['FechaInicioISO'].max().date()}")

    kappa_rows, oos_rows, floor_rows, failures = [], [], [], []
    t_grid = [20, 40, 80, 120, 200, 300, 400]

    for fuel_index, fuel in enumerate(FUELS):
        prices = df[fuel].to_numpy(dtype=float)
        valid = np.isfinite(np.log(prices[1:] / prices[:-1]))
        returns = np.log(prices[1:] / prices[:-1])[valid]
        dates = df["FechaInicioISO"].to_numpy()[1:][valid]
        print(f"\n=== {fuel}: n={len(returns)} retornos semanales ===")

        for k in (2, 3):
            for length in t_grid:
                if length <= k + 4 or length > len(returns):
                    continue
                f_window = ngrc_matrix(returns[-length:], k)
                raw, lw = kappa_diag(f_window)
                kappa_rows.append({"fuel": fuel, "k": k, "T": length,
                                   "kappa_raw": raw, "kappa_ledoitwolf": lw})

        d_in = 1 + K + K * (K + 1) // 2
        reservoir = make_reservoir(d_in, RES_DIM, seed=SEED + fuel_index)
        first_target = K + T_TRAIN
        for target in range(first_target, len(returns), STEP):
            fs, fn, fts, ftn, y_train, y_test = causal_window(
                returns, target, T_TRAIN, K
            )
            date_test = pd.Timestamp(dates[target])
            metadata = {
                "fuel": fuel,
                "target_index": target,
                "fecha": date_test.date().isoformat(),
                "categoria": categoria(date_test),
                "definicion_ventana": tipo_categoria(date_test),
            }
            history_returns = returns[target - T_TRAIN:target]
            reference_floor = max(float(np.median(y_train)) * 1e-4, 1e-12)

            predictions = []
            try:
                scaler_ols, w_ols = fit_ols(fs, y_train)
                pred = float((scaler_ols.transform(fts[None, :]) @ w_ols).ravel()[0])
                predictions.append(("ols_clip_legacy", pred, np.nan))
            except Exception as exc:
                failures.append({**metadata, "mode": "ols_clip_legacy", "error": repr(exc)})

            for link, label in (("direct", "ridge_cv_clip"), ("log", "ridge_log_cv")):
                try:
                    model = fit_ridge_temporal(fs, y_train, link=link)
                    predictions.append((label, predict_ridge(model, fts), model["lambda"]))
                except Exception as exc:
                    failures.append({**metadata, "mode": label, "error": repr(exc)})

            try:
                w_nnls = fit_nnls_nonnegative(fn, y_train)
                predictions.append(("nnls_base_no_negativa", float(ftn @ w_nnls), np.nan))
            except Exception as exc:
                failures.append({**metadata, "mode": "nnls_base_no_negativa", "error": repr(exc)})

            try:
                soft_model = fit_softplus_temporal(fs, y_train)
                predictions.append(("ngrc_softplus_cv", predict_softplus(soft_model, fts),
                                    soft_model["alpha"]))
            except Exception as exc:
                failures.append({**metadata, "mode": "ngrc_softplus_cv", "error": repr(exc)})

            try:
                ssrc_model = fit_ssrc_log_temporal(fs, y_train, reservoir)
                predictions.append(("ssrc_recurrente_log_cv",
                                    predict_ssrc_log(ssrc_model, fts),
                                    ssrc_model["readout"]["lambda"]))
            except Exception as exc:
                failures.append({**metadata, "mode": "ssrc_recurrente_log_cv", "error": repr(exc)})

            predictions.extend([
                ("naive", float(y_train[-1]), np.nan),
                ("ewma_094", ewma_forecast(history_returns, 0.94), 0.94),
            ])
            for is_gjr, label in ((False, "garch_11"), (True, "gjr_garch_11")):
                try:
                    predictions.append((label, fit_garch_forecast(history_returns, is_gjr), np.nan))
                except Exception as exc:
                    failures.append({**metadata, "mode": label, "error": repr(exc)})

            for mode, pred, parameter in predictions:
                if mode not in {"ols_clip_legacy", "ridge_cv_clip"} and pred < 0:
                    raise AssertionError(f"{mode} produjo una varianza negativa")
                add_prediction(oos_rows, floor_rows, metadata, mode, y_test,
                               pred, y_train, parameter)

            if reference_floor <= 0:
                raise AssertionError("el piso causal debe ser positivo")

    df_kappa = pd.DataFrame(kappa_rows)
    df_oos = pd.DataFrame(oos_rows)
    df_floor = pd.DataFrame(floor_rows)
    df_fail = pd.DataFrame(failures)
    df_kappa.to_csv(OUT / "kappa_vs_T_combustibles.csv", index=False)
    df_oos.to_csv(OUT / "oos_combustibles.csv", index=False)
    df_floor.to_csv(OUT / "sensibilidad_piso_combustibles.csv", index=False)
    df_fail.to_csv(OUT / "fallos_ajuste_combustibles.csv", index=False)

    summary = (df_oos.groupby(["fuel", "mode", "categoria"], dropna=False)
               .agg(mase_mediana=("mase", "median"), qlike_mediana=("qlike", "median"),
                    negativas_crudas=("prediccion_cruda_negativa", "sum"), n=("mase", "count"))
               .reset_index())
    floor_summary = (df_floor.groupby(["mode", "multiplicador_piso"])["qlike"]
                     .median().reset_index())
    with (OUT / "resumen_combustibles.md").open("w", encoding="utf-8") as handle:
        handle.write("# Combustibles Honduras: validación causal secundaria\n\n")
        handle.write(
            "Transformaciones ajustadas solo con entrenamiento; Ridge y lectura SSRC "
            "seleccionan regularización mediante validación temporal interna. NNLS usa una "
            "base no negativa. Se incluyen EWMA, GARCH(1,1) y GJR-GARCH(1,1).\n\n"
        )
        events = "; ".join(f"{name}: {start.date()}-{end.date()}"
                           for name, (start, end) in EVENTOS.items())
        handle.write(f"T_TRAIN={T_TRAIN}, paso={STEP}, k={K}. Eventos: {events}.\n\n")
        handle.write("## Resultados por combustible, método y categoría\n\n")
        handle.write(summary.to_markdown(index=False))
        handle.write("\n\n## Sensibilidad de QLIKE al piso\n\n")
        handle.write(floor_summary.to_markdown(index=False))
        handle.write(f"\n\nAjustes fallidos registrados: {len(df_fail)}.\n")

    print("\nResumen OOS")
    print(summary.to_string(index=False))
    print(f"\nAjustes fallidos: {len(df_fail)}. Salidas en {OUT}")


if __name__ == "__main__":
    main()
