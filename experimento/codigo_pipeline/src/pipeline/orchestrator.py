"""
Pipeline Orchestrator for TCROC and Reservoir Computing.
Executes data ingestion, grid search, final model fitting, readout evaluation,
multi-step forecasting, and bootstrap validation.
"""
import os
import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.decomposition import PCA

from ..models.legacy.nnspsolver import nnspsolver

from config.settings import GLOBAL_SEED, FIG_DPI
from config.hyperparameters import (
    W_VALUES, LAMBDA_VALUES, RES_DIM, SPECTRAL_RADIUS, RES_DENSITY, RES_LEAK,
    RES_INPUT_SCALE, READOUT_MODE, HUB_LOO_MODE,
    TEST_START_YEAR, TEST_END_YEAR, FORECAST_HORIZON, MAX_SUSTAINABLE_GROWTH
)
from sklearn.cross_decomposition import PLSRegression
from config.topology import SYNTHETIC_HUB_NAME, ENTITY_COL, TIME_COL, FEATURE_COLS, HIERARCHICAL_ORDER

from ..data.ckan_loader import CKANLoader
from ..data.preprocessor import clean_dataframe
from ..data.aggregator import aggregate_data

from ..features.tcroc import build_alpha_by_entity, invert_tcroc_next

from ..models.reservoir import make_reservoir, run_reservoir
from ..models.optimization import build_topology_mask, estimate_coupling_matrix, bootstrap_coupling_matrix
from ..models.metric_tools import evaluate_metrics_oos, evaluate_frobenius_oos

from ..visualization.ieee_styles import apply_ieee_style
from ..visualization.timeline import plot_timeline
from ..visualization.sensitivity import plot_sensitivity_heatmap
from ..visualization.structure import plot_structure_matrix
from ..visualization.spectrum import plot_eigenvalue_spectrum
from ..visualization.readout import plot_hub_readout, plot_hub_projection, plot_regime_decomposition

class MLOpsPipeline:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
        apply_ieee_style()
        self.df_final = None
        self.best_w = None
        self.best_lam = None
        self.z_final = None
        self.p_matrix_active = None
        self.active_ents = None
        # Almacenar transformadores PCA y escaladores por entidad
        self.pca_transformers = {}
        self.scalers = {}

    def _build_embeddings(self, alpha_data, entities, fit_end_year, store=False):
        """Fit preprocessing only on the training period, then transform all years."""
        w_in, w_res = make_reservoir(
            d_res=RES_DIM, rho=SPECTRAL_RADIUS,
            density=RES_DENSITY, seed=GLOBAL_SEED
        )
        w_in = w_in * RES_INPUT_SCALE   # input scaling selected by ablation (operating point of tanh)
        result = {}
        for ent in entities:
            years = np.asarray(alpha_data[ent]["years"])
            train_mask = years <= fit_end_year
            if np.sum(train_mask) < 2:
                continue

            a_raw = alpha_data[ent]["alpha"]
            scaler = StandardScaler().fit(a_raw[:, train_mask].T)
            a_std = scaler.transform(a_raw.T).T
            h_states = run_reservoir(a_std, w_in, w_res, leak=RES_LEAK)

            if READOUT_MODE == "pls":
                # Supervised readout: orient the latent toward the amount rate (selected by ablation).
                # PLS scores maximise covariance with the target, so they are already positively
                # aligned; no sign flip is needed and the transformer stays consistent for forecasting.
                reducer = PLSRegression(n_components=1)
                reducer.fit(h_states[:, train_mask].T, a_raw[0, train_mask])
                z = reducer.transform(h_states.T).flatten()
            else:
                reducer = PCA(n_components=1).fit(h_states[:, train_mask].T)
                z = reducer.transform(h_states.T).flatten()
                # PCA signs are arbitrary. Orient every entity against its amount
                # feature on the training sample before estimating nonnegative links.
                corr = np.corrcoef(z[train_mask], a_raw[0, train_mask])[0, 1]
                if np.isfinite(corr) and corr < 0:
                    reducer.components_ *= -1
                    z *= -1

            item = {"years": years, "z": z}
            if store:
                item.update({
                    "H": h_states,
                    "alpha_scale": alpha_data[ent]["alpha_scale"],
                    "alpha_raw": a_raw,
                })
                self.scalers[ent] = scaler
                self.pca_transformers[ent] = reducer
            result[ent] = item
        return result

    def _build_hub_loo_z(self, entities, w_size, decay, fit_end_year):
        """Construye las trayectorias Leave-One-Out (LOO) del nodo central a nivel de cartera cruda.

        La cartera central se calcula sustrayendo la serie temporal de cada entidad k
        antes de aplicar la transformación no lineal (log1p -> TCROC -> reservorio -> PCA).
        Devuelve {spoke: {'years', 'z'}} o None si HUB_LOO_MODE != 'raw'.
        """
        if HUB_LOO_MODE != "raw":
            return None
        base = self.df_final.groupby([ENTITY_COL, TIME_COL], as_index=False)[FEATURE_COLS].sum()
        hub_s = base[base[ENTITY_COL] == SYNTHETIC_HUB_NAME].set_index(TIME_COL)[FEATURE_COLS]
        spokes = [e for e in entities if e != SYNTHETIC_HUB_NAME]
        frames = []
        for k in spokes:
            k_s = base[base[ENTITY_COL] == k].set_index(TIME_COL)[FEATURE_COLS]
            d = hub_s.sub(k_s, fill_value=0.0).clip(lower=0.0).reset_index()
            d[ENTITY_COL] = "__LOO__" + k
            frames.append(d)
        df_loo = pd.concat(frames, ignore_index=True)
        names = ["__LOO__" + k for k in spokes]
        alpha_loo = build_alpha_by_entity(df_loo, names, w_size, decay)
        z_loo = self._build_embeddings(
            alpha_loo, [nm for nm in names if nm in alpha_loo], fit_end_year
        )
        return {k: z_loo["__LOO__" + k] for k in spokes if "__LOO__" + k in z_loo}

    def step_1_data_ingestion(self):
        print("\n=== STEP 1: DATA INGESTION ===")
        loader = CKANLoader()
        df_raw = loader.fetch_data()
        with open(os.path.join(self.output_dir, "data_provenance.json"), "w", encoding="utf-8") as f:
            json.dump(loader.last_metadata, f, indent=2, ensure_ascii=False)
        df_clean = clean_dataframe(df_raw)
        self.df_final = aggregate_data(df_clean)
        print(f"Data aggregated. Shape: {self.df_final.shape}")
        
        # Plot Timeline
        plot_timeline(self.df_final.copy(), os.path.join(self.images_dir, "timeline.png"))

    def step_2_grid_search(self):
        print("\n=== STEP 2: SENSITIVITY ANALYSIS (GRID SEARCH) ===")
        unique_entities = sorted(self.df_final[ENTITY_COL].dropna().unique().tolist())
        results_log = []
        
        for w_size in W_VALUES:
            for decay in LAMBDA_VALUES:
                # Feature Extraction
                alpha_data = build_alpha_by_entity(self.df_final, unique_entities, w_size, decay)
                active_entities = sorted(alpha_data.keys())
                
                if SYNTHETIC_HUB_NAME not in active_entities: continue

                z_data = self._build_embeddings(
                    alpha_data, active_entities, TEST_START_YEAR - 1
                )
                active_entities = [e for e in active_entities if e in z_data]

                # Construir representaciones LOO para la cartera central
                hub_loo = self._build_hub_loo_z(
                    active_entities, w_size, decay, TEST_START_YEAR - 1
                )

                # Estimation
                topo_mask = build_topology_mask(active_entities, SYNTHETIC_HUB_NAME)
                try:
                    p_est = estimate_coupling_matrix(
                        active_entities, z_data, topo_mask, SYNTHETIC_HUB_NAME,
                        training_end_year=TEST_START_YEAR-1, loo_strategy=True,
                        hub_loo_z=hub_loo
                    )
                except Exception as e:
                    continue

                # Evaluation: OOS Metrics (MASE, NRMSE)
                metrics = evaluate_metrics_oos(
                    p_est, active_entities, z_data, topo_mask,
                    TEST_START_YEAR, TEST_END_YEAR,
                    hub_loo_z=hub_loo, hub_name=SYNTHETIC_HUB_NAME
                )

                # Evaluation: OOS Frobenius Reconstruction Error (Paper criterion)
                frob_err, frob_cov = evaluate_frobenius_oos(
                    p_est, active_entities, z_data, topo_mask,
                    TEST_START_YEAR, TEST_END_YEAR,
                    hub_loo_z=hub_loo, hub_name=SYNTHETIC_HUB_NAME
                )
                
                results_log.append({
                    "W": w_size, 
                    "Lambda": decay, 
                    "ErrFrob_OOS": frob_err,
                    "NRMSE": metrics["NRMSE"],
                    "MASE": metrics["MASE"],
                    "Count": frob_cov
                })
        
        df_results = pd.DataFrame(results_log)
        if not df_results.empty:
            # Paper criterion (V001 legacy): maximize Coverage first, then minimize Frobenius Error.
            # This ensures maximum entity admissibility before optimizing reconstruction.
            df_sorted = df_results.sort_values(
                by=["Count", "ErrFrob_OOS"], 
                ascending=[False, True]
            ).reset_index(drop=True)
            print("Top 10 Configurations (sorted by Coverage -> Frobenius Error):")
            print(df_sorted.head(10))
            
            best_config = df_sorted.iloc[0]
            self.best_w = int(best_config["W"])
            self.best_lam = float(best_config["Lambda"])
            
            # ── Diagnóstico enriquecido ──
            print(f"\n{'='*60}")
            print(f"  BEST CONFIG: W={self.best_w}, Lambda={self.best_lam:.3f}")
            print(f"  ErrFrob={best_config['ErrFrob_OOS']:.4f}  MASE={best_config['MASE']:.4f}  NRMSE={best_config['NRMSE']:.4f}  Count={int(best_config['Count'])}")
            print(f"{'='*60}\n")
            
            # ── Exportar grid completo a CSV ──
            df_results.to_csv(os.path.join(self.output_dir, "grid_search_full.csv"), index=False)
            
            # Heatmap: Frobenius Error (paper Figure)
            pivot_table = df_results.pivot_table(index="W", columns="Lambda", values="ErrFrob_OOS", aggfunc="min")
            pivot_table = pivot_table.sort_index(ascending=True) 
            plot_sensitivity_heatmap(pivot_table, self.best_w, self.best_lam, os.path.join(self.images_dir, "Fig_Optimization_Surface_ENG.png"), metric_name="Frobenius")
        else:
            raise ValueError("Grid Search failed to find valid configurations.")

    def step_3_final_model(self):
        print("\n=== STEP 3: FINAL MODEL FITTING ===")
        unique_entities = sorted(self.df_final[ENTITY_COL].dropna().unique().tolist())
        
        # Features
        alpha_final_dict = build_alpha_by_entity(self.df_final, unique_entities, self.best_w, self.best_lam)
        self.active_ents = [e for e in HIERARCHICAL_ORDER if e in alpha_final_dict]
        
        self.z_final = {}
        self.pca_transformers = {}
        self.scalers = {}
        self.z_final = self._build_embeddings(
            alpha_final_dict, self.active_ents, TEST_START_YEAR - 1, store=True
        )
        self.active_ents = [e for e in self.active_ents if e in self.z_final]
        print(f"Active entities ({len(self.active_ents)}): {self.active_ents}")
            
        # LOO del nodo central para el modelo final
        self.hub_loo_z = self._build_hub_loo_z(
            self.active_ents, self.best_w, self.best_lam, TEST_START_YEAR - 1
        )

        # Estimate P*
        topo_mask_final = build_topology_mask(self.active_ents, SYNTHETIC_HUB_NAME)
        self.p_matrix_active = estimate_coupling_matrix(
            self.active_ents, self.z_final, topo_mask_final, SYNTHETIC_HUB_NAME,
            training_end_year=TEST_START_YEAR-1, loo_strategy=True,
            hub_loo_z=self.hub_loo_z
        )
        
        # Plots
        plot_structure_matrix(self.p_matrix_active, self.active_ents, self.best_w, self.best_lam, os.path.join(self.images_dir, "structure_matrix.png"))
        
        # Espectro de autovalores mediante regresión Ridge
        h_t0 = np.hstack([self.z_final[e]["H"][:, :-1] for e in self.active_ents]).T
        h_t1 = np.hstack([self.z_final[e]["H"][:, 1:] for e in self.active_ents]).T

        try:
            ridge_pres = Ridge(alpha=1.0, fit_intercept=False)
            ridge_pres.fit(h_t0, h_t1)
            pres_matrix = ridge_pres.coef_
        except Exception as e:
            print(f"Warning: Ridge failed for Pres ({e}), falling back to dummy identity")
            pres_matrix = np.eye(RES_DIM) * 0.95
        
        rho_pres = np.max(np.abs(np.linalg.eigvals(pres_matrix)))
        print(f"rho(P_res) = {rho_pres:.4f}")
        
        plot_eigenvalue_spectrum(pres_matrix, os.path.join(self.images_dir, "eigenvalue_spectrum.png"))

    def step_4_readout_analysis(self):
        print("\n=== STEP 4: READOUT & STRATEGIC ANALYSIS ===")
        # Systemic Hub Readout
        alpha_obs_stack = []
        h_state_stack = []
        for ent in self.active_ents:
            alpha_obs_stack.append(self.z_final[ent]["alpha_raw"][:, 1:])
            h_state_stack.append(self.z_final[ent]["H"][:, 1:])
            
        h_train = np.hstack(h_state_stack).T
        alpha_train = np.hstack(alpha_obs_stack).T
        readout = Ridge(alpha=1.0).fit(h_train, alpha_train)

        hub_data = self.z_final[SYNTHETIC_HUB_NAME]
        h_hub = hub_data["H"].T
        pred_hub = readout.predict(h_hub)
        
        # Métricas de precisión del readout del nodo central
        obs_amt = hub_data["alpha_raw"][0]
        obs_cnt = hub_data["alpha_raw"][1]
        pred_amt = pred_hub[:, 0]
        pred_cnt = pred_hub[:, 1]
        
        r2_amt = np.corrcoef(obs_amt, pred_amt)[0, 1]
        r2_cnt = np.corrcoef(obs_cnt, pred_cnt)[0, 1]
        rmse_amt = np.sqrt(np.mean((obs_amt - pred_amt)**2))
        rmse_cnt = np.sqrt(np.mean((obs_cnt - pred_cnt)**2))
        
        print(f"\n  Hub Readout Quality:")
        print(f"    Amount:  R = {r2_amt:.4f}, RMSE = {rmse_amt:.6f}")
        print(f"    Count:   R = {r2_cnt:.4f}, RMSE = {rmse_cnt:.6f}")
        print(f"    N points: {len(obs_amt)}")
        
        # Exportar métricas de evaluación a CSV
        metrics_summary = pd.DataFrame([{
            "Metric": "Hub_Readout_Amount", "R": r2_amt, "RMSE": rmse_amt, "N": len(obs_amt)
        }, {
            "Metric": "Hub_Readout_Count", "R": r2_cnt, "RMSE": rmse_cnt, "N": len(obs_cnt)
        }, {
            "Metric": "Best_Config", "W": self.best_w, "Lambda": self.best_lam
        }])
        metrics_summary.to_csv(os.path.join(self.output_dir, "paper_metrics.csv"), index=False)
        
        plot_hub_readout(hub_data, pred_hub, os.path.join(self.images_dir, "hub_readout.png"))
        plot_regime_decomposition(hub_data, os.path.join(self.images_dir, "regime_decomposition.png"))

    def step_5_forecasting(self):
        print("\n=== STEP 5: STRATEGIC FORECAST (2025-2027) ===")
        TRAIN_END_YEAR = 2024
        FORECAST_YEARS = [2025, 2026, 2027]
        GAMMA = 1.05
        
        topo_mask = build_topology_mask(self.active_ents, SYNTHETIC_HUB_NAME)
        P_learned = estimate_coupling_matrix(
            self.active_ents, self.z_final, topo_mask, SYNTHETIC_HUB_NAME,
            training_end_year=TRAIN_END_YEAR, loo_strategy=True,
            hub_loo_z=getattr(self, "hub_loo_z", None)
        )
        
        # Train Independent Readouts
        X_r, y_amt, y_cnt = [], [], []
        for e in self.active_ents:
            mask_yrs = self.z_final[e]["years"] <= TRAIN_END_YEAR
            if np.sum(mask_yrs) > 0:
                X_r.append(self.z_final[e]["H"][:, mask_yrs].T)
                alphas = self.z_final[e]["alpha_raw"][:, mask_yrs].T
                y_amt.append(alphas[:, 0])
                y_cnt.append(alphas[:, 1])

        X_stack = np.vstack(X_r)
        readout_amt = Ridge(alpha=1.0).fit(X_stack, np.hstack(y_amt))
        readout_cnt = Ridge(alpha=1.0).fit(X_stack, np.hstack(y_cnt))
        
        # Propagation
        rho = np.max(np.abs(np.linalg.eigvals(P_learned)))
        scaling = max(1, rho/GAMMA)
        P_forecast = P_learned / scaling
        
        z_curr = np.zeros(len(self.active_ents))
        levels_coupled = {}
        histories = {}
        
        for i, e in enumerate(self.active_ents):
            yrs = self.z_final[e]["years"]
            if TRAIN_END_YEAR in yrs:
                idx = np.where(yrs == TRAIN_END_YEAR)[0][0]
                z_curr[i] = self.z_final[e]["z"][idx]
            else:
                z_curr[i] = self.z_final[e]["z"][-1] if len(self.z_final[e]["z"]) > 0 else 0.0
            
            sub = self.df_final[(self.df_final[ENTITY_COL]==e) & (self.df_final[TIME_COL]==TRAIN_END_YEAR)]
            if not sub.empty:
                levels_coupled[e] = [sub[FEATURE_COLS[0]].values[0], sub[FEATURE_COLS[1]].values[0]]
            else:
                levels_coupled[e] = [0.0, 0.0]
            hist = self.df_final[
                (self.df_final[ENTITY_COL] == e) &
                (self.df_final[TIME_COL] <= TRAIN_END_YEAR)
            ].sort_values(TIME_COL)
            histories[e] = {
                FEATURE_COLS[0]: hist[FEATURE_COLS[0]].astype(float).tolist(),
                FEATURE_COLS[1]: hist[FEATURE_COLS[1]].astype(float).tolist(),
            }

        print(f"\n{'Entity':<20} | {'Year':<4} | {'Pred Amount':>15} | {'Pred Count':>10}")
        print("-" * 60)

        z_c = z_curr.copy()
        forecast_rows = []
        
        for yr in FORECAST_YEARS:
            z_c = P_forecast @ z_c
            
            for i, e in enumerate(self.active_ents):
                # Reconstruir estado reservorio H desde el espacio latente z
                if e in self.pca_transformers:
                    pca_e = self.pca_transformers[e]
                    h_vec_c = pca_e.inverse_transform([[z_c[i]]])  # (1, 50)
                else:
                    h_prof = self.z_final[e]["H"].mean(axis=1)
                    h_prof /= (np.linalg.norm(h_prof) + 1e-9)
                    h_vec_c = (h_prof * z_c[i]).reshape(1, -1)
                
                a_amt_c = readout_amt.predict(h_vec_c)[0]
                a_cnt_c = readout_cnt.predict(h_vec_c)[0]
                
                pred_amt_c = invert_tcroc_next(
                    histories[e][FEATURE_COLS[0]], a_amt_c,
                    self.best_w, self.best_lam
                )
                pred_cnt_c = invert_tcroc_next(
                    histories[e][FEATURE_COLS[1]], a_cnt_c,
                    self.best_w, self.best_lam
                )
                histories[e][FEATURE_COLS[0]].append(pred_amt_c)
                histories[e][FEATURE_COLS[1]].append(pred_cnt_c)
                levels_coupled[e] = [pred_amt_c, pred_cnt_c]
                
                print(f"{e:<20} | {yr} | ${pred_amt_c:,.0f} | {pred_cnt_c:.1f}")
                
                forecast_rows.append({
                    "Entity": e, "Year": yr,
                    "Pred_Amount": pred_amt_c, "Pred_Count": pred_cnt_c,
                    "z_latent": z_c[i], "alpha_amt": a_amt_c, "alpha_cnt": a_cnt_c
                })
        
        # Exportar proyecciones a CSV
        df_forecast = pd.DataFrame(forecast_rows)
        df_forecast.to_csv(os.path.join(self.output_dir, "forecast_table.csv"), index=False)
        print(f"\nForecast saved to {os.path.join(self.output_dir, 'forecast_table.csv')}")

    def step_6_bootstrap_validation(self):
        print("\n=== STEP 6: BOOTSTRAP VALIDATION ===")
        topo_mask = build_topology_mask(self.active_ents, SYNTHETIC_HUB_NAME)
        
        P_mean, P_std, P_cv, P_sig = bootstrap_coupling_matrix(
            self.active_ents, self.z_final, topo_mask, SYNTHETIC_HUB_NAME, n_boot=100,
            hub_loo_z=getattr(self, "hub_loo_z", None)
        )
        
        print(f"\nBootstrap Analysis (N=100) on P*:")
        print(f"{'Target Entity':<20} | {'Mean Coeff (Sum)':<16} | {'CV (Avg)':<10} | {'Significant?':<12}")
        print("-" * 65)
        
        boot_rows = []
        
        for i, ent in enumerate(self.active_ents):
            row_mean = np.sum(P_mean[i, :]) 
            
            allowed_indices = np.where(topo_mask[i,:] > 0)[0]
            if len(allowed_indices) > 0:
                row_cvs = P_cv[i, allowed_indices]
                avg_cv = np.mean(row_cvs)
            else:
                avg_cv = 0.0
                
            is_sig = avg_cv < 0.25
            sig_str = "YES" if is_sig else "NO"
            print(f"{ent:<20} | {row_mean:<16.4f} | {avg_cv:<10.1%} | {sig_str:<12}")
            
            boot_rows.append({
                "Entity": ent, "Mean_Sum": row_mean, 
                "Avg_CV": avg_cv, "Significant": is_sig
            })
        
        # Exportar resumen bootstrap a CSV
        pd.DataFrame(boot_rows).to_csv(
            os.path.join(self.output_dir, "bootstrap_summary.csv"), index=False
        )

    def run(self):
        self.step_1_data_ingestion()
        self.step_2_grid_search()
        self.step_3_final_model()
        self.step_4_readout_analysis()
        self.step_5_forecasting()
        self.step_6_bootstrap_validation()
        print("\n" + "="*60)
        print("  Pipeline execution complete.")
        print(f"  Images: {self.images_dir}")
        print(f"  CSVs:   {self.output_dir}")
        print("="*60)
