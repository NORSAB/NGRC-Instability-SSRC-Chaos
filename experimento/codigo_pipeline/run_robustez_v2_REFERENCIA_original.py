"""
ROBUSTEZ COMPLETA BAJO PROTOCOLO V2 (sin fuga): insumos para migrar el paper CONCAPAN.
Re-corre con embeddings fit<=2019, W=3, lambda=0.88, arch (50, 0.95, 0.05):
  1) 20 semillas              2) 5 ventanas rodantes (2016-2020 .. 2020-2024)
  3) Ablacion de componentes  4) NG-RC determinista (k=3)
  5) Feature ablation (TCRA vs log-diff vs canal combinado)
Salida: output_2025/robustez_v2.json
"""
import os, json, warnings, itertools
import numpy as np
warnings.filterwarnings("ignore")

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from config.topology import TIME_COL, ENTITY_COL, FEATURE_COLS, HIERARCHICAL_ORDER, SYNTHETIC_HUB_NAME
from src.data.ckan_loader import CKANLoader
from src.data.preprocessor import clean_dataframe
from src.data.aggregator import aggregate_data
from src.features.tcroc import build_alpha_by_entity
from src.models.reservoir import make_reservoir, run_reservoir
from src.models.optimization import build_topology_mask, estimate_coupling_matrix
from src.models.metric_tools import evaluate_metrics_oos, evaluate_frobenius_oos

# Hiperparámetros de calibración empírica
W, LAM, DIM, RHO, DENS = 3, 0.86, 50, 0.95, 0.05
OUT = os.path.join(os.getcwd(), "output_2025")
res = {}

df = aggregate_data(clean_dataframe(CKANLoader().fetch_data()))
df = df[df[TIME_COL] <= 2025].copy()
ents_all = sorted(df[ENTITY_COL].dropna().unique().tolist())
alpha = build_alpha_by_entity(df, ents_all, W, LAM)
cand = [e for e in HIERARCHICAL_ORDER if e in alpha]

# Series crudas LOO para el nodo central re-incrustadas por variante
_hub_raw = df[df[ENTITY_COL] == SYNTHETIC_HUB_NAME].groupby(TIME_COL)[FEATURE_COLS].sum()
_lf = []
for _k in [e for e in cand if e != SYNTHETIC_HUB_NAME]:
    _kr = df[df[ENTITY_COL] == _k].groupby(TIME_COL)[FEATURE_COLS].sum()
    _d = _hub_raw.sub(_kr, fill_value=0.0).clip(lower=0.0).reset_index()
    _d[ENTITY_COL] = "__LOO__" + _k
    _lf.append(_d)
import pandas as _pd
alpha.update(build_alpha_by_entity(_pd.concat(_lf, ignore_index=True),
                                   ["__LOO__" + e for e in cand if e != SYNTHETIC_HUB_NAME], W, LAM))
LOO_NAMES = [n for n in alpha if n.startswith("__LOO__")]

def embed(fit_end, seed=7, reservoir=True):
    w_in, w_res = make_reservoir(d_res=DIM, rho=RHO, density=DENS, seed=seed)
    out = {}
    for ent in cand + LOO_NAMES:
        yrs = np.asarray(alpha[ent]["years"]); m = yrs <= fit_end
        if np.sum(m) < 2: continue
        a = alpha[ent]["alpha"]
        sc = StandardScaler().fit(a[:, m].T)
        feats = run_reservoir(sc.transform(a.T).T, w_in, w_res) if reservoir else sc.transform(a.T).T
        pca = PCA(n_components=1).fit(feats[:, m].T)
        z = pca.transform(feats.T).flatten()
        c = np.corrcoef(z[m], a[0, m])[0, 1]
        if np.isfinite(c) and c < 0: z *= -1
        out[ent] = {"years": yrs, "z": z}
    return out

def evaluate(z, test_start, hub=True):
    ents = [e for e in cand if e in z]
    if hub and SYNTHETIC_HUB_NAME not in ents: return None
    if not hub: ents = [e for e in ents if e != SYNTHETIC_HUB_NAME]
    n = len(ents)
    mask = build_topology_mask(ents, SYNTHETIC_HUB_NAME) if hub else np.eye(n, dtype=int)
    try:
        hub_loo = ({e: z["__LOO__" + e] for e in ents if ("__LOO__" + e) in z} or None) if hub else None
        P = estimate_coupling_matrix(ents, z, mask, SYNTHETIC_HUB_NAME,
                                     training_end_year=test_start-1, loo_strategy=hub,
                                     hub_loo_z=hub_loo)
        met = evaluate_metrics_oos(P, ents, z, mask, test_start,
                                   hub_loo_z=hub_loo, hub_name=SYNTHETIC_HUB_NAME)
        fr, _ = evaluate_frobenius_oos(P, ents, z, mask, test_start,
                                       hub_loo_z=hub_loo, hub_name=SYNTHETIC_HUB_NAME)
        return dict(MASE=met["MASE"], NRMSE=met["NRMSE"], Frob=fr, n=met["Count"])
    except Exception as e:
        return None

