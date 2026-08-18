"""
Automated editorial quality, accessibility, packaging, and reproducibility verification suite.
Validates:
1. Packaging and reproducibility files existence & dependencies (numpy, scipy, pandas, matplotlib, scikit-learn, requests, pytest).
2. Dual License specification (MIT for code, CC-BY 4.0 for docs).
3. Accessibility Alt-Text coverage & strict length validation (25-55 words) for figures (9) and tables (5).
4. Typography standards (zero parenthetical em-dashes in prose) across all 4 LaTeX manuscripts.
"""
import re
from pathlib import Path
import pytest

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
CHAOS_DIR = BASE / "paper_chaos_aip"


class TestPackagingAndReproducibility:
    """Verifica la existencia y consistencia de los artefactos de empaquetado Zenodo."""

    def test_root_environment_and_license_files_exist(self):
        req = BASE / "requirements.txt"
        env = BASE / "environment.yml"
        lic = BASE / "LICENSE"
        rep = BASE / "reproduce_all.py"
        zen = BASE / "ZENODO_REPRODUCIBILITY.md"

        for f in [req, env, lic, rep, zen]:
            assert f.exists() and f.stat().st_size > 50, f"Falta archivo de empaquetado: {f.name}"

    def test_requirements_contains_all_core_packages(self):
        req = (BASE / "requirements.txt").read_text(encoding="utf-8")
        required_pkgs = ["numpy", "scipy", "pandas", "matplotlib", "scikit-learn", "requests", "pytest"]
        for pkg in required_pkgs:
            assert pkg in req, f"Falta dependencia clave '{pkg}' en requirements.txt"

    def test_dual_license_specification(self):
        lic = (BASE / "LICENSE").read_text(encoding="utf-8")
        assert "MIT License" in lic, "Falta declaración MIT License en LICENSE"
        assert "CC-BY 4.0" in lic or "Creative Commons" in lic, "Falta declaración CC-BY 4.0 en LICENSE"


class TestAccessibilityAltTextCoverage:
    """Verifica que el 100% de las 9 figuras y 5 tablas tengan Alt Text accesible documentado y con longitud adecuada."""

    EXPECTED_ITEMS = [
        ("Figure 1", "fig1_ridge_scaling"),
        ("Figure 2", "fig2_shock_geometry"),
        ("Figure 3", "fig3_horizon_decay"),
        ("Figure 4", "fig4_floor_sensitivity"),
        ("Figure S1", "figS1_bcie_mase"),
        ("Figure S2", "figS2_fuel_prices"),
        ("Figure S3", "figS3_fuel_volatility_may2020"),
        ("Figure S4", "figS4_ratio_sensitivity"),
        ("Figure S5", "figS5_rossler_scaling"),
        ("Table I", "table1_ablation"),
        ("Table II", "table2_volatility"),
        ("Table S1", "tableS1_bcie_comparison"),
        ("Table S2", "tableS2_fuel_comparison"),
        ("Table S3", "tableS3_mechanistic_comparison"),
    ]

    def test_all_figures_and_tables_have_alt_text_markdown(self):
        md_file = CHAOS_DIR / "ALT_TEXT_FIGURES_TABLES.md"
        assert md_file.exists() and md_file.stat().st_size > 1000, "Falta ALT_TEXT_FIGURES_TABLES.md"
        content = md_file.read_text(encoding="utf-8")

        for label, tag in self.EXPECTED_ITEMS:
            assert label in content, f"Falta Alt Text para {label} en ALT_TEXT_FIGURES_TABLES.md"
            assert tag in content, f"Falta tag {tag} en ALT_TEXT_FIGURES_TABLES.md"

    def test_all_figures_and_tables_have_alt_text_plaintext(self):
        txt_file = CHAOS_DIR / "alt_text_aip.txt"
        assert txt_file.exists() and txt_file.stat().st_size > 1000, "Falta alt_text_aip.txt"
        content = txt_file.read_text(encoding="utf-8")

        for label, tag in self.EXPECTED_ITEMS:
            assert tag in content, f"Falta tag {tag} en alt_text_aip.txt"

    def test_alt_text_length_and_quality(self):
        txt_file = CHAOS_DIR / "alt_text_aip.txt"
        content = txt_file.read_text(encoding="utf-8")
        
        # Extraer bloques de descripción
        blocks = re.findall(r"(?:Fig \d+|Fig S\d+|Table [I|V|S\d]+)[^\n]*:\n([^\n]+)", content)
        assert len(blocks) == 14, f"Se esperaban 14 bloques de alt-text en alt_text_aip.txt, se encontraron {len(blocks)}"

        for block in blocks:
            words = block.split()
            n_words = len(words)
            assert 25 <= n_words <= 55, f"Alt-text fuera del rango [25, 55] palabras ({n_words} palabras): '{block[:50]}...'"

    def test_supplementary_tex_files_have_alt_texts(self):
        """Verifica que supplementary.tex y supplementary_es.tex contengan bloques de Alt Text."""
        supp_en = (CHAOS_DIR / "supplementary.tex").read_text(encoding="utf-8")
        supp_es = (CHAOS_DIR / "supplementary_es.tex").read_text(encoding="utf-8")

        assert "Alt Text:" in supp_en, "supplementary.tex debe contener bloques de Alt Text para figuras y tablas"
        assert "Texto alternativo:" in supp_es or "Alt Text:" in supp_es, "supplementary_es.tex debe contener bloques de Alt Text"


