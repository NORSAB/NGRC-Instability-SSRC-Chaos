#!/usr/bin/env python3
"""
Builds a clean, English-only publication-ready folder for this article:
manuscript, supplementary material, and the full reproduction code/data,
with no Spanish-language files and no internal working documents.

This is what gets zipped for Zenodo and used for the journal submission.
Run from the project root: python build_clean_english_package.py
"""

import hashlib
import shutil
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
OUT_DIR = ROOT_DIR.parent / "PAQUETE_PUBLICACION_INGLES"
OUTPUT_ZIP = ROOT_DIR.parent / "Articulo_4_Chaos_Zenodo_Ingles.zip"
FIXED_ZIP_TIMESTAMP = (2026, 8, 27, 0, 0, 0)

EXCLUDE_DIRS = {
    ".git", ".pytest_cache", "__pycache__", "tmp", ".vscode", ".idea",
    "figures_es", "paper", "Material nuevo a analizar",
}

EXCLUDE_FILES = {
    "package_zenodo_release.py",
    "build_clean_english_package.py",
    "make_figures_bilingual.py",
    ".gitignore",
    "main_es.tex", "main_es.pdf", "main_esNotes.bib",
    "supplementary_es.tex", "supplementary_es.pdf", "supplementary_esNotes.bib",
}

ROOT_PUBLIC_MARKDOWN = {
    "README.md",
    "ZENODO_REPRODUCIBILITY.md",
}

EXCLUDE_EXTS = {
    ".pyc", ".aux", ".log", ".out", ".toc", ".synctex.gz", ".nav", ".snm", ".tmp", ".bbl", ".blg",
}


def should_skip_file(filename: str) -> bool:
    if filename in EXCLUDE_FILES:
        return True
    if filename.startswith("PROMPT_") or filename.startswith("CHECKPOINT_"):
        return True
    ext = Path(filename).suffix.lower()
    if ext in EXCLUDE_EXTS:
        return True
    return False


