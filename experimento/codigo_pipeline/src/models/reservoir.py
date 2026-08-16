"""
SSRC Reservoir Computing Model
"""
import numpy as np

def make_reservoir(d_in: int = 2, d_res: int = 50, rho: float = 0.95, 
                   density: float = 0.08, seed: int = 7):
    """
    Initializes SSRC reservoir weights ensuring spectral stability.
    """
    rng = np.random.default_rng(seed)
    w_in = rng.normal(0, 1, (d_res, d_in))
    w_res = rng.normal(0, 1, (d_res, d_res)) * (rng.uniform(0, 1, (d_res, d_res)) < density)
    
    try:
        eigenvalues = np.linalg.eigvals(w_res)
        max_eig = np.max(np.abs(eigenvalues)) + 1e-12
        w_res *= (rho / max_eig)
    except Exception:
        w_res *= rho
        
    return w_in, w_res


def run_reservoir(alpha_matrix: np.ndarray, w_in: np.ndarray, w_res: np.ndarray,
                  leak: float = None) -> np.ndarray:
    """
    Projects input dynamics into the high-dimensional latent space H.
    Output H is (D_res x T).

    Leaky-integrator ESN update (Jaeger et al. 2007), as in the thesis SSRC:
        h_t = (1 - a) h_{t-1} + a * tanh(W_in u_t + W_res h_{t-1}),  a = leak in (0, 1].
    leak = 1.0 recovers the classic ESN. When leak is None (the default) the value is
    read from config.hyperparameters.RES_LEAK, the rate SELECTED on the BCIE data, so the
    whole experiment suite stays consistent. Sweep scripts pass leak explicitly.
    """
    if leak is None:
        try:
            from config.hyperparameters import RES_LEAK as _RES_LEAK
            leak = _RES_LEAK
        except Exception:
            leak = 1.0
    steps = alpha_matrix.shape[1]
    dim_res = w_res.shape[0]

    h_states = np.zeros((dim_res, steps))
    h_curr = np.zeros(dim_res)
    a = leak

    for t in range(steps):
        h_curr = (1.0 - a) * h_curr + a * np.tanh(w_in @ alpha_matrix[:, t] + w_res @ h_curr)
        h_states[:, t] = h_curr

    return h_states
