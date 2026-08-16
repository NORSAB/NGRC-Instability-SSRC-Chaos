"""
Data Preprocessor
"""
import unicodedata
import pandas as pd
from config.topology import GROUP_FOUNDERS, GROUP_REGIONAL_NON_FOUNDERS, GROUP_EXTRA_REGIONAL, GROUP_PROGRAMMATIC

def _norm_txt(s):
    return "".join(ch for ch in unicodedata.normalize("NFKD", str(s).lower()) if not unicodedata.combining(ch))

def classify_partner(row):
    """
    Classifies the entity based on the groups defined in the global configuration.
    """
    p = _norm_txt(row.get("pais", ""))
    s = _norm_txt(row.get("sector_institucional", ""))
    
    founders_norm = {_norm_txt(x) for x in GROUP_FOUNDERS}
    reg_nf_norm = {_norm_txt(x) for x in GROUP_REGIONAL_NON_FOUNDERS}
    extra_norm = {_norm_txt(x) for x in GROUP_EXTRA_REGIONAL}
    prog_norm = {_norm_txt(x) for x in GROUP_PROGRAMMATIC}

    if p in prog_norm: return "Regional (Spoke)"
    if p == "institucional" or s == "institucional": return "Institutional"
    
    if p in founders_norm: return "Founders"
    if p in reg_nf_norm: return "Regional Non-Founders"
    if p in extra_norm: return "Extra-Regional"
    
    return "Other"

def clean_dataframe(df_raw):
    # Normalize columns
    new_cols = []
    for c in df_raw.columns:
        s = unicodedata.normalize("NFKD", str(c).strip())
        s_clean = "".join(ch for ch in s if not unicodedata.combining(ch)).lower().replace(" ", "_").replace("-", "_")
        s_final = "".join(ch for ch in s_clean if ch.isalnum() or ch=='_')
        new_cols.append(s_final)
    df_raw.columns = new_cols

    if "cantidad_aprobaciones" not in df_raw.columns:
        df_raw["cantidad_aprobaciones"] = 1
        
    df_raw["tipo_socio"] = df_raw.apply(classify_partner, axis=1)
    return df_raw
