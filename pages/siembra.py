"""
pages/siembra.py
----------------
Detalle del proceso Siembra.
[Equivalente a pages/3_Siembra.py de Streamlit]
"""

from __future__ import annotations

import pandas as pd
from dash import Input, Output, callback, dcc, html

from styles.theme import page_header, empty_state
from pages._common import filter_panel
from components.ui import (
    kpi_card,
    kpi_row,
    fmt_num,
    detail_table,
    dotacion_block,
)
from components.charts import line_temporal, barh_ranking
from components.sidebar import get_data_filtrada
from utils.metrics import kpis_siembra, analisis_dotacion, interpretacion_dotacion


def layout():
    return html.Div(
        [
            page_header(
                "Siembra",
                subtitle="Plantas sembradas, horas y productividad por persona",
            ),
            filter_panel(),
        html.Div(id="siembra-contenido"),
        ],
        className="ops-page ops-process-page process-siembra"
    )


@callback(
    Output("siembra-contenido", "children"),
    Input("store-archivo", "data"),
    Input("store-data", "data"),
    Input("store-filtros", "data"),
)
def render(archivo, store_data, filtros):
    if not archivo:
        return empty_state("No se encontraron registros en Supabase para este proceso.")

    df = get_data_filtrada(store_data, filtros, "Siembra")
    k = kpis_siembra(df)

    cobertura = f"{k['dias_operativos']} días operativos · {k['registros']} registros"

    # -----------------------------------------------------------------------
    # Indicadores del proceso
    # -----------------------------------------------------------------------
    kpis = kpi_row(
        [
            kpi_card(
                "Plantas sembradas",
                fmt_num(k["total_plantas"]),
                sub=cobertura,
                nivel="neutral",
            ),
            kpi_card(
                "Plantas por persona/día",
                fmt_num(k["prod_persona_dia"])
                if k["prod_persona_dia"] is not None
                else "-",
                sub=f"Estándar: {fmt_num(k['estandar_persona'])}",
                nivel=k["nivel_cumpl"],
            ),
            kpi_card(
                "Horas acumuladas",
                fmt_num(k["total_horas"], decimals=1),
                sub="Suma de horas trabajadas",
                nivel="neutral",
            ),
        ]
    )

    # -----------------------------------------------------------------------
    # Gestión de personal
    # -----------------------------------------------------------------------
    dot = analisis_dotacion(df, "Siembra")
    dot_block = dotacion_block(
        dot,
        interpretacion_dotacion(dot, "Siembra"),
    )

    # -----------------------------------------------------------------------
    # Tendencia diaria
    # -----------------------------------------------------------------------
    if not df.empty and "Fecha" in df.columns and "Plantas" in df.columns:
        serie = df.dropna(subset=["Fecha"]).copy()
        serie["_FechaDia"] = pd.to_datetime(
            serie["Fecha"],
            errors="coerce",
        ).dt.date

        serie = (
            serie.dropna(subset=["_FechaDia"])
            .groupby("_FechaDia", as_index=False)["Plantas"]
            .sum()
        )

        serie.columns = ["Fecha", "Plantas"]

        fig = line_temporal(
            serie,
            x="Fecha",
            y="Plantas",
            titulo="Plantas sembradas por día",
            y_label="Plantas",
        )

        tend = dcc.Graph(
            figure=fig,
            config={"displayModeBar": False},
        )
    else:
        tend = empty_state("Sin datos temporales.")

    # -----------------------------------------------------------------------
    # Ranking por finca
    # -----------------------------------------------------------------------
    if not df.empty and "Finca" in df.columns:
        rank_finca = dcc.Graph(
            figure=barh_ranking(
                df,
                cat="Finca",
                val="Plantas",
                titulo="Plantas por finca",
            ),
            config={"displayModeBar": False},
        )
    else:
        rank_finca = empty_state("Sin datos por finca.")

    # -----------------------------------------------------------------------
    # Ranking por lote
    # -----------------------------------------------------------------------
    if not df.empty and "Lote" in df.columns:
        d = df.copy()
        d["Lote"] = d["Lote"].astype(str)

        rank_lote = dcc.Graph(
            figure=barh_ranking(
                d,
                cat="Lote",
                val="Plantas",
                titulo="Plantas por lote",
            ),
            config={"displayModeBar": False},
        )
    else:
        rank_lote = empty_state("Sin datos por lote.")

    # -----------------------------------------------------------------------
    # Detalle de registros
    # -----------------------------------------------------------------------
    tabla = detail_table(
        df,
        columnas=[
            "Fecha",
            "Finca",
            "Lote",
            "Horas",
            "Numero Trabajadores",
            "Plantas",
            "Observaciones",
        ],
        height=360,
        id="siembra-detalle",
    )

    return html.Div(
        [
            html.H2("Indicadores del proceso"),
            kpis,

            html.H2("Gestión de personal"),
            dot_block,

            html.H2("Tendencia diaria"),
            tend,

            html.H2("Plantas por finca y lote"),
            html.Div([rank_finca, rank_lote], className="two-col"),

            html.H2("Detalle de registros"),
            tabla,
        ]
    )