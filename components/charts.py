"""
components/charts.py
--------------------
Graficos sobrios y responsivos para el portal operativo.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from config.settings import COLOR, CATEGORICAL_COLORS


def _truncar(texto, max_len: int = 20) -> str:
    s = str(texto)
    return s if len(s) <= max_len else s[:max_len - 1] + "..."


def _tick_step(count: int, max_ticks: int = 8) -> int:
    if count <= max_ticks:
        return 1
    return max(1, int((count + max_ticks - 1) // max_ticks))


def daily_complete_series(
    df: pd.DataFrame,
    date_col: str,
    value_cols: str | list[str],
    start=None,
    end=None,
) -> pd.DataFrame:
    """Agrupa por dia y rellena fechas faltantes con cero."""
    cols = [value_cols] if isinstance(value_cols, str) else list(value_cols)
    out_cols = ["Fecha", *cols]
    if df is None or df.empty or date_col not in df.columns:
        return pd.DataFrame(columns=out_cols)

    present = [c for c in cols if c in df.columns]
    if not present:
        return pd.DataFrame(columns=out_cols)

    d = df[[date_col, *present]].copy()
    d["_FechaDia"] = pd.to_datetime(d[date_col], errors="coerce").dt.normalize()
    d = d.dropna(subset=["_FechaDia"])
    if d.empty:
        return pd.DataFrame(columns=out_cols)

    for col in present:
        d[col] = pd.to_numeric(d[col], errors="coerce").fillna(0)

    grouped = d.groupby("_FechaDia", as_index=True)[present].sum().sort_index()
    start_ts = pd.to_datetime(start, errors="coerce") if start is not None else grouped.index.min()
    end_ts = pd.to_datetime(end, errors="coerce") if end is not None else grouped.index.max()
    if pd.isna(start_ts):
        start_ts = grouped.index.min()
    if pd.isna(end_ts):
        end_ts = grouped.index.max()
    start_ts = pd.Timestamp(start_ts).normalize()
    end_ts = pd.Timestamp(end_ts).normalize()
    if end_ts < start_ts:
        start_ts, end_ts = end_ts, start_ts

    full_index = pd.date_range(start_ts, end_ts, freq="D")
    grouped = grouped.reindex(full_index, fill_value=0).rename_axis("Fecha").reset_index()
    for col in cols:
        if col not in grouped.columns:
            grouped[col] = 0
    return grouped[out_cols]


def _base_layout(
    fig: go.Figure,
    height: int = 320,
    show_legend: bool = False,
    x_tickangle: int = 0,
    bottom_margin: int = 54,
    left_margin: int = 58,
    hovermode: str = "closest",
) -> go.Figure:
    fig.update_layout(
        template="simple_white",
        height=height,
        autosize=True,
        margin=dict(l=left_margin, r=22, t=58, b=bottom_margin),
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
        hovermode=hovermode,
        bargap=0.34,
        transition=dict(duration=300),
    )
    fig.update_xaxes(
        showgrid=False,
        linecolor=COLOR["border_soft"],
        zeroline=False,
        tickangle=x_tickangle,
        automargin=True,
        tickfont=dict(color=COLOR["text_soft"], size=10),
        title_font=dict(color=COLOR["text_soft"], size=11),
        showline=True,
    )
    fig.update_yaxes(
        gridcolor=COLOR["grid"],
        griddash="dot",
        linecolor=COLOR["border_soft"],
        zeroline=False,
        tickfont=dict(color=COLOR["text_soft"], size=10),
        title_font=dict(color=COLOR["text_soft"], size=11),
        automargin=True,
    )
    return fig


def line_temporal(df: pd.DataFrame, x: str, y: str, titulo: str = "", y_label: str = "") -> go.Figure:
    fig = go.Figure()
    if df is not None and not df.empty and x in df.columns and y in df.columns:
        d = df[[x, y]].dropna().sort_values(x)
        d[y] = pd.to_numeric(d[y], errors="coerce").fillna(0)
        tickvals = None
        if len(d) > 0:
            step = _tick_step(len(d), max_ticks=8)
            tickvals = d[x].iloc[::step].tolist()
            if d[x].iloc[-1] not in tickvals:
                tickvals.append(d[x].iloc[-1])
        fig.add_trace(go.Scatter(
            x=d[x],
            y=d[y],
            mode="lines+markers",
            line=dict(color=COLOR["primary"], width=3, shape="linear"),
            marker=dict(size=7, color="white", line=dict(color=COLOR["primary"], width=2)),
            fill="tozeroy",
            fillcolor="rgba(31, 107, 58, 0.10)",
            name=y_label or y,
            connectgaps=False,
            hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.0f}<extra></extra>",
        ))
        if tickvals:
            fig.update_xaxes(tickmode="array", tickvals=tickvals, tickformat="%d/%m")
    fig.update_layout(title=dict(text=titulo, x=0, font=dict(size=13)))
    fig.update_yaxes(title=y_label)
    return _base_layout(fig, x_tickangle=-30, bottom_margin=70, hovermode="x unified")


def barh_ranking(df: pd.DataFrame, cat: str, val: str, titulo: str = "", top: int = 10, color: str = None) -> go.Figure:
    fig = go.Figure()
    altura = 320
    if df is not None and not df.empty and cat in df.columns and val in df.columns:
        d = (
            df[[cat, val]]
            .dropna()
            .groupby(cat, as_index=False)[val]
            .sum()
            .sort_values(val, ascending=True)
            .tail(top)
        )
        d["_label_full"] = d[cat].astype(str)
        d[cat] = d[cat].apply(lambda v: _truncar(v, 26))
        altura = max(240, 74 + 30 * len(d))
        fig.add_trace(go.Bar(
            x=d[val],
            y=d[cat].astype(str),
            orientation="h",
            marker=dict(color=color or COLOR["primary"], line=dict(color="rgba(255,255,255,0.85)", width=1), opacity=0.92),
            customdata=d["_label_full"],
            hovertemplate="%{customdata}: %{x:,.0f}<extra></extra>",
        ))
    fig.update_layout(title=dict(text=titulo, x=0, font=dict(size=13)))
    return _base_layout(fig, height=altura, left_margin=104, bottom_margin=34)


def bar_vertical(df: pd.DataFrame, cat: str, val: str, titulo: str = "", color: str = None, y_label: str = "") -> go.Figure:
    fig = go.Figure()
    tickangle = 0
    if df is not None and not df.empty and cat in df.columns and val in df.columns:
        d = (
            df[[cat, val]]
            .dropna()
            .groupby(cat, as_index=False)[val]
            .sum()
            .sort_values(cat)
        )
        d["_label_full"] = d[cat].astype(str)
        d[cat] = d[cat].apply(lambda v: _truncar(v, 18))
        tickangle = -30 if len(d) > 5 or d["_label_full"].map(len).max() > 10 else 0
        fig.add_trace(go.Bar(
            x=d[cat].astype(str),
            y=d[val],
            marker=dict(color=color or COLOR["primary"], line=dict(color="rgba(255,255,255,0.85)", width=1), opacity=0.92),
            customdata=d["_label_full"],
            hovertemplate="%{customdata}: %{y:,.0f}<extra></extra>",
        ))
    fig.update_layout(title=dict(text=titulo, x=0, font=dict(size=13)))
    fig.update_yaxes(title=y_label)
    return _base_layout(fig, x_tickangle=tickangle, bottom_margin=74 if tickangle else 54)


def bar_stacked_composition(categorias: list[str], series: dict, titulo: str = "", y_label: str = "") -> go.Figure:
    full_categories = [str(c) for c in categorias]
    categorias = [_truncar(c, 18) for c in categorias]
    fig = go.Figure()
    for i, (nombre, valores) in enumerate(series.items()):
        fig.add_trace(go.Bar(
            x=categorias,
            y=valores,
            name=nombre,
            marker=dict(color=CATEGORICAL_COLORS[i % len(CATEGORICAL_COLORS)], line=dict(color="white", width=1), opacity=0.95),
            customdata=full_categories,
            hovertemplate=f"%{{customdata}}<br>{nombre}: %{{y:,.0f}}<extra></extra>",
        ))
    angle = -25 if len(categorias) > 4 or any(len(c) > 10 for c in full_categories) else 0
    fig.update_layout(barmode="stack", title=dict(text=titulo, x=0, font=dict(size=13)))
    fig.update_yaxes(title=y_label)
    return _base_layout(fig, show_legend=True, x_tickangle=angle, bottom_margin=84 if angle else 64)


def bar_plan_vs_real(categorias: list[str], plan: list[float], real: list[float], titulo: str = "", y_label: str = "") -> go.Figure:
    full_categories = [str(c) for c in categorias]
    categorias = [_truncar(c, 18) for c in categorias]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categorias,
        y=plan,
        name="Estandar (Plan)",
        marker=dict(color="#D7DED8", line=dict(color="white", width=1), opacity=0.95),
        customdata=full_categories,
        hovertemplate="%{customdata}<br>Plan: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=categorias,
        y=real,
        name="Real",
        marker=dict(color=COLOR["primary"], line=dict(color="white", width=1), opacity=0.95),
        customdata=full_categories,
        hovertemplate="%{customdata}<br>Real: %{y:,.0f}<extra></extra>",
    ))
    angle = -25 if len(categorias) > 4 or any(len(c) > 10 for c in full_categories) else 0
    fig.update_layout(barmode="group", title=dict(text=titulo, x=0, font=dict(size=13)))
    fig.update_yaxes(title=y_label)
    return _base_layout(fig, show_legend=True, x_tickangle=angle, bottom_margin=84 if angle else 64)


def donut_composicion(labels: list[str], values: list[float], titulo: str = "") -> go.Figure:
    fig = go.Figure()
    total = sum(v or 0 for v in values or [])
    if labels and values and len(labels) == len(values) and total > 0:
        palette = ["#1F6B3A", "#6F9866", "#C9B46A", "#F18A1F", "#A33A3A", "#8FC93A"]
        fig.add_trace(go.Pie(
            labels=labels,
            values=values,
            hole=0.68,
            sort=False,
            direction="clockwise",
            marker=dict(colors=palette[:len(labels)], line=dict(color="white", width=4)),
            textposition="inside",
            textinfo="percent",
            insidetextorientation="horizontal",
            textfont=dict(size=11, color=COLOR["text"]),
            pull=[0.018 if i == 0 else 0 for i in range(len(labels))],
            hovertemplate="%{label}<br>%{value:,.2f} kg - %{percent}<extra></extra>",
        ))
        fig.add_annotation(
            text=f"<b>{total:,.0f}</b><br><span style='font-size:11px'>kg</span>",
            x=.5,
            y=.5,
            showarrow=False,
            font=dict(size=18, color=COLOR["text"]),
        )
    fig.update_layout(
        title=dict(text=titulo, x=0, font=dict(size=13)),
        uniformtext_minsize=10,
        uniformtext_mode="hide",
        legend=dict(orientation="h", y=-0.10, x=0.5, xanchor="center"),
    )
    return _base_layout(fig, show_legend=True, height=360, bottom_margin=62)
