"""
pages/cosecha.py
----------------
Detalle del proceso Cosecha con análisis de rentabilidad de maquinaria y
gestión de personal.
[Equivalente a pages/4_Cosecha.py de Streamlit]
"""

from __future__ import annotations

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
    maquinaria_table,
)
from components.charts import daily_complete_series, line_temporal, barh_ranking
from components.sidebar import get_data_filtrada
from utils.metrics import (
    kpis_cosecha,
    analisis_maquinaria,
    analisis_dotacion,
    interpretacion_dotacion,
)
from config.settings import ESTANDARES


def layout():
    return html.Div(
        [
            page_header(
                "Cosecha",
                subtitle="Producción, calidad de cosecha, rentabilidad de maquinaria",
            ),
            filter_panel(),
        html.Div(id="cosecha-contenido"),
        ],
        className="ops-page ops-process-page process-cosecha"
    )


@callback(
    Output("cosecha-contenido", "children"),
    Input("store-archivo", "data"),
    Input("store-data", "data"),
    Input("store-filtros", "data"),
)
def render(archivo, store_data, filtros):
    if not archivo:
        return empty_state("No se encontraron registros en Supabase para este proceso.")

    df = get_data_filtrada(store_data, filtros, "Cosecha")
    k = kpis_cosecha(df)
    est = ESTANDARES["Cosecha"]

    cobertura = f"{k['dias_operativos']} días operativos · {k['registros']} registros"

    # ---------- KPIs ----------
    kpis1 = kpi_row(
        [
            kpi_card(
                "Kilogramos cosechados",
                fmt_num(k["total_kg"]) + " kg",
                sub=cobertura,
                nivel="neutral",
            ),
            kpi_card(
                "Kg por persona/día",
                fmt_num(k["prod_persona_dia"])
                if k["prod_persona_dia"] is not None
                else "-",
                sub=f"Estándar: {fmt_num(k['estandar_persona'])}",
                nivel=k["nivel_cumpl"],
            ),
            kpi_card(
                "Cumplimiento",
                fmt_pct(k["cumpl_prod"]),
                sub="Real vs estándar",
                nivel=k["nivel_cumpl"],
            ),
            kpi_card(
                "Descarte",
                fmt_pct(k["pct_descarte"]),
                sub=f"{fmt_num(k['total_descarte'])} kg descartados",
                nivel=k["nivel_descarte"],
            ),
        ]
    )

    kpis2 = kpi_row(
        [
            kpi_card(
                "Promedio diario",
                fmt_num(k["prom_kg_jornada"])
                if k["prom_kg_jornada"] is not None
                else "-",
                sub="Kg por día operativo",
                nivel="neutral",
            ),
            kpi_card(
                "Horas acumuladas",
                fmt_num(k["total_horas"], decimals=1),
                sub="Horas trabajadas",
                nivel="neutral",
            ),
            kpi_card(
                "Toneladas producidas",
                fmt_num(k["total_kg"] / 1000, 2) + " t",
                sub="Convertido desde kg",
                nivel="neutral",
            ),
        ]
    )

    # ---------- Cumplimiento vs estándar ----------
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
                    decimals=0,
                    nivel=k["nivel_cumpl"],
                ),
            ],
            className="section-panel",
        )

    # ---------- Rentabilidad de maquinaria ----------
    maq = analisis_maquinaria(df)

    if maq["con_maq"]["jornadas"] == 0 and maq["sin_maq"]["jornadas"] == 0:
        maq_block = empty_state("Sin datos suficientes para comparar uso de maquinaria.")
    else:
        tabla_m = maquinaria_table(maq)

        con_hp = maq["con_maq"].get("kg_por_hora_persona")
        sin_hp = maq["sin_maq"].get("kg_por_hora_persona")

        lectura = None

        if con_hp and sin_hp:
            if con_hp > sin_hp * 1.05:
                lectura = html.Div(
                    [
                        "La maquinaria ",
                        html.B("mejora la eficiencia por hora-persona"),
                        f": {fmt_num(con_hp, 2)} kg/hora-persona con máquina vs "
                        f"{fmt_num(sin_hp, 2)} sin máquina. Conviene evaluar si el "
                        "costo de arriendo de la maquinaria compensa el ahorro en "
                        "mano de obra.",
                    ],
                    className="section-panel",
                )
            elif sin_hp > con_hp * 1.05:
                lectura = html.Div(
                    [
                        "La operación manual ",
                        html.B("rinde más por hora-persona"),
                        f": {fmt_num(sin_hp, 2)} kg/hora-persona vs "
                        f"{fmt_num(con_hp, 2)} con máquina. Revisar si el uso de "
                        "maquinaria está justificado por otros factores como terreno, "
                        "clima o escala.",
                    ],
                    className="section-panel",
                )
            else:
                lectura = html.Div(
                    [
                        "La eficiencia por hora-persona es ",
                        html.B("similar con y sin maquinaria"),
                        ". La decisión depende de costos fijos, disponibilidad y "
                        "condiciones del lote.",
                    ],
                    className="section-panel",
                )

        maq_block = html.Div([tabla_m, lectura] if lectura else [tabla_m])

    # ---------- Dotación ----------
    dot = analisis_dotacion(df, "Cosecha")
    dot_block = dotacion_block(dot, interpretacion_dotacion(dot, "Cosecha"))

    # ---------- Tendencia ----------
    if not df.empty and "Fecha" in df.columns and "Produccion Kg" in df.columns:
        f = filtros or {}
        serie = daily_complete_series(
            df,
            date_col="Fecha",
            value_cols=["Produccion Kg", "Descarte Kg"],
            start=f.get("fecha_inicio"),
            end=f.get("fecha_fin"),
        )

        serie.columns = ["Fecha", "Producción Kg", "Descarte Kg"]

        fig1 = line_temporal(
            serie[["Fecha", "Producción Kg"]],
            x="Fecha",
            y="Producción Kg",
            titulo="Producción diaria",
            y_label="Kg",
        )

        fig2 = line_temporal(
            serie[["Fecha", "Descarte Kg"]],
            x="Fecha",
            y="Descarte Kg",
            titulo="Descarte diario",
            y_label="Kg",
        )

        tend = html.Div(
            [
                dcc.Graph(figure=fig1, config={"displayModeBar": False, "responsive": True}),
                dcc.Graph(figure=fig2, config={"displayModeBar": False, "responsive": True}),
            ],
            className="two-col",
        )
    else:
        tend = empty_state("Sin datos temporales disponibles.")

    # ---------- Ranking finca/proyecto ----------
    rank_finca = (
        dcc.Graph(
            figure=barh_ranking(
                df,
                cat="Finca",
                val="Produccion Kg",
                titulo="Kg cosechados por finca",
            ),
            config={"displayModeBar": False},
        )
        if not df.empty and "Finca" in df.columns
        else empty_state("Sin información por finca.")
    )

    rank_proy = (
        dcc.Graph(
            figure=barh_ranking(
                df,
                cat="Proyecto",
                val="Produccion Kg",
                titulo="Kg cosechados por proyecto",
            ),
            config={"displayModeBar": False},
        )
        if not df.empty and "Proyecto" in df.columns
        else empty_state("Sin información por proyecto.")
    )

    tabla = detail_table(
        df,
        columnas=[
            "Fecha",
            "Finca",
            "Proyecto",
            "Lote",
            "Surcos",
            "Numero Trabajadores",
            "Horas",
            "Maquinaria",
            "Horas Maquina",
            "Produccion Kg",
            "Descarte Kg",
            "Observaciones",
        ],
        height=400,
        id="cosecha-detalle",
    )

    return html.Div(
        [
            html.H2("Indicadores del proceso"),
            kpis1,
            kpis2,

            html.H2("Cumplimiento vs estándar"),
            pvr,

            html.H2("Rentabilidad de maquinaria"),
            html.Div(
                "Comparativo con y sin uso de maquinaria bajo tres lentes: "
                "kg promedio por día operativo, kg por hora trabajada y kg por "
                "hora-persona. El factor tiempo es clave porque la maquinaria "
                "se paga por jornada completa.",
                className="muted",
            ),
            maq_block,

            html.H2("Gestión de personal"),
            dot_block,

            html.H2("Tendencia diaria"),
            tend,

            html.H2("Producción por finca y proyecto"),
            html.Div([rank_finca, rank_proy], className="two-col"),

            html.H2("Detalle de registros"),
            tabla,
        ]
    )
