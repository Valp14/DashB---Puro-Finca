"""
pages/plan_vs_real.py
---------------------
Comparativo consolidado plan vs real por proceso.
[Equivalente a pages/9_Plan_vs_Real.py de Streamlit]
"""

from __future__ import annotations

import pandas as pd
from dash import Input, Output, callback, html

from config.settings import ESTANDARES
from styles.theme import page_header, empty_state
from pages._common import filter_panel
from components.ui import fmt_pct, plan_vs_real_row, detail_table
from components.sidebar import get_data_filtrada
from utils.metrics import (
    kpis_corte,
    kpis_siembra,
    kpis_cosecha,
    kpis_lavado,
    kpis_empaque,
    kpis_cargue,
    nivel_cumplimiento,
)


def layout():
    return html.Div([
        page_header("Plan vs real",
                    subtitle="Comparativo de metas operativas vs resultados reales"),
        filter_panel(),
        html.Div(id="plan-vs-real-contenido"),
    ], className="ops-page ops-process-page process-plan-real")


def _cumpl_label(pct):
    return "Sin datos" if pct is None else fmt_pct(pct)


def _estado(pct):
    niv = nivel_cumplimiento(pct)
    return {"ok": "Cumple", "alerta": "Alerta",
            "critico": "Crítico", "na": "Sin datos"}[niv]


