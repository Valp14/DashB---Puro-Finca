"""
pages/productividad.py
----------------------
Vista consolidada de productividad entre procesos.
[Equivalente a pages/1_Productividad_General.py del proyecto Streamlit]
"""

from __future__ import annotations

import pandas as pd
from dash import Input, Output, callback, dcc, html

from config.settings import PROCESOS
from styles.theme import page_header, empty_state
from pages._common import filter_panel
from components.ui import (kpi_card, kpi_row, fmt_num, fmt_pct, detail_table)
from components.charts import bar_plan_vs_real, barh_ranking, line_temporal
from components.sidebar import get_data_filtrada
from utils.metrics import (
    kpis_corte, kpis_siembra, kpis_cosecha,
    kpis_lavado, kpis_empaque, kpis_cargue,
    analisis_dotacion,
)


def layout():
    return html.Div([
        page_header("Productividad general",
                    subtitle="Comparativo entre procesos y tendencias de desempeño"),
        filter_panel(),
        html.Div(id="productividad-contenido"),
    ], className="ops-page ops-process-page process-productividad")


@callback(
    Output("productividad-contenido", "children"),
    Input("store-archivo", "data"),
    Input("store-data",    "data"),
    Input("store-filtros", "data"),
)
def render(archivo, store_data, filtros):
    if not archivo:
        return empty_state("No se encontraron datos en Supabase para calcular la productividad general.")

    data = {p: get_data_filtrada(store_data, filtros, p) for p in PROCESOS}
    kcorte   = kpis_corte(data["Corte Esquejes"])
    ksiembra = kpis_siembra(data["Siembra"])
    kcosecha = kpis_cosecha(data["Cosecha"])
    klavado  = kpis_lavado(data["Lavado Clasificacion"])
    kempaque = kpis_empaque(data["Empaque"])
    kcargue  = kpis_cargue(data["Cargue Vehiculo"])

    # ---------- Cumplimiento por proceso (6 tarjetas) ----------
    fila = kpi_row([
        kpi_card("Corte",   fmt_pct(kcorte["cumpl_prod"]),  sub="esquejes/persona/día",  nivel=kcorte["nivel_cumpl"]),
        kpi_card("Siembra", fmt_pct(ksiembra["cumpl_prod"]),sub="plantas/persona/día",   nivel=ksiembra["nivel_cumpl"]),
        kpi_card("Cosecha", fmt_pct(kcosecha["cumpl_prod"]),sub="kg/persona/día",        nivel=kcosecha["nivel_cumpl"]),
        kpi_card("Lavado",  fmt_pct(klavado["cumpl_prod"]), sub="kg/persona/día",        nivel=klavado["nivel_cumpl"]),
        kpi_card("Empaque", fmt_pct(kempaque["cumpl_empacado"]), sub="vs meta 95%", nivel=kempaque["nivel_cumpl"]),
        kpi_card("Cargue",  fmt_pct(kcargue["cumpl_ton"]), sub="t promedio/despacho",    nivel=kcargue["nivel_cumpl"]),
    ])

    # ---------- Índice de cumplimiento comparable entre procesos ----------
    cats, plan, real = [], [], []
    for lbl, pct in (
        ("Corte", kcorte["cumpl_prod"]),
        ("Siembra", ksiembra["cumpl_prod"]),
        ("Cosecha", kcosecha["cumpl_prod"]),
        ("Lavado", klavado["cumpl_prod"]),
        ("Empaque", kempaque["cumpl_empacado"]),
        ("Cargue", kcargue["cumpl_ton"]),
    ):
        if pct is not None:
            cats.append(lbl)
            plan.append(100.0)
            real.append(pct * 100.0)

    if cats:
        fig_prod = bar_plan_vs_real(cats, plan, real,
                                    titulo="Cumplimiento relativo por proceso",
                                    y_label="% del estándar / meta")
        prod_chart = dcc.Graph(figure=fig_prod, config={"displayModeBar": False})
    else:
        prod_chart = empty_state("Sin datos suficientes para comparar cumplimiento entre procesos.")

    # ---------- Dotacion consolidada ----------
    filas = []
    diag_map = {"subcontratacion": "Subcontratación",
                "sobrecontratacion": "Sobrecontratación",
                "alineado": "Alineado", "sin_datos": "Sin datos"}
    for proc in PROCESOS:
        dot = analisis_dotacion(data[proc], proc)
        filas.append({
            "Proceso":              proc,
            "Requerido (personas)": dot["estandar"],
            "Asignado promedio":    round(dot["promedio_real"], 1) if dot.get("promedio_real") is not None else None,
            "Desviación %":         round(dot["desviacion_pct"] * 100, 1) if dot.get("desviacion_pct") is not None else None,
            "Días operativos":      dot.get("total_jornadas", 0),
            "Diagnóstico":          diag_map.get(dot["diagnostico"], "Sin datos"),
        })
    tabla_dot = detail_table(pd.DataFrame(filas), id="tabla-dotacion-prod")

    # ---------- Ranking por finca ----------
    ranking_chart = empty_state("No hay datos suficientes para construir el ranking.")
    for hoja, col in (("Cosecha", "Produccion Kg"),
                      ("Lavado Clasificacion", "Kg Lavados"),
                      ("Empaque", "Kg Empacados")):
        df = data.get(hoja, pd.DataFrame())
        if df is not None and not df.empty and "Finca" in df.columns and col in df.columns:
            fig = barh_ranking(df, cat="Finca", val=col,
                               titulo=f"Producción acumulada por finca ({hoja}) · kg")
            ranking_chart = dcc.Graph(figure=fig, config={"displayModeBar": False})
            break

    # ---------- Tendencia cosecha ----------
    df_cos = data.get("Cosecha", pd.DataFrame())
    if not df_cos.empty and "Fecha" in df_cos.columns and "Produccion Kg" in df_cos.columns:
        serie = df_cos.dropna(subset=["Fecha"]).copy()
        serie["_FechaDia"] = pd.to_datetime(serie["Fecha"], errors="coerce").dt.date
        serie = (serie.dropna(subset=["_FechaDia"])
                     .groupby("_FechaDia", as_index=False)["Produccion Kg"].sum())
        serie.columns = ["Fecha", "Produccion Kg"]
        fig = line_temporal(serie, x="Fecha", y="Produccion Kg",
                            titulo="Kg cosechados por día", y_label="Kg")
        tend_chart = dcc.Graph(figure=fig, config={"displayModeBar": False})
    else:
        tend_chart = empty_state("Sin datos de cosecha para graficar tendencia.")

    return html.Div([
        html.H2("Cumplimiento vs estándar"),
        fila,

        html.H2("Cumplimiento comparable"),
        html.Div("Para evitar mezclar unidades incompatibles, esta comparación "
                 "normaliza cada proceso como porcentaje de su estándar o meta. "
                 "Los ceros distorsionantes se excluyen del cálculo cuando así "
                 "lo define la metodología.",
                 className="muted"),
        prod_chart,

        html.H2("Gestión de personal por proceso"),
        html.Div("Comparativo de personas requeridas vs promedio realmente "
                 "asignado. Diagnóstico de subcontratación, sobrecontratación "
                 "o asignación alineada al estándar.", className="muted"),
        tabla_dot,

        html.H2("Producción por finca"),
        ranking_chart,

        html.H2("Tendencia diaria de cosecha"),
        tend_chart,
    ])
