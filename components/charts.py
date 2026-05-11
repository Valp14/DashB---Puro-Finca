"""
components/charts.py
--------------------
Graficos sobrios con etiquetas SIEMPRE horizontales (tickangle=0).
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.graph_objects as go

from config.settings import COLOR, CATEGORICAL_COLORS


def _truncar(texto, max_len: int = 20) -> str:
    s = str(texto)
    return s if len(s) <= max_len else s[:max_len-1] + "…"


def _base_layout(fig: go.Figure, height: int = 320,
                 show_legend: bool = False) -> go.Figure:
    """Layout visual unificado para todas las gráficas internas.

    Mantiene las mismas firmas y datos, pero actualiza el acabado visual
    para que los módulos se vean como tarjetas ejecutivas responsivas.
    """
    fig.update_layout(
        template="simple_white",
        height=height,
        margin=dict(l=22, r=18, t=52, b=44),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family='"Plus Jakarta Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            color=COLOR["text"],
            size=12,
        ),
        title=dict(
            x=0,
            xanchor="left",
            font=dict(size=14, color=COLOR["text"], family='"Plus Jakarta Sans", sans-serif'),
            pad=dict(t=4, b=10),
        ),
        showlegend=show_legend,
        legend=dict(
            orientation="h",
            y=-0.20,
            x=0,
            font=dict(size=11, color=COLOR["text_soft"]),
            bgcolor="rgba(0,0,0,0)",
            itemclick="toggleothers",
            itemdoubleclick="toggle",
        ),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor=COLOR["border"],
            font=dict(family='"Plus Jakarta Sans", sans-serif', color=COLOR["text"], size=12),
        ),
        bargap=0.34,
        transition=dict(duration=300),
    )
    # CRITICO: etiquetas siempre horizontales
    fig.update_xaxes(
        showgrid=False,
        linecolor=COLOR["border_soft"],
        zeroline=False,
        tickangle=0,
        automargin=True,
        tickfont=dict(color=COLOR["text_soft"], size=11),
        title_font=dict(color=COLOR["text_soft"], size=11),
        showline=True,
    )
    fig.update_yaxes(
        gridcolor=COLOR["grid"],
        griddash="dot",
        linecolor=COLOR["border_soft"],
        zeroline=False,
        tickfont=dict(color=COLOR["text_soft"], size=11),
        title_font=dict(color=COLOR["text_soft"], size=11),
    )
    return fig

def line_temporal(df: pd.DataFrame, x: str, y: str,
                  titulo: str = "", y_label: str = "") -> go.Figure:
    fig = go.Figure()
    if df is not None and not df.empty and x in df.columns and y in df.columns:
        d = df[[x, y]].dropna().sort_values(x)
        fig.add_trace(go.Scatter(
            x=d[x], y=d[y],
            mode="lines+markers",
            line=dict(color=COLOR["primary"], width=3, shape="spline", smoothing=0.55),
            marker=dict(size=7, color="white", line=dict(color=COLOR["primary"], width=2)),
            fill="tozeroy",
            fillcolor="rgba(31, 107, 58, 0.10)",
            name=y_label or y,
            hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>",
        ))
    fig.update_layout(title=dict(text=titulo, x=0, font=dict(size=13)))
    fig.update_yaxes(title=y_label)
    return _base_layout(fig)


def barh_ranking(df: pd.DataFrame, cat: str, val: str, titulo: str = "",
                 top: int = 10, color: str = None) -> go.Figure:
    fig = go.Figure()
    altura = 320
    if df is not None and not df.empty and cat in df.columns and val in df.columns:
        d = (df[[cat, val]]
             .dropna()
             .groupby(cat, as_index=False)[val].sum()
             .sort_values(val, ascending=True)
             .tail(top))
        d[cat] = d[cat].apply(_truncar)
        # Altura dinámica: 28 px por barra + padding
        altura = max(220, 60 + 28 * len(d))
        fig.add_trace(go.Bar(
            x=d[val], y=d[cat].astype(str),
            orientation="h",
            marker=dict(color=color or COLOR["primary"], line=dict(color="rgba(255,255,255,0.85)", width=1), opacity=0.92),
            hovertemplate="%{y}: %{x:,.0f}<extra></extra>",
        ))
    fig.update_layout(title=dict(text=titulo, x=0, font=dict(size=13)))
    return _base_layout(fig, height=altura)


def bar_vertical(df: pd.DataFrame, cat: str, val: str, titulo: str = "",
                 color: str = None, y_label: str = "") -> go.Figure:
    fig = go.Figure()
    if df is not None and not df.empty and cat in df.columns and val in df.columns:
        d = (df[[cat, val]]
             .dropna()
             .groupby(cat, as_index=False)[val].sum()
             .sort_values(cat))
        d[cat] = d[cat].apply(_truncar)
        fig.add_trace(go.Bar(
            x=d[cat].astype(str), y=d[val],
            marker=dict(color=color or COLOR["primary"], line=dict(color="rgba(255,255,255,0.85)", width=1), opacity=0.92),
            hovertemplate="%{x}: %{y:,.0f}<extra></extra>",
        ))
    fig.update_layout(title=dict(text=titulo, x=0, font=dict(size=13)))
    fig.update_yaxes(title=y_label)
    return _base_layout(fig)


def bar_stacked_composition(categorias: list[str], series: dict,
                            titulo: str = "", y_label: str = "") -> go.Figure:
    categorias = [_truncar(c) for c in categorias]
    fig = go.Figure()
    for i, (nombre, valores) in enumerate(series.items()):
        fig.add_trace(go.Bar(
            x=categorias, y=valores,
            name=nombre,
            marker=dict(color=CATEGORICAL_COLORS[i % len(CATEGORICAL_COLORS)], line=dict(color="white", width=1), opacity=0.95),
            hovertemplate=f"{nombre}: %{{y:,.0f}}<extra></extra>",
        ))
    fig.update_layout(barmode="stack",
                      title=dict(text=titulo, x=0, font=dict(size=13)))
    fig.update_yaxes(title=y_label)
    return _base_layout(fig, show_legend=True)


def bar_plan_vs_real(categorias: list[str], plan: list[float],
                     real: list[float], titulo: str = "",
                     y_label: str = "") -> go.Figure:
    categorias = [_truncar(c) for c in categorias]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categorias, y=plan, name="Estándar (Plan)",
        marker=dict(color="#D7DED8", line=dict(color="white", width=1), opacity=0.95),
        hovertemplate="Plan: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=categorias, y=real, name="Real",
        marker=dict(color=COLOR["primary"], line=dict(color="white", width=1), opacity=0.95),
        hovertemplate="Real: %{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(barmode="group",
                      title=dict(text=titulo, x=0, font=dict(size=13)))
    fig.update_yaxes(title=y_label)
    return _base_layout(fig, show_legend=True)


def donut_composicion(labels: list[str], values: list[float],
                      titulo: str = "") -> go.Figure:
    fig = go.Figure()
    total = sum(v or 0 for v in values or [])
    if labels and values and len(labels) == len(values) and total > 0:
        palette = ["#1F6B3A", "#6F9866", "#C9B46A", "#F18A1F", "#A33A3A", "#8FC93A"]
        fig.add_trace(go.Pie(
            labels=labels, values=values,
            hole=0.68,
            sort=False,
            direction="clockwise",
            marker=dict(colors=palette[:len(labels)], line=dict(color="white", width=4)),
            textposition="outside",
            textinfo="label+percent",
            textfont=dict(size=11, color=COLOR["text"]),
            pull=[0.018 if i == 0 else 0 for i in range(len(labels))],
            hovertemplate="%{label}<br>%{value:,.2f} kg · %{percent}<extra></extra>",
        ))
        fig.add_annotation(
            text=f"<b>{total:,.0f}</b><br><span style='font-size:11px'>kg</span>",
            x=.5, y=.5, showarrow=False, font=dict(size=18, color=COLOR["text"]),
        )
    fig.update_layout(title=dict(text=titulo, x=0, font=dict(size=13)), uniformtext_minsize=10, uniformtext_mode="hide")
    return _base_layout(fig, show_legend=False, height=360)