# 1) 20 semillas
seeds = []
for s in range(1, 21):
    r = evaluate(embed(2019, seed=s), 2020)
    if r: seeds.append(dict(seed=s, **r))
mases = [r["MASE"] for r in seeds]
res["seeds"] = dict(n=len(mases), mean=float(np.mean(mases)), std=float(np.std(mases)),
                    min=float(np.min(mases)), max=float(np.max(mases)),
                    cv_pct=float(100*np.std(mases)/np.mean(mases)),
                    seed7=float([r["MASE"] for r in seeds if r["seed"]==7][0]),
                    detail=seeds)
print("seeds:", {k: round(v,4) for k,v in res["seeds"].items() if isinstance(v,float)})

# 2) Rolling windows
roll = []
for ts in range(2016, 2021):
    r = evaluate(embed(ts-1, seed=7), ts)
    if r: roll.append(dict(test_start=ts, **r))
res["rolling"] = dict(windows=roll, mean=float(np.mean([r["MASE"] for r in roll])),
                      below1=sum(1 for r in roll if r["MASE"] < 1))
print("rolling:", [(r["test_start"], round(r["MASE"],3)) for r in roll])

# 3) Ablacion
z_full = embed(2019, 7, reservoir=True)
z_nores = embed(2019, 7, reservoir=False)
res["ablation"] = {
    "full": evaluate(z_full, 2020),
    "no_reservoir": evaluate(z_nores, 2020),
    "no_hub": evaluate(z_full, 2020, hub=False),
    "minimal": evaluate(z_nores, 2020, hub=False),
}
print("ablation:", {k: (round(v["MASE"],3) if v else None) for k,v in res["ablation"].items()})

# 4) NG-RC determinista (k=3), embeddings sin fuga
def embed_ngrc(fit_end, k=3):
    out = {}
    for ent in cand:
        yrs = np.asarray(alpha[ent]["years"])
        a = alpha[ent]["alpha"]
        T = a.shape[1]
        if T < k + 2: continue
        m_all = yrs <= fit_end
        sc = StandardScaler().fit(a[:, m_all].T)
        a_std = sc.transform(a.T).T
        lin = np.array([a_std[:, t-k+1:t+1].flatten() for t in range(k-1, T)])
        nn = lin.shape[1]
        quad = np.array([lin[:, i]*lin[:, j] for i in range(nn) for j in range(i, nn)]).T
        F = np.hstack([np.ones((lin.shape[0],1)), lin, quad])
        yrs2 = yrs[k-1:]
        m2 = yrs2 <= fit_end
        if np.sum(m2) < 2: continue
        sc2 = StandardScaler().fit(F[m2])
        Fs = sc2.transform(F)
        pca = PCA(n_components=1).fit(Fs[m2])
        z = pca.transform(Fs).flatten()
        c = np.corrcoef(z[m2], a[0, k-1:][m2])[0, 1]
        if np.isfinite(c) and c < 0: z *= -1
        out[ent] = {"years": yrs2, "z": z}
    return out
res["ngrc_k3"] = evaluate(embed_ngrc(2019), 2020)
print("ngrc:", res["ngrc_k3"])

# 5) Feature ablation (mismo reservorio seed 7, fit_end 2019)
def embed_feats(kind):
    out = {}
    w_in_full, w_res = make_reservoir(d_res=DIM, rho=RHO, density=DENS, seed=7)
    for ent in cand:
        sub = df[df[ENTITY_COL] == ent].groupby(TIME_COL, as_index=False)[FEATURE_COLS].sum()
        yrs = sub[TIME_COL].values.astype(int)
        if len(yrs) < 4: continue
        amt = np.log1p(np.maximum(sub[FEATURE_COLS[0]].values.astype(float), 0))
        cnt = np.log1p(np.maximum(sub[FEATURE_COLS[1]].values.astype(float), 0))
        r1, r2 = np.diff(amt), np.diff(cnt)
        feat = np.vstack([r1, r2]) if kind == "logdiff" else (r1 + r2).reshape(1, -1)
        yrs2 = yrs[1:]
        m = yrs2 <= 2019
        if np.sum(m) < 2 or feat.shape[1] < 3: continue
        sc = StandardScaler().fit(feat[:, m].T)
        h = run_reservoir(sc.transform(feat.T).T, w_in_full[:, :feat.shape[0]], w_res)
        pca = PCA(n_components=1).fit(h[:, m].T)
        z = pca.transform(h.T).flatten()
        c = np.corrcoef(z[m], feat[0, m])[0, 1]
        if np.isfinite(c) and c < 0: z *= -1
        out[ent] = {"years": yrs2, "z": z}
    return out
res["feature_ablation"] = {
    "tcra": evaluate(z_full, 2020),
    "logdiff": evaluate(embed_feats("logdiff"), 2020),
    "strength_1ch": evaluate(embed_feats("strength"), 2020),
}
print("features:", {k: (round(v["MASE"],3) if v else None) for k,v in res["feature_ablation"].items()})

with open(os.path.join(OUT, "robustez_v2.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print("\nGuardado:", os.path.join(OUT, "robustez_v2.json"))
