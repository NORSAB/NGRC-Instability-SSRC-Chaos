"""
Structural Optimization and Topology Masking
"""
import numpy as np
import sys
import os

# Ensure legacy folder is in path for TransitionMatrix internal imports
# TransitionMatrix.py does 'from nnspsolver import nnspsolver'
current_dir = os.path.dirname(os.path.abspath(__file__))
legacy_dir = os.path.join(current_dir, 'legacy')
if legacy_dir not in sys.path:
    sys.path.append(legacy_dir)

try:
    from legacy.TransitionMatrix import TransitionMatrix
except ImportError:
    # Fallback/Direct import attempts if package structure varies
    try:
        from .legacy.TransitionMatrix import TransitionMatrix
    except ImportError:
        # If running from root and src is package
        from src.models.legacy.TransitionMatrix import TransitionMatrix

from config.hyperparameters import TEST_START_YEAR

try:
    from config.hyperparameters import ESTIMATOR_MODE
except ImportError:
    ESTIMATOR_MODE = "legacy"


def _rowwise_nnls_matrix(data_matrix: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Solución EXACTA de la ecuación (3) del artículo (separable por filas):

        P* = argmin_{P >= 0, P en M} sum_t || z_{t+1} - P z_t ||^2

    Cada fila i es un NNLS independiente sobre las columnas que permite la máscara.
    A diferencia del solver legado (TransitionMatrix), NO impone normalización de
    columnas a suma 1 — ese paso no forma parte de la ecuación publicada y bajo el
    LOO infla la persistencia por construcción (ver HALLAZGO_C1_LOO_HUB.md).
    """
    from scipy.optimize import nnls as _nnls
    n, T = data_matrix.shape
    X0 = data_matrix[:, :-1]   # estados en t
    X1 = data_matrix[:, 1:]    # estados en t+1
    P = np.zeros((n, n))
    for i in range(n):
        cols = np.where(mask[i, :] > 0)[0]
        if len(cols) == 0:
            continue
        A = X0[cols, :].T                       # (T-1, m)
        coef, _ = _nnls(A, X1[i, :])
        P[i, cols] = coef
    return P

def _solve_P(data_matrix: np.ndarray, mask: np.ndarray, sample_size: int, n: int) -> np.ndarray:
    """Despacha al solver según ESTIMATOR_MODE (misma ventana de transiciones en ambos)."""
    if ESTIMATOR_MODE == "paper_eq":
        return _rowwise_nnls_matrix(data_matrix[:, :sample_size + 1], mask)
    return TransitionMatrix(data=data_matrix, SM=mask, sample_size=sample_size,
                            error=1e-6, nz=n)


def build_topology_mask(entities: list, hub_name: str) -> np.ndarray:
    """
    Constructs the 16+1 Hub-and-Spoke mask (Paper Sec II-E).
    """
    n = len(entities)
    mask = np.zeros((n, n), int)
    
    try:
        h_idx = entities.index(hub_name)
    except ValueError:
        return np.eye(n, dtype=int)
        
    for i in range(n):
        for j in range(n):
            if i == j or i == h_idx or j == h_idx:
                mask[i, j] = 1
    return mask

def estimate_coupling_matrix(entities: list, z_data: dict, mask: np.ndarray, hub_name: str,
                             training_end_year: int = None, loo_strategy: bool = False,
                             hub_loo_z: dict = None) -> np.ndarray:
    """
    Estimates the Coupling Matrix P* using the SSRC TransitionMatrix solver.

    Args:
        entities: List of entity names (order matters).
        z_data: Dictionary of {entity: {'years': [...], 'z': [...]}}.
        mask: Topology mask (binary matrix).
        hub_name: Name of the Hub entity.
        training_end_year: Last year to include in training (inclusive). If None, uses all available pre-test.
        loo_strategy: If True, applies Leave-One-Out reconstruction for the Hub.
        hub_loo_z: Optional {spoke: {'years': [...], 'z': [...]}} with the hub re-embedded from the
            RAW portfolio minus that spoke (fix C1). If provided, replaces the legacy latent-sum
            reconstruction: log1p/TCROC/tanh/PCA are nonlinear, so subtracting in latent space is
            NOT equivalent to removing k from the raw portfolio. See HALLAZGO_C1_LOO_HUB.md.

    Returns:
        P_matrix: Estimated coupling matrix (stochastic cols).
    """
    n = len(entities)
    
    # 1. Align Data
    # Find common years intersection up to training cutoff
    all_years = set()
    for e in entities:
        all_years.update(z_data[e]["years"])
    all_years = sorted(list(all_years))
    
    cutoff = training_end_year if training_end_year is not None else (TEST_START_YEAR - 1)
    train_years = [y for y in all_years if y <= cutoff]
    
    # We need at least 2 points to have 1 transition
    if len(train_years) < 2:
        raise ValueError(f"Insufficient training data. Found {len(train_years)} years, need at least 2.")
        
    T_indices = len(train_years)
    # TransitionMatrix expects data of shape (n, Total_Samples)
    # It internally uses samples 0..sample_size as X0 and 1..sample_size+1 as X1
    # So if we have T_indices years, we have T_indices-1 transitions.
    # We pass the full block. sample_size should be T_indices - 1.
    
    data_matrix = np.zeros((n, T_indices))
    
    for i, ent in enumerate(entities):
        e_years = z_data[ent]["years"]
        e_vals = z_data[ent]["z"]
        # Map year -> val
        y_map = dict(zip(e_years, e_vals))
        
        for t_idx, yr in enumerate(train_years):
            data_matrix[i, t_idx] = y_map.get(yr, 0.0)
            
    sample_size = T_indices - 1
    
    # 2. Estimate P
    # If LOO is disabled, simple single call
    if not loo_strategy:
        P_est = _solve_P(data_matrix, mask, sample_size, n)
        return P_est # A[i,j] = influence of j on i. Rows are targets.
        
    # 3. LOO Strategy
    h_idx = -1
    if hub_name in entities:
        h_idx = entities.index(hub_name)
    
    P_final = np.zeros((n, n))
    
    for k in range(n):
        # Prepare data for target k
        data_k = data_matrix.copy()
        
        if loo_strategy and h_idx >= 0 and k != h_idx:
            if hub_loo_z is not None and entities[k] in hub_loo_z:
                # Nodo central LOO re-incrustado desde la cartera cruda
                ymap = dict(zip(hub_loo_z[entities[k]]["years"], hub_loo_z[entities[k]]["z"]))
                data_k[h_idx, :] = np.array([ymap.get(y, 0.0) for y in train_years], dtype=float)
            else:
                # Agregación sintética directa en espacio latente
                synthetic_hub = np.zeros(T_indices)
                for j in range(n):
                    if j != h_idx and j != k:
                        synthetic_hub += data_matrix[j, :]
                data_k[h_idx, :] = synthetic_hub

        # Estimate (solver segun ESTIMATOR_MODE)
        try:
            P_k = _solve_P(data_k, mask, sample_size, n)
            # Take the k-th row (target k equation)
            P_final[k, :] = P_k[k, :]

        except Exception as e:
            print(f"Warning: LOO estimation failed for entity {entities[k]}: {e}")
            # Fallback? zero row

    return P_final


def bootstrap_coupling_matrix(entities: list, z_data: dict, mask: np.ndarray, hub_name: str,
                              n_boot: int = 1000, seed: int = 42, hub_loo_z: dict = None):
    """
    Performs bootstrap resampling (Monte Carlo with noise) to estimate confidence intervals for P*.

    Args:
        entities: List of entity names.
        z_data: Dictionary of data.
        mask: Topology mask.
        hub_name: Hub entity.
        n_boot: Number of bootstrap iterations.
        seed: Random seed.
        hub_loo_z: Diccionario opcional de incrustaciones LOO del nodo central.

    Returns:
        P_mean: Mean coupling matrix.
        P_std: Standard deviation of coefficients.
        P_cv: Coefficient of Variation (Std/Mean).
        P_sig: Significance mask (True if CV < 0.25).
    """
    n = len(entities)
    P_stack = []
    
    # Prepare base data
    all_years = sorted(list(set().union(*[z_data[e]["years"] for e in entities])))
    cutoff = TEST_START_YEAR - 1
    train_years = [y for y in all_years if y <= cutoff]
    T_indices = len(train_years)
    
    if T_indices < 2: return np.zeros((n,n)), np.zeros((n,n)), np.zeros((n,n)), np.zeros((n,n), bool)
    
    sample_size = T_indices - 1
    
    data_matrix = np.zeros((n, T_indices))
    for i, ent in enumerate(entities):
        y_map = dict(zip(z_data[ent]["years"], z_data[ent]["z"]))
        for t_idx, yr in enumerate(train_years):
            data_matrix[i, t_idx] = y_map.get(yr, 0.0)
            
    # Bootstrap Strategy: Monte Carlo noise injection + LOO Reconstruction
    rng = np.random.RandomState(seed)
    noise_level = 0.05 # 5% noise relative to std dev
    
    data_std = np.std(data_matrix, axis=1, keepdims=True)
    
    # Pre-calculate Hub index
    h_idx = -1
    if hub_name in entities:
        h_idx = entities.index(hub_name)

    # Pre-alineación de incrustaciones LOO del nodo central
    H_loo, has_loo = None, None
    if hub_loo_z is not None and h_idx >= 0:
        H_loo = np.zeros((n, T_indices))
        has_loo = np.zeros(n, dtype=bool)
        for k, ent in enumerate(entities):
            if ent in hub_loo_z:
                ymap = dict(zip(hub_loo_z[ent]["years"], hub_loo_z[ent]["z"]))
                H_loo[k, :] = [ymap.get(y, 0.0) for y in train_years]
                has_loo[k] = True
        H_std = np.std(H_loo, axis=1, keepdims=True)

    for _ in range(n_boot):
        # Inyección de perturbación gaussiana
        noise = rng.normal(0, 1, size=data_matrix.shape) * (noise_level * (data_std + 1e-9))
        data_noisy = data_matrix + noise
        if H_loo is not None:
            H_noisy = H_loo + rng.normal(0, 1, size=H_loo.shape) * (noise_level * (H_std + 1e-9))

        P_boot_iter = np.zeros((n, n))

        # Bucle LOO para cada entidad k
        for k in range(n):
            data_k = data_noisy.copy()

            if h_idx >= 0 and k != h_idx:
                if H_loo is not None and has_loo[k]:
                    data_k[h_idx, :] = H_noisy[k, :]
                else:
                    synthetic_hub = np.zeros(T_indices)
                    for j in range(n):
                        if j != h_idx and j != k:
                            synthetic_hub += data_noisy[j, :]
                    data_k[h_idx, :] = synthetic_hub

            try:
                P_k = _solve_P(data_k, mask, sample_size, n)
                # Take the k-th row (target k equation)
                P_boot_iter[k, :] = P_k[k, :]
            except Exception:
                pass
        
        P_stack.append(P_boot_iter)
            
    P_stack = np.array(P_stack)
    
    if len(P_stack) == 0:
        return np.zeros((n,n)), np.zeros((n,n)), np.zeros((n,n)), np.zeros((n,n), bool)
        
    P_mean = np.mean(P_stack, axis=0)
    P_std = np.std(P_stack, axis=0)
    P_cv = P_std / (np.abs(P_mean) + 1e-9)
    # Significant if Dispersion is low (e.g. CV < 0.25)
    P_sig = P_cv < 0.25
    
    return P_mean, P_std, P_cv, P_sig