@callback(
    Output("plan-vs-real-contenido", "children"),
    Input("store-archivo", "data"),
    Input("store-data",    "data"),
    Input("store-filtros", "data"),
)
def render(archivo, store_data, filtros):
    if not archivo:
        return empty_state("No se encontraron datos en Supabase para ver este comparativo.")

    kcorte   = kpis_corte(get_data_filtrada(store_data, filtros, "Corte Esquejes"))
    ksiembra = kpis_siembra(get_data_filtrada(store_data, filtros, "Siembra"))
    kcosecha = kpis_cosecha(get_data_filtrada(store_data, filtros, "Cosecha"))
    klavado  = kpis_lavado(get_data_filtrada(store_data, filtros, "Lavado Clasificacion"))
    kempaque = kpis_empaque(get_data_filtrada(store_data, filtros, "Empaque"))
    kcargue  = kpis_cargue(get_data_filtrada(store_data, filtros, "Cargue Vehiculo"))

    meta_ton_periodo = kcosecha["meta_ton_periodo"]

    filas = [
        {"Proceso": "Corte de esquejes", "Indicador": "Esquejes por persona/día",
         "Plan": kcorte["estandar_persona"],
         "Real": round(kcorte["prod_persona_dia"], 0) if kcorte["prod_persona_dia"] is not None else None,
         "Cumplimiento": _cumpl_label(kcorte["cumpl_prod"]),
         "Estado": _estado(kcorte["cumpl_prod"])},
        {"Proceso": "Siembra", "Indicador": "Plantas por persona/día",
         "Plan": ksiembra["estandar_persona"],
         "Real": round(ksiembra["prod_persona_dia"], 0) if ksiembra["prod_persona_dia"] is not None else None,
         "Cumplimiento": _cumpl_label(ksiembra["cumpl_prod"]),
         "Estado": _estado(ksiembra["cumpl_prod"])},
        {"Proceso": "Cosecha", "Indicador": "Kg por persona/día",
         "Plan": kcosecha["estandar_persona"],
         "Real": round(kcosecha["prod_persona_dia"], 0) if kcosecha["prod_persona_dia"] is not None else None,
         "Cumplimiento": _cumpl_label(kcosecha["cumpl_prod"]),
         "Estado": _estado(kcosecha["cumpl_prod"])},
        {"Proceso": "Cosecha", "Indicador": "Toneladas del período",
         "Plan": meta_ton_periodo,
         "Real": round(kcosecha["total_kg"] / 1000, 2) if kcosecha["total_kg"] is not None else None,
         "Cumplimiento": _cumpl_label(kcosecha["cumpl_meta_periodo"]),
         "Estado": "—"},
        {"Proceso": "Lavado y clasificación", "Indicador": "Kg por persona/día",
         "Plan": klavado["estandar_persona"],
         "Real": round(klavado["prod_persona_dia"], 0) if klavado["prod_persona_dia"] is not None else None,
         "Cumplimiento": _cumpl_label(klavado["cumpl_prod"]),
         "Estado": _estado(klavado["cumpl_prod"])},
        {"Proceso": "Lavado y clasificación", "Indicador": "% Primera calidad",
         "Plan": "60%", "Real": fmt_pct(klavado["pct_1"]),
         "Cumplimiento": _cumpl_label(
             (klavado["pct_1"] / 0.60) if klavado["pct_1"] is not None else None),
         "Estado": "—"},
        {"Proceso": "Lavado y clasificación",
         "Indicador": "% Caja comercializable (1ra+2da+3ra)",
         "Plan": "90%", "Real": fmt_pct(klavado["pct_comercial"]),
         "Cumplimiento": _cumpl_label(
             (klavado["pct_comercial"] / 0.90) if klavado["pct_comercial"] is not None else None),
         "Estado": "—"},
        {"Proceso": "Empaque", "Indicador": "Cumplimiento empaque vs meta",
         "Plan": "95%", "Real": fmt_pct(kempaque["pct_empacado"]),
         "Cumplimiento": _cumpl_label(kempaque["cumpl_empacado"]),
         "Estado": "—"},
        {"Proceso": "Cargue y despacho", "Indicador": "Toneladas promedio/despacho",
         "Plan": ESTANDARES["Cargue Vehiculo"]["toneladas"],
         "Real": round(kcargue["ton_promedio"], 2) if kcargue["ton_promedio"] is not None else None,
         "Cumplimiento": _cumpl_label(kcargue["cumpl_ton"]),
         "Estado": _estado(kcargue["cumpl_ton"])},
    ]
    tabla_resumen = detail_table(pd.DataFrame(filas), id="plan-real-resumen")

    corte_det = html.Div([
        html.H3("Corte de esquejes"),
        html.Div(plan_vs_real_row("Esquejes por persona/día",
                                  plan=kcorte["estandar_persona"],
                                  real=kcorte["prod_persona_dia"],
                                  unidad="esquejes", nivel=kcorte["nivel_cumpl"]),
                 className="section-panel"),
    ])
    siembra_det = html.Div([
        html.H3("Siembra"),
        html.Div(plan_vs_real_row("Plantas por persona/día",
                                  plan=ksiembra["estandar_persona"],
                                  real=ksiembra["prod_persona_dia"],
                                  unidad="plantas", nivel=ksiembra["nivel_cumpl"]),
                 className="section-panel"),
    ])
    cosecha_det = html.Div([
        html.H3("Cosecha"),
        html.Div([
            plan_vs_real_row("Kg por persona/día",
                             plan=kcosecha["estandar_persona"],
                             real=kcosecha["prod_persona_dia"],
                             unidad="kg", nivel=kcosecha["nivel_cumpl"]),
            html.Hr(),
            plan_vs_real_row("Toneladas del período",
                             plan=meta_ton_periodo,
                             real=(kcosecha["total_kg"] / 1000) if kcosecha["total_kg"] is not None else None,
                             unidad="t", decimals=2, nivel="neutral"),
        ], className="section-panel"),
    ])
    lavado_det = html.Div([
        html.H3("Lavado y clasificación"),
        html.Div([
            plan_vs_real_row("Kg por persona/día",
                             plan=klavado["estandar_persona"],
                             real=klavado["prod_persona_dia"],
                             unidad="kg", nivel=klavado["nivel_cumpl"]),
            html.Hr(),
            plan_vs_real_row("% Primera calidad", plan=60,
                             real=(klavado["pct_1"] * 100) if klavado["pct_1"] is not None else None,
                             unidad="%", decimals=1, nivel=klavado["nivel_primera"]),
            html.Hr(),
            plan_vs_real_row("% Comercializable (1ra+2da+3ra)", plan=90,
                             real=(klavado["pct_comercial"] * 100) if klavado["pct_comercial"] is not None else None,
                             unidad="%", decimals=1, nivel=klavado["nivel_comercial"]),
        ], className="section-panel"),
    ])
    empaque_det = html.Div([
        html.H3("Empaque"),
        html.Div(
            plan_vs_real_row("% Empacado / recibido",
                             plan=kempaque["estandar_pct"] * 100,
                             real=(kempaque["pct_empacado"] * 100) if kempaque["pct_empacado"] is not None else None,
                             unidad="%", decimals=1, nivel=kempaque["nivel_cumpl"]),
            className="section-panel",
        ),
    ])
    cargue_det = html.Div([
        html.H3("Cargue y despacho"),
        html.Div(plan_vs_real_row("Toneladas promedio por despacho",
                                  plan=ESTANDARES["Cargue Vehiculo"]["toneladas"],
                                  real=kcargue["ton_promedio"],
                                  unidad="t", decimals=2, nivel=kcargue["nivel_cumpl"]),
                 className="section-panel"),
    ])

    return html.Div([
        html.H2("Resumen plan vs real"),
        tabla_resumen,
        html.H2("Detalle por proceso"),
        corte_det, siembra_det, cosecha_det, lavado_det, empaque_det, cargue_det,
    ])
