"""
Experimento diario: ¿el universo mas rico (FX diario Latam + cripto) resuelve por si solo
el mal condicionamiento kappa(cov(F))=inf que se encontro en el panel anual del BCIE
(ver ../experimento/EXP_ngrc_regularizado_HALLAZGO_PRELIMINAR.md)?
=============================================================================================
Guion descriptivo de COVARIANZA, separado de la seleccion de lambda Ridge del readout.
Comparte solo la descarga con ``volatility_models.py`` y no depende del pipeline BCIE.

Universo:
  FX Latam vs USD (hub implicito = USD): MXN, BRL, COP, CLP, PEN, ARS, GTQ
  Cripto (anexo de robustez, universo mas volatil): BTC-USD, ETH-USD

Para cada serie, en retornos logaritmicos diarios, se construye el MISMO bloque de estado
NG-RC (constante + lineal(delays) + cuadratico) que en run_ngrc_regularizado.py, para una
grilla de tamanos de ventana T (30..1500 dias) y k in {2,3}. Se mide kappa(cov(F)) crudo y
regularizado (Ledoit-Wolf) en cada punto, para ubicar el T de cruce donde deja de ser
practicamente singular — la pregunta central de esta fase.

Salida: output/kappa_vs_T.csv, output/kappa_vs_T_resumen.md
"""
import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
import warnings
warnings.filterwarnings("ignore")

from volatility_models import ALL_SYMBOLS, CRYPTO_SYMBOLS, fetch_daily_closes


def ngrc_states(x_std, k):
    """Identico a run_ngrc_regularizado.py, pero univariado (retorno log diario, no
    bivariado como alpha_data): x_std shape (T,). Retorna F (D, T-k+1)."""
    T = len(x_std)
    if T < k + 1:
        return None
    lin = np.array([x_std[t - k + 1: t + 1] for t in range(k - 1, T)])  # (T-k+1, k)
    n = lin.shape[1]
    quad_cols = [lin[:, i] * lin[:, j] for i in range(n) for j in range(i, n)]
    F = np.hstack([np.ones((lin.shape[0], 1)), lin, np.array(quad_cols).T])
    return F.T  # (D, T-k+1)


def kappa_for_window(logret_window, k):
    """logret_window: array de retornos log en la ventana. Retorna (kappa_raw, kappa_lw).

    FIX 2026-08-12: la columna 0 de F es la constante (sesgo). np.cov CENTRA cada columna
    (resta su media) antes de calcular covarianza — una columna constante queda en varianza
    EXACTA cero tras centrar, lo que fuerza kappa=inf mecanicamente sin importar T ni el
    resto de las columnas (bug, no hallazgo). Se excluye la constante antes de cov/PCA, tal
    como hace sklearn.PCA implicitamente (centra y la columna constante queda inerte, pero
    SVD no reporta un "kappa" explicito asi que el bug no aparecia en el guion original)."""
    x_std = (logret_window - logret_window.mean()) / (logret_window.std() + 1e-12)
    F = ngrc_states(x_std, k)
    if F is None or F.shape[1] < 5:
        return None
    Fs = F.T[:, 1:]  # (T-k+1, D-1) — se excluye la columna constante (indice 0)
    cov_raw = np.cov(Fs, rowvar=False)
    kappa_raw = float(np.linalg.cond(cov_raw))
    try:
        cov_lw = LedoitWolf().fit(Fs).covariance_
        kappa_lw = float(np.linalg.cond(cov_lw))
    except Exception:
        kappa_lw = np.nan
    return kappa_raw, kappa_lw, F.shape[0], Fs.shape[0]


print("Descargando series diarias (Yahoo Finance, publico, sin autenticacion, period1/period2)...")
series = {}
for name, sym in ALL_SYMBOLS.items():
    try:
        yrs = 10 if name in CRYPTO_SYMBOLS else 15
        s = fetch_daily_closes(sym, years_back=yrs)
        series[name] = s
        print(f"  {name:<5} ({sym}): {len(s)} puntos, {s.index.min()} a {s.index.max()}")
    except Exception as e:
        print(f"  {name}: FALLO ({e})")

T_GRID = [30, 60, 120, 250, 500, 1000, 2000, 3000]
rows = []
for name, s in series.items():
    logret = np.log(s.values[1:] / s.values[:-1])
    logret = logret[np.isfinite(logret)]
    for k in (2, 3):
        for T in T_GRID:
            if T > len(logret):
                continue
            window = logret[-T:]  # ventana mas reciente disponible de longitud T
            out = kappa_for_window(window, k)
            if out is None:
                continue
            kappa_raw, kappa_lw, D, n_rows = out
            rows.append(dict(entity=name, k=k, T=T, D_features=D, n_rows=n_rows,
                             kappa_raw=kappa_raw, kappa_lw=kappa_lw,
                             well_conditioned=bool(np.isfinite(kappa_raw) and kappa_raw < 100)))
            print(f"  {name:<5} k={k} T={T:<5} D={D:<3} kappa_raw={kappa_raw:>14.2e} kappa_LW={kappa_lw:>10.2f}")

df = pd.DataFrame(rows)
df.to_csv("output/kappa_vs_T.csv", index=False)

# Resumen: T minimo donde kappa_raw < 100 (bien condicionado), por entidad y k
cross = (df[df["well_conditioned"]]
         .groupby(["entity", "k"])["T"].min()
         .reset_index()
         .rename(columns={"T": "T_cruce_bien_condicionado"}))
never = (df.groupby(["entity", "k"])["well_conditioned"].any()
         .reset_index())
never = never[~never["well_conditioned"]][["entity", "k"]]

with open("output/kappa_vs_T_resumen.md", "w", encoding="utf-8") as f:
    f.write("# kappa(cov(F)) vs T — universo diario FX Latam + cripto\n\n")
    f.write("T minimo (dias) donde kappa_raw < 100 (deja de ser practicamente singular):\n\n")
    f.write(cross.to_markdown(index=False) if not cross.empty else "(ninguna combinacion cruzo el umbral)")
    f.write("\n\n")
    if not never.empty:
        f.write("Combinaciones que NUNCA bajan de kappa=100 en la grilla probada (30-3000 dias):\n\n")
        f.write(never.to_markdown(index=False))
        f.write("\n")

print("\n==== Resumen: T minimo con kappa_raw < 100 ====")
print(cross.to_string(index=False))
if not never.empty:
    print("\n==== NUNCA bien condicionado en la grilla 30-3000 dias ====")
    print(never.to_string(index=False))
print("\nGuardado en output/kappa_vs_T.csv y output/kappa_vs_T_resumen.md")
