"""
pages/lavado.py
---------------
Lavado y clasificación: calidad, productividad y pérdidas.
Comercializable = 1ra + 2da + 3ra.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from styles.theme import page_header, empty_state
from pages._common import filter_panel
from components.ui import (
    kpi_card,
    kpi_row,
    fmt_num,
    fmt_pct,
    plan_vs_real_row,
    detail_table,
    dotacion_block,
)
from components.charts import (
    line_temporal,
    barh_ranking,
    bar_plan_vs_real,
)
from components.sidebar import get_data_filtrada
from utils.metrics import kpis_lavado, analisis_dotacion, interpretacion_dotacion
from config.settings import ESTANDARES


# ---------------------------------------------------------------------------
# Gráfica corregida: dona limpia sin etiquetas montadas
# ---------------------------------------------------------------------------

def donut_calidad_limpia(labels, values, titulo="Composición del producto clasificado"):
    """
    Dona para distribución por calidad.

    Corrección visual:
    - Evita etiquetas externas montadas.
    - Muestra porcentajes dentro de la dona.
    - Deja los nombres en la leyenda.
    - Mantiene la estética de marca Puro Finca.
    """

    colores = [
        "#1f6f3a",  # Primera
        "#f28c18",  # Segunda
        "#73c423",  # Tercera
        "#1bb470",  # Semilla
        "#b23a3a",  # Descarte si aparece
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.62,
            sort=False,
            direction="clockwise",
            marker=dict(
                colors=colores[:len(labels)],
                line=dict(color="#f4f1e8", width=3),
            ),
            textinfo="percent",
            textposition="inside",
            insidetextorientation="horizontal",
            textfont=dict(size=12, color="#1a1d1a"),
            hovertemplate="<b>%{label}</b><br>%{value:,.0f} kg<br>%{percent}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text=titulo,
            x=0.02,
            xanchor="left",
            font=dict(size=14, color="#1a1d1a"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=390,
        margin=dict(l=20, r=20, t=70, b=20),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.08,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#4a4d48"),
            itemclick=False,
            itemdoubleclick=False,
        ),
        uniformtext=dict(
            minsize=10,
            mode="hide",
        ),
    )

    return fig


def layout():
    return html.Div(
        [
            page_header(
                "Lavado y clasificación",
                subtitle="Recepción, lavado, calidad y pérdidas operativas",
            ),
            filter_panel(),
        html.Div(id="lavado-contenido"),
        ],
        className="ops-page ops-process-page process-lavado"
    )


@callback(
    Output("lavado-contenido", "children"),
    Input("store-archivo", "data"),
    Input("store-data", "data"),
    Input("store-filtros", "data"),
)
def render(archivo, store_data, filtros):
    if not archivo:
        return empty_state("No se encontraron registros en Supabase para este proceso.")

    df = get_data_filtrada(store_data, filtros, "Lavado Clasificacion")
    k = kpis_lavado(df)

    est = ESTANDARES["Lavado Clasificacion"]
    est_cos = ESTANDARES["Cosecha"]

    cobertura = f"{k['dias_operativos']} días operativos · {k['registros']} registros"

    # -----------------------------------------------------------------------
    # KPIs principales
    # -----------------------------------------------------------------------

    kpis1 = kpi_row(
        [
            kpi_card(
                "Kg recibidos (total)",
                fmt_num(k["total_recibido"]),
                sub=cobertura,
                nivel="neutral",
            ),
            kpi_card(
                "Kg lavados (total)",
                fmt_num(k["total_lavado"]),
                sub="Efectivamente lavados",
                nivel="neutral",
            ),
            kpi_card(
                "Primera calidad",
                fmt_pct(k["pct_1"]),
                sub=f"{fmt_num(k['total_1'])} kg · objetivo 60%",
                nivel=k["nivel_primera"],
            ),
            kpi_card(
                "Caja comercializable",
                fmt_pct(k["pct_comercial"]),
                sub="1ra + 2da + 3ra sobre salida total",
                nivel=k["nivel_comercial"],
            ),
        ]
    )

    kpis2 = kpi_row(
        [
            kpi_card(
                "Segunda calidad",
                fmt_pct(k["pct_2"]),
                sub=f"{fmt_num(k['total_2'])} kg",
                nivel="neutral",
            ),
            kpi_card(
                "Tercera calidad",
                fmt_pct(k["pct_3"]),
                sub=f"{fmt_num(k['total_3'])} kg",
                nivel="neutral",
            ),
            kpi_card(
                "Pérdida en lavado",
                fmt_pct(k["pct_perdida"]),
                sub=f"{fmt_num(k['total_descarte'])} kg",
                nivel=k["nivel_perdida"],
            ),
            kpi_card(
                "Kg por persona/día (promedio)",
                fmt_num(k["prod_persona_dia"])
                if k["prod_persona_dia"] is not None
                else "-",
                sub=f"Estándar: {fmt_num(k['estandar_persona'])}",
                nivel=k["nivel_cumpl"],
            ),
        ]
    )

    # -----------------------------------------------------------------------
    # Plan vs Real
    # -----------------------------------------------------------------------

    if df is None or df.empty:
        pvr = empty_state("Sin registros con los filtros actuales.")
    else:
        pvr = html.Div(
            [
                plan_vs_real_row(
                    "Kilogramos por persona/día",
                    plan=est["kg_persona_dia"],
                    real=k["prod_persona_dia"],
                    unidad="kg",
                    nivel=k["nivel_cumpl"],
                ),
                html.Hr(),
                plan_vs_real_row(
                    "% Primera calidad",
                    plan=est_cos["pct_primera"] * 100,
                    real=(k["pct_1"] * 100) if k["pct_1"] is not None else None,
                    unidad="%",
                    decimals=1,
                    nivel=k["nivel_primera"],
                ),
                html.Hr(),
                plan_vs_real_row(
                    "% Caja comercializable (1ra+2da+3ra)",
                    plan=est_cos["pct_comercializable"] * 100,
                    real=(k["pct_comercial"] * 100)
                    if k["pct_comercial"] is not None
                    else None,
                    unidad="%",
                    decimals=1,
                    nivel=k["nivel_comercial"],
                ),
            ],
            className="section-panel",
        )

    # -----------------------------------------------------------------------
    # Dotación
    # -----------------------------------------------------------------------

    dot = analisis_dotacion(df, "Lavado Clasificacion")
    dot_block = dotacion_block(
        dot,
        interpretacion_dotacion(dot, "Lavado Clasificacion"),
    )

    # -----------------------------------------------------------------------
    # Distribución por calidad
    # -----------------------------------------------------------------------

    labels, values = [], []

    if k["total_1"] and k["total_1"] > 0:
        labels.append("Primera")
        values.append(k["total_1"])

    if k["total_2"] and k["total_2"] > 0:
        labels.append("Segunda")
        values.append(k["total_2"])

    if k["total_3"] and k["total_3"] > 0:
        labels.append("Tercera")
        values.append(k["total_3"])

    if k["total_semilla"] and k["total_semilla"] > 0:
        labels.append("Semilla")
        values.append(k["total_semilla"])

    if k.get("total_descarte") and k["total_descarte"] > 0:
        labels.append("Descarte")
        values.append(k["total_descarte"])

    if labels:
        donut = dcc.Graph(
            figure=donut_calidad_limpia(
                labels,
                values,
                titulo="Composición del producto clasificado",
            ),
            config={"displayModeBar": False},
            style={"height": "410px"},
        )
    else:
        donut = empty_state("Sin datos de clasificación.")

    # -----------------------------------------------------------------------
    # % por calidad vs estándar
    # -----------------------------------------------------------------------

    if any(v is not None for v in [k["pct_1"], k["pct_2"], k["pct_3"]]):
        cats = ["Primera", "Segunda", "Tercera"]

        plan = [
            est_cos["pct_primera"] * 100,
            est_cos["pct_segunda"] * 100,
            est_cos["pct_tercera"] * 100,
        ]

        real = [
            (k["pct_1"] or 0) * 100,
            (k["pct_2"] or 0) * 100,
            (k["pct_3"] or 0) * 100,
        ]

        barras = dcc.Graph(
            figure=bar_plan_vs_real(
                cats,
                plan,
                real,
                titulo="% por calidad vs estándar",
                y_label="%",
            ),
            config={"displayModeBar": False},
            style={"height": "410px"},
        )
    else:
        barras = empty_state("Sin datos para comparar con estándar.")

    # -----------------------------------------------------------------------
    # Tendencia diaria
    # -----------------------------------------------------------------------

    if not df.empty and "Fecha" in df.columns and "Kg Lavados" in df.columns:
        serie = df.dropna(subset=["Fecha"]).copy()
        serie["_FechaDia"] = pd.to_datetime(
            serie["Fecha"],
            errors="coerce",
        ).dt.date

        serie = (
            serie.dropna(subset=["_FechaDia"])
            .groupby("_FechaDia", as_index=False)["Kg Lavados"]
            .sum()
        )

        serie.columns = ["Fecha", "Kg Lavados"]

        tend = dcc.Graph(
            figure=line_temporal(
                serie,
                x="Fecha",
                y="Kg Lavados",
                titulo="Kg lavados por día",
                y_label="Kg",
            ),
            config={"displayModeBar": False},
        )
    else:
        tend = empty_state("Sin datos temporales.")

    # -----------------------------------------------------------------------
    # Ranking por finca y lote
    # -----------------------------------------------------------------------

    rank_finca = (
        dcc.Graph(
            figure=barh_ranking(
                df,
                cat="Finca",
                val="Kg Lavados",
                titulo="Kg lavados por finca",
            ),
            config={"displayModeBar": False},
        )
        if not df.empty and "Finca" in df.columns
        else empty_state("Sin datos por finca.")
    )

    if not df.empty and "Lote" in df.columns:
        d = df.copy()
        d["Lote"] = d["Lote"].astype(str)

        rank_lote = dcc.Graph(
            figure=barh_ranking(
                d,
                cat="Lote",
                val="Kg Lavados",
                titulo="Kg lavados por lote",
            ),
            config={"displayModeBar": False},
        )
    else:
        rank_lote = empty_state("Sin datos por lote.")

    # -----------------------------------------------------------------------
    # Detalle
    # -----------------------------------------------------------------------

    tabla = detail_table(
        df,
        columnas=[
            "Fecha",
            "Finca",
            "Lote",
            "Kg Recibidos",
            "Kg Lavados",
            "Kg 1ra",
            "Kg 2da",
            "Kg 3ra",
            "Kg Semilla",
            "Kg Descarte Lavado",
            "Numero Trabajadores",
            "Horas",
            "Observaciones",
        ],
        height=400,
        id="lavado-detalle",
    )

    return html.Div(
        [
            html.H2("Indicadores del proceso"),
            kpis1,
            kpis2,

            html.H2("Cumplimiento vs estándar"),
            pvr,

            html.H2("Gestión de personal"),
            dot_block,

            html.H2("Distribución por calidad"),
            html.Div([donut, barras], className="two-col"),

            html.Div(
                "La tercera calidad sí se considera comercializable. "
                "No comercializable corresponde a semilla y descarte.",
                className="section-panel",
                style={
                    "fontSize": "0.92rem",
                    "padding": "0.85rem 1rem",
                    "marginTop": "-0.6rem",
                    "marginBottom": "1.2rem",
                    "color": "#4a4d48",
                },
            ),

            html.H2("Tendencia diaria"),
            tend,

            html.H2("Lavado por finca y lote"),
            html.Div([rank_finca, rank_lote], className="two-col"),

            html.H2("Detalle de registros"),
            tabla,
        ]
    )