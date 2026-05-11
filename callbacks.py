"""
callbacks.py
------------
Callbacks globales: sincronización de datos, gestión de filtros y enrutamiento.

[MIGRACION Streamlit -> Dash]
Todo lo que en Streamlit era reactivo por inferencia (rerun completo del
script) aqui se convierte en callbacks explicitos con Input/Output/State.

Los callbacks por pagina viven en pages/<pagina>.py.
"""

from __future__ import annotations

import base64
import io
from datetime import date

import pandas as pd
from dash import Input, Output, State, callback, ctx, dcc, no_update, html

from config.settings import PROCESOS
from utils.data_loader import load_excel
from utils.filters import opciones_unicas, rango_fechas
from components.sidebar import store_to_dataframes
from services.access_control import allowed_pages


# ---------------------------------------------------------------------------
# 1. Upload del Excel de respaldo (flujo oculto; Supabase es la fuente principal)
# ---------------------------------------------------------------------------
@callback(
    Output("store-data",    "data"),
    Output("store-archivo", "data"),
    Output("upload-status", "children"),
    Input("upload-excel", "contents"),
    State("upload-excel", "filename"),
    prevent_initial_call=True,
)
def on_upload(contents, filename):
    """Parse del archivo de respaldo y almacenamiento en dcc.Store."""
    if not contents:
        return no_update, no_update, no_update

    try:
        _, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string)
        datos = load_excel(io.BytesIO(decoded))
    except Exception as e:
        return {}, False, html.Span(f"Error: {e}",
                                    style={"color": "#A33A3A"})

    # Serializar a records para dcc.Store (JSON-safe)
    serializable = {}
    for p in PROCESOS:
        df = datos.get(p, pd.DataFrame())
        if df.empty:
            serializable[p] = []
            continue
        tmp = df.copy()
        for c in tmp.columns:
            if pd.api.types.is_datetime64_any_dtype(tmp[c]):
                tmp[c] = tmp[c].dt.strftime("%Y-%m-%dT%H:%M:%S")
        serializable[p] = tmp.to_dict("records")

    cargado = any(serializable[p] for p in PROCESOS)
    estado = (html.Span(["Cargado: ", html.B(filename)],
                        style={"color": "#2E7D4F"})
              if cargado
              else html.Span("Archivo vacio o formato no reconocido",
                             style={"color": "#B5791F"}))

    return serializable, cargado, estado


# ---------------------------------------------------------------------------
# 2. Poblar opciones de los dropdowns cuando llega data
#    (reemplaza opciones_unicas() en el sidebar de Streamlit)
# ---------------------------------------------------------------------------
@callback(
    Output("filtro-finca",    "options"),
    Output("filtro-lote",     "options"),
    Output("filtro-proyecto", "options"),
    Output("filtro-cliente",  "options"),
    Output("filtro-destino",  "options"),
    Output("filtro-fechas",   "min_date_allowed"),
    Output("filtro-fechas",   "max_date_allowed"),
    Input("store-data", "data"),
    Input("url", "pathname"),
)
def poblar_opciones(store_data, pathname):
    if not store_data:
        return [], [], [], [], [], None, None

    dfs = list(store_to_dataframes(store_data).values())

    def _opts(col):
        return [{"label": str(v), "value": str(v)}
                for v in opciones_unicas(dfs, col)]

    fmin, fmax = rango_fechas(dfs)
    return (_opts("Finca"), _opts("Lote"), _opts("Proyecto"),
            _opts("Cliente"), _opts("Destino"),
            fmin, fmax)


# ---------------------------------------------------------------------------
# 3. Limpiar filtros (reemplaza el callback on_click _reset_filtros)
# ---------------------------------------------------------------------------
@callback(
    Output("filtro-finca",    "value", allow_duplicate=True),
    Output("filtro-lote",     "value", allow_duplicate=True),
    Output("filtro-proyecto", "value", allow_duplicate=True),
    Output("filtro-cliente",  "value", allow_duplicate=True),
    Output("filtro-destino",  "value", allow_duplicate=True),
    Output("filtro-fechas",   "start_date", allow_duplicate=True),
    Output("filtro-fechas",   "end_date",   allow_duplicate=True),
    Input("btn-reset-filtros", "n_clicks"),
    prevent_initial_call=True,
)
def reset_filtros(n):
    if not n:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update
    return [], [], [], [], [], None, None


# ---------------------------------------------------------------------------
# 4. Sincronizar el store-filtros con los valores de los dropdowns
#    (reemplaza st.session_state["filtros"])
# ---------------------------------------------------------------------------
@callback(
    Output("store-filtros", "data"),
    Input("filtro-fechas",   "start_date"),
    Input("filtro-fechas",   "end_date"),
    Input("filtro-finca",    "value"),
    Input("filtro-lote",     "value"),
    Input("filtro-proyecto", "value"),
    Input("filtro-cliente",  "value"),
    Input("filtro-destino",  "value"),
)
def sync_filtros(fi, ff, fincas, lotes, proyectos, clientes, destinos):
    return {
        "fecha_inicio": fi,
        "fecha_fin":    ff,
        "fincas":       fincas or [],
        "lotes":        lotes or [],
        "proyectos":    proyectos or [],
        "clientes":     clientes or [],
        "destinos":     destinos or [],
    }