class TestProseQualityStandards:
    """Verifica la estricta ausencia de rayas de interrupción parentéticas en la prosa de los manuscritos."""

    ALLOWED_EXCEPTIONS = [
        "Writing -- Original Draft",
        "Redacción -- Borrador Original",
        "& -- \\\\",
        "& --\\\\",
        # Verbatim published article title (Crossref DOI 10.1063/5.0283386); the
        # em dash is part of the real title, not authored interruption prose.
        "Reservoir computing bootcamp---From Python/NumPy tutorial",
    ]

    def _find_em_dashes(self, tex_file: Path):
        violations = []
        if not tex_file.exists():
            return violations
        lines = tex_file.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, 1):
            clean_line = line.split("%")[0].strip()
            if not clean_line:
                continue
            for exc in self.ALLOWED_EXCEPTIONS:
                clean_line = clean_line.replace(exc, "")
            if "---" in clean_line or " -- " in clean_line:
                violations.append((idx, line))
        return violations

    def test_no_parenthetical_em_dashes_in_prose(self):
        """Audita main.tex, main_es.tex, supplementary.tex, supplementary_es.tex para garantizar 0 rayas parentéticas."""
        tex_files = [
            CHAOS_DIR / "main.tex",
            CHAOS_DIR / "main_es.tex",
            CHAOS_DIR / "supplementary.tex",
            CHAOS_DIR / "supplementary_es.tex"
        ]
        all_violations = {}
        for tf in tex_files:
            v = self._find_em_dashes(tf)
            if v:
                all_violations[tf.name] = v

        msg = "\nRayas de interrupción encontradas en prosa:\n"
        for fname, viols in all_violations.items():
            for line_no, content in viols:
                msg += f"  - {fname}:{line_no} -> {content[:80]}...\n"

        assert len(all_violations) == 0, msg


