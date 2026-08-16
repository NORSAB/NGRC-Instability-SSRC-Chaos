"""Ventanas descriptivas y su procedencia metodologica.

Las ventanas no se usan para ajustar modelos. COVID-19, Eta/Iota y Ucrania se
fijaron por calendario externo antes de comparar los lectores. La ventana de
Medio Oriente 2026 se identifico despues de observar la serie y, por tanto, se
marca siempre como exploratoria; no puede sustentar inferencia confirmatoria.
"""
import pandas as pd

EVENTOS = {
    "covid_2020": (pd.Timestamp("2020-02-15"), pd.Timestamp("2020-05-15")),
    "eta_iota_2020": (pd.Timestamp("2020-11-01"), pd.Timestamp("2020-12-21")),
    "ucrania_2022": (pd.Timestamp("2022-02-15"), pd.Timestamp("2022-06-15")),
    "medio_oriente_2026": (pd.Timestamp("2026-03-01"), pd.Timestamp("2026-06-30")),
}

TIPO_EVENTO = {
    "covid_2020": "calendario_externo",
    "eta_iota_2020": "calendario_externo",
    "ucrania_2022": "calendario_externo",
    "medio_oriente_2026": "exploratoria_ex_post",
}


def categoria(fecha: pd.Timestamp) -> str:
    for nombre, (ini, fin) in EVENTOS.items():
        if ini <= fecha <= fin:
            return nombre
    return "calma"


def tipo_categoria(fecha: pd.Timestamp) -> str:
    nombre = categoria(fecha)
    return TIPO_EVENTO.get(nombre, "sin_evento")
