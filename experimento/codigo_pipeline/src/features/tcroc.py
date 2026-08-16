"""
TCROC Feature Extraction
"""
import numpy as np
from config.topology import TIME_COL, ENTITY_COL, FEATURE_COLS

def tcroc_alpha(series: np.ndarray, w_size: int, decay: float, eps: float = 1e-12) -> np.ndarray:
    """
    Computes the Temporal Consistent Rate of Change (TCROC).
    Mathematically equivalent to local Weighted Least Squares (WLS).
    """
    x = np.asarray(series, dtype=float)
    t_len = len(x)
    alpha = np.full(t_len, np.nan)
    
    if t_len < w_size + 1:
        return alpha
    
    weights = np.array([decay**k for k in range(w_size)], dtype=float)
    weights = weights / (weights.sum() + eps)
    
    for t in range(w_size, t_len):
        v_curr = x[t-w_size+1 : t+1]
        v_prev = x[t-w_size : t]
        w_rev = weights[::-1]
        
        num = np.sum(w_rev * v_curr * v_prev)
        den = np.sum(w_rev * v_prev**2) + eps
        alpha[t] = (num / den) - 1.0
        
    return alpha


def invert_tcroc_next(history, alpha_next: float, w_size: int, decay: float,
                      eps: float = 1e-12) -> float:
    """Recover the next raw level implied by a forecast TCROC coefficient.

    ``tcroc_alpha`` is estimated on ``log1p(level)``. Multiplying the raw level
    by ``1 + alpha`` is therefore not its inverse. This function solves the
    weighted normal equation for the unknown next log-level and maps it back
    with ``expm1``.
    """
    raw = np.maximum(np.asarray(history, dtype=float), 0.0)
    if len(raw) < w_size:
        raise ValueError(f"Need at least {w_size} historical levels")

    prev = np.log1p(raw[-w_size:])
    weights = np.array([decay**k for k in range(w_size)], dtype=float)
    weights /= weights.sum() + eps
    w_rev = weights[::-1]

    denominator = np.sum(w_rev * prev**2) + eps
    known_numerator = np.sum(w_rev[:-1] * prev[1:] * prev[:-1])
    last_term = w_rev[-1] * prev[-1]
    if abs(last_term) <= eps:
        return float(raw[-1])

    next_log = (((1.0 + alpha_next) * denominator) - known_numerator) / last_term
    next_log = float(np.clip(next_log, 0.0, 50.0))
    return float(np.expm1(next_log))


def build_alpha_by_entity(df, entities, w_size, decay):
    """
    Extracts multivariate feature matrices for each entity using Log-TCROC.
    Applies log(1+x) transformation as per paper Section II-A.
    """
    results = {}
    for ent in entities:
        sub = df[df[ENTITY_COL] == ent].groupby(TIME_COL, as_index=False)[FEATURE_COLS].sum()
        years = sub[TIME_COL].values.astype(int)
        
        if len(sub) < w_size + 2:
            continue
            
        mats = []
        for col in FEATURE_COLS:
            raw_vals = np.maximum(sub[col].values.astype(float), 0)
            log_vals = np.log1p(raw_vals)
            mats.append(tcroc_alpha(log_vals, w_size, decay)[w_size:])
            
        alpha_matrix = np.vstack(mats)
        
        if alpha_matrix.shape[1] > 1:
            results[ent] = {
                "years": years[w_size:],
                "alpha": alpha_matrix,
                "alpha_scale": alpha_matrix[0] - alpha_matrix[1],
                "raw_vals": sub[FEATURE_COLS].values[w_size:]
            }
    return results