class TestStatisticalBootstrapInference:
    """Verifica que el bootstrap de dos vías sea verdaderamente cruzado y reproducible."""

    def test_two_way_block_bootstrap_shared_time_indices(self):
        """Verifica la lógica algorítmica de remuestreo temporal compartido y la estructura del output."""
        import numpy as np
        import pandas as pd
        from experimento_lorenz.run_two_way_block_bootstrap import (
            block_bootstrap_indices,
            resample_two_way_block_diff,
            BLOCK_SIZE,
        )

        # 1. Validación algorítmica del generador de índices por bloques
        rng = np.random.RandomState(42)
        n_w, n_s = 50, 30
        w_idx = block_bootstrap_indices(n_w, BLOCK_SIZE, rng)
        s_idx = rng.choice(n_s, size=n_s, replace=True)

        assert len(w_idx) == n_w, f"w_idx debe tener longitud {n_w}"
        assert len(s_idx) == n_s, f"s_idx debe tener longitud {n_s}"

        # 2. Verificar que la indexación bidimensional (w_idx[:, None], s_idx) comparte idénticos índices de tiempo
        synthetic_matrix = np.arange(n_w * n_s).reshape(n_w, n_s)
        sampled = synthetic_matrix[w_idx[:, None], s_idx]
        assert sampled.shape == (n_w, n_s), "La matriz remuestreada debe preservar dimensiones (n_w, n_s)"

        # Comprobar que a lo largo de cualquier columna de semillas j, las filas evaluadas son exactamente w_idx
        for col_j in range(n_s):
            col_seed_orig = s_idx[col_j]
            expected_col = synthetic_matrix[w_idx, col_seed_orig]
            np.testing.assert_array_equal(sampled[:, col_j], expected_col, err_msg="El remuestreo temporal debe ser idéntico en todas las semillas")

        # 3. Probar la función de producción resample_two_way_block_diff con datos de covarianza cruzada no trivial
        # Se inyecta una fuerte tendencia temporal compartida y ruido estocástico
        time_trend = np.linspace(0, 10, n_w)[:, None]
        seed_trend = np.linspace(0, 2, n_s)[None, :]
        noise_a = rng.normal(0, 0.05, size=(n_w, n_s))
        noise_b = rng.normal(0, 0.05, size=(n_w, n_s))

        mat_a = time_trend + seed_trend + noise_a
        mat_b = time_trend + seed_trend + 0.5 + noise_b

        d_mean, ci_low, ci_high = resample_two_way_block_diff(mat_a, mat_b, block_size=BLOCK_SIZE, n_boot=200, rng=rng)
        assert abs(d_mean - (-0.5)) < 0.05, f"La diferencia media debe ser ~ -0.5, obtenida {d_mean}"
        shared_ci_width = ci_high - ci_low

        # Verificar que el remuestreo independiente/desalineado de tiempo produce una varianza al menos 10x mayor
        unshared_diffs = []
        for _ in range(200):
            w_idx_a = block_bootstrap_indices(n_w, BLOCK_SIZE, rng)
            w_idx_b = block_bootstrap_indices(n_w, BLOCK_SIZE, rng)
            s_idx_b = rng.choice(n_s, size=n_s, replace=True)
            unshared_diffs.append(np.mean(mat_a[w_idx_a[:, None], s_idx_b] - mat_b[w_idx_b[:, None], s_idx_b]))
        unshared_ci_low, unshared_ci_high = np.percentile(unshared_diffs, [2.5, 97.5])
        unshared_ci_width = unshared_ci_high - unshared_ci_low

        assert unshared_ci_width > 10 * shared_ci_width, (
            f"El remuestreo temporal compartido debe cancelar la tendencia temporal "
            f"(ancho compartido={shared_ci_width:.4f}, no compartido={unshared_ci_width:.4f})"
        )

        # 4. Validación de integridad del CSV canónico
        csv_file = BASE / "experimento_lorenz" / "output" / "lorenz_two_way_block_bootstrap.csv"
        assert csv_file.exists(), "Debe existir lorenz_two_way_block_bootstrap.csv"
        df = pd.read_csv(csv_file)
        assert len(df) == 9, f"Se esperaban 9 regímenes en el bootstrap de Lorenz, encontrados {len(df)}"
        assert "diff_mean_vs_ridge" in df.columns
        assert "ci_vs_ridge_2.5" in df.columns
        assert "ci_vs_ridge_97.5" in df.columns
        assert not df["diff_mean_vs_ridge"].isna().any(), "No deben existir valores NaN en diff_mean_vs_ridge"


