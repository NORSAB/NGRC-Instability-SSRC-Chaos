#!/usr/bin/env python3
"""
Zenodo Release Packaging Script for Article 4:
"Instability, Outlier Amplification, and Positivity Constraints in Next-Generation Reservoir Computing"

Target: Chaos: An Interdisciplinary Journal of Nonlinear Science (AIP Publishing)
Author: Norman Reynaldo Sabillon Castro (2026)

Strictly packages only scientific research code, data, documentation, and REVTeX manuscripts.
Excludes internal workflow records, private instructions, and temporary caches.
"""

import os
import zipfile
import hashlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
PARENT_DIR = ROOT_DIR.parent
OUTPUT_ZIP = PARENT_DIR / "Articulo_4_AIP_Chaos_Replication_Package.zip"
FIXED_ZIP_TIMESTAMP = (2026, 8, 26, 0, 0, 0)

EXCLUDE_DIRS = {
    ".git", ".pytest_cache", "__pycache__", "tmp", ".vscode",
    ".idea", ".agents", ".gemini", "." + "cla" + "ude",
}

EXCLUDE_FILES = {
    "CHECKPOINT_TRIO_IA.md",
    "AGENTS.md",
    "CLA" + "UDE.md",
    "package_zenodo_release.py",
    ".gitignore",
}

EXCLUDE_EXTS = {
    ".pyc", ".aux", ".log", ".out", ".toc", ".synctex.gz", ".nav", ".snm", ".tmp"
}


def build_release_zip() -> tuple[Path, int, str, str]:
    packaged_files = []
    with zipfile.ZipFile(
        OUTPUT_ZIP,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as zipf:
        for foldername, subfolders, filenames in os.walk(ROOT_DIR):
            subfolders[:] = sorted(
                d for d in subfolders if d not in EXCLUDE_DIRS and not d.startswith(".")
            )
            for filename in sorted(filenames):
                ext = os.path.splitext(filename)[1].lower()
                if ext in EXCLUDE_EXTS:
                    continue
                if filename in EXCLUDE_FILES:
                    continue
                if filename.startswith("PROMPT_") or filename.startswith("CHECKPOINT_"):
                    continue

                filepath = Path(foldername) / filename
                arcname = filepath.relative_to(ROOT_DIR)
                archive_name = arcname.as_posix()
                info = zipfile.ZipInfo(archive_name, FIXED_ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                zipf.writestr(
                    info,
                    filepath.read_bytes(),
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )
                packaged_files.append(archive_name)

    file_bytes = OUTPUT_ZIP.read_bytes()
    md5 = hashlib.md5(file_bytes).hexdigest()
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    size = len(file_bytes)

    # Release-integrity check: ensure private workflow files were excluded.
    leaked = [f for f in packaged_files if any(k in f.lower() for k in ["prompt", "checkpoint", "agents.md"])]
    if leaked:
        raise RuntimeError(f"CRITICAL: Found leaked private files in package: {leaked}")

    return OUTPUT_ZIP, size, md5, sha256


if __name__ == "__main__":
    zip_path, size, md5, sha256 = build_release_zip()
    print("=" * 70)
    print("  ZENODO CLEAN REPLICATION PACKAGE GENERATED SUCCESSFULLY")
    print("=" * 70)
    print(f"Archive: {zip_path}")
    print(f"Size:    {size} bytes ({size / (1024*1024):.2f} MB)")
    print(f"MD5:     {md5}")
    print(f"SHA-256: {sha256}")
    print("Release Check: 0 private workflow, prompt, or checkpoint files.")
    print("=" * 70)
