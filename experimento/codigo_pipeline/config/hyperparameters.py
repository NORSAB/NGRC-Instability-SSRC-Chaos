"""
Hyperparameters for TCROC operator and Reservoir Computing architecture.
"""

# --- HYPERPARAMETER GRID ---
# Window size for temporal convolution (TCROC operator)
W_VALUES = [2, 3, 4, 5]

# Exponential decay factor lambda for temporal weighting
LAMBDA_VALUES = [
    0.60, 0.62, 0.64, 0.66, 0.68, 0.70, 0.72, 0.74, 0.76, 0.78,
    0.80, 0.82, 0.84, 0.86, 0.88, 0.90, 0.92, 0.94, 0.96, 0.98,
    0.99, 1.00
]

# --- RESERVOIR COMPUTING PARAMETERS ---
RES_DIM = 50                  # Reservoir state space dimension d_res
SPECTRAL_RADIUS = 0.95        # Spectral radius rho(W_res) <= 0.99 ensuring Echo State Property
RES_DENSITY = 0.05            # Sparsity density of reservoir adjacency matrix W_res
RES_INPUT_SCALE = 1.0         # Input weight matrix scaling factor
READOUT_MODE = "pca"          # Latent dimension reduction mode (PCA first principal component)
RES_LEAK = 1.00               # Leaking rate for discrete-time reservoir state update (1.0 = standard ESN)
MIN_TRANSITIONS = 3           # Minimum historical observations required for entity inclusion

# --- VALIDATION & FORECASTING PROTOCOL ---
TEST_START_YEAR = 2020        # Out-of-sample backtest start period
TEST_END_YEAR = 2024          # Out-of-sample backtest end period
FORECAST_HORIZON = 5          # Multi-step projection horizon H
MAX_SUSTAINABLE_GROWTH = 1.05 # Upper bound scaling factor for spectral radius calibration
USE_LOO_STRATEGY = True       # Leave-One-Out protocol for central node identification
ESTIMATOR_MODE = "paper_eq"   # Canonical row-separable Non-Negative Least Squares (NNLS) solver
HUB_LOO_MODE = "raw"          # Portfolio aggregation on raw series prior to nonlinear embedding
