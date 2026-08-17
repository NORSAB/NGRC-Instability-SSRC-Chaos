"""Pure calculations shared by the Article 4 figure generator and tests."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RidgeTraceScaling:
    """Ridge-only trace scaling used by the quartic-inflation figure."""

    magnitudes: np.ndarray
    lambdas: np.ndarray
    slope: float
    intercept: float
    n_rows: int
    modes: tuple[str, ...]


def ridge_trace_scaling(grid: pd.DataFrame, n_fit: int = 3) -> RidgeTraceScaling:
    """Estimate the large-shock log-log slope using Ridge windows only.

    The SSRC trace heuristic is defined on a different feature space and cannot
    be pooled with the Ridge NG-RC values.  This function enforces that
    separation before aggregation.
    """
    required = {
        "mode",
        "ventana_incluye_shock",
        "magnitud_sigma",
        "lambda_traza_legacy",
    }
    missing = required.difference(grid.columns)
    if missing:
        raise ValueError(f"Missing shock-grid columns: {sorted(missing)}")

    selected = grid.loc[
        grid["mode"].eq("ridge")
        & grid["ventana_incluye_shock"].astype(bool)
        & grid["lambda_traza_legacy"].notna()
    ].copy()
    if selected.empty:
        raise ValueError("The shock grid contains no valid Ridge shock windows")

    modes = tuple(sorted(selected["mode"].astype(str).unique()))
    if modes != ("ridge",):
        raise AssertionError(f"Figure 1 must be Ridge-only, found modes={modes}")

    medians = (
        selected.groupby("magnitud_sigma")["lambda_traza_legacy"]
        .median()
        .sort_index()
    )
    if len(medians) < n_fit:
        raise ValueError(f"Need at least {n_fit} shock magnitudes, found {len(medians)}")

    magnitudes = medians.index.to_numpy(dtype=float)
    lambdas = medians.to_numpy(dtype=float)
    if np.any(magnitudes <= 0) or np.any(lambdas <= 0):
        raise ValueError("Log-log scaling requires positive magnitudes and lambdas")

    fit_idx = np.argsort(magnitudes)[-n_fit:]
    slope, intercept = np.polyfit(
        np.log(magnitudes[fit_idx]), np.log(lambdas[fit_idx]), 1
    )
    return RidgeTraceScaling(
        magnitudes=magnitudes,
        lambdas=lambdas,
        slope=float(slope),
        intercept=float(intercept),
        n_rows=len(selected),
        modes=modes,
    )
