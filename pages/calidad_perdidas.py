"""
pages/calidad_perdidas.py
-------------------------
Calidad, comercializable (1ra+2da+3ra), perdidas por etapa y flujo de produccion.
[Equivalente a pages/8_Calidad_y_Perdidas.py de Streamlit]
"""

from __future__ import annotations

import pandas as pd
from dash import Input, Output, callback, dcc, html

from styles.theme import page_header, empty_state
from pages._common import filter_panel
from components.ui import kpi_card, kpi_row, fmt_num, fmt_pct, pill
from components.charts import donut_composicion, bar_stacked_composition
from components.sidebar import get_data_filtrada
from utils.metrics import kpis_cosecha, kpis_lavado, kpis_empaque, kpis_cargue


def layout():
    return html.Div([
        page_header("Calidad y pérdidas",
                    subtitle="Composición por calidad, producto comercializable y pérdidas por etapa"),
        filter_panel(),
        html.Div(id="calidad-perdidas-contenido"),
    ], className="ops-page ops-process-page process-calidad")


@callback(
    Output("calidad-perdidas-contenido", "children"),
    Input("store-archivo", "data"),
    Input("store-data",    "data"),
    Input("store-filtros", "data"),
)
def render(archivo, store_data, filtros):
    if not archivo:
        return empty_state("No se encontraron datos en Supabase para ver esta vista.")

    kcos = kpis_cosecha(get_data_filtrada(store_data, filtros, "Cosecha"))
    klav = kpis_lavado(get_data_filtrada(store_data, filtros, "Lavado Clasificacion"))
    kemp = kpis_empaque(get_data_filtrada(store_data, filtros, "Empaque"))
    kcar = kpis_cargue(get_data_filtrada(store_data, filtros, "Cargue Vehiculo"))

    # ---------- KPIs de calidad ----------
    kpis = kpi_row([
        kpi_card("Primera calidad", fmt_pct(klav["pct_1"]),
                 sub=f"{fmt_num(klav['total_1'])} kg · objetivo 60%",
                 nivel=klav["nivel_primera"]),
        kpi_card("Segunda calidad", fmt_pct(klav["pct_2"]),
                 sub=f"{fmt_num(klav['total_2'])} kg · objetivo 25%",
                 nivel="neutral"),
        kpi_card("Tercera calidad", fmt_pct(klav["pct_3"]),
                 sub=f"{fmt_num(klav['total_3'])} kg · objetivo 15%",
                 nivel="neutral"),
        kpi_card("Caja comercializable", fmt_pct(klav["pct_comercial"]),
                 sub="1ra + 2da + 3ra sobre salida total",
                 nivel=klav["nivel_comercial"]),
    ])

    # ---------- Distribucion por calidad ----------
    labels, values = [], []
    if klav["total_1"] > 0:       labels.append("Primera"); values.append(klav["total_1"])
    if klav["total_2"] > 0:       labels.append("Segunda"); values.append(klav["total_2"])
    if klav["total_3"] > 0:       labels.append("Tercera"); values.append(klav["total_3"])
    if klav["total_semilla"] > 0: labels.append("Semilla"); values.append(klav["total_semilla"])

    donut1 = (dcc.Graph(figure=donut_composicion(labels, values,
                                                 titulo="Composición del producto clasificado"),
                        config={"displayModeBar": False})
              if labels else empty_state("Sin datos de clasificación."))

    comercial = (klav["total_1"] or 0) + (klav["total_2"] or 0) + (klav["total_3"] or 0)
    no_com = (klav["total_semilla"] or 0) + (klav["total_descarte"] or 0)
    if comercial + no_com > 0:
        donut2 = dcc.Graph(
            figure=donut_composicion(["Comercializable", "No comercializable"],
                                     [comercial, no_com],
                                     titulo="Comercializable vs no comercializable"),
            config={"displayModeBar": False})
    else:
        donut2 = empty_state("Sin datos para comparación.")

    aclaracion = html.Div([
        "La ", html.B("tercera calidad sí es comercializable"),
        ". No comercializable = semilla y descarte.",
    ], className="muted")

    # ---------- Volumen por etapa ----------
    etapas = []
    if kcos["total_kg"] > 0:       etapas.append(("Cosechado", kcos["total_kg"]))
    if klav["total_recibido"] > 0: etapas.append(("Recibido lavado", klav["total_recibido"]))
    if klav["total_lavado"] > 0:   etapas.append(("Lavado", klav["total_lavado"]))
    if kemp["total_empacado"] > 0: etapas.append(("Empacado", kemp["total_empacado"]))
    if kcar["total_toneladas"] > 0:
        etapas.append(("Despachado", kcar["total_toneladas"] * 1000))

    flujo_children = []
    if etapas:
        cats = [e[0] for e in etapas]
        vals = [e[1] for e in etapas]
        fig = bar_stacked_composition(categorias=cats,
                                      series={"Kilogramos": vals},
                                      titulo="Kilogramos por etapa del proceso",
                                      y_label="Kg")
        flujo_children.append(dcc.Graph(figure=fig, config={"displayModeBar": False}))
        flujo_children.append(html.Div(
            "Los volúmenes por etapa se muestran como referencia operativa del "
            "período filtrado. No se calcula merma trazable entre etapas porque "
            "el sistema actual aún no enlaza lotes/partidas de extremo a extremo.",
            className="section-panel",
        ))
    else:
        flujo_children.append(empty_state("Sin datos suficientes para construir el flujo."))

    # ---------- Perdidas consolidadas ----------
    total_perdida = (kcos["total_descarte"] or 0) + (klav["total_descarte"] or 0)
    total_prod    = kcos["total_kg"] or 0
    pct_global    = (total_perdida / total_prod) if total_prod > 0 else None
    perdidas_row = kpi_row([
        kpi_card("Descarte en cosecha", fmt_num(kcos["total_descarte"]) + " kg",
                 sub=f"{fmt_pct(kcos['pct_descarte'])} de producción",
                 nivel=kcos["nivel_descarte"]),
        kpi_card("Pérdida en lavado", fmt_num(klav["total_descarte"]) + " kg",
                 sub=f"{fmt_pct(klav['pct_perdida'])} de recibidos",
                 nivel=klav["nivel_perdida"]),
        kpi_card("Pérdida global", fmt_num(total_perdida) + " kg",
                 sub=f"{fmt_pct(pct_global)} de la cosecha total",
                 nivel="neutral"),
    ])

    # ---------- Alertas de calidad ----------
    alertas = []
    if klav.get("pct_1") is not None and klav["nivel_primera"] != "ok":
        alertas.append((
            "critico" if klav["nivel_primera"] == "critico" else "alerta",
            f"Primera calidad en {fmt_pct(klav['pct_1'])}: por debajo del objetivo 60%.",
        ))
    if klav.get("pct_comercial") is not None and klav["nivel_comercial"] != "ok":
        alertas.append((
            "critico" if klav["nivel_comercial"] == "critico" else "alerta",
            f"Comercializable en {fmt_pct(klav['pct_comercial'])}: revisar calidad del proceso.",
        ))
    if klav.get("pct_perdida") is not None and klav["nivel_perdida"] != "ok":
        alertas.append((
            "critico" if klav["nivel_perdida"] == "critico" else "alerta",
            f"Pérdida en lavado en {fmt_pct(klav['pct_perdida'])}: por encima del umbral.",
        ))

    if alertas:
        alertas_block = html.Div(
            html.Ul([html.Li([pill(niv), " ", msg],
                             style={"marginBottom": "6px"})
                     for niv, msg in alertas],
                    style={"margin": "0", "paddingLeft": "1rem"}),
            className="section-panel",
        )
    else:
        alertas_block = html.Div(
            "Sin alertas activas de calidad. Los indicadores están dentro "
            "de los umbrales.", className="section-panel")

    return html.Div([
        html.H2("Indicadores de calidad"), kpis,
        html.H2("Distribución por calidad"),
        html.Div([donut1, donut2], className="two-col"),
        aclaracion,
        html.H2("Volumen por etapa"),
        html.Div(flujo_children),
        html.H2("Pérdidas acumuladas"), perdidas_row,
        html.H2("Alertas de calidad"), alertas_block,
    ])
