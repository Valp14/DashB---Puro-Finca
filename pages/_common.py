"""
pages/_common.py
----------------
Helpers compartidos por las paginas: lectura de stores + empty state si no
hay datos disponibles. Evita repetir boilerplate en cada pagina.

[MIGRACION Streamlit -> Dash]
En Streamlit se usaba `st.session_state.get("archivo_cargado")` + `st.stop()`.
Aqui encapsulamos esa logica para que cada callback de pagina decida si
renderizar el dashboard o un mensaje vacio.
"""

from __future__ import annotations

from dash import dcc, html
from components.sidebar import store_to_dataframes, get_data_filtrada
from styles.theme import empty_state, page_header

__all__ = ["store_to_dataframes", "get_data_filtrada",
           "empty_state", "page_header", "filter_panel", "require_archivo"]


def require_archivo(archivo: bool, mensaje: str = ""):
    """
    Devuelve (True, None) si hay datos disponibles, o (False, layout_vacio).
    """
    if archivo:
        return True, None
    msg = mensaje or "No se encontraron datos disponibles en Supabase."
    return False, empty_state(msg)


def filter_panel(title: str = "Filtros de la pestaña", compact: bool = False):
    """Panel de filtros local para cada vista.

    Mantiene los mismos IDs globales para no tocar la lógica existente: al cambiar
    los controles se actualiza store-filtros y cada página recalcula sus datos.
    """
    def _dropdown(id_, placeholder):
        return dcc.Dropdown(
            id=id_,
            multi=True,
            placeholder=placeholder,
            options=[],
            value=[],
            persistence=True,
            persistence_type="session",
        )

    return html.Details([
        html.Summary([
            html.Div([
                html.Div(title, className="page-filter-title"),
                html.Div("Ajusta el periodo y los segmentos visibles en esta sección.", className="page-filter-subtitle"),
            ], className="page-filter-copy"),
            html.Div([
                html.Span("Mostrar filtros", className="filter-toggle-label filter-toggle-show"),
                html.Span("Ocultar filtros", className="filter-toggle-label filter-toggle-hide"),
            ], className="filter-toggle-text"),
        ], className="page-filter-summary"),
        html.Div([
            html.Div([
                html.Div([
                    html.Div("Fecha", className="control-label"),
                    dcc.DatePickerRange(
                        id="filtro-fechas",
                        display_format="YYYY-MM-DD",
                        start_date_placeholder_text="Desde",
                        end_date_placeholder_text="Hasta",
                        className="page-date-range",
                        persistence=True,
                        persistence_type="session",
                    ),
                ], className="page-filter-field page-filter-field-date"),
                html.Div([html.Div("Finca", className="control-label"), _dropdown("filtro-finca", "Todas")], className="page-filter-field"),
                html.Div([html.Div("Lote", className="control-label"), _dropdown("filtro-lote", "Todos")], className="page-filter-field"),
                html.Div([html.Div("Proyecto", className="control-label"), _dropdown("filtro-proyecto", "Todos")], className="page-filter-field"),
                html.Div([html.Div("Cliente", className="control-label"), _dropdown("filtro-cliente", "Todos")], className="page-filter-field"),
                html.Div([html.Div("Destino", className="control-label"), _dropdown("filtro-destino", "Todos")], className="page-filter-field"),
                html.Button([html.Span("⌁"), " Limpiar filtros"], id="btn-reset-filtros", className="btn-filter-reset", n_clicks=0),
            ], className="page-filter-grid"),
        ], className="page-filter-body"),
    ], className="page-filter-panel page-filter-panel-compact" if compact else "page-filter-panel")
