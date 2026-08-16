"""Diagnostico secundario de tres bases NNLS.

La variante intermedia no garantiza positividad. Se conserva para documentar por que la
base enteramente no negativa es la comparacion coherente, no como lector principal.
"""
import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from volatility_models import (
    ALL_SYMBOLS, CRYPTO_SYMBOLS, QLIKE_FLOORS, causal_train_slice, fetch_daily_closes,
    fit_nnls_nonnegative, fit_nnls_signed_legacy, ngrc_features, predict_nnls,
    qlike_sensitivity,
)


K = 3
T_TRAIN = 500
STEP = 20
OUTPUT = Path(__file__).resolve().parent / "output"
VARIANTS = ("signed", "intermediate", "nonnegative")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", nargs="*", choices=sorted(ALL_SYMBOLS))
    parser.add_argument("--max-windows", type=int, default=None)
    args = parser.parse_args()
    selected = args.symbols or list(ALL_SYMBOLS)
    rows = []
    OUTPUT.mkdir(exist_ok=True)

    for name in selected:
        try:
            years = 10 if name in CRYPTO_SYMBOLS else 15
            closes = fetch_daily_closes(ALL_SYMBOLS[name], years)
            time.sleep(0.3)
        except Exception as exc:
            print(f"{name}: descarga fallida ({exc})")
            continue
        returns = np.log(closes.values[1:] / closes.values[:-1])
        returns = returns[np.isfinite(returns)]
        features = {}
        target = None
        for variant in VARIANTS:
            features[variant], y_variant, _ = ngrc_features(returns, K, variant)
            if target is None:
                target = y_variant
            elif not np.allclose(target, y_variant):
                raise AssertionError("Targets desalineados entre variantes")
        indices = list(range(T_TRAIN, len(target), STEP))
        if args.max_windows is not None:
            indices = indices[:args.max_windows]
        for t0 in indices:
            y_train = causal_train_slice(target, t0, T_TRAIN)
            y_test = target[t0]
            naive_mae = float(np.mean(np.abs(np.diff(y_train))))
            for variant in VARIANTS:
                train = causal_train_slice(features[variant], t0, T_TRAIN)
                test = features[variant][t0]
                if variant == "nonnegative":
                    model = fit_nnls_nonnegative(train, y_train)
                    raw = float(predict_nnls(model, test)[0])
                    positive = True
                else:
                    model = fit_nnls_signed_legacy(train, y_train)
                    raw = float(np.r_[1.0, test] @ model["beta"])
                    positive = False
                pred = raw if positive else max(raw, 1e-12)
                record = {
                    "entity": name, "t0": t0,
                    "variant": {"signed": "nnls_original_legacy",
                                "intermediate": "nnls_intermedia_legacy",
                                "nonnegative": "nnls_nonneg"}[variant],
                    "raw_pred": raw, "pred_negativa": bool(raw < 0),
                    "positive_by_construction": positive,
                    "yhat_clipped": pred, "y_test": y_test,
                    "mase": abs(y_test - pred) / (naive_mae + 1e-14),
                }
                record.update(qlike_sensitivity(y_test, pred, QLIKE_FLOORS))
                record["qlike"] = record["qlike_floor_1e-10"]
                rows.append(record)
        print(f"{name}: {len(indices)} ventanas")

    if not rows:
        raise RuntimeError("No se generaron resultados; se conservan los outputs previos")
    frame = pd.DataFrame(rows)
    frame.to_csv(OUTPUT / "oos_nnls_variante_intermedia.csv", index=False)
    summary = (frame.groupby("variant")
               .agg(pct_negativas=("pred_negativa", "mean"),
                    qlike_mediana=("qlike", "median"), qlike_media=("qlike", "mean"),
                    mase_mediana=("mase", "median"), mase_media=("mase", "mean"),
                    n=("variant", "count"))
               .reset_index())
    summary["pct_negativas"] = (100 * summary["pct_negativas"]).round(2)
    by_entity = (frame.groupby(["entity", "variant"])
                 .agg(pct_negativas=("pred_negativa", "mean"),
                      qlike_mediana=("qlike", "median"),
                      mase_mediana=("mase", "median"), n=("variant", "count"))
                 .reset_index())
    by_entity["pct_negativas"] = (100 * by_entity["pct_negativas"]).round(2)
    with (OUTPUT / "oos_nnls_variante_intermedia_resumen.md").open("w", encoding="utf-8") as file:
        file.write("# Diagnostico de tres bases NNLS\n\n")
        file.write(summary.to_markdown(index=False))
        file.write("\n\n## Por serie\n\n")
        file.write(by_entity.to_markdown(index=False))
        file.write("\n")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
