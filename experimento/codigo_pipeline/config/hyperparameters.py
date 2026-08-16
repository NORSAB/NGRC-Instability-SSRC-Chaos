"""
Hyperparameters for TCROC and Reservoir Computing
"""

# --- HYPERPARAMETER GRID ---
# Window size for TCROC operator
W_VALUES = [2, 3, 4, 5]

# Exponential decay factor for TCROC
LAMBDA_VALUES = [
    0.60, 0.62, 0.64, 0.66, 0.68, 0.70, 0.72, 0.74, 0.76, 0.78,
    0.80, 0.82, 0.84, 0.86, 0.88, 0.90, 0.92, 0.94, 0.96, 0.98,
    0.99, 1.00
]

# --- RESERVOIR COMPUTING PARAMETERS ---
# Todos seleccionados sobre NUESTROS datos (cartera BCIE, anual), protocolo v2 sin fuga temporal,
# criterio Frobenius OOS 2020-2024 / MASE, semillas 7, 19, 31. No heredados de la tesis.
RES_DIM = 50              # Dimension of the reservoir state space (meseta dentro del ruido de semillas)
SPECTRAL_RADIUS = 0.95    # Radio espectral del reservorio (<=0.99 por la propiedad de estado de eco)
RES_DENSITY = 0.05        # Densidad de W_res (en la meseta de configs equivalentes)
RES_INPUT_SCALE = 1.0     # Escala de entrada (W_in *= s_in). PROBADA y NO adoptada: en la ablación parecía
                          # ayudar, pero al integrarla al pipeline completo la ganancia es marginal y dentro
                          # del ruido entre semillas (MASE 0.885->0.877; razón vs naive 0.856->0.863, sin
                          # mejora real). Se conserva a=1.0. Ver HALLAZGOS_ABLACION_SSRC.md.
READOUT_MODE = "pca"      # Lectura del estado. PLS (supervisada) PROBADA y NO adoptada: la mejora de la
                          # ablación NO sobrevive la integración (la grilla re-elige lambda peor, el MASE del
                          # titular sube a ~1.08). Se conserva PCA(1), el modelo verificado.
RES_LEAK = 1.00           # Tasa de fuga del Leaky-ESN, SELECCIONADA sobre nuestros datos (no heredada).
                          # Se probó a in [0.3..1.0] (run_leaky_sweep / run_select_reservoir). La fuga
                          # baja el Frobenius del operador, pero es un artefacto de SOBRE-SUAVIZADO: la
                          # habilidad predictiva real (ratio SSRC/Naive del MASE de soporte común) queda
                          # IGUAL (0.856 con o sin fuga), mientras el MASE titular se ve peor (denominador
                          # reescalado). La tesis usaba fuga porque sus datos eran semanales (dinámica
                          # rápida); con datos ANUALES, a=1 es lo óptimo en la métrica que importa.
MIN_TRANSITIONS = 3       # Minimum required transitions for entity admissibility

# --- VALIDATION & FORECASTING PROTOCOL ---
TEST_START_YEAR = 2020    # Start of the exogenous shock period
TEST_END_YEAR = 2024      # Last year in the model-selection/backtest window
FORECAST_HORIZON = 5      # Number of years to project
MAX_SUSTAINABLE_GROWTH = 1.05 # Gamma factor for Spectral Calibration
USE_LOO_STRATEGY = True   # Enable Leave-One-Out for Hub identification
ESTIMATOR_MODE = "paper_eq"  # Solver de P* (auditoría C1, 2026-06-15):
                          #   "paper_eq" -> resuelve EXACTAMENTE la ec. (3) del artículo:
                          #                 argmin_{P>=0, mascara} sum_t ||z_{t+1} - P z_t||^2,
                          #                 que es separable por filas (NNLS por fila). Sin pasos extra.
                          #   "legacy"   -> TransitionMatrix (ajuste conjunto + normalización de columnas
                          #                 a suma 1). La normalización NO está en la ecuación del paper y
                          #                 bajo LOO infla la persistencia por construcción (P[k,k]->1
                          #                 cuando P[hub,k]->0 al excluir k del hub). Ver HALLAZGO_C1_LOO_HUB.md.
HUB_LOO_MODE = "raw"      # Cómo se construye el hub-sin-k del LOO (fix C1, 2026-06-15):
                          #   "raw"    -> OFICIAL: se resta el país k de la cartera CRUDA (exacto, el hub
                          #               es suma lineal de montos) y se RE-INCRUSTA (log1p/TCROC/tanh/PCA).
                          #   "latent" -> método anterior (suma de estados latentes de los demás radios).
                          #               DEFLACTA el acoplamiento por escala (~20 p.p.) y por la
                          #               no-linealidad (~11 p.p.). Ver HALLAZGO_C1_LOO_HUB.md.
