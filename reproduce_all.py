#!/usr/bin/env python3
"""
Master Reproducibility Orchestrator for Article 4:
"Instability, Outlier Amplification, and Positivity Constraints in Next-Generation Reservoir Computing"

Target Journal: Chaos: An Interdisciplinary Journal of Nonlinear Science (AIP Publishing)
Author: Norman Reynaldo Sabillón Castro (2026)

This script automates the end-to-end replication pipeline:
1. Environment and dependency verification (including scikit-learn & requests)
2. Optional full dynamical and econometric simulation re-execution (--mode=full)
3. Automated test suite execution (pytest)
4. Regeneration of 600 DPI publication figures (English & Spanish)
5. Strict LaTeX manuscript compilation with log auditing (Overfull/Citations)
"""

import sys
import subprocess
import os
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
CHAOS_DIR = ROOT_DIR / "paper_chaos_aip"

def print_header(title: str):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)

def check_dependencies() -> bool:
    print_header("Step 1: Checking Python Dependencies")
    required = ["numpy", "scipy", "pandas", "matplotlib", "sklearn", "requests", "pytest"]
    pkg_display = {
        "sklearn": "scikit-learn",
        "numpy": "numpy",
        "scipy": "scipy",
        "pandas": "pandas",
        "matplotlib": "matplotlib",
        "requests": "requests",
        "pytest": "pytest"
    }
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
            print(f"  [OK] {pkg_display.get(pkg, pkg)}")
        except ImportError:
            print(f"  [MISSING] {pkg_display.get(pkg, pkg)}")
            missing.append(pkg_display.get(pkg, pkg))
    if missing:
        print(f"\nError: Missing packages: {missing}. Run: pip install -r requirements.txt")
        return False
    return True

def run_simulations() -> bool:
    print_header("Step 2 (Full Mode): Running Numerical Simulations & Benchmarks")
    sim_scripts = [
        ROOT_DIR / "experimento_lorenz" / "run_two_way_block_bootstrap.py",
        ROOT_DIR / "experimento_lorenz" / "run_lorenz_lyapunov_curve.py",
        ROOT_DIR / "experimento_rossler" / "run_rossler_validation.py",
        ROOT_DIR / "experimento_diario_fx_cripto" / "qlike_tail_diagnostics.py",
        ROOT_DIR / "experimento_combustibles_honduras" / "run_combustibles_hn.py",
    ]
    for script in sim_scripts:
        if not script.exists():
            print(f"  [ERROR] Required simulation script not found: {script}")
            return False
        print(f"  Running simulation: {script.name}...")
        res = subprocess.run([sys.executable, str(script)], cwd=str(script.parent))
        if res.returncode != 0:
            print(f"  [FAIL] Simulation script {script.name} returned non-zero exit code.")
            return False
        print(f"  [OK] {script.name} completed.")
    return True

def run_tests() -> bool:
    print_header("Step 3: Running Unit, Verification & Koinonía Tests (pytest)")
    res = subprocess.run([sys.executable, "-m", "pytest", "-v"], cwd=str(ROOT_DIR))
    if res.returncode == 0:
        print("\n  [OK] All test suites passed successfully.")
        return True
    else:
        print("\n  [FAIL] Test suite failed.")
        return False

def generate_figures() -> bool:
    print_header("Step 4: Generating Bilingual Publication Figures (600 DPI)")
    fig_script = CHAOS_DIR / "make_figures_bilingual.py"
    supp_script = CHAOS_DIR / "make_supplementary_figures_english.py"

    if fig_script.exists():
        print(f"  Executing {fig_script.name}...")
        res = subprocess.run([sys.executable, str(fig_script)], cwd=str(CHAOS_DIR))
        if res.returncode != 0:
            print(f"  [FAIL] Error running {fig_script.name}")
            return False
        print(f"  [OK] Main bilingual figures generated.")

    if supp_script.exists():
        print(f"  Executing {supp_script.name}...")
        res = subprocess.run([sys.executable, str(supp_script)], cwd=str(CHAOS_DIR))
        if res.returncode != 0:
            print(f"  [FAIL] Error running {supp_script.name}")
            return False
        print(f"  [OK] Supplementary figures generated.")

    return True

def audit_latex_log(log_path: Path) -> dict:
    stats = {"overfull": 0, "underfull": 0, "undefined_refs": 0, "undefined_cites": 0, "errors": 0}
    if not log_path.exists():
        return stats
    with open(log_path, "r", encoding="latin-1", errors="ignore") as f:
        for line in f:
            if "Overfull \\hbox" in line:
                stats["overfull"] += 1
            elif "Underfull \\hbox" in line:
                stats["underfull"] += 1
            elif "LaTeX Warning: Reference" in line and "undefined" in line:
                stats["undefined_refs"] += 1
            elif "LaTeX Warning: Citation" in line and "undefined" in line:
                stats["undefined_cites"] += 1
            elif "LaTeX Error:" in line or "Fatal error" in line:
                stats["errors"] += 1
    return stats

def compile_latex() -> bool:
    print_header("Step 5: Compiling LaTeX Manuscripts (REVTeX 4-2) & Auditing Logs")
    try:
        subprocess.run(["pdflatex", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("  [ERROR] pdflatex command not found on PATH. Required for publication PDF compilation.")
        return False

    docs = ["main.tex", "supplementary.tex", "main_es.tex", "supplementary_es.tex"]
    all_ok = True
    for doc in docs:
        doc_path = CHAOS_DIR / doc
        if not doc_path.exists():
            continue
        print(f"\n  Compiling {doc} (2 passes with -interaction=nonstopmode -halt-on-error)...")
        for p in range(1, 3):
            res = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", doc],
                cwd=str(CHAOS_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if res.returncode != 0:
                print(f"  [FAIL] Compilation error on pass {p} of {doc}:")
                print("\n".join(res.stdout.splitlines()[-15:]))
                all_ok = False
                break

        log_path = CHAOS_DIR / doc.replace(".tex", ".log")
        stats = audit_latex_log(log_path)
        pdf_name = doc.replace(".tex", ".pdf")
        if (CHAOS_DIR / pdf_name).exists() and res.returncode == 0:
            print(f"  [OK] {pdf_name} compiled successfully.")
            print(f"       Log Audit: Overfull={stats['overfull']}, Undefined Refs={stats['undefined_refs']}, Undefined Cites={stats['undefined_cites']}, Underfull={stats['underfull']}")
            if stats["undefined_refs"] > 0 or stats["undefined_cites"] > 0:
                print("       [WARN] Undefined references or citations detected!")
        else:
            all_ok = False

    return all_ok

def main():
    parser = argparse.ArgumentParser(description="Master Reproducibility Orchestrator for Article 4 (AIP Chaos)")
    parser.add_argument("--mode", choices=["quick", "full"], default="quick",
                        help="Execution mode: 'quick' (tests, figures, compilation) or 'full' (simulations, tests, figures, compilation)")
    args = parser.parse_args()

    print_header(f"NG-RC & SSRC REPRODUCIBILITY MASTER PIPELINE (Mode: {args.mode.upper()})")
    print(f"Working Directory: {ROOT_DIR}")

    if not check_dependencies():
        sys.exit(1)

    if args.mode == "full":
        if not run_simulations():
            sys.exit(1)

    if not run_tests():
        sys.exit(1)

    if not generate_figures():
        sys.exit(1)

    if not compile_latex():
        sys.exit(1)

    print_header(f"REPLICATION PIPELINE ({args.mode.upper()} MODE) COMPLETED SUCCESSFULLY (100% GREEN)")

if __name__ == "__main__":
    main()
