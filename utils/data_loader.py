"""
utils/data_loader.py
--------------------
Lectura robusta del Excel operativo.

[MIGRACION Streamlit -> Dash]
Este modulo NO depende de Streamlit y se mantiene identico al original.
La funcion load_excel acepta tanto paths como objetos tipo BytesIO, por lo
que funciona bien con el contenido decodificado de dcc.Upload.
"""

from __future__ import annotations

import io
import unicodedata
from typing import Dict, Optional

import pandas as pd

from config.settings import (
    SHEET_ALIASES,
    COLUMN_ALIASES,
    NUMERIC_COLUMNS,
    COL_ORIGEN,
    ORIGEN_ACTUAL,
    ORIGEN_HISTORICO,
    PROCESOS,
    CARGUE_UMBRAL_KG_A_T,
)


# ---------------------------------------------------------------------------
# Helpers de normalizacion de texto
# ---------------------------------------------------------------------------
def _strip_accents(text: str) -> str:
    if not isinstance(text, str):
        return text
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _norm_key(text: str) -> str:
    if not isinstance(text, str):
        return ""
    t = _strip_accents(text).lower().strip()
    for ch in "¿?¡!.,;:()[]{}\"'`":
        t = t.replace(ch, " ")
    t = " ".join(t.split())
    return t


def _resolve_sheet_name(available: list[str], canonical: str) -> Optional[str]:
    aliases = SHEET_ALIASES.get(canonical, [canonical])
    norm_available = {_norm_key(s): s for s in available}
    for alias in aliases:
        k = _norm_key(alias)
        if k in norm_available:
            return norm_available[k]
    return None


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    for col in df.columns:
        key = _norm_key(str(col))
        if key in COLUMN_ALIASES:
            rename_map[col] = COLUMN_ALIASES[key]
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def _coerce_types(df: pd.DataFrame, sheet: str) -> pd.DataFrame:
    if df.empty:
        return df

    for col in ("Fecha", "Timestamp"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in NUMERIC_COLUMNS.get(sheet, []):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ("Finca", "Lote", "Proyecto", "Cliente",
                "Destino", "Placa", "Maquinaria"):
        if col in df.columns:
            df[col] = df[col].astype("object").where(df[col].notna(), None)
            df[col] = df[col].apply(
                lambda x: " ".join(str(x).split()) if x is not None else None
            )

    return df


def _enrich_time(df: pd.DataFrame) -> pd.DataFrame:
    if "Fecha" in df.columns and not df["Fecha"].isna().all():
        df["Anio"]    = df["Fecha"].dt.year
        df["Mes"]     = df["Fecha"].dt.to_period("M").astype(str)
        df["Semana"]  = df["Fecha"].dt.to_period("W").astype(str)
    elif "Timestamp" in df.columns and not df["Timestamp"].isna().all():
        if "Fecha" not in df.columns:
            df["Fecha"] = df["Timestamp"].dt.normalize()
            df["Anio"]    = df["Fecha"].dt.year
            df["Mes"]     = df["Fecha"].dt.to_period("M").astype(str)
            df["Semana"]  = df["Fecha"].dt.to_period("W").astype(str)
    return df


def _sanear_cargue(df: pd.DataFrame) -> pd.DataFrame:
    """Si Toneladas > umbral -> se asume que estaba en kg y se divide por 1000."""
    if df.empty or "Toneladas" not in df.columns:
        return df
    df = df.copy()
    df["Toneladas"] = pd.to_numeric(df["Toneladas"], errors="coerce").astype("float64")
    df["Unidad Origen"] = "t"
    mask = df["Toneladas"] > CARGUE_UMBRAL_KG_A_T
    if mask.any():
        df.loc[mask, "Toneladas"] = df.loc[mask, "Toneladas"] / 1000.0
        df.loc[mask, "Unidad Origen"] = "kg → t (auto)"
    return df


# ---------------------------------------------------------------------------
# API publica
# ---------------------------------------------------------------------------
def load_excel(file) -> Dict[str, pd.DataFrame]:
    """
    Carga el Excel principal y devuelve un dict por hoja canonica.

    `file` puede ser:
      - Ruta (str/Path)
      - Objeto con .read() (ej. BytesIO de dcc.Upload decodificado)
    """
    if hasattr(file, "read"):
        raw = file.read()
        buffer = io.BytesIO(raw)
        xls = pd.ExcelFile(buffer, engine="openpyxl")
    elif isinstance(file, (bytes, bytearray)):
        xls = pd.ExcelFile(io.BytesIO(file), engine="openpyxl")
    else:
        xls = pd.ExcelFile(file, engine="openpyxl")

    available = xls.sheet_names
    out: Dict[str, pd.DataFrame] = {}

    for canonical in PROCESOS:
        real_name = _resolve_sheet_name(available, canonical)
        if real_name is None:
            out[canonical] = pd.DataFrame()
            continue
        try:
            df = pd.read_excel(xls, sheet_name=real_name)
        except Exception:
            out[canonical] = pd.DataFrame()
            continue

        df.columns = [str(c).strip() for c in df.columns]
        df = _rename_columns(df)
        df = _coerce_types(df, canonical)

        if canonical == "Cargue Vehiculo":
            df = _sanear_cargue(df)

        df = _enrich_time(df)
        df[COL_ORIGEN] = ORIGEN_ACTUAL
        out[canonical] = df

    return out
