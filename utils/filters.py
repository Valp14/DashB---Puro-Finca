"""
utils/filters.py
----------------
Filtros globales aplicables de forma segura a cualquier hoja.

[MIGRACION Streamlit -> Dash]
Sin cambios, no depende de Streamlit.
"""

from __future__ import annotations

from datetime import date
from typing import Iterable, Optional

import pandas as pd

from config.settings import COL_ORIGEN


def filtrar(
    df: pd.DataFrame,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    fincas: Optional[Iterable[str]] = None,
    lotes: Optional[Iterable[str]] = None,
    proyectos: Optional[Iterable[str]] = None,
    clientes: Optional[Iterable[str]] = None,
    destinos: Optional[Iterable[str]] = None,
    origenes: Optional[Iterable[str]] = None,
    strict_missing_dimensions: bool = True,
) -> pd.DataFrame:
    """Aplica filtros globales a un DataFrame."""
    if df is None or df.empty:
        return df

    out = df.copy()

    if fecha_inicio is not None or fecha_fin is not None:
        if "Fecha" not in out.columns:
            return out.iloc[0:0].copy() if strict_missing_dimensions else out
        fechas = pd.to_datetime(out["Fecha"], errors="coerce")
        if fecha_inicio is not None:
            out = out[fechas.notna() & (fechas >= pd.Timestamp(fecha_inicio))]
            fechas = pd.to_datetime(out["Fecha"], errors="coerce")
        if fecha_fin is not None:
            fin_inclusivo = pd.Timestamp(fecha_fin) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
            out = out[fechas.notna() & (fechas <= fin_inclusivo)]

    def _apply_dimension(values, column, transform=None):
        nonlocal out
        if not values:
            return
        if column not in out.columns:
            out = out.iloc[0:0].copy() if strict_missing_dimensions else out
            return
        selected = list(values)
        serie = out[column]
        if transform is not None:
            serie = transform(serie)
            selected = [transform(pd.Series([x])).iloc[0] for x in selected]
        out = out[serie.isin(selected)]

    _apply_dimension(fincas, "Finca")
    _apply_dimension(lotes, "Lote", transform=lambda s: s.astype(str))
    _apply_dimension(proyectos, "Proyecto")
    _apply_dimension(clientes, "Cliente")
    _apply_dimension(destinos, "Destino")
    _apply_dimension(origenes, COL_ORIGEN)

    return out


def opciones_unicas(dfs: Iterable[pd.DataFrame], col: str) -> list:
    vals = set()
    for df in dfs:
        if df is not None and not df.empty and col in df.columns:
            for v in df[col].dropna().unique().tolist():
                vals.add(v)
    return sorted([v for v in vals if v is not None and str(v) != "nan"],
                  key=lambda x: str(x))


def rango_fechas(dfs: Iterable[pd.DataFrame]) -> tuple[Optional[date], Optional[date]]:
    mins, maxs = [], []
    for df in dfs:
        if df is not None and not df.empty and "Fecha" in df.columns:
            s = pd.to_datetime(df["Fecha"], errors="coerce").dropna()
            if not s.empty:
                mins.append(s.min())
                maxs.append(s.max())
    if not mins:
        return (None, None)
    return (min(mins).date(), max(maxs).date())