def replace_required(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    if old not in content:
        raise RuntimeError(f"Expected package adaptation was not found in {path}")
    path.write_text(content.replace(old, new), encoding="utf-8")


def adapt_english_only_package() -> None:
    accessibility_test = OUT_DIR / "experimento_lorenz/test_editorial_and_reproducibility.py"
    replace_required(
        accessibility_test,
        '''        """Verifica que supplementary.tex y supplementary_es.tex contengan bloques de Alt Text."""
        supp_en = (CHAOS_DIR / "supplementary.tex").read_text(encoding="utf-8")
        supp_es = (CHAOS_DIR / "supplementary_es.tex").read_text(encoding="utf-8")

        assert "Alt Text:" in supp_en, "supplementary.tex debe contener bloques de Alt Text para figuras y tablas"
        assert "Texto alternativo:" in supp_es or "Alt Text:" in supp_es, "supplementary_es.tex debe contener bloques de Alt Text"
''',
        '''        """Verify that the English supplementary file contains Alt Text blocks."""
        supp_en = (CHAOS_DIR / "supplementary.tex").read_text(encoding="utf-8")
        assert "Alt Text:" in supp_en, "supplementary.tex must contain Alt Text blocks"
''',
    )

    sync_test = OUT_DIR / "experimento_lorenz/test_paper_sync_and_data.py"
    replace_required(
        sync_test,
        '''    def test_spanish_figures_exist(self):
        fig_dir = CHAOS_DIR / "figures_es"
        assert fig_dir.exists(), "Directorio figures_es/ no existe"
        for fig in self.REQUIRED_FIGURES:
            p = fig_dir / fig
            assert p.exists() and p.stat().st_size > 1000, f"Falta figura en espanol: {fig}"
''',
        '''    def test_spanish_figures_are_excluded(self):
        assert not (CHAOS_DIR / "figures_es").exists()
''',
    )
    replace_required(
        sync_test,
        '''class TestLaTeXBilingualParity:
    """Verifica que las versiones en ingles y espanol tengan paridad numerica 1:1."""

    def test_table1_numbers_match_between_en_and_es(self):
        main_en = (CHAOS_DIR / "main.tex").read_text(encoding="utf-8")
        main_es = (CHAOS_DIR / "main_es.tex").read_text(encoding="utf-8")

        key_numbers = [
            "0.0292", "0.0154", "0.2391", "0.2406", "0.242",
            "0.3628", "0.3987", "0.927", "1.131",
            "2.359", "2.383", "2.456", "2.565", "3.472", "14.33"
        ]
        for num in key_numbers:
            assert num in main_en, f"Cifra {num} falta en main.tex"
            assert num in main_es, f"Cifra {num} falta en main_es.tex"


''',
        '',
    )
    replace_required(
        sync_test,
        '''        """Verifica la sincronización exacta entre Table I (main.tex / main_es.tex)
        y lorenz_rigorous_summary.csv en todas las cifras decimales.
        Usa el CSV canónico como única fuente de verdad."""
''',
        '''        """Verify exact synchronization between Table I and the canonical CSV."""
''',
    )
    replace_required(
        sync_test,
        '''        main_en = (CHAOS_DIR / "main.tex").read_text(encoding="utf-8")
        main_es = (CHAOS_DIR / "main_es.tex").read_text(encoding="utf-8")
''',
        '''        main_en = (CHAOS_DIR / "main.tex").read_text(encoding="utf-8")
''',
    )
    replace_required(
        sync_test,
        '''                assert expected in main_es, (
                    f"{r['regime']} H={r['horizon']} col={col}: "
                    f"{expected} (del CSV vigente) no aparece en main_es.tex - Table I desincronizada"
                )
''',
        '',
    )

    paper_test = OUT_DIR / "paper_chaos_aip/test_editorial_and_reproducibility.py"
    replace_required(
        paper_test,
        '    for name in ("supplementary.tex", "supplementary_es.tex"):\n',
        '    for name in ("supplementary.tex",):\n',
    )
    replace_required(
        paper_test,
        '''def test_theorem_requires_an_interior_shock_in_both_languages():
    for name in ("main.tex", "main_es.tex"):
''',
        '''def test_theorem_requires_an_interior_shock():
    for name in ("main.tex",):
''',
    )
    replace_required(
        paper_test,
        '        HERE / "make_figures_bilingual.py",\n',
        '        HERE / "make_figures_english.py",\n',
    )

    reproduce = OUT_DIR / "reproduce_all.py"
    replace_required(
        reproduce,
        'print_header("Step 4: Generating Bilingual Publication Figures (600 DPI)")',
        'print_header("Step 4: Generating English Publication Figures (600 DPI)")',
    )
    replace_required(
        reproduce,
        'fig_script = CHAOS_DIR / "make_figures_bilingual.py"',
        'fig_script = CHAOS_DIR / "make_figures_english.py"',
    )


def build_clean_folder() -> Path:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    copied = 0
    for src_dir, subdirs, files in ROOT_DIR.walk() if hasattr(Path, "walk") else __import__("os").walk(ROOT_DIR):
        src_dir = Path(src_dir)
        rel_dir = src_dir.relative_to(ROOT_DIR)
        subdirs[:] = sorted(
            d for d in subdirs
            if d not in EXCLUDE_DIRS and not d.startswith(".")
        )
        for filename in sorted(files):
            if should_skip_file(filename):
                continue
            src_file = src_dir / filename
            if rel_dir == Path(".") and src_file.suffix.lower() == ".md":
                if filename not in ROOT_PUBLIC_MARKDOWN:
                    continue
            dst_file = OUT_DIR / rel_dir / filename
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            copied += 1

    adapt_english_only_package()

    return OUT_DIR, copied


def build_deterministic_zip(source_dir: Path) -> tuple[int, str, str]:
    with zipfile.ZipFile(
        OUTPUT_ZIP,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for source_file in sorted(path for path in source_dir.rglob("*") if path.is_file()):
            archive_name = source_file.relative_to(source_dir).as_posix()
            info = zipfile.ZipInfo(archive_name, FIXED_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info,
                source_file.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )

    payload = OUTPUT_ZIP.read_bytes()
    return (
        len(payload),
        hashlib.md5(payload).hexdigest(),
        hashlib.sha256(payload).hexdigest(),
    )


if __name__ == "__main__":
    out_dir, n = build_clean_folder()
    size, md5, sha256 = build_deterministic_zip(out_dir)
    print(f"Clean English-only publication folder built: {out_dir}")
    print(f"Files copied: {n}")
    print(f"Archive: {OUTPUT_ZIP}")
    print(f"Size: {size} bytes")
    print(f"MD5: {md5}")
    print(f"SHA-256: {sha256}")
