"""
Evaluation Metrics — v6 Mejorado
=================================
Cambios:
  MEJORA-2: evaluate_metrics_oos ahora retorna per-entity breakdown
  MEJORA-3: Trend Accuracy incluida en output
"""
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error


def _hub_loo_maps(hub_loo_z):
    """Precompute year->z maps for the true-LOO hub embeddings (fix C1)."""
    if not hub_loo_z:
        return {}
    return {ent: dict(zip(d["years"], d["z"])) for ent, d in hub_loo_z.items()}


def evaluate_frobenius_oos(p_matrix: np.ndarray, entities: list, z_data: dict,
                           mask: np.ndarray, test_start: int,
                           test_end: int = None, hub_loo_z: dict = None,
                           hub_name: str = None) -> tuple:
    """
    Calculates the Relative Frobenius Reconstruction Error (OOS).
    
    This is the metric used in the paper for hyperparameter selection:
        Err = Σ_i ||y_val_i - X_val_i · P[i,:]|| / Σ_i ||y_val_i||
    
    For each entity i, we collect target years y in the explicit validation
    window, predict z_y = P[i,:] · z_{y-1} (using only mask-allowed sources),
    and accumulate the Frobenius norm of the error relative to the true values.
    
    Returns:
        (frobenius_error, coverage): Tuple of (relative error, number of valid transitions)
    """
    state_maps = {e: dict(zip(z_data[e]["years"], z_data[e]["z"])) for e in entities}
    loo_maps = _hub_loo_maps(hub_loo_z)
    N = len(entities)

    total_num = 0.0  # Numerator: sum of ||y - yhat||
    total_den = 0.0  # Denominator: sum of ||y||
    coverage = 0

    for i, target_ent in enumerate(entities):
        # Columns allowed by topology mask
        cols = [j for j in range(N) if mask[i, j] == 1]
        if not cols:
            continue

        # Build validation dataset with target years inside [test_start, test_end].
        Xv, yv = [], []
        years_i = sorted(state_maps[target_ent].keys())

        for target_year in years_i:
            if target_year < test_start or (
                test_end is not None and target_year > test_end
            ):
                continue
            source_year = target_year - 1
            if source_year not in state_maps[target_ent]:
                continue

            # Check all source entities have data at the preceding time.
            ok = True
            xrow = []
            for j in cols:
                ej = entities[j]
                # Usar representación LOO correspondiente si el regresor es el nodo central
                if hub_name is not None and ej == hub_name and target_ent in loo_maps:
                    if source_year not in loo_maps[target_ent]:
                        ok = False
                        break
                    xrow.append(loo_maps[target_ent][source_year])
                    continue
                if source_year not in state_maps[ej]:
                    ok = False
                    break
                xrow.append(state_maps[ej][source_year])
            
            if ok:
                Xv.append(xrow)
                yv.append(state_maps[target_ent][target_year])
        
        if not yv:
            continue
        
        Xv = np.asarray(Xv, dtype=float)
        yv = np.asarray(yv, dtype=float)
        
        # Predict: yhat = Xv @ w where w = P[i, cols]
        w = np.array([p_matrix[i, j] for j in cols], dtype=float)
        yhat = Xv @ w
        
        total_num += np.linalg.norm(yv - yhat)
        total_den += np.linalg.norm(yv) + 1e-12
        coverage += len(yv)
    
    err = total_num / (total_den + 1e-12)
    return err, coverage


