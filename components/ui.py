"""
components/ui.py
----------------
Componentes visuales reutilizables.

[MIGRACION Streamlit -> Dash]
Cada funcion ahora devuelve un objeto Dash (html.Div, dash_table.DataTable,
etc.) en lugar de renderizarse inline con st.markdown(..., unsafe_allow_html).
Las funciones de formato (fmt_num, fmt_pct) NO cambian.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
from dash import html, dash_table

from config.settings import COLOR
from styles.theme import NIVEL_COLOR, NIVEL_LABEL


# ---------------------------------------------------------------------------
# Formato de numeros (IDENTICO al original, no depende de Streamlit)
# ---------------------------------------------------------------------------
def fmt_num(value, decimals: int = 0, suffix: str = "") -> str:
    if value is None:
        return "-"
    try:
        if pd.isna(value):
            return "-"
    except Exception:
        pass
    try:
        if decimals == 0:
            return f"{int(round(float(value))):,}{suffix}".replace(",", ".")
        formatted = f"{float(value):,.{decimals}f}"
        enteros, _, decs = formatted.partition(".")
        enteros = enteros.replace(",", ".")
        return f"{enteros},{decs}{suffix}" if decs else f"{enteros}{suffix}"
    except Exception:
        return str(value)


def fmt_pct(value, decimals: int = 1) -> str:
    if value is None:
        return "-"
    try:
        if pd.isna(value):
            return "-"
    except Exception:
        pass
    try:
        return f"{float(value) * 100:.{decimals}f}%".replace(".", ",")
    except Exception:
        return "-"


# ---------------------------------------------------------------------------
# Tarjetas KPI
# ---------------------------------------------------------------------------
def kpi_card(label: str, value: str, sub: Optional[str] = None,
             nivel: str = "neutral") -> html.Div:
    """
    [Streamlit kpi_card -> html.Div]
    Devuelve un html.Div con la misma estructura/clases CSS del original.
    """
    return html.Div(
        [
            html.Div(label, className="kpi-label"),
            html.Div(value, className="kpi-value"),
            html.Div(sub if sub else "\u00a0", className="kpi-sub"),
        ],
        className=f"kpi-card kpi-accent-{nivel}",
    )


def kpi_row(cards: list) -> html.Div:
    """Fila de KPIs (4 columnas por defecto). Reemplaza st.columns(4)."""
    cls = "kpi-row"
    if len(cards) == 3:
        cls = "kpi-row-3"
    elif len(cards) == 6:
        cls = "kpi-row-6"
    return html.Div(cards, className=cls)


def pill(nivel: str, texto: Optional[str] = None) -> html.Span:
    """[Streamlit pill HTML string -> html.Span]"""
    label = texto if texto is not None else NIVEL_LABEL.get(nivel, "-")
    return html.Span(label, className=f"pill pill-{nivel}")


def compliance_bar(pct: Optional[float], nivel: str = "neutral") -> html.Div:
    """[Streamlit compliance_bar HTML -> html.Div]"""
    if pct is None or (isinstance(pct, float) and pd.isna(pct)):
        width = 0
        color = COLOR["border"]
    else:
        try:
            width = max(0, min(float(pct) * 100, 100))
        except Exception:
            width = 0
        color = NIVEL_COLOR.get(nivel, COLOR["primary"])
    return html.Div(
        html.Div(className="bar-fill",
                 style={"width": f"{width}%", "background": color}),
        className="bar-track",
    )


def plan_vs_real_row(label: str, plan, real, unidad: str = "",
                     decimals: int = 0, nivel: str = "neutral") -> html.Div:
    """
    Fila plan vs real. En Streamlit usaba 5 columnas con st.columns([3,2,2,2,3]);
    aqui lo reproducimos con CSS grid.
    """
    cumpl = None
    try:
        if plan and real is not None and not pd.isna(real):
            cumpl = float(real) / float(plan) if float(plan) != 0 else None
    except Exception:
        cumpl = None

    return html.Div(
        [
            html.Div(html.B(label)),
            html.Div([
                html.Div("Plan", className="muted"),
                html.Div(f"{fmt_num(plan, decimals)} {unidad}".strip()),
            ]),
            html.Div([
                html.Div("Real", className="muted"),
                html.Div(f"{fmt_num(real, decimals)} {unidad}".strip()),
            ]),
            html.Div([
                html.Div("Cumplimiento", className="muted"),
                html.Div(fmt_pct(cumpl)),
            ]),
            html.Div([
                compliance_bar(cumpl, nivel),
                html.Div(pill(nivel), style={"marginTop": "4px"}),
            ]),
        ],
        style={
            "display": "grid",
            "gridTemplateColumns": "3fr 2fr 2fr 2fr 3fr",
            "gap": "12px",
            "alignItems": "center",
            "padding": "8px 0",
        },
    )


def detail_table(df: pd.DataFrame, columnas: Optional[list] = None,
                 height: Optional[int] = None,
                 id: Optional[str] = None):
    """
    [Streamlit st.dataframe -> dash_table.DataTable]
    """
    if df is None or df.empty:
        return html.Div("Sin registros para mostrar con los filtros actuales",
                        className="empty-state")

    show = df.copy()
    if columnas:
        cols_presentes = [c for c in columnas if c in show.columns]
        show = show[cols_presentes]

    for c in show.columns:
        if pd.api.types.is_datetime64_any_dtype(show[c]):
            show[c] = show[c].dt.strftime("%Y-%m-%d")

    return dash_table.DataTable(
        id=id or "detail-table",
        data=show.to_dict("records"),
        columns=[{"name": c, "id": c} for c in show.columns],
        style_table={
            "overflowX": "auto",
            "height": f"{height}px" if height else "auto",
            "border": f"1px solid {COLOR['border']}",
            "borderRadius": "10px",
            "overflow": "hidden",
        },
        style_cell={
            "fontFamily": '"Plus Jakarta Sans", -apple-system, Segoe UI, sans-serif',
            "fontSize": "13px",
            "padding": "10px 12px",
            "textAlign": "left",
            "border": "none",
            "borderBottom": f"1px solid {COLOR['border_soft']}",
            "color": COLOR["text"],
            "whiteSpace": "normal",
            "height": "auto",
            "fontVariantNumeric": "tabular-nums",
        },
        style_header={
            "backgroundColor": COLOR["panel"],
            "color": COLOR["text_soft"],
            "fontWeight": "700",
            "textTransform": "uppercase",
            "fontSize": "11px",
            "letterSpacing": "0.06em",
            "borderBottom": f"1px solid {COLOR['border']}",
            "padding": "12px",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"},
             "backgroundColor": COLOR["panel_soft"]},
            {"if": {"state": "selected"},
             "backgroundColor": COLOR["primary_soft"],
             "border": f"1px solid {COLOR['primary']}"},
        ],
        page_size=25,
        sort_action="native",
        filter_action="none",
    )


# ---------------------------------------------------------------------------
# Bloque de Dotacion
# ---------------------------------------------------------------------------
def dotacion_block(dot: dict, interpretacion: str) -> html.Div:
    """4 KPIs de dotacion + panel de interpretacion."""
    c1 = kpi_card(
        "Dotación estándar",
        f"{dot['estandar']} personas" if dot.get("estandar") is not None else "-",
        sub="Según manual operativo",
        nivel="neutral",
    )
    valor_prom = fmt_num(dot["promedio_real"], 1) if dot.get("promedio_real") is not None else "-"
    c2 = kpi_card(
        "Promedio asignado",
        f"{valor_prom} personas" if valor_prom != "-" else "-",
        sub="Por jornada, sin ceros",
        nivel=dot.get("nivel", "na"),
    )

    dp = dot.get("desviacion_pct")
    if dp is not None:
        try:
            signo = "+" if float(dp) > 0 else ""
            valor_desv = f"{signo}{fmt_pct(dp)}"
        except (TypeError, ValueError):
            valor_desv = "-"
    else:
        valor_desv = "-"
    c3 = kpi_card(
        "Desviación vs estándar",
        valor_desv,
        sub="Real vs requerido",
        nivel=dot.get("nivel", "na"),
    )

    sub = dot.get("jornadas_sub", 0)
    sobre = dot.get("jornadas_sobre", 0)
    fuera = sub + sobre
    nivel_jor = "ok" if fuera == 0 else "alerta"
    c4 = kpi_card(
        "Jornadas fuera de rango",
        fmt_num(fuera),
        sub=f"{sub} sub · {sobre} sobre",
        nivel=nivel_jor,
    )

    componentes = [kpi_row([c1, c2, c3, c4])]
    if interpretacion:
        componentes.append(
            html.Div(
                # interpretacion viene del original con etiquetas <b>; las
                # insertamos usando dangerously_allow_html via dcc.Markdown.
                # Aqui usamos html con dangerously_set_inner_html NO existe,
                # asi que renderizamos como Markdown.
                _render_inline_html(interpretacion),
                className="section-panel",
            )
        )
    return html.Div(componentes)


def _render_inline_html(texto: str):
    """
    Utility: convierte un fragmento con <b>...</b> en una lista de hijos
    mezclando html.B y strings. Util porque Dash no ejecuta HTML arbitrario.
    """
    import re
    partes = re.split(r"(<b>.*?</b>)", texto)
    out = []
    for p in partes:
        if p.startswith("<b>") and p.endswith("</b>"):
            out.append(html.B(p[3:-4]))
        elif p:
            out.append(p)
    return out


# ---------------------------------------------------------------------------
# Tabla comparativa de maquinaria (html estatico)
# ---------------------------------------------------------------------------
def maquinaria_table(analisis: dict) -> html.Table:
    """Tabla comparativa con/sin maquinaria (equivalente al HTML del original)."""
    con = analisis.get("con_maq", {})
    sin = analisis.get("sin_maq", {})

    def _cell(con_val, sin_val, decimals=0, invertir=False):
        if con_val is None and sin_val is None:
            return "-", "-", "-", "neu"
        if con_val is None:
            return "-", fmt_num(sin_val, decimals), "-", "neu"
        if sin_val is None:
            return fmt_num(con_val, decimals), "-", "-", "neu"
        dif_pct = (con_val - sin_val) / sin_val if sin_val != 0 else None
        if dif_pct is None:
            return fmt_num(con_val, decimals), fmt_num(sin_val, decimals), "-", "neu"
        signo = "+" if dif_pct > 0 else ""
        dif_str = f"{signo}{dif_pct*100:.1f}%".replace(".", ",")
        mejor = (dif_pct > 0) if not invertir else (dif_pct < 0)
        klass = "pos" if mejor else "neg"
        return fmt_num(con_val, decimals), fmt_num(sin_val, decimals), dif_str, klass

    f1 = _cell(con.get("kg_promedio"), sin.get("kg_promedio"), 0)
    f2 = _cell(con.get("kg_por_hora"), sin.get("kg_por_hora"), 1)
    f3 = _cell(con.get("kg_por_hora_persona"), sin.get("kg_por_hora_persona"), 2)

    return html.Table(
        [
            html.Thead(html.Tr([
                html.Th("Métrica de rentabilidad"),
                html.Th("Con maquinaria"),
                html.Th("Sin maquinaria"),
                html.Th("Diferencia"),
            ])),
            html.Tbody([
                html.Tr([
                    html.Td("Kg promedio por día operativo", className="metric-label"),
                    html.Td(f1[0]), html.Td(f1[1]),
                    html.Td(f1[2], className=f1[3]),
                ]),
                html.Tr([
                    html.Td("Kg por hora trabajada", className="metric-label"),
                    html.Td(f2[0]), html.Td(f2[1]),
                    html.Td(f2[2], className=f2[3]),
                ]),
                html.Tr([
                    html.Td("Kg por hora-persona", className="metric-label"),
                    html.Td(f3[0]), html.Td(f3[1]),
                    html.Td(f3[2], className=f3[3]),
                ]),
                html.Tr([
                    html.Td("Días operativos", className="metric-label"),
                    html.Td(str(con.get("jornadas", 0))),
                    html.Td(str(sin.get("jornadas", 0))),
                    html.Td("—", className="neu"),
                ]),
            ]),
        ],
        className="compare-table",
    )
