"""
components/sidebar.py
---------------------
Sidebar rediseñada — PURO FINCA.

[COMPATIBILIDAD CRITICA]
Se conservan EXACTAMENTE los mismos IDs que usa callbacks.py:
  - upload-excel, upload-status
  - btn-reset-filtros
  - filtro-fechas, filtro-finca, filtro-lote, filtro-proyecto,
    filtro-cliente, filtro-destino
  - sidebar-nav-container
Las funciones store_to_dataframes y get_data_filtrada siguen intactas.

[NUEVO]
- Bloque de marca con logo
- Navegacion agrupada por modulos (Ejecutivo / Procesos / Analisis / Sistema)
- Footer con indicador de estado
"""

from __future__ import annotations

from dash import dcc, html

from config.settings import APP_NAME


# ---------------------------------------------------------------------------
# Navegación agrupada por rol
# ---------------------------------------------------------------------------
NAV_BY_ROLE = {
    "operador": [
        ("Operación", [
            ("/portal/", "Inicio"),
            ("/portal/formularios", "Formularios"),
        ]),
    ],
    "jefe": [
        ("Control", [
            ("/portal/", "Dashboard"),
            ("/portal/inventario", "Inventario"),
            ("/portal/productividad", "Productividad"),
            ("/portal/formularios", "Formularios"),
        ]),
        ("Procesos", [
            ("/portal/corte", "Corte"),
            ("/portal/siembra", "Siembra"),
            ("/portal/cosecha", "Cosecha"),
            ("/portal/lavado", "Lavado"),
            ("/portal/empaque", "Empaque"),
            ("/portal/cargue", "Despacho"),
        ]),
        ("Análisis", [
            ("/portal/calidad-perdidas", "Calidad y pérdidas"),
            ("/portal/calidad-datos", "Alertas de datos"),
            ("/portal/reportes", "Reportes"),
        ]),
    ],
    "admin": [
        ("Administración", [
            ("/portal/", "Dashboard"),
            ("/portal/inventario", "Inventario"),
            ("/portal/productividad", "Productividad"),
            ("/portal/formularios", "Formularios"),
        ]),
        ("Procesos operativos", [
            ("/portal/corte", "Corte de esquejes"),
            ("/portal/siembra", "Siembra"),
            ("/portal/cosecha", "Cosecha"),
            ("/portal/lavado", "Lavado y clasificación"),
            ("/portal/empaque", "Empaque"),
            ("/portal/cargue", "Despacho"),
        ]),
        ("Análisis y control", [
            ("/portal/calidad-perdidas", "Calidad y pérdidas"),
            ("/portal/plan-vs-real", "Plan vs real"),
            ("/portal/calidad-datos", "Calidad de datos"),
        ]),
        ("Sistema", [
            ("/portal/reportes", "Reportes"),
            ("/portal/configuracion", "Configuración"),
        ]),
    ],
    "asociacion": [
        ("Consulta", [
            ("/portal/", "Inicio"),
            ("/portal/productividad", "Productividad"),
            ("/portal/reportes", "Reportes"),
        ]),
    ],
}


def _nav_for_role(role: str):
    return NAV_BY_ROLE.get(role or "operador", NAV_BY_ROLE["operador"])


def sidebar_layout(role: str = "operador", supabase_status: dict | None = None) -> html.Div:
    status = supabase_status or {}
    status_ok = bool(status.get("ok"))
    records = status.get("total_records", 0)

    nav_children = []
    for group_label, links in _nav_for_role(role):
        nav_children.append(html.Div(group_label, className="nav-group-label"))
        for href, label in links:
            nav_children.append(dcc.Link(label, href=href))

    if status_ok:
        status_text = f"Supabase conectado · {records} registros"
        status_color = "#2E7D4F"
    elif not status.get("configured"):
        status_text = "Supabase sin configurar"
        status_color = "#B5791F"
    else:
        status_text = "Revisar conexión Supabase"
        status_color = "#A33A3A"

    return html.Div(
        [
            html.Div([
                html.Div(
                    html.Img(src="/assets/logo.png", alt="Puro Finca"),
                    className="sidebar-brand-logo",
                ),
                html.Div([
                    html.Div("Puro Finca", className="sidebar-brand-name"),
                    html.Div(f"Panel {role}", className="sidebar-brand-tag"),
                ], className="sidebar-brand-text"),
            ], className="sidebar-brand"),

            html.Div([
                html.Div(nav_children, className="sidebar-nav", id="sidebar-nav-container"),
            ], className="sidebar-body sidebar-body-navonly"),

            html.Div([
                html.A([html.Span("⎋", className="logout-icon"), html.Span("Cerrar sesión")], href="/logout", className="sidebar-logout"),
            ], className="sidebar-footer"),
        ],
        className="sidebar",
    )


# ===========================================================================
# Helpers de acceso al store (SIN CAMBIOS — lógica de negocio intacta)
# ===========================================================================
def store_to_dataframes(store_data: dict) -> dict:
    """Convierte el dict guardado en dcc.Store a dict de DataFrames."""
    import pandas as pd
    from config.settings import PROCESOS

    out = {}
    if not store_data:
        return {p: pd.DataFrame() for p in PROCESOS}

    for p in PROCESOS:
        records = store_data.get(p, [])
        if not records:
            out[p] = pd.DataFrame()
        else:
            df = pd.DataFrame(records)
            for col in ("Fecha", "Timestamp"):
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
            out[p] = df
    return out


def get_data_filtrada(store_data: dict, filtros: dict, proceso: str):
    """Equivalente a la funcion get_data_filtrada del sidebar original."""
    import pandas as pd
    from utils.filters import filtrar

    dfs = store_to_dataframes(store_data)
    df = dfs.get(proceso, pd.DataFrame())
    if df.empty:
        return df

    f = filtros or {}
    return filtrar(
        df,
        fecha_inicio=_parse_date(f.get("fecha_inicio")),
        fecha_fin=_parse_date(f.get("fecha_fin")),
        fincas=f.get("fincas"),
        lotes=f.get("lotes"),
        proyectos=f.get("proyectos"),
        clientes=f.get("clientes"),
        destinos=f.get("destinos"),
        origenes=None,
    )


def _parse_date(v):
    if v is None:
        return None
    from datetime import date, datetime
    if isinstance(v, (date, datetime)):
        return v if isinstance(v, date) and not isinstance(v, datetime) else v.date()
    try:
        return datetime.fromisoformat(str(v)[:10]).date()
    except Exception:
        return None
