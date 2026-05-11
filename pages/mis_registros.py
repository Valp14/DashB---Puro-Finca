"""Mis registros: vista simple para operador."""

from __future__ import annotations

import pandas as pd
from dash import Input, Output, callback, dash_table, html

from config.settings import PROCESOS
from components.sidebar import store_to_dataframes
from auth import current_role, current_user
from services.access_control import can_read_operational_data
from services.supabase_data import load_user_operational_store


def layout():
    return html.Div([
        html.Div([
            html.Div("Operación", className="eyebrow"),
            html.H1("Mis registros"),
            html.P("Consulta los últimos registros operativos cargados desde Supabase.", className="lead"),
        ], className="page-hero"),
        html.Div(id="mis-registros-contenido", className="panel-card"),
    ], className="ops-page ops-process-page process-registros")


@callback(Output("mis-registros-contenido", "children"), Input("store-data", "data"))
def render(store_data):
    if not can_read_operational_data(current_role()):
        store_data = load_user_operational_store(current_user())

    if False:
        return html.Div(
            "Por seguridad, este perfil no descarga el histórico completo en el navegador.",
            className="muted",
        )

    dfs = store_to_dataframes(store_data or {})
    rows = []
    for proceso in PROCESOS:
        df = dfs.get(proceso, pd.DataFrame())
        if df is None or df.empty:
            continue
        tmp = df.copy()
        tmp["Proceso"] = proceso
        keep = [c for c in ["Proceso", "Fecha", "Finca", "Proyecto", "Lote", "Cliente", "Destino", "Observaciones"] if c in tmp.columns]
        # Buscar columna principal de cantidad
        for c in ["Produccion Kg", "Kg Lavados", "Kg Empacados", "Kg Despachados", "Esquejes", "Plantas"]:
            if c in tmp.columns and c not in keep:
                keep.append(c)
                break
        rows.extend(tmp[keep].tail(10).to_dict("records"))

    if not rows:
        error = (store_data or {}).get("_supabase_error") if isinstance(store_data, dict) else None
        if error and "creado_por_app" in error:
            return html.Div(
                "Falta actualizar Supabase para mostrar tus registros. Ejecuta sql_mis_registros_operador_only.sql.",
                className="muted",
            )
        return html.Div("Todavía no hay registros para mostrar.", className="muted")

    df_all = pd.DataFrame(rows)
    if "Fecha" in df_all.columns:
        df_all["Fecha"] = pd.to_datetime(df_all["Fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
        df_all = df_all.sort_values("Fecha", ascending=False, na_position="last")

    return html.Div([
        html.H2("Últimos registros"),
        dash_table.DataTable(
            data=df_all.to_dict("records"),
            columns=[{"name": c, "id": c} for c in df_all.columns],
            page_size=15,
            sort_action="native",
            filter_action="native",
            style_table={"overflowX": "auto"},
            style_cell={"fontFamily": "Manrope, sans-serif", "fontSize": "14px", "padding": "10px", "textAlign": "left"},
            style_header={"fontWeight": "700"},
        )
    ])
