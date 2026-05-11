"""
layout_portal.py
----------------
Layout raíz del portal interno (área autenticada).

Cambios respecto al original:
- Topbar superior con menú hamburguesa para móvil
- Indicador de usuario logueado + botón "Cerrar sesión"
- Sidebar fija en escritorio, drawer deslizable en móvil
"""

from __future__ import annotations

from dash import dcc, html

from auth import current_user, current_role
from components.sidebar import sidebar_layout
from services.supabase_data import load_operational_store, get_connection_status
from config.company import COMPANY
from services.access_control import can_read_operational_data, empty_operational_store


def serve_layout() -> html.Div:
    user = current_user() or "Usuario"
    role = current_role()
    initial_data = (
        load_operational_store()
        if can_read_operational_data(role)
        else empty_operational_store()
    )
    supabase_status = get_connection_status(initial_data)

    return html.Div(
        [
            dcc.Location(id="url", refresh=False),

            # Stores globales
            dcc.Store(id="store-data",    storage_type="memory", data=initial_data),
            dcc.Store(id="store-archivo", storage_type="memory", data=supabase_status.get("ok", False)),
            dcc.Store(id="store-user-role", storage_type="session", data=role),
            dcc.Store(id="store-supabase-status", storage_type="memory", data=supabase_status),
            dcc.Store(id="store-filtros", storage_type="session", data={}),
            dcc.Store(id="store-sidebar-open", data=False),

            # Descargas
            dcc.Download(id="download-csv"),
            dcc.Download(id="download-xlsx"),
            dcc.Download(id="download-xlsx-consolidado"),
            dcc.Download(id="download-pdf"),

            # Componentes ocultos de compatibilidad: la carga manual ya no vive en el menú lateral.
            html.Div([
                html.Div(id="upload-status"),
                dcc.Upload(id="upload-excel", children=html.Div("Importar Excel"), multiple=False, accept=".xlsx,.xlsm"),
            ], className="compat-hidden"),

            # Botón flotante para abrir/cerrar el panel lateral.
            html.Button(
                html.Span("☰", className="topbar-burger-icon"),
                id="btn-toggle-sidebar",
                className="sidebar-floating-toggle",
                n_clicks=0,
                title="Abrir / cerrar menú",
            ),

            # Layout principal
            html.Div(
                [
                    html.Div(
                        sidebar_layout(role=role, supabase_status=supabase_status),
                        id="sidebar-wrapper",
                        className="sidebar-wrapper",
                    ),
                    # Backdrop para móvil
                    html.Div(id="sidebar-backdrop",
                             className="sidebar-backdrop"),
                    html.Div(
                        id="page-content",
                        className="main-content",
                    ),
                ],
                className="app-container",
            ),
        ]
    )
