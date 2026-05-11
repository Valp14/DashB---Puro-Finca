"""
pages/calidad_datos.py
----------------------
Deteccion de inconsistencias, registros sospechosos y errores de captura.
[Equivalente a pages/12_Calidad_de_Datos.py de Streamlit]

[MIGRACION Streamlit -> Dash]
Esta pagina tiene filtros LOCALES (severidad y proceso) ademas de la
reactividad con store-data. Los filtros locales se hacen con dos
dcc.Dropdown (multi) + un callback propio.
"""

from __future__ import annotations

import pandas as pd
from dash import Input, Output, callback, dcc, html

from config.settings import PROCESOS
from styles.theme import page_header, empty_state
from components.ui import (kpi_card, kpi_row, fmt_num, pill, detail_table)
from components.sidebar import store_to_dataframes
from utils.metrics import detectar_inconsistencias


def layout():
    return html.Div([
        page_header("Calidad de datos",
                    subtitle="Inconsistencias detectadas, registros sospechosos y acciones recomendadas"),

        # Los datos se almacenan en un dcc.Store local para que los filtros
        # no tengan que recalcular las inconsistencias cada vez.
        dcc.Store(id="qc-store-inc"),
        html.Div(id="qc-contenido"),

        html.Div("Esta página no aplica los filtros globales: se evalúa siempre "
                 "sobre la totalidad del archivo para no ocultar errores al "
                 "filtrar.",
                 className="muted",
                 style={"marginTop": "1rem"}),
    ], className="ops-page ops-process-page process-calidad-datos")


# ---------------------------------------------------------------------------
# Callback 1: calcular inconsistencias (solo cuando cambia el archivo cargado)
# ---------------------------------------------------------------------------
@callback(
    Output("qc-store-inc", "data"),
    Input("store-data",    "data"),
)
def calcular_inconsistencias(store_data):
    if not store_data:
        return []
    data_all = store_to_dataframes(store_data)
    inc = detectar_inconsistencias(data_all)
    if inc.empty:
        return []
    show = inc.copy()
    if "Fecha" in show.columns:
        show["Fecha"] = pd.to_datetime(show["Fecha"], errors="coerce")
        show["Fecha"] = show["Fecha"].dt.strftime("%Y-%m-%d")
    return show.to_dict("records")


