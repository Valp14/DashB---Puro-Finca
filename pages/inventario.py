"""Página de inventario actual desde Supabase.

Intervención visual: esta página se rediseña como módulo ejecutivo de inventario,
sin modificar navegación, callbacks globales ni lógica de conexión.
"""

from __future__ import annotations

import math
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dash_table, dcc, html

from services.supabase_data import get_inventory_rows, get_inventory_kpis
from pages._common import filter_panel


COLOR_GREEN = "#2F6B35"
COLOR_GREEN_2 = "#6F9666"
COLOR_SAGE = "#A8B77A"
COLOR_BEIGE = "#E7C987"
COLOR_ORANGE = "#D9782D"
COLOR_SOFT = "#F6F7F2"
COLOR_BORDER = "#E5E9E2"
COLOR_TEXT = "#172417"
COLOR_MUTED = "#677568"


# ---------------------------------------------------------------------------
# Formato y utilidades de datos
# ---------------------------------------------------------------------------
def _num(value, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _fmt_kg(value):
    try:
        return f"{float(value):,.2f} kg".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00 kg"


def _fmt_pct(value):
    try:
        return f"{float(value):.0f}%"
    except Exception:
        return "0%"


def _pretty(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "Sin clasificar"
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return "Sin clasificar"
    replacements = {
        "cuarto_curacion": "Cuarto de curación",
        "bodega_grande": "Bodega grande",
        "producto_empacado": "Producto empacado",
        "no_lavado": "No lavada",
        "lavado": "Lavada",
        "primera": "Primera",
        "segunda": "Segunda",
        "tercera": "Tercera",
        "semilla": "Semilla",
        "descarte": "Descarte",
        "granel": "Granel",
    }
    normalized = text.lower().replace(" ", "_")
    return replacements.get(normalized, text.replace("_", " ").title())


def _column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lookup = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lookup:
            return lookup[c.lower()]
    return None


def _group_sum(df: pd.DataFrame, group_col: str | None, value_col: str | None) -> pd.DataFrame:
    if df.empty or not group_col or not value_col:
        return pd.DataFrame(columns=["label", "kg"])
    d = df[[group_col, value_col]].copy()
    d[value_col] = pd.to_numeric(d[value_col], errors="coerce").fillna(0)
    d[group_col] = d[group_col].apply(_pretty)
    d = (
        d.groupby(group_col, as_index=False)[value_col]
        .sum()
        .sort_values(value_col, ascending=False)
    )
    d.columns = ["label", "kg"]
    return d[d["kg"] > 0]


def _detect_merma(df: pd.DataFrame, value_col: str | None) -> float:
    if df.empty or not value_col:
        return 0.0
    cols = [c for c in [
        _column(df, ["clase", "clasificacion", "clasificación"]),
        _column(df, ["estado"]),
        _column(df, ["ubicacion", "ubicación"]),
    ] if c]
    if not cols:
        return 0.0
    mask = pd.Series(False, index=df.index)
    for c in cols:
        mask = mask | df[c].astype(str).str.lower().str.contains("descarte|merma|no_apta|no apta", na=False)
    return pd.to_numeric(df.loc[mask, value_col], errors="coerce").fillna(0).sum()


# ---------------------------------------------------------------------------
# Componentes visuales propios de inventario
# ---------------------------------------------------------------------------
def _icon(symbol: str, accent: str = "green"):
    return html.Div(symbol, className=f"inv-icon inv-icon-{accent}")


def _kpi_card(title: str, value: str, icon: str, note: str = "Inventario actual", accent: str = "green"):
    return html.Div([
        _icon(icon, accent),
        html.Div([
            html.Div(title, className="inv-kpi-title"),
            html.Div(value, className="inv-kpi-value"),
            html.Div(note, className=f"inv-kpi-note inv-note-{accent}"),
        ], className="inv-kpi-copy"),
    ], className="inv-kpi-card")


def _filter_chip(label: str, value: str, icon: str = "▾"):
    return html.Div([
        html.Div(label, className="inv-filter-label"),
        html.Div([html.Span(value), html.Span(icon, className="inv-filter-caret")], className="inv-filter-value"),
    ], className="inv-filter-chip")


def _progress_rows(data: pd.DataFrame, total: float):
    if data.empty or total <= 0:
        return html.Div("Sin datos de clasificación para mostrar.", className="inv-empty-mini")

    rows = []
    for _, row in data.head(6).iterrows():
        kg = _num(row["kg"])
        pct = (kg / total * 100) if total else 0
        rows.append(html.Div([
            html.Div(row["label"], className="inv-progress-name"),
            html.Div(html.Div(style={"width": f"{min(pct, 100):.2f}%"}), className="inv-progress-track"),
            html.Div(_fmt_kg(kg), className="inv-progress-kg"),
            html.Div(_fmt_pct(pct), className="inv-progress-pct"),
        ], className="inv-progress-row"))

    return html.Div([
        html.Div(rows, className="inv-progress-list"),
        html.Div([html.Span("0%"), html.Span("25%"), html.Span("50%"), html.Span("75%"), html.Span("100%")], className="inv-progress-scale"),
    ])


def _chart_card(title: str, subtitle: str, icon: str, total_text: str, body, extra_class: str = ""):
    return html.Div([
        html.Div([
            html.Div([_icon(icon), html.Div([html.H3(title), html.P(subtitle)])], className="inv-card-title"),
            html.Div(total_text, className="inv-total-pill") if total_text else None,
        ], className="inv-card-header"),
        html.Div(body, className="inv-card-body"),
    ], className=f"inv-chart-card {extra_class}".strip())


def _donut_figure(data: pd.DataFrame, total: float) -> go.Figure:
    labels = data["label"].tolist() if not data.empty else []
    values = data["kg"].tolist() if not data.empty else []
    colors = [COLOR_GREEN, COLOR_SAGE, COLOR_BEIGE, COLOR_ORANGE, "#B65B3A", "#CAD7C2"]
    fig = go.Figure()
    if labels and sum(values) > 0:
        fig.add_trace(go.Pie(
            labels=labels,
            values=values,
            hole=0.66,
            sort=False,
            direction="clockwise",
            marker=dict(colors=colors[:len(labels)], line=dict(color="white", width=3)),
            textinfo="none",
            hovertemplate="%{label}<br>%{value:,.2f} kg · %{percent}<extra></extra>",
        ))
        fig.add_annotation(text=f"<b>{_fmt_kg(total).replace(' kg', '')}</b><br>kg", x=0.5, y=0.52, showarrow=False, font=dict(size=16, color=COLOR_TEXT))
        fig.add_annotation(text="Total", x=0.5, y=0.39, showarrow=False, font=dict(size=11, color=COLOR_MUTED))
    fig.update_layout(
        height=270,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font=dict(family='"Plus Jakarta Sans", sans-serif', color=COLOR_TEXT, size=12),
    )
    return fig


def _bar_figure(data: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    d = data.head(7).sort_values("kg") if not data.empty else data
    if not d.empty:
        fig.add_trace(go.Bar(
            x=d["label"],
            y=d["kg"],
            marker=dict(color=COLOR_GREEN_2, line=dict(width=0)),
            width=0.52,
            hovertemplate="%{x}<br>%{y:,.2f} kg<extra></extra>",
        ))
    fig.update_layout(
        height=300,
        margin=dict(l=32, r=14, t=8, b=46),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font=dict(family='"Plus Jakarta Sans", sans-serif', color=COLOR_TEXT, size=12),
    )
    fig.update_xaxes(showgrid=False, tickangle=0, tickfont=dict(size=11, color=COLOR_MUTED), linecolor=COLOR_BORDER)
    fig.update_yaxes(title="kg", gridcolor="#EEF1EC", zeroline=False, tickfont=dict(size=11, color=COLOR_MUTED), linecolor=COLOR_BORDER)
    return fig


def _legend_rows(data: pd.DataFrame, total: float):
    colors = [COLOR_GREEN, COLOR_SAGE, COLOR_BEIGE, COLOR_ORANGE, "#B65B3A", "#CAD7C2"]
    if data.empty:
        return html.Div("Sin estados para mostrar.", className="inv-empty-mini")
    return html.Div([
        html.Div([
            html.Span(style={"background": colors[i % len(colors)]}, className="inv-legend-dot"),
            html.Span(row["label"], className="inv-legend-label"),
            html.Span(_fmt_kg(row["kg"]), className="inv-legend-kg"),
            html.Span(_fmt_pct((row["kg"] / total * 100) if total else 0), className="inv-legend-pct"),
        ], className="inv-legend-row")
        for i, row in data.head(6).reset_index(drop=True).iterrows()
    ], className="inv-legend-list")


def _build_table(df: pd.DataFrame):
    if df.empty:
        return html.Div(
            "No hay inventario disponible para mostrar. Revisa que existan ajustes o movimientos en Supabase.",
            className="inv-empty-state",
        )

    rename = {
        "ubicacion": "Ubicación",
        "clase": "Clase",
        "estado": "Estado",
        "presentacion": "Presentación",
        "unidades_disponibles": "Unidades",
        "kg_disponibles": "Kg disponibles",
    }
    show = df.rename(columns=rename).copy()
    for col in ["Ubicación", "Clase", "Estado", "Presentación"]:
        if col in show.columns:
            show[col] = show[col].apply(_pretty)
    if "Kg disponibles" in show.columns:
        show["Kg disponibles"] = pd.to_numeric(show["Kg disponibles"], errors="coerce").fillna(0).round(2)

    preferred = [c for c in ["Ubicación", "Clase", "Estado", "Presentación", "Unidades", "Kg disponibles"] if c in show.columns]
    if preferred:
        show = show[preferred]

    return dash_table.DataTable(
        data=show.to_dict("records"),
        columns=[{"name": c, "id": c} for c in show.columns],
        page_size=12,
        sort_action="native",
        filter_action="native",
        style_table={"overflowX": "auto", "borderRadius": "18px", "overflow": "hidden"},
        style_cell={
            "fontFamily": '"Plus Jakarta Sans", -apple-system, Segoe UI, sans-serif',
            "fontSize": "13px",
            "padding": "12px 14px",
            "textAlign": "left",
            "border": "none",
            "borderBottom": "1px solid #EEF1EC",
            "color": COLOR_TEXT,
            "backgroundColor": "white",
        },
        style_header={
            "fontWeight": "800",
            "backgroundColor": COLOR_SOFT,
            "color": COLOR_MUTED,
            "textTransform": "uppercase",
            "fontSize": "11px",
            "letterSpacing": "0.06em",
            "border": "none",
            "borderBottom": f"1px solid {COLOR_BORDER}",
        },
        style_filter={"backgroundColor": "#FAFBF8", "border": "none"},
        style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#FCFDFB"}],
    )


def _filter_df(df: pd.DataFrame, filtros: dict | None) -> pd.DataFrame:
    if df.empty or not filtros:
        return df
    out = df.copy()

    def col(candidates):
        return _column(out, candidates)

    # Rango de fechas, si el inventario tiene columna temporal.
    date_col = col(["Fecha", "fecha", "Timestamp", "created_at", "updated_at", "fecha_movimiento"])
    if date_col and (filtros.get("fecha_inicio") or filtros.get("fecha_fin")):
        dates = pd.to_datetime(out[date_col], errors="coerce")
        if filtros.get("fecha_inicio"):
            out = out[dates >= pd.to_datetime(filtros.get("fecha_inicio"), errors="coerce")]
            dates = pd.to_datetime(out[date_col], errors="coerce")
        if filtros.get("fecha_fin"):
            out = out[dates <= pd.to_datetime(filtros.get("fecha_fin"), errors="coerce")]

    mapping = [
        ("fincas", ["Finca", "finca"]),
        ("lotes", ["Lote", "lote"]),
        ("proyectos", ["Proyecto", "proyecto"]),
        ("clientes", ["Cliente", "cliente"]),
        ("destinos", ["Destino", "destino"]),
    ]
    for key, candidates in mapping:
        values = filtros.get(key) or []
        c = col(candidates)
        if c and values:
            wanted = {str(v) for v in values}
            out = out[out[c].astype(str).isin(wanted)]
    return out


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
def _inventory_content(filtros=None):
    rows = get_inventory_rows()
    kpis = get_inventory_kpis()

    df = pd.DataFrame(rows)
    df = _filter_df(df, filtros)
    value_col = _column(df, ["kg_disponibles", "kg disponible", "kg", "kilogramos"])
    class_col = _column(df, ["clase", "clasificacion", "clasificación"])
    state_col = _column(df, ["estado"])
    location_col = _column(df, ["ubicacion", "ubicación"])
    presentation_col = _column(df, ["presentacion", "presentación"])

    total = _num(kpis.get("kg_total_disponible")) or (pd.to_numeric(df[value_col], errors="coerce").fillna(0).sum() if value_col else 0)
    curacion = _num(kpis.get("kg_cuarto_curacion"))
    bodega = _num(kpis.get("kg_bodega_grande"))
    empacado = _num(kpis.get("kg_producto_empacado"))
    merma = _num(kpis.get("kg_merma")) or _num(kpis.get("kg_descarte")) or _detect_merma(df, value_col)

    by_class = _group_sum(df, class_col, value_col)
    by_state = _group_sum(df, state_col, value_col)
    by_location = _group_sum(df, location_col, value_col)
    by_presentation = _group_sum(df, presentation_col, value_col)
    bars_source = by_location if not by_location.empty else by_presentation
    bars_title = "Inventario por ubicación" if not by_location.empty else "Inventario por presentación"
    bars_subtitle = "Distribución de kg disponibles" if not by_location.empty else "Formato disponible en inventario"

    table = _build_table(df)

    return html.Div([
        html.Div([
            html.Div([
                html.Div("Inventario", className="inv-eyebrow"),
                html.H1("Inventario actual"),
                html.P(
                    "Saldos calculados desde movimientos y ajustes en Supabase, con una lectura rápida por ubicación, clasificación y estado del producto.",
                    className="inv-lead",
                ),
            ], className="inv-hero-copy"),
            html.Div([
                html.Div("Actualizado desde Supabase", className="inv-status-title"),
                html.Div("Vista operativa", className="inv-status-sub"),
            ], className="inv-status-pill"),
        ], className="inv-page-header"),

        html.Div([
            _kpi_card("Inventario disponible", _fmt_kg(total), "▦", "Saldo general disponible", "green"),
            _kpi_card("Bodega grande", _fmt_kg(bodega), "⌂", "Segunda, tercera y semilla", "green"),
            _kpi_card("Cuarto de curación", _fmt_kg(curacion), "◌", "Producto en proceso", "sage"),
            _kpi_card("Producto empacado", _fmt_kg(empacado), "▣", "Disponible para despacho", "green"),
            _kpi_card("Merma / descarte", _fmt_kg(merma), "⌫", "Registro no apto", "orange"),
        ], className="inv-kpi-grid"),


        html.Div([
            _chart_card(
                "Inventario por clasificación",
                "Disponibilidad por clasificación",
                "⌑",
                f"Total {_fmt_kg(total)}",
                _progress_rows(by_class, total),
                "inv-classification-card",
            ),
            _chart_card(
                "Estado del producto",
                "Distribución por estado",
                "◌",
                f"{len(by_state)} estados" if not by_state.empty else "Sin estados",
                html.Div([
                    dcc.Graph(figure=_donut_figure(by_state, total), config={"displayModeBar": False}, className="inv-donut"),
                    _legend_rows(by_state, total),
                ], className="inv-donut-layout"),
                "inv-state-card",
            ),
            _chart_card(
                bars_title,
                bars_subtitle,
                "▥",
                f"Total {_fmt_kg(total)}",
                dcc.Graph(figure=_bar_figure(bars_source), config={"displayModeBar": False}, className="inv-bars"),
                "inv-bars-card",
            ),
        ], className="inv-visual-grid"),

        html.Div([
            html.Div([
                html.Div([html.H2("Detalle de inventario"), html.P("Consulta ordenable y filtrable de los saldos actuales.")], className="inv-section-title"),
                html.Div(f"{len(df):,} registros".replace(",", "."), className="inv-total-pill") if not df.empty else None,
            ], className="inv-table-header"),
            table,
        ], className="inv-table-card"),
    ], className="inventory-content")


def layout():
    return html.Div([
        filter_panel("Filtros de inventario"),
        html.Div(id="inventario-contenido"),
    ], className="inventory-page ops-page ops-process-page process-inventario")


@callback(
    Output("inventario-contenido", "children"),
    Input("store-filtros", "data"),
)
def render_inventory(filtros):
    return _inventory_content(filtros or {})