# ---------------------------------------------------------------------------
# 5. Router: traduce URL -> layout de pagina
# ---------------------------------------------------------------------------
@callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def render_page(pathname):
    # Import local para evitar ciclos
    from pages import (
        inicio, productividad, corte, siembra, cosecha, lavado, empaque,
        cargue, calidad_perdidas, plan_vs_real, reportes, configuracion,
        calidad_datos, inventario, formularios, mis_registros,
    )
    from auth import current_role

    ruta = (pathname or "/portal/").rstrip("/") or "/portal"
    mapa = {
        "/portal":                  inicio.layout,
        "/portal/inventario":       inventario.layout,
        "/portal/formularios":      formularios.layout,
        "/portal/mis-registros":    mis_registros.layout,
        "/portal/productividad":    productividad.layout,
        "/portal/corte":            corte.layout,
        "/portal/siembra":          siembra.layout,
        "/portal/cosecha":          cosecha.layout,
        "/portal/lavado":           lavado.layout,
        "/portal/empaque":          empaque.layout,
        "/portal/cargue":           cargue.layout,
        "/portal/calidad-perdidas": calidad_perdidas.layout,
        "/portal/plan-vs-real":     plan_vs_real.layout,
        "/portal/reportes":         reportes.layout,
        "/portal/configuracion":    configuracion.layout,
        "/portal/calidad-datos":    calidad_datos.layout,
    }
    role = current_role()
    permitido = allowed_pages(role)
    if ruta not in permitido:
        return html.Div([
            html.H2("Acceso restringido"),
            html.Div("Tu perfil no tiene permiso para consultar esta sección.", className="muted"),
        ], className="panel-card")

    fn = mapa.get(ruta)
    if fn is None:
        return html.Div([
            html.H2("Página no encontrada"),
            html.Div(f"La ruta {pathname!r} no existe.", className="muted"),
        ])
    return fn()


# ---------------------------------------------------------------------------
# 6. Toggle de sidebar móvil
# ---------------------------------------------------------------------------
@callback(
    Output("sidebar-wrapper",   "className"),
    Output("sidebar-backdrop",  "className"),
    Output("store-sidebar-open", "data"),
    Input("btn-toggle-sidebar", "n_clicks"),
    Input("sidebar-backdrop",   "n_clicks"),
    Input("url",                "pathname"),
    State("store-sidebar-open", "data"),
    prevent_initial_call=True,
)
def toggle_sidebar(n_burger, n_backdrop, pathname, is_open):
    triggered = ctx.triggered_id
    if triggered == "url":
        # Al navegar se conserva visible en escritorio, pero cerrada como drawer en móvil.
        new_state = False
        sb_class = "sidebar-wrapper"
    elif triggered == "btn-toggle-sidebar":
        new_state = not is_open
        sb_class = "sidebar-wrapper sidebar-open" if new_state else "sidebar-wrapper sidebar-collapsed"
    elif triggered == "sidebar-backdrop":
        new_state = False
        sb_class = "sidebar-wrapper"
    else:
        new_state = bool(is_open)
        sb_class = "sidebar-wrapper sidebar-open" if new_state else "sidebar-wrapper"

    bd_class = "sidebar-backdrop sidebar-backdrop-visible" if new_state else "sidebar-backdrop"
    return sb_class, bd_class, new_state


# ---------------------------------------------------------------------------
# 7. Generación de PDF ejecutivo
# ---------------------------------------------------------------------------
@callback(
    Output("download-pdf", "data"),
    Input("btn-export-pdf", "n_clicks"),
    State("store-data",    "data"),
    State("store-archivo", "data"),
    State("store-filtros", "data"),
    prevent_initial_call=True,
)
def export_pdf(n, store_data, archivo, filtros):
    if not n or not archivo:
        return no_update

    from utils.metrics import (kpis_corte, kpis_siembra, kpis_cosecha,
                                kpis_lavado, kpis_empaque, kpis_cargue)
    from utils.pdf import build_executive_report
    from auth import current_user
    from pathlib import Path
    from datetime import datetime
    import dash

    # Obtener data filtrada por proceso
    from components.sidebar import get_data_filtrada
    df_corte   = get_data_filtrada(store_data, filtros, "Corte Esquejes")
    df_siembra = get_data_filtrada(store_data, filtros, "Siembra")
    df_cosecha = get_data_filtrada(store_data, filtros, "Cosecha")
    df_lavado  = get_data_filtrada(store_data, filtros, "Lavado Clasificacion")
    df_empaque = get_data_filtrada(store_data, filtros, "Empaque")
    df_cargue  = get_data_filtrada(store_data, filtros, "Cargue Vehiculo")

    cosecha_serie = None
    if not df_cosecha.empty and "Fecha" in df_cosecha.columns and "Produccion Kg" in df_cosecha.columns:
        tmp = df_cosecha.dropna(subset=["Fecha"]).copy()
        tmp["_FechaDia"] = pd.to_datetime(tmp["Fecha"], errors="coerce").dt.date
        tmp = tmp.dropna(subset=["_FechaDia"])
        cosecha_serie = (tmp.groupby("_FechaDia", as_index=False)["Produccion Kg"]
                           .sum())
        cosecha_serie.columns = ["Fecha", "Produccion Kg"]

    base_dir = Path(__file__).resolve().parent
    logo_path = base_dir / "assets" / "logo.png"

    pdf_bytes = build_executive_report(
        kpis_corte=kpis_corte(df_corte),
        kpis_siembra=kpis_siembra(df_siembra),
        kpis_cosecha=kpis_cosecha(df_cosecha),
        kpis_lavado=kpis_lavado(df_lavado),
        kpis_empaque=kpis_empaque(df_empaque),
        kpis_cargue=kpis_cargue(df_cargue),
        cosecha_serie=cosecha_serie,
        filtros_aplicados=filtros,
        user_email=current_user(),
        logo_path=str(logo_path) if logo_path.exists() else None,
    )

    fname = f"puro_finca_reporte_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return dcc.send_bytes(pdf_bytes, filename=fname)