def evaluate_metrics_oos(p_matrix: np.ndarray, entities: list, z_data: dict,
                         mask: np.ndarray, test_start: int,
                         test_end: int = None, hub_loo_z: dict = None,
                         hub_name: str = None) -> dict:
    """
    Calculates OOS Error (NRMSE) and MASE for the validation period.
    
    Returns:
        dict with keys: NRMSE, MASE, Count, TrendAcc, per_entity
    """
    all_years = set().union(*[z_data[e]["years"] for e in entities])
    val_years = sorted([
        y for y in all_years
        if y >= test_start and (test_end is None or y <= test_end)
    ])
    
    if not val_years: return {"NRMSE": np.inf, "MASE": np.inf, "Count": 0, "TrendAcc": 0.0, "per_entity": {}}

    sq_error_sum = 0.0
    abs_error_sum = 0.0
    y_true_all = []
    
    naive_mae_sum = 0.0
    naive_count = 0
    
    # Registro por entidad y métricas de dirección
    entity_errors = {e: {"abs_errors": [], "sq_errors": [], "y_true": [], "y_pred": [], "years": []} for e in entities}
    
    trend_correct = 0
    trend_total = 0
    
    state_maps = {e: dict(zip(z_data[e]["years"], z_data[e]["z"])) for e in entities}
    loo_maps = _hub_loo_maps(hub_loo_z)

    count = 0
    for i, target_ent in enumerate(entities):
        train_vals = [v for y, v in state_maps[target_ent].items() if y < test_start]
        if len(train_vals) > 1:
            naive_diffs = np.abs(np.diff(train_vals))
            naive_mae_sum += np.sum(naive_diffs)
            naive_count += len(naive_diffs)

        source_indices = [j for j in range(len(entities)) if p_matrix[i, j] > 0]
        if not source_indices: continue

        for t in val_years:
            if t not in state_maps[target_ent]: continue
            prev_t = t - 1
            if prev_t not in state_maps[target_ent]: continue

            # Regresor del nodo central según asignación LOO
            row_vals = []
            for j in source_indices:
                ej = entities[j]
                if hub_name is not None and ej == hub_name and target_ent in loo_maps:
                    row_vals.append(loo_maps[target_ent].get(prev_t, np.nan))
                else:
                    row_vals.append(state_maps[ej].get(prev_t, np.nan))
            if np.isnan(row_vals).any(): continue
            
            y_pred = np.dot(row_vals, p_matrix[i, source_indices])
            y_true = state_maps[target_ent][t]
            
            sq_error_sum += (y_true - y_pred) ** 2
            abs_error_sum += np.abs(y_true - y_pred)
            y_true_all.append(y_true)
            count += 1
            
            # ── MEJORA-2: Per-entity ──
            entity_errors[target_ent]["abs_errors"].append(np.abs(y_true - y_pred))
            entity_errors[target_ent]["sq_errors"].append((y_true - y_pred)**2)
            entity_errors[target_ent]["y_true"].append(y_true)
            entity_errors[target_ent]["y_pred"].append(y_pred)
            entity_errors[target_ent]["years"].append(t)
            
            # ── MEJORA-3: Trend accuracy ──
            true_dir = np.sign(y_true - state_maps[target_ent][prev_t])
            pred_dir = np.sign(y_pred - state_maps[target_ent][prev_t])
            if true_dir == pred_dir:
                trend_correct += 1
            trend_total += 1

    if count == 0: return {"NRMSE": np.inf, "MASE": np.inf, "Count": 0, "TrendAcc": 0.0, "per_entity": {}}

    rmse = np.sqrt(sq_error_sum / count)
    range_y = np.max(y_true_all) - np.min(y_true_all)
    nrmse = rmse / (range_y + 1e-12)
    
    denom = naive_mae_sum / (naive_count + 1e-12)
    mase = (abs_error_sum / count) / denom
    
    trend_acc = trend_correct / (trend_total + 1e-12)
    
    # ── MEJORA-2: Per-entity MASE ──
    per_entity = {}
    for ent in entities:
        ee = entity_errors[ent]
        if len(ee["abs_errors"]) > 0:
            ent_mae = np.mean(ee["abs_errors"])
            ent_mase = ent_mae / denom if denom > 0 else np.inf
            ent_rmse = np.sqrt(np.mean(ee["sq_errors"]))
            per_entity[ent] = {
                "MASE": ent_mase, "RMSE": ent_rmse,
                "MAE": ent_mae, "Count": len(ee["abs_errors"]),
                "years": ee["years"], "y_true": ee["y_true"], "y_pred": ee["y_pred"]
            }
    
    return {
        "NRMSE": nrmse, "MASE": mase, "Count": count, 
        "TrendAcc": trend_acc, "per_entity": per_entity
    }


def calculate_metrics(y_true, y_pred, y_hist):
    """Calculates NRMSE, MASE, and Trend Accuracy."""
    if len(y_true) == 0: return np.nan, np.nan, np.nan
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    data_range = np.max(y_true) - np.min(y_true)
    nrmse = rmse / (data_range + 1e-9) if data_range > 0 else 0.0
    
    if len(y_hist) > 1:
        naive_mae = np.mean(np.abs(np.diff(y_hist)))
        forecast_mae = mean_absolute_error(y_true, y_pred)
        mase = forecast_mae / (naive_mae + 1e-9)
    else:
        mase = np.nan
        
    if len(y_true) < 2: return nrmse, mase, np.nan
    diff_true = np.diff(y_true)
    diff_pred = np.diff(y_pred)
    acc = np.mean(np.sign(diff_true) == np.sign(diff_pred))
    
    return nrmse, mase, acc
