"""
pages/corte.py
--------------
Detalle del proceso Corte de Esquejes.
[Equivalente a pages/2_Corte_Esquejes.py de Streamlit]
"""

from __future__ import annotations

import pandas as pd
from dash import Input, Output, callback, dcc, html

from styles.theme import page_header, empty_state
from pages._common import filter_panel
from components.ui import (kpi_card, kpi_row, fmt_num, fmt_pct,
                            plan_vs_real_row, detail_table, dotacion_block)
from components.charts import line_temporal, barh_ranking
from components.sidebar import get_data_filtrada
from utils.metrics import kpis_corte, analisis_dotacion, interpretacion_dotacion
from config.settings import ESTANDARES


def layout():
    return html.Div([
        page_header("Corte de esquejes",
                    subtitle="Producción, horas y productividad por persona"),
        filter_panel(),
        html.Div(id="corte-contenido"),
    ], className="ops-page ops-process-page process-corte")


@callback(
    Output("corte-contenido", "children"),
    Input("store-archivo", "data"),
    Input("store-data",    "data"),
    Input("store-filtros", "data"),
)
def render(archivo, store_data, filtros):
    if not archivo:
        return empty_state("No se encontraron registros en Supabase para este proceso.")

    df = get_data_filtrada(store_data, filtros, "Corte Esquejes")
    k = kpis_corte(df)
    est = ESTANDARES["Corte Esquejes"]
    cobertura = f"{k['dias_operativos']} días operativos · {k['registros']} registros"

    # ---------- KPIs ----------
    kpis = kpi_row([
        kpi_card("Esquejes cortados", fmt_num(k["total_esquejes"]),
                 sub=cobertura, nivel="neutral"),
        kpi_card("Esquejes por persona/día",
                 fmt_num(k["prod_persona_dia"]) if k["prod_persona_dia"] is not None else "-",
                 sub=f"Estándar: {fmt_num(k['estandar_persona'])}",
                 nivel=k["nivel_cumpl"]),
        kpi_card("Cumplimiento", fmt_pct(k["cumpl_prod"]),
                 sub="Real vs estándar", nivel=k["nivel_cumpl"]),
        kpi_card("Horas acumuladas", fmt_num(k["total_horas"], decimals=1),
                 sub="Suma de horas en proceso", nivel="neutral"),
    ])

    # ---------- Plan vs Real ----------
    if df is None or df.empty:
        pvr = empty_state("Sin registros con los filtros actuales.")
    else:
        pvr = html.Div(
            plan_vs_real_row(
                "Esquejes por persona/día",
                plan=est["esquejes_persona_dia"],
                real=k["prod_persona_dia"],
                unidad="esquejes",
                nivel=k["nivel_cumpl"],
            ),
            className="section-panel",
        )

    # ---------- Gestion de personal ----------
    dot = analisis_dotacion(df, "Corte Esquejes")
    dot_block = dotacion_block(dot, interpretacion_dotacion(dot, "Corte Esquejes"))

    # ---------- Tendencia diaria ----------
    if not df.empty and "Fecha" in df.columns and "Esquejes" in df.columns:
        serie = df.dropna(subset=["Fecha"]).copy()
        serie["_FechaDia"] = pd.to_datetime(serie["Fecha"], errors="coerce").dt.date
        serie = (serie.dropna(subset=["_FechaDia"])
                     .groupby("_FechaDia", as_index=False)["Esquejes"].sum())
        serie.columns = ["Fecha", "Esquejes"]
        fig = line_temporal(serie, x="Fecha", y="Esquejes",
                            titulo="Esquejes cortados por día", y_label="Esquejes")
        tend = dcc.Graph(figure=fig, config={"displayModeBar": False})
    else:
        tend = empty_state("Sin datos temporales.")

    # ---------- Ranking por finca / lote ----------
    if not df.empty and "Finca" in df.columns:
        fig_f = barh_ranking(df, cat="Finca", val="Esquejes",
                             titulo="Esquejes por finca")
        rank_finca = dcc.Graph(figure=fig_f, config={"displayModeBar": False})
    else:
        rank_finca = empty_state("Sin datos por finca.")

    if not df.empty and "Lote" in df.columns:
        d = df.copy()
        d["Lote"] = d["Lote"].astype(str)
        fig_l = barh_ranking(d, cat="Lote", val="Esquejes",
                             titulo="Esquejes por lote")
        rank_lote = dcc.Graph(figure=fig_l, config={"displayModeBar": False})
    else:
        rank_lote = empty_state("Sin datos por lote.")

    # ---------- Detalle ----------
    tabla = detail_table(df,
        columnas=["Fecha", "Finca", "Lote", "Horas", "Numero Trabajadores",
                  "Esquejes", "Observaciones"], height=360,
        id="corte-detalle")

    return html.Div([
        html.H2("Indicadores del proceso"),
        kpis,
        html.H2("Cumplimiento vs estándar"),
        pvr,
        html.H2("Gestión de personal"),
        dot_block,
        html.H2("Tendencia diaria"),
        tend,
        html.H2("Producción por finca y lote"),
        html.Div([rank_finca, rank_lote], className="two-col"),
        html.H2("Detalle de registros"),
        tabla,
    ])
