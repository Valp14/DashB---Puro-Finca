"""
styles/theme.py
---------------
Helpers de layout y marca (Puro Finca).

[COMPATIBILIDAD]
Mantiene las firmas originales: page_header(), empty_state(),
proceso_index(), NIVEL_COLOR, NIVEL_LABEL.

[NUEVO - rediseño 2026]
Agrega helpers de branding y contenido editable sin romper el resto del
sistema: hero_section, narrative_block, narrative_grid, narrative_card,
analyst_notes, section_header y exec_summary.
"""

from __future__ import annotations

from typing import Optional, List, Iterable

from dash import html

from config.settings import COLOR


# ---------------------------------------------------------------------------
# Mapeos usados por componentes/ui.py (sin cambios respecto al original)
# ---------------------------------------------------------------------------
NIVEL_COLOR = {
    "ok":       COLOR["ok"],
    "alerta":   COLOR["warn"],
    "critico":  COLOR["critical"],
    "na":       COLOR["text_mute"],
}

NIVEL_LABEL = {
    "ok":       "Cumple",
    "alerta":   "Alerta",
    "critico":  "Critico",
    "na":       "Sin dato",
}


# ---------------------------------------------------------------------------
# Encabezado corporativo (compatible)
# ---------------------------------------------------------------------------
def page_header(title: str, subtitle: str = "",
                description: str = "", is_home: bool = False) -> html.Div:
    """Encabezado con acento vertical y descripcion opcional.

    Si is_home=True, se asume que la pagina ya provee un hero_section y
    este page_header queda oculto (retorna un div vacio). Las paginas
    internas siguen usandolo igual que antes.
    """
    if is_home:
        # En la nueva home, el hero reemplaza al page_header.
        # Retornamos un contenedor invisible para no romper layouts
        # que ya lo incluyen.
        return html.Div(style={"display": "none"})

    header_content = [html.H1(title)]
    if subtitle:
        header_content.append(html.Div(subtitle, className="subtitle"))

    header = html.Div(
        [
            html.Div(className="header-accent"),
            html.Div(header_content, className="header-content"),
        ],
        className="corporate-header",
    )

    out = [header]
    if description:
        out.append(
            html.Div(
                html.Div(description, className="intro-text"),
                className="intro-panel",
            )
        )
    return html.Div(out, className="fade-in-up")


# ---------------------------------------------------------------------------
# Empty state (compatible)
# ---------------------------------------------------------------------------
def empty_state(mensaje: str = "Sin datos disponibles aun") -> html.Div:
    return html.Div(mensaje, className="empty-state")


# ---------------------------------------------------------------------------
# Indice de procesos (compatible, con chips modernizados)
# ---------------------------------------------------------------------------
def proceso_index() -> html.Div:
    procesos_mostrar = [
        "Corte de esquejes", "Siembra", "Cosecha",
        "Lavado y clasificación", "Empaque", "Cargue y despacho",
        "Calidad y pérdidas", "Calidad de datos",
    ]
    chips = [html.Span(p, className="proceso-chip") for p in procesos_mostrar]
    return html.Div([
        html.Div("Módulos de análisis", className="muted",
                 style={"marginBottom": "6px", "fontWeight": "600",
                        "fontSize": "0.72rem", "letterSpacing": "0.08em",
                        "textTransform": "uppercase"}),
        html.Div(chips, className="proceso-index"),
    ])


# ===========================================================================
# NUEVOS COMPONENTES DE MARCA (no afectan paginas existentes)
# ===========================================================================

