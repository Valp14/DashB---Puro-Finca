"""
pages/cargue.py
---------------
Cargue y despacho. La unidad se normaliza automaticamente en el loader.
[Equivalente a pages/7_Cargue_Despacho.py de Streamlit]
"""

from __future__ import annotations

import pandas as pd
from dash import Input, Output, callback, dcc, html

from styles.theme import page_header, empty_state
from pages._common import filter_panel
from components.ui import (kpi_card, kpi_row, fmt_num, fmt_pct,
                            plan_vs_real_row, detail_table, dotacion_block)
from components.charts import barh_ranking
from components.sidebar import get_data_filtrada
from utils.metrics import kpis_cargue, analisis_dotacion, interpretacion_dotacion
from config.settings import ESTANDARES


def layout():
    return html.Div([
        page_header("Cargue y despacho",
                    subtitle="Toneladas despachadas, cumplimiento vs estándar y distribución por cliente"),
        filter_panel(),
        html.Div(id="cargue-contenido"),
    ], className="ops-page ops-process-page process-cargue")


@callback(
    Output("cargue-contenido", "children"),
    Input("store-archivo", "data"),
    Input("store-data",    "data"),
    Input("store-filtros", "data"),
)
def render(archivo, store_data, filtros):
    if not archivo:
        return empty_state("No se encontraron registros en Supabase para este proceso.")

    df = get_data_filtrada(store_data, filtros, "Cargue Vehiculo")
    k = kpis_cargue(df)
    est = ESTANDARES["Cargue Vehiculo"]
    cobertura = f"{k['despachos']} despachos · {k['dias_operativos']} días operativos"

    # ---------- Aviso de normalizacion (si aplica) ----------
    aviso = None
    if not df.empty and "Unidad Origen" in df.columns:
        convertidos = df[df["Unidad Origen"].astype(str).str.contains("kg", na=False)]
        if not convertidos.empty:
            aviso = html.Div([
                html.B("Aviso de calidad de datos: "),
                f"{len(convertidos)} registro(s) fueron digitados en kilogramos "
                "en lugar de toneladas. Se convirtieron automáticamente para "
                "los cálculos. Recomendación: ajustar el formulario de captura "
                "para etiquetar el campo como \"Kilogramos\". Ver pestaña ",
                html.B("Calidad de datos"), ".",
            ], className="section-panel warn-accent")

    # ---------- KPIs ----------
    kpis1 = kpi_row([
        kpi_card("Toneladas despachadas",
                 fmt_num(k["total_toneladas"], 2) + " t",
                 sub=cobertura, nivel="neutral"),
        kpi_card("Promedio por despacho",
                 (fmt_num(k["ton_promedio"], 2) + " t") if k["ton_promedio"] is not None else "-",
                 sub=f"Estándar: {est['toneladas']} t", nivel=k["nivel_cumpl"]),
        kpi_card("Cumplimiento", fmt_pct(k["cumpl_ton"]),
                 sub="t promedio / estándar", nivel=k["nivel_cumpl"]),
        kpi_card("Horas acumuladas", fmt_num(k["total_horas"], 1),
                 sub="Suma de horas de cargue", nivel="neutral"),
    ])

    clientes_unicos = (df["Cliente"].nunique()
                       if not df.empty and "Cliente" in df.columns else 0)
    kpis2 = kpi_row([
        kpi_card("Cajas totales",  fmt_num(k["total_cajas"]),  sub="Acumulado", nivel="neutral"),
        kpi_card("Sacos totales",  fmt_num(k["total_sacos"]),  sub="Acumulado", nivel="neutral"),
        kpi_card("Bolsas totales", fmt_num(k["total_bolsas"]), sub="Acumulado", nivel="neutral"),
        kpi_card("Clientes únicos", fmt_num(clientes_unicos),
                 sub="Con al menos un despacho", nivel="neutral"),
    ])

    # ---------- Plan vs Real ----------
    if df is None or df.empty:
        pvr = empty_state("Sin registros con los filtros actuales.")
    else:
        pvr = html.Div(
            plan_vs_real_row("Toneladas promedio por despacho",
                             plan=est["toneladas"], real=k["ton_promedio"],
                             unidad="t", decimals=2, nivel=k["nivel_cumpl"]),
            className="section-panel",
        )

    # ---------- Dotacion ----------
    dot = analisis_dotacion(df, "Cargue Vehiculo")
    dot_block = dotacion_block(dot, interpretacion_dotacion(dot, "Cargue Vehiculo"))

    # ---------- Ranking cliente / destino ----------
    rank_cli = (dcc.Graph(figure=barh_ranking(df, cat="Cliente", val="Toneladas",
                                              titulo="Toneladas por cliente"),
                          config={"displayModeBar": False})
                if not df.empty and "Cliente" in df.columns
                else empty_state("Sin datos por cliente."))
    rank_dest = (dcc.Graph(figure=barh_ranking(df, cat="Destino", val="Toneladas",
                                               titulo="Toneladas por destino"),
                           config={"displayModeBar": False})
                 if not df.empty and "Destino" in df.columns
                 else empty_state("Sin datos por destino."))

    tabla = detail_table(df,
        columnas=["Fecha", "Toneladas", "Cajas", "Sacos", "Bolsas",
                  "Numero Trabajadores", "Horas", "Cliente", "Destino",
                  "Placa", "Unidad Origen", "Observaciones"],
        height=380, id="cargue-detalle")

    contenido = []
    if aviso is not None:
        contenido.append(aviso)
    contenido += [
        html.H2("Indicadores del proceso"), kpis1, kpis2,
        html.H2("Cumplimiento vs estándar"), pvr,
        html.H2("Gestión de personal"), dot_block,
        html.H2("Distribución de despachos"),
        html.Div([rank_cli, rank_dest], className="two-col"),
        html.H2("Detalle de despachos"), tabla,
    ]
    return html.Div(contenido)
