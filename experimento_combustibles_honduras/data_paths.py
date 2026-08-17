"""Resolve the Honduras fuel-data snapshot without author-specific paths."""

import os
from pathlib import Path


FILENAME = "repositorio_combustibles_honduras.csv"
ARTICLE_ROOT = Path(__file__).resolve().parents[1]


def resolve_fuel_repository(explicit: str | Path | None = None) -> Path:
    """Return an existing fuel snapshot from an explicit or portable location.

    Resolution order is: explicit argument, ``PAPER4_FUEL_REPOSITORY``, a
    packaged ``data/`` directory, and the research workspace sibling used by
    the current project layout.  A directory value is expanded with FILENAME.
    """
    configured = explicit or os.environ.get("PAPER4_FUEL_REPOSITORY")
    candidates: list[Path] = []
    if configured:
        path = Path(configured).expanduser()
        candidates.append(path / FILENAME if path.is_dir() else path)
    candidates.extend(
        [
            ARTICLE_ROOT / "data" / FILENAME,
            ARTICLE_ROOT.parents[1] / "Datos_Combustibles_Honduras" / FILENAME,
        ]
    )

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    attempted = "\n  - ".join(str(path) for path in candidates)
    raise FileNotFoundError(
        "Honduras fuel snapshot not found. Set PAPER4_FUEL_REPOSITORY to the "
        f"CSV file or its directory. Attempted:\n  - {attempted}"
    )