def hero_section(
    title: str,
    subtitle: str = "",
    eyebrow: str = "Panel Ejecutivo · 2026",
    meta: Optional[List[dict]] = None,
    badge_number: Optional[str] = None,
    badge_label: str = "Procesos",
) -> html.Div:
    """Hero visual de la pagina de inicio.

    Parámetros
    ----------
    title : str
        Titulo principal. Se puede resaltar una palabra envolviendola con
        "<em>...</em>" (se convierte en span con clase de gradiente).
    subtitle : str
        Descripcion corta bajo el titulo.
    eyebrow : str
        Pequeña etiqueta sobre el titulo.
    meta : list[dict]
        Lista opcional de {"label": "...", "value": "..."}.
    badge_number : str
        Numero grande en el badge circular a la derecha.
    badge_label : str
        Etiqueta bajo el numero del badge.
    """
    # Procesar <em>...</em> en el titulo
    title_children = _split_em_tag(title)

    meta_nodes = []
    for item in (meta or []):
        meta_nodes.append(html.Div([
            html.Div(item.get("label", ""), className="hero-meta-label"),
            html.Div(item.get("value", ""), className="hero-meta-value"),
        ], className="hero-meta-item"))

    inner = [
        html.Div([
            html.Div(eyebrow, className="hero-eyebrow") if eyebrow else None,
            html.H1(title_children, className="hero-title"),
            html.P(subtitle, className="hero-description") if subtitle else None,
            html.Div(meta_nodes, className="hero-meta") if meta_nodes else None,
        ], className="hero-text"),
    ]

    if badge_number is not None:
        inner.append(html.Div(
            html.Div([
                html.Div(badge_number, className="hero-badge-n"),
                html.Div(badge_label, className="hero-badge-label"),
            ], className="hero-badge-inner"),
            className="hero-badge",
        ))

    return html.Div(
        html.Div([c for c in inner if c is not None], className="hero-inner"),
        className="hero-section fade-in-up",
    )


def _split_em_tag(texto: str):
    """Convierte 'Hola <em>mundo</em>' en ['Hola ', html.Span('mundo')]."""
    import re
    if "<em>" not in texto:
        return texto
    partes = re.split(r"(<em>.*?</em>)", texto)
    out = []
    for p in partes:
        if p.startswith("<em>") and p.endswith("</em>"):
            out.append(html.Em(p[4:-5]))
        elif p:
            out.append(p)
    return out


def narrative_block(
    title: str,
    paragraphs: Iterable[str],
    eyebrow: str = "",
    editable: bool = True,
) -> html.Div:
    """Bloque de texto narrativo editable (Lorem ipsum / copy real).

    Se usa para misión, visión, propuesta de valor, contexto operativo,
    conclusiones ejecutivas, etc.
    """
    children = []
    if eyebrow:
        children.append(html.Div(eyebrow, className="narrative-eyebrow"))
    children.append(html.H3(title, className="narrative-title"))
    children.append(html.Div(
        [html.P(p) for p in paragraphs],
        className="narrative-body",
    ))

    props = {"className": "narrative-block"}
    if editable:
        props["data-editable"] = "true"
    return html.Div(children, **props)


def narrative_grid(cards: List[dict]) -> html.Div:
    """Grid de 3 tarjetas narrativas (mision/vision/propuesta, por ejemplo).

    cards: [{"icon": "✦", "title": "...", "text": "..."}]
    """
    nodes = []
    for c in cards:
        nodes.append(html.Div([
            html.Div(c.get("icon", "◆"), className="narrative-card-icon"),
            html.H4(c.get("title", ""), className="narrative-card-title"),
            html.P(c.get("text", ""), className="narrative-card-text"),
        ], className="narrative-card"))
    return html.Div(nodes, className="narrative-grid stagger")


def analyst_notes(text: str, label: str = "Notas del analista") -> html.Div:
    """Bloque destacado para insights escritos por el analista.

    Visualmente diferente de section-panel: fondo crema y acento naranja.
    """
    return html.Div([
        html.Div(label, className="analyst-notes-label"),
        html.Div(text, className="analyst-notes-body"),
    ], className="analyst-notes")


def section_header(title: str, subtitle: str = "",
                   actions: Optional[list] = None) -> html.Div:
    """Encabezado de seccion con titulo + subtitulo y acciones opcionales."""
    left_children = [html.H2(title)]
    if subtitle:
        left_children.append(html.Div(subtitle, className="section-header-sub"))

    children = [html.Div(left_children, className="section-header-left")]
    if actions:
        children.append(html.Div(actions, className="section-header-actions"))

    return html.Div(children, className="section-header")


def exec_summary(
    narrative_title: str,
    narrative_paragraphs: Iterable[str],
    quote_text: str,
    quote_author: str,
    narrative_eyebrow: str = "Resumen ejecutivo",
) -> html.Div:
    """Grid 2-columnas: bloque narrativo + cita destacada."""
    return html.Div([
        narrative_block(narrative_title, narrative_paragraphs,
                        eyebrow=narrative_eyebrow, editable=True),
        html.Div([
            html.Div(quote_text, className="exec-quote-text"),
            html.Span(quote_author, className="exec-quote-author"),
        ], className="exec-quote"),
    ], className="exec-summary")
