"""
Topology and Entity Definitions: v6 Limpio
=============================================
Cambios:
  LIMPIEZA: Eliminado ORDEN_PAISES redundante.
            HIERARCHICAL_ORDER es la única referencia de orden canónico.
"""

# --- TOPOLOGY DEFINITIONS (16+1 STRATEGY) ---
SYNTHETIC_HUB_NAME = "BCIE Systemic Hub"

GROUP_FOUNDERS = [
    "Guatemala", "El Salvador", "Honduras", "Nicaragua", "Costa Rica"
]
GROUP_REGIONAL_NON_FOUNDERS = [
    "Panamá", "República Dominicana", "Belice"
]
GROUP_EXTRA_REGIONAL = [
    "México", "China (Taiwán)", "Argentina", "Colombia", "España", "Cuba", "Corea"
]
GROUP_PROGRAMMATIC = ["Regional"]

ALL_SPOKES = GROUP_FOUNDERS + GROUP_REGIONAL_NON_FOUNDERS + GROUP_EXTRA_REGIONAL + GROUP_PROGRAMMATIC

# --- HIERARCHICAL ORDER DEFINITION ---
# Canonical ordering: Hub first, then Founders, Regional Non-Founders,
# Extra-Regional, and Programmatic entity last.
HIERARCHICAL_ORDER = [
    SYNTHETIC_HUB_NAME,              # 1. Systemic Hub
    "Guatemala",                     # 2. Founders
    "El Salvador",
    "Honduras",
    "Nicaragua",
    "Costa Rica",
    "Panamá",                        # 7. Regional Non-Founders
    "República Dominicana",
    "Belice",
    "México",                        # 10. Extra-Regional
    "China (Taiwán)",
    "Argentina",
    "Colombia",
    "España",
    "Corea",
    "Cuba",
    "Regional"                       # 17. Programmatic
]

# --- DATA COLUMN DEFINITIONS ---
ENTITY_COL = "pais"
TIME_COL = "anio_aprobacion"
FEATURE_COLS = ["monto_aprobado_usd", "cantidad_aprobaciones"]