# ---------------------------------------------------------------------------
# Callback 2: renderizar la pagina (depende del archivo cargado + inc local)
# ---------------------------------------------------------------------------
@callback(
    Output("qc-contenido", "children"),
    Input("store-archivo", "data"),
    Input("qc-store-inc",  "data"),
)
def render(archivo, inc_records):
    if not archivo:
        return empty_state("No se encontraron datos en Supabase para revisar la calidad de datos.")

    inc = pd.DataFrame(inc_records) if inc_records else pd.DataFrame()

    # ---------- KPIs resumen ----------
    total  = len(inc)
    altas  = int((inc["Severidad"] == "Alta").sum())  if not inc.empty else 0
    medias = int((inc["Severidad"] == "Media").sum()) if not inc.empty else 0
    bajas  = int((inc["Severidad"] == "Baja").sum())  if not inc.empty else 0

    nivel_total = "ok" if total == 0 else ("alerta" if total <= 3 else "critico")
    kpis = kpi_row([
        kpi_card("Inconsistencias totales", fmt_num(total),
                 sub="Registros con al menos una regla activa",
                 nivel=nivel_total),
        kpi_card("Severidad alta", fmt_num(altas),
                 sub="Requieren corrección inmediata",
                 nivel="critico" if altas > 0 else "ok"),
        kpi_card("Severidad media", fmt_num(medias),
                 sub="Revisar antes de presentar",
                 nivel="alerta" if medias > 0 else "ok"),
        kpi_card("Severidad baja", fmt_num(bajas),
                 sub="Sugerencia de mejora", nivel="neutral"),
    ])

    # ---------- Reglas aplicadas (tabla estatica) ----------
    reglas = pd.DataFrame([
        {"#": 1, "Proceso": "Todos",   "Regla": "Fecha faltante o inválida",             "Severidad": "Media"},
        {"#": 2, "Proceso": "Todos",   "Regla": "Valores negativos en columnas numéricas","Severidad": "Alta"},
        {"#": 3, "Proceso": "Lavado",  "Regla": "Kg lavados > kg recibidos",             "Severidad": "Alta"},
        {"#": 4, "Proceso": "Lavado",  "Regla": "Suma clasificada > kg lavados",         "Severidad": "Alta"},
        {"#": 5, "Proceso": "Cargue",  "Regla": "Valor digitado en kg (> umbral t)",     "Severidad": "Media"},
        {"#": 6, "Proceso": "Cosecha", "Regla": "Producción sin trabajadores",           "Severidad": "Media"},
        {"#": 7, "Proceso": "Cosecha", "Regla": "Producción sin horas",                  "Severidad": "Media"},
        {"#": 8, "Proceso": "Cosecha", "Regla": "Maquinaria declarada sin horas máquina","Severidad": "Baja"},
        {"#": 9, "Proceso": "Empaque", "Regla": "Kg empacados > kg recibidos",           "Severidad": "Alta"},
    ])

    # ---------- Detalle con filtros locales ----------
    if inc.empty:
        detalle = html.Div([
            html.B("Sin inconsistencias detectadas. "),
            "Todos los registros cumplen las reglas de validación aplicadas.",
        ], className="section-panel ok-accent")
    else:
        sev_opts = sorted(inc["Severidad"].unique().tolist())
        proc_opts = sorted(inc["Proceso"].unique().tolist())
        detalle = html.Div([
            html.Div([
                html.Div([
                    html.Div("Filtrar por severidad", className="control-label"),
                    dcc.Dropdown(id="qc-severidad", multi=True,
                                 options=[{"label": s, "value": s} for s in sev_opts],
                                 value=sev_opts),
                ]),
                html.Div([
                    html.Div("Filtrar por proceso", className="control-label"),
                    dcc.Dropdown(id="qc-proceso", multi=True,
                                 options=[{"label": p, "value": p} for p in proc_opts],
                                 value=proc_opts),
                ]),
            ], className="two-col"),
            html.Div(id="qc-tabla-detalle"),
        ])

    # ---------- Recomendaciones ----------
    recs = html.Div([
        html.B("Severidad alta "), pill("critico", "Alta"),
        ": corregir en el archivo de origen antes de usar los indicadores "
        "para decisiones. Afectan directamente cálculos de calidad, merma "
        "o productividad.",
        html.Br(), html.Br(),
        html.B("Severidad media "), pill("alerta", "Media"),
        ": revisar cuando sea posible. Pueden afectar promedios o análisis "
        "específicos. El dashboard sigue funcionando correctamente gracias "
        "al tratamiento de ceros.",
        html.Br(), html.Br(),
        html.B("Severidad baja "), pill("na", "Baja"),
        ": sugerencias para mejorar la captura. No bloquean análisis pero "
        "enriquecen la trazabilidad.",
    ], className="section-panel")

    return html.Div([
        html.H2("Resumen de inconsistencias"), kpis,
        html.H2("Reglas de validación aplicadas"),
        detail_table(reglas, id="tbl-reglas-qc"),
        html.H2("Detalle de hallazgos"), detalle,
        html.H2("Recomendaciones"), recs,
    ])


# ---------------------------------------------------------------------------
# Callback 3: aplicar filtros locales (solo se dispara si la tabla existe)
# ---------------------------------------------------------------------------
@callback(
    Output("qc-tabla-detalle", "children"),
    Input("qc-severidad", "value"),
    Input("qc-proceso",   "value"),
    Input("qc-store-inc", "data"),
    prevent_initial_call=False,
)
def filtrar_detalle(sev_sel, proc_sel, inc_records):
    if not inc_records:
        return empty_state("Sin hallazgos registrados.")
    inc = pd.DataFrame(inc_records)
    sev_sel  = sev_sel  or []
    proc_sel = proc_sel or []
    if sev_sel:
        inc = inc[inc["Severidad"].isin(sev_sel)]
    if proc_sel:
        inc = inc[inc["Proceso"].isin(proc_sel)]
    if inc.empty:
        return empty_state("Sin hallazgos para los filtros actuales.")
    return detail_table(inc, id="tbl-qc-detalle", height=400)
