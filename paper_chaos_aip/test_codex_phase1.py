"""Regression tests for the scientific and data fixes assigned to Codex."""

from pathlib import Path

import pandas as pd

try:
    from paper_chaos_aip.figure_calculations import ridge_trace_scaling
except ModuleNotFoundError:
    import sys
    sys.path.insert(0, str(HERE))
    from figure_calculations import ridge_trace_scaling



HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def test_figure1_trace_scaling_is_ridge_only():
    grid = pd.read_csv(ROOT / "experimento_lorenz/output/oos_grid_shocks.csv")
    result = ridge_trace_scaling(grid)

    assert result.modes == ("ridge",)
    assert result.n_rows > 0
    assert abs(result.slope - 3.9333110335651114) < 1e-10


def test_fuel_table_percentages_match_canonical_csv():
    oos = pd.read_csv(
        ROOT / "experimento_combustibles_honduras/output/oos_combustibles.csv"
    )
    expected = {}
    for mode in ("ols_clip_legacy", "ridge_cv_clip"):
        rows = oos.loc[oos["mode"].eq(mode)]
        expected[mode] = 100.0 * rows["prediccion_cruda_negativa"].mean()

    assert abs(expected["ols_clip_legacy"] - 13.662790697674419) < 1e-12
    assert abs(expected["ridge_cv_clip"] - 0.872093023255814) < 1e-12

    for name in ("supplementary.tex", "supplementary_es.tex"):
        tex = (HERE / name).read_text(encoding="utf-8")
        assert "13.7\\%" in tex
        assert "0.9\\%" in tex
        assert "& 0.542 & 0.587 & 47\\%" not in tex
        assert "& 0.552 & 0.734 & 3\\%" not in tex


def test_theorem_requires_an_interior_shock_in_both_languages():
    for name in ("main.tex", "main_es.tex"):
        tex = (HERE / name).read_text(encoding="utf-8")
        assert "k \\le t^* \\le T-k+1" in tex
        assert "t \\in [t^*, t^* + k - 1]" in tex


def test_assigned_scripts_contain_no_author_absolute_fuel_path():
    files = (
        HERE / "make_figures_bilingual.py",
        HERE / "make_supplementary_figures_english.py",
        ROOT / "experimento_combustibles_honduras/run_combustibles_hn.py",
        ROOT / "experimento_combustibles_honduras/investigar_ruptura_nnls.py",
        ROOT / "experimento_combustibles_honduras/graficos_combustibles.py",
    )
    forbidden = "D:\\2026\\Tesis2026\\Datos_Combustibles_Honduras"
    for path in files:
        assert forbidden not in path.read_text(encoding="utf-8")
