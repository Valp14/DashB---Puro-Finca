"""
pages/empaque.py
----------------
Proceso de Empaque.
[Equivalente a pages/6_Empaque.py de Streamlit]
"""

from __future__ import annotations

import pandas as pd
from dash import Input, Output, callback, dcc, html

from styles.theme import page_header, empty_state
from pages._common import filter_panel
from components.ui import (kpi_card, kpi_row, fmt_num, fmt_pct,
                            detail_table, dotacion_block)
from components.charts import line_temporal, barh_ranking, donut_composicion
from components.sidebar import get_data_filtrada
from utils.metrics import kpis_empaque, analisis_dotacion, interpretacion_dotacion


def layout():
    return html.Div([
        page_header("Empaque",
                    subtitle="Kilogramos empacados y distribución por tipo de empaque"),
        filter_panel(),
        html.Div(id="empaque-contenido"),
    ], className="ops-page ops-process-page process-empaque")


@callback(
    Output("empaque-contenido", "children"),
    Input("store-archivo", "data"),
    Input("store-data",    "data"),
    Input("store-filtros", "data"),
)
def render(archivo, store_data, filtros):
    if not archivo:
        return empty_state("No se encontraron registros en Supabase para este proceso.")

    df = get_data_filtrada(store_data, filtros, "Empaque")
    k = kpis_empaque(df)
    cobertura = f"{k['dias_operativos']} días operativos · {k['registros']} registros"

    kpis1 = kpi_row([
        kpi_card("Kg recibidos (total)", fmt_num(k["total_recibido"]),
                 sub=cobertura, nivel="neutral"),
        kpi_card("Kg empacados (total)", fmt_num(k["total_empacado"]),
                 sub="Efectivamente empacados", nivel="neutral"),
        kpi_card("Empacado / recibido", fmt_pct(k["pct_empacado"]),
                 sub=f"Meta: {fmt_pct(k['estandar_pct'])}", nivel=k["nivel_cumpl"]),
        kpi_card("En cajas", fmt_num(k["total_cajas"]),
                 sub=f"{fmt_pct(k['pct_cajas'])} del total", nivel="neutral"),
    ])
    # Fila parcial (solo 2 de 4). Usamos kpi_row igual con 4 items:
    kpis2 = kpi_row([
        kpi_card("En sacos", fmt_num(k["total_sacos"]),
                 sub=f"{fmt_pct(k['pct_sacos'])} del total", nivel="neutral"),
        kpi_card("En bolsas", fmt_num(k["total_bolsas"]),
                 sub=f"{fmt_pct(k['pct_bolsas'])} del total", nivel="neutral"),
        html.Div(),  # vacios para mantener grid de 4
        html.Div(),
    ])

    # Dotacion
    dot = analisis_dotacion(df, "Empaque")
    dot_block = dotacion_block(dot, interpretacion_dotacion(dot, "Empaque"))

    # Distribucion por tipo de empaque
    labels, values = [], []
    if k["total_cajas"] > 0:  labels.append("Cajas");  values.append(k["total_cajas"])
    if k["total_sacos"] > 0:  labels.append("Sacos");  values.append(k["total_sacos"])
    if k["total_bolsas"] > 0: labels.append("Bolsas"); values.append(k["total_bolsas"])
    if labels:
        donut = dcc.Graph(
            figure=donut_composicion(labels, values, titulo="Kg por tipo de empaque"),
            config={"displayModeBar": False})
    else:
        donut = empty_state("Sin datos de distribución por tipo de empaque.")

    # Tendencia
    if not df.empty and "Fecha" in df.columns and "Kg Empacados" in df.columns:
        serie = df.dropna(subset=["Fecha"]).copy()
        serie["_FechaDia"] = pd.to_datetime(serie["Fecha"], errors="coerce").dt.date
        serie = (serie.dropna(subset=["_FechaDia"])
                     .groupby("_FechaDia", as_index=False)["Kg Empacados"].sum())
        serie.columns = ["Fecha", "Kg Empacados"]
        tend = dcc.Graph(
            figure=line_temporal(serie, x="Fecha", y="Kg Empacados",
                                 titulo="Kg empacados por día", y_label="Kg"),
            config={"displayModeBar": False})
    else:
        tend = empty_state("Sin datos temporales.")

    rank_finca = (dcc.Graph(figure=barh_ranking(df, cat="Finca", val="Kg Empacados",
                                                titulo="Kg empacados por finca"),
                            config={"displayModeBar": False})
                  if not df.empty and "Finca" in df.columns
                  else empty_state("Sin datos por finca."))
    if not df.empty and "Lote" in df.columns:
        d = df.copy(); d["Lote"] = d["Lote"].astype(str)
        rank_lote = dcc.Graph(figure=barh_ranking(d, cat="Lote", val="Kg Empacados",
                                                  titulo="Kg empacados por lote"),
                              config={"displayModeBar": False})
    else:
        rank_lote = empty_state("Sin datos por lote.")

    tabla = detail_table(df,
        columnas=["Fecha", "Finca", "Lote", "Kg Recibidos", "Kg Empacados",
                  "Kg Cajas", "Kg Sacos", "Kg Bolsas",
                  "Numero Trabajadores", "Horas", "Observaciones"],
        height=400, id="empaque-detalle")

    return html.Div([
        html.H2("Indicadores del proceso"), kpis1, kpis2,
        html.H2("Gestión de personal"), dot_block,
        html.H2("Distribución por tipo de empaque"), donut,
        html.H2("Tendencia diaria"), tend,
        html.H2("Empaque por finca y lote"),
        html.Div([rank_finca, rank_lote], className="two-col"),
        html.H2("Detalle de registros"), tabla,
    ])
