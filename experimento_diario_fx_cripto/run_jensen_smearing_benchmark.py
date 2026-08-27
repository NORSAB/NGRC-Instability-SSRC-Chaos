"""Benchmark causal de correccion de Jensen para el readout logaritmico SSRC.

Autor: Norman Sabillon (2026)

El factor ``exp(sigma_hat**2 / 2)`` se estima por entidad con residuos OOS que ya
estaban observados antes de cada pronostico. Esta calibracion expandible evita usar
errores futuros y permite medir por separado el efecto sobre la media y la mediana de
QLIKE. El script consume el CSV OOS canonico y no descarga ni reemplaza datos.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from volatility_models import qlike


HERE = Path(__file__).resolve().parent
DEFAULT_INPUT = HERE / "output" / "oos_univariado.csv"
DEFAULT_OUTPUT_DIR = HERE / "output"
DEFAULT_MODE = "ssrc_log"
DEFAULT_FLOOR = 1e-10
DEFAULT_MIN_HISTORY = 20


def normal_smearing_factor(log_residuals: np.ndarray) -> tuple[float, float]:
    """Devuelve varianza muestral y ``exp(varianza / 2)`` bajo normalidad."""
    residuals = np.asarray(log_residuals, dtype=float)
    if residuals.ndim != 1 or len(residuals) < 2:
        raise ValueError("Se requieren al menos dos residuos logaritmicos")
    if np.any(~np.isfinite(residuals)):
        raise ValueError("Los residuos logaritmicos deben ser finitos")
    variance = float(np.var(residuals, ddof=1))
    exponent = 0.5 * variance
    if exponent > np.log(np.finfo(float).max):
        raise OverflowError("El factor de dispersion excede el rango de punto flotante")
    return variance, float(np.exp(exponent))


def apply_causal_smearing(
    frame: pd.DataFrame,
    mode: str = DEFAULT_MODE,
    min_history: int = DEFAULT_MIN_HISTORY,
    floor: float = DEFAULT_FLOOR,
) -> pd.DataFrame:
    """Aplica la correccion usando solo residuos OOS anteriores de la misma entidad."""
    required = {"entity", "t0", "mode", "y_test", "yhat"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Faltan columnas OOS: {sorted(missing)}")
    if min_history < 2:
        raise ValueError("min_history debe ser al menos 2")
    if floor <= 0 or not np.isfinite(floor):
        raise ValueError("floor debe ser positivo y finito")

    selected = frame.loc[frame["mode"].astype(str).eq(mode)].copy()
    selected = selected.loc[
        np.isfinite(selected["y_test"].astype(float))
        & np.isfinite(selected["yhat"].astype(float))
    ]
    if selected.empty:
        raise ValueError(f"No hay observaciones para mode={mode!r}")

    rows: list[dict[str, float | int | str | bool]] = []
    for entity, group in selected.groupby("entity", sort=True):
        ordered = group.sort_values("t0", kind="mergesort")
        y_true = np.maximum(ordered["y_test"].to_numpy(dtype=float), floor)
        y_pred = np.maximum(ordered["yhat"].to_numpy(dtype=float), floor)
        residuals = np.log(y_true + floor) - np.log(y_pred + floor)
        t0_values = ordered["t0"].to_numpy()

        for position in range(len(ordered)):
            record: dict[str, float | int | str | bool] = {
                "entity": str(entity),
                "t0": int(t0_values[position]),
                "mode": mode,
                "history_size": position,
                "y_test": float(y_true[position]),
                "yhat_original": float(y_pred[position]),
                "evaluable": position >= min_history,
                "residual_variance": np.nan,
                "smearing_factor": np.nan,
                "yhat_smearing": np.nan,
                "qlike_original": np.nan,
                "qlike_smearing": np.nan,
                "qlike_reduction": np.nan,
                "improved": False,
            }
            if position >= min_history:
                variance, factor = normal_smearing_factor(residuals[:position])
                corrected = max((y_pred[position] + floor) * factor - floor, floor)
                original_loss = qlike(y_true[position], y_pred[position], floor)
                corrected_loss = qlike(y_true[position], corrected, floor)
                record.update(
                    {
                        "residual_variance": variance,
                        "smearing_factor": factor,
                        "yhat_smearing": corrected,
                        "qlike_original": original_loss,
                        "qlike_smearing": corrected_loss,
                        "qlike_reduction": original_loss - corrected_loss,
                        "improved": corrected_loss < original_loss,
                    }
                )
            rows.append(record)
    return pd.DataFrame(rows)


def summarize_smearing(detail: pd.DataFrame) -> pd.DataFrame:
    """Resume QLIKE por entidad e incluye una fila global ponderada por observacion."""
    required = {
        "entity",
        "evaluable",
        "qlike_original",
        "qlike_smearing",
        "qlike_reduction",
        "improved",
        "smearing_factor",
    }
    missing = required.difference(detail.columns)
    if missing:
        raise ValueError(f"Faltan columnas del benchmark: {sorted(missing)}")
    evaluated = detail.loc[detail["evaluable"].astype(bool)].copy()
    if evaluated.empty:
        raise ValueError("No hay filas evaluables despues del periodo de calibracion")

    def aggregate(group: pd.DataFrame, label: str) -> dict[str, float | int | str]:
        original_mean = float(group["qlike_original"].mean())
        corrected_mean = float(group["qlike_smearing"].mean())
        return {
            "entity": label,
            "n": int(len(group)),
            "qlike_mean_original": original_mean,
            "qlike_mean_smearing": corrected_mean,
            "mean_absolute_reduction": original_mean - corrected_mean,
            "mean_relative_reduction": (
                (original_mean - corrected_mean) / original_mean
                if original_mean > 0
                else np.nan
            ),
            "qlike_median_original": float(group["qlike_original"].median()),
            "qlike_median_smearing": float(group["qlike_smearing"].median()),
            "median_point_reduction": float(group["qlike_reduction"].median()),
            "fraction_observations_improved": float(group["improved"].mean()),
            "smearing_factor_median": float(group["smearing_factor"].median()),
            "smearing_factor_max": float(group["smearing_factor"].max()),
        }

    rows = [aggregate(group, str(entity)) for entity, group in evaluated.groupby("entity")]
    entity_summary = pd.DataFrame(rows)
    median_series = entity_summary.drop(columns=["entity"]).median(numeric_only=True).to_dict()
    median_series["entity"] = "__median_series__"
    median_series["n"] = int(len(entity_summary))
    median_series["mean_absolute_reduction"] = (
        median_series["qlike_mean_original"] - median_series["qlike_mean_smearing"]
    )
    median_series["mean_relative_reduction"] = (
        median_series["mean_absolute_reduction"] / median_series["qlike_mean_original"]
        if median_series["qlike_mean_original"] > 0
        else np.nan
    )
    rows.append(median_series)
    rows.append(aggregate(evaluated, "__all__"))
    return pd.DataFrame(rows)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--mode", default=DEFAULT_MODE)
    parser.add_argument("--min-history", type=int, default=DEFAULT_MIN_HISTORY)
    parser.add_argument("--floor", type=float, default=DEFAULT_FLOOR)
    parser.add_argument("--no-save", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    source = pd.read_csv(args.input)
    detail = apply_causal_smearing(
        source,
        mode=args.mode,
        min_history=args.min_history,
        floor=args.floor,
    )
    summary = summarize_smearing(detail)
    print(summary.to_string(index=False, float_format=lambda value: f"{value:.6g}"))
    if not args.no_save:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        detail.to_csv(args.output_dir / "jensen_smearing_detail.csv", index=False)
        summary.to_csv(args.output_dir / "jensen_smearing_summary.csv", index=False)
        print(f"Resultados guardados en {args.output_dir}")


if __name__ == "__main__":
    main()
