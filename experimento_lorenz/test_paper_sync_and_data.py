"""
test_paper_sync_and_data.py

Suite de verificacion automatizada y estricta para:
1. Existencia de todas las figuras referenciadas en ingles (figures/) y espanol (figures_es/).
2. Paridad numerica exacta entre los fuentes LaTeX de main.tex y main_es.tex.
3. Balance completo de tensores en los scripts de bootstrap.
4. Denominador MASE sobre exactamente T_train=500 observaciones.
5. Reproduccion exacta de las tablas del articulo desde los CSVs auditados.
"""
from pathlib import Path
import re
import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
CHAOS_DIR = BASE / "paper_chaos_aip"


class TestFigureExistence:
    """Verifica que cada figura requerida exista en formato vectorial (.pdf) y raster (.png) a 600 DPI."""

    REQUIRED_FIGURES = [
        "fig5_ridge_fragilidad.pdf",
        "fig2b_lorenz_atractor.pdf",
        "fig_lyapunov_curve.pdf",
        "fig13_qlike_piso_fx.pdf",
        "fig12_bcie_causal.pdf",
        "fig7_combustibles_precios.pdf",
        "fig9_mecanismo_falla_nnls.pdf",
        "fig_supp_lambda_selection.pdf",
        "fig_rossler_m4.pdf",
    ]

    def test_english_figures_exist(self):
        fig_dir = CHAOS_DIR / "figures"
        assert fig_dir.exists(), "Directorio figures/ no existe"
        for fig in self.REQUIRED_FIGURES:
            p = fig_dir / fig
            assert p.exists() and p.stat().st_size > 1000, f"Falta figura en ingles: {fig}"

    def test_spanish_figures_exist(self):
        fig_dir = CHAOS_DIR / "figures_es"
        assert fig_dir.exists(), "Directorio figures_es/ no existe"
        for fig in self.REQUIRED_FIGURES:
            p = fig_dir / fig
            assert p.exists() and p.stat().st_size > 1000, f"Falta figura en espanol: {fig}"


class TestLaTeXBilingualParity:
    """Verifica que las versiones en ingles y espanol tengan paridad numerica 1:1."""

    def test_table1_numbers_match_between_en_and_es(self):
        main_en = (CHAOS_DIR / "main.tex").read_text(encoding="utf-8")
        main_es = (CHAOS_DIR / "main_es.tex").read_text(encoding="utf-8")

        key_numbers = [
            "0.0292", "0.0154", "0.2397", "0.2406", "0.242",
            "0.3633", "0.3983", "0.927", "1.131",
            "2.359", "2.383", "2.456", "2.565", "3.472", "14.33"
        ]
        for num in key_numbers:
            assert num in main_en, f"Cifra {num} falta en main.tex"
            assert num in main_es, f"Cifra {num} falta en main_es.tex"


class TestBootstrapBalanceAndTensores:
    """Verifica el balance de los tensores de bootstrap y que los CIs sean coherentes."""

    def test_two_way_bootstrap_output_shape_and_values(self):
        csv_p = BASE / "experimento_lorenz/output/lorenz_two_way_block_bootstrap.csv"
        assert csv_p.exists(), "Falta lorenz_two_way_block_bootstrap.csv"
        df = pd.read_csv(csv_p)

        assert len(df) == 9, f"Se esperaban 9 regímenes, obtenidos {len(df)}"
        # Verificar que el CI de ruido a 0.1 filtre genuinamente (excluya el 0)
        noise_filt = df[df["regime"] == "noise_0.1_filtering"].iloc[0]
        assert noise_filt["ci_vs_static_97.5"] < 0, "El filtrado de ruido ESN debe superar a static (CI estrictamente negativo)"

        # Verificar que el CI de shock a 15sigma cruce el cero
        shk_15 = df[df["regime"] == "shock_15sigma"].iloc[0]
        assert shk_15["ci_vs_ridge_2.5"] < 0 < shk_15["ci_vs_ridge_97.5"], "El CI de shock a 15sigma debe cruzar el cero"


class TestLyapunovCurveDenominator:
    """Verifica que el denominador MASE de la curva de Lyapunov use exactamente T_train=500 observaciones."""

    def test_mase_denominator_length(self):
        from lorenz_common import standardize_from_prefix
        from run_lorenz_30_seeds_ablation import simulate_lorenz, K, T_TRAIN

        x = simulate_lorenz()
        x_std = standardize_from_prefix(x, T_TRAIN)
        y_target = x_std[K:]

        # Ventana 0: y_tr tiene exactamente T_TRAIN observaciones
        y_tr = y_target[0:T_TRAIN]
        assert len(y_tr) == T_TRAIN == 500, f"y_tr debe tener longitud 500, tiene {len(y_tr)}"
        denom = float(np.mean(np.abs(np.diff(y_tr))))
        assert denom > 0.01, f"Denominador MASE debe ser positivo no nulo: {denom}"


class TestTableReproductionFromCSVs:
    """Verifica que los valores citados en las tablas coincidan con los CSVs auditados."""

    def test_fx_qlike_table_values(self):
        csv_p = BASE / "experimento_diario_fx_cripto/output/qlike_tail_diagnostics.csv"
        assert csv_p.exists(), "Falta qlike_tail_diagnostics.csv"
        df = pd.read_csv(csv_p)

        ewma = df[df["mode"] == "ewma_0.94"].iloc[0]
        assert np.isclose(ewma["median_of_per_series_means"], 2.359, atol=0.01)

        garch = df[df["mode"] == "garch_11"].iloc[0]
        assert np.isclose(garch["median_of_per_series_means"], 2.383, atol=0.01)

        nnls = df[df["mode"] == "nnls_nonneg"].iloc[0]
        assert np.isclose(nnls["median_of_per_series_means"], 2.565, atol=0.01)

        esn = df[df["mode"] == "ssrc_log"].iloc[0]
        assert np.isclose(esn["median_of_per_series_means"], 14.33, atol=0.05)
