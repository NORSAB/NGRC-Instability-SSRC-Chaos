"""Walk-forward causal de volatilidad diaria para FX latinoamericano y cripto.

Revision metodologica del experimento del Articulo 4:

* ``ssrc_log`` es un SSRC/ESN realmente recurrente; ``W_res`` participa en cada estado.
* El lambda de cada readout Ridge se elige con validacion temporal dentro del train.
* ``nnls_nonneg`` combina pesos y base no negativos, por lo que no necesita recorte.
* ``log_ridge`` y ``softplus_ridge`` imponen positividad mediante el enlace.
* EWMA, GARCH(1,1) y GJR-GARCH(1,1) son comparadores de volatilidad pertinentes.
* OLS, Ridge-identidad y NNLS sobre base con signo se conservan como especificaciones
  heredadas y se etiquetan ``legacy`` o ``clip``; no sostienen el argumento principal.
* QLIKE se reporta para cuatro pisos, de modo que el ranking no dependa de uno oculto.

No se regulariza ninguna covarianza en este guion. ``lambda`` significa exclusivamente
penalizacion Ridge del readout.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from volatility_models import (
    ALL_SYMBOLS,
    CRYPTO_SYMBOLS,
    QLIKE_FLOORS,
    causal_train_slice,
    ewma_forecast,
    fetch_daily_closes,
    fit_nnls_nonnegative,
    fit_nnls_signed_legacy,
    fit_ols,
    fit_ridge_temporal,
    fit_ssrc_temporal,
    garch_forecast,
    make_ssrc,
    ngrc_features,
    predict_nnls,
    predict_ols,
    predict_ridge,
    predict_ssrc,
    qlike_sensitivity,
)


K = 3
T_TRAIN = 500
STEP = 20
SHOCK_SIGMA = 6.0
RES_DIM = 50
RES_RHO = 0.95
RES_DENSITY = 0.05
RES_LEAK = 0.5
SEED = 7
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", nargs="*", choices=sorted(ALL_SYMBOLS),
                        help="Subconjunto opcional; por defecto usa las nueve series.")
    parser.add_argument("--max-windows", type=int, default=None,
                        help="Limite diagnostico por serie. Omitir para la corrida completa.")
    parser.add_argument("--step", type=int, default=STEP)
    return parser.parse_args()


def _category(train_shock: bool, test_shock: bool) -> str:
    if train_shock and test_shock:
        return "ambos"
    if train_shock:
        return "train_tuvo_shock"
    if test_shock:
        return "test_es_shock"
    return "calma_total"


def _append(rows, *, entity, t0, mode, y_test, yhat, raw_pred, naive_mae,
            train_shock, test_shock, positive, status="ok", model=None):
    yhat = max(float(yhat), 1e-14)
    record = {
        "entity": entity,
        "t0": t0,
        "mode": mode,
        "train_tuvo_shock": bool(train_shock),
        "test_es_shock": bool(test_shock),
        "categoria": _category(train_shock, test_shock),
        "y_test": float(y_test),
        "raw_pred": float(raw_pred),
        "yhat": yhat,
        "pred_negativa_cruda": bool(raw_pred < 0),
        "positive_by_construction": bool(positive),
        "mase": abs(float(y_test) - yhat) / (naive_mae + 1e-14),
        "error_signed": yhat - float(y_test),
        "fit_status": status,
        "lambda_multiplier": np.nan,
        "lambda_value": np.nan,
        "validation_qlike": np.nan,
    }
    if model is not None:
        for key in ("lambda_multiplier", "lambda_value", "validation_qlike"):
            if key in model:
                record[key] = model[key]
    record.update(qlike_sensitivity(y_test, yhat, QLIKE_FLOORS))
    record["qlike"] = record["qlike_floor_1e-10"]
    rows.append(record)


def run_entity(name: str, closes: pd.Series, step: int, max_windows: int | None) -> list[dict]:
    raw_returns = np.log(closes.values[1:] / closes.values[:-1])
    returns = raw_returns[np.isfinite(raw_returns)]
    signed, target, target_returns = ngrc_features(returns, K, "signed")
    nonnegative, target_nonnegative, _ = ngrc_features(returns, K, "nonnegative")
    if signed is None or not np.allclose(target, target_nonnegative):
        return []

    w_in, w_res = make_ssrc(
        signed.shape[1], RES_DIM, rho=RES_RHO, density=RES_DENSITY, seed=SEED
    )
    rows: list[dict] = []
    window_indices = list(range(T_TRAIN, len(target), step))
    if max_windows is not None:
        window_indices = window_indices[:max_windows]

    for number, t0 in enumerate(window_indices, start=1):
        signed_train = causal_train_slice(signed, t0, T_TRAIN)
        nonnegative_train = causal_train_slice(nonnegative, t0, T_TRAIN)
        y_train = causal_train_slice(target, t0, T_TRAIN)
        return_train = causal_train_slice(target_returns, t0, T_TRAIN)
        signed_test = signed[t0]
        nonnegative_test = nonnegative[t0]
        y_test = target[t0]

        # La etiqueta de shock tambien es causal: sigma se estima en la ventana de train.
        threshold = SHOCK_SIGMA * float(np.std(return_train))
        train_shock = bool(np.any(np.abs(return_train) > threshold))
        test_shock = bool(abs(target_returns[t0]) > threshold)
        naive_mae = float(np.mean(np.abs(np.diff(y_train))))

        naive = max(float(target[t0 - 1]), 1e-14)
        _append(rows, entity=name, t0=t0, mode="naive", y_test=y_test,
                yhat=naive, raw_pred=naive, naive_mae=naive_mae,
                train_shock=train_shock, test_shock=test_shock, positive=True)

        ewma = ewma_forecast(y_train, 0.94)
        _append(rows, entity=name, t0=t0, mode="ewma_0.94", y_test=y_test,
                yhat=ewma, raw_pred=ewma, naive_mae=naive_mae,
                train_shock=train_shock, test_shock=test_shock, positive=True)

        for mode, gjr in (("garch_11", False), ("gjr_garch_11", True)):
            try:
                forecast, status = garch_forecast(return_train, gjr=gjr)
                _append(rows, entity=name, t0=t0, mode=mode, y_test=y_test,
                        yhat=forecast, raw_pred=forecast, naive_mae=naive_mae,
                        train_shock=train_shock, test_shock=test_shock,
                        positive=True, status=status)
            except Exception as exc:
                print(f"  {name} t0={t0}: {mode} fallo: {exc}")

        try:
            model = fit_ols(signed_train, y_train)
            raw = float(predict_ols(model, signed_test)[0])
            _append(rows, entity=name, t0=t0, mode="ols_clip_legacy", y_test=y_test,
                    yhat=max(raw, 1e-12), raw_pred=raw, naive_mae=naive_mae,
                    train_shock=train_shock, test_shock=test_shock, positive=False)
        except Exception as exc:
            print(f"  {name} t0={t0}: OLS fallo: {exc}")

        try:
            model = fit_ridge_temporal(signed_train, y_train, link="identity")
            raw = float(predict_ridge(model, signed_test)[0])
            _append(rows, entity=name, t0=t0, mode="ridge_clip", y_test=y_test,
                    yhat=max(raw, 1e-12), raw_pred=raw, naive_mae=naive_mae,
                    train_shock=train_shock, test_shock=test_shock,
                    positive=False, model=model)
        except Exception as exc:
            print(f"  {name} t0={t0}: Ridge fallo: {exc}")

        for mode, link in (("log_ridge", "log"), ("softplus_ridge", "softplus")):
            try:
                model = fit_ridge_temporal(signed_train, y_train, link=link)
                pred = float(predict_ridge(model, signed_test)[0])
                _append(rows, entity=name, t0=t0, mode=mode, y_test=y_test,
                        yhat=pred, raw_pred=pred, naive_mae=naive_mae,
                        train_shock=train_shock, test_shock=test_shock,
                        positive=True, model=model)
            except Exception as exc:
                print(f"  {name} t0={t0}: {mode} fallo: {exc}")

        try:
            model = fit_nnls_signed_legacy(signed_train, y_train)
            raw = float(np.r_[1.0, signed_test] @ model["beta"])
            _append(rows, entity=name, t0=t0, mode="nnls_signed_clip_legacy",
                    y_test=y_test, yhat=max(raw, 1e-12), raw_pred=raw,
                    naive_mae=naive_mae, train_shock=train_shock,
                    test_shock=test_shock, positive=False)
        except Exception as exc:
            print(f"  {name} t0={t0}: NNLS legacy fallo: {exc}")

        try:
            model = fit_nnls_nonnegative(nonnegative_train, y_train)
            pred = float(predict_nnls(model, nonnegative_test)[0])
            _append(rows, entity=name, t0=t0, mode="nnls_nonneg", y_test=y_test,
                    yhat=pred, raw_pred=pred, naive_mae=naive_mae,
                    train_shock=train_shock, test_shock=test_shock, positive=True)
        except Exception as exc:
            print(f"  {name} t0={t0}: NNLS no negativo fallo: {exc}")

        try:
            model = fit_ssrc_temporal(
                signed_train, y_train, w_in, w_res, leak=RES_LEAK
            )
            pred = predict_ssrc(model, signed_test)
            _append(rows, entity=name, t0=t0, mode="ssrc_log", y_test=y_test,
                    yhat=pred, raw_pred=pred, naive_mae=naive_mae,
                    train_shock=train_shock, test_shock=test_shock,
                    positive=True, model=model)
        except Exception as exc:
            print(f"  {name} t0={t0}: SSRC fallo: {exc}")

        if number % 25 == 0:
            print(f"  {name}: {number}/{len(window_indices)} ventanas")
    return rows


def main():
    args = _parse_args()
    selected = args.symbols or list(ALL_SYMBOLS)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    series = {}
    print("Descargando series diarias...")
    for name in selected:
        try:
            years = 10 if name in CRYPTO_SYMBOLS else 15
            series[name] = fetch_daily_closes(ALL_SYMBOLS[name], years_back=years)
            print(f"  {name:<5}: {len(series[name])} puntos")
            time.sleep(0.3)
        except Exception as exc:
            print(f"  {name}: FALLO ({exc})")

    rows = []
    for name, closes in series.items():
        print(f"\n{name}: ejecutando walk-forward")
        rows.extend(run_entity(name, closes, args.step, args.max_windows))
    if not rows:
        raise RuntimeError("No se genero ningun resultado; no se sobrescriben outputs previos")

    frame = pd.DataFrame(rows)
    frame.to_csv(OUTPUT_DIR / "oos_univariado.csv", index=False)
    summary = (frame.groupby(["mode", "categoria"], dropna=False)
               .agg(mase_mediana=("mase", "median"), mase_media=("mase", "mean"),
                    qlike_mediana=("qlike", "median"), qlike_media=("qlike", "mean"),
                    pct_pred_negativa_cruda=("pred_negativa_cruda", "mean"),
                    n=("mase", "count"))
               .reset_index())
    floor_summary = (frame.groupby("mode")[[f"qlike_floor_{x:.0e}" for x in QLIKE_FLOORS]]
                     .median().reset_index())
    with (OUTPUT_DIR / "oos_resumen_calma_vs_shock.md").open("w", encoding="utf-8") as file:
        file.write("# OOS univariado causal: calma y shocks\n\n")
        file.write("Los modelos `legacy` o `clip` no garantizan positividad estructural. "
                   "`ssrc_log` es recurrente y su readout usa lambda validado temporalmente.\n\n")
        file.write(summary.to_markdown(index=False))
        file.write("\n\n## Sensibilidad de QLIKE al piso (medianas globales)\n\n")
        file.write(floor_summary.to_markdown(index=False))
        file.write("\n")
    print("\nResumen global por metodo:")
    print(frame.groupby("mode").agg(mase=("mase", "median"), qlike=("qlike", "median"),
                                     n=("mase", "count")).to_string())
    print(f"\nGuardado en {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
