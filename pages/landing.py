"""
pages/landing.py
----------------
Landing page pública de Puro Finca S.A.S — basada en el documento
corporativo oficial de la empresa.

Secciones (en orden):
  1. Navbar con logo + CTA al portal interno
  2. Hero — agroexportación con ciencia, tecnología e innovación
  3. Banda de stats / cifras destacadas
  4. ¿Quiénes somos?
  5. Objetivo general
  6. Servicios / líneas de negocio (con imágenes reales)
  7. Proyecto líder — batata
  8. Misión y visión
  9. Objetivos específicos (6 tarjetas)
 10. Beneficios sobre fondo verde
 11. CTA al portal
 12. Footer con contacto
"""

from __future__ import annotations

from dash import html

from config.company import (
    COMPANY, ABOUT_PARAGRAPHS, MISSION, VISION,
    OBJECTIVE_GENERAL, SPECIFIC_OBJECTIVES,
    SERVICES, BENEFITS, STATS, FLAGSHIP_PROJECT,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _section_eyebrow(text: str, light: bool = False) -> html.Span:
    cls = "public-section-eyebrow" + (" light" if light else "")
    return html.Span(text, className=cls)


# ---------------------------------------------------------------------------
# 1. Navbar
# ---------------------------------------------------------------------------
def _navbar() -> html.Div:
    return html.Div([
        html.Div([
            html.A([
                html.Img(src="/assets/logo.png", alt="Puro Finca",
                         className="public-navbar-logo"),
                html.Div([
                    html.Span(COMPANY["short_name"],
                              className="public-navbar-name"),
                    html.Span("S.A.S",
                              className="public-navbar-suffix"),
                ], className="public-navbar-name-wrap"),
            ], href="/", className="public-navbar-brand"),

            html.Div([
                html.A("Nosotros",     href="#nosotros",     className="public-nav-link"),
                html.A("Servicios",    href="#servicios",    className="public-nav-link"),
                html.A("Proyecto",     href="#proyecto",     className="public-nav-link"),
                html.A("Misión",       href="#mision",       className="public-nav-link"),
                html.A("Contacto",     href="#contacto",     className="public-nav-link"),
            ], className="public-navbar-links"),

            html.A("Portal interno →",
                   href="/login",
                   className="public-cta-btn"),
        ], className="public-navbar-inner"),
    ], className="public-navbar")


# ---------------------------------------------------------------------------
# 2. Hero
# ---------------------------------------------------------------------------
def _hero() -> html.Section:
    return html.Section([
        # Imagen de fondo difuminada
        html.Div(className="public-hero-bg-image",
                 style={"backgroundImage": "url('/assets/hero-cultivo.jpg')"}),

        html.Div([
            html.Div([
                html.Span("Empresa agrícola · Región Caribe · Colombia",
                          className="public-hero-eyebrow"),
                html.H1([
                    "Agroexportación con ",
                    html.Em("ciencia,"), html.Br(),
                    "tecnología e innovación."
                ], className="public-hero-title"),
                html.P(
                    "Equipo profesional especializado en proyectos de alto "
                    "impacto en el sector agrícola. Producción, "
                    "transformación y comercialización de batata para "
                    "mercados nacionales e internacionales.",
                    className="public-hero-text"),
                html.Div([
                    html.A("Conocer nuestros servicios", href="#servicios",
                           className="public-cta-btn primary"),
                    html.A("Acceder al portal →", href="/login",
                           className="public-cta-btn ghost"),
                ], className="public-hero-actions"),
            ], className="public-hero-text-col"),

            html.Div([
                html.Div([
                    html.Img(src="/assets/logo.png", alt="Puro Finca",
                             className="public-hero-logo"),
                    html.Div([
                        html.Div("Puro Finca", className="public-hero-card-name"),
                        html.Div("S.A.S", className="public-hero-card-sub"),
                    ], className="public-hero-card-brand"),

                    html.Div(className="public-hero-card-divider"),

                    html.Div([
                        html.Div([
                            html.Div("5+", className="public-hero-stat-n"),
                            html.Div("Años en el mercado",
                                     className="public-hero-stat-label"),
                        ], className="public-hero-stat"),
                        html.Div([
                            html.Div("06", className="public-hero-stat-n"),
                            html.Div("Procesos integrados",
                                     className="public-hero-stat-label"),
                        ], className="public-hero-stat"),
                    ], className="public-hero-card-stats"),
                ], className="public-hero-card"),
            ], className="public-hero-visual-col"),
        ], className="public-hero-inner"),
    ], className="public-hero", id="inicio")


# ---------------------------------------------------------------------------
# 3. Stats band
# ---------------------------------------------------------------------------
def _stats_band() -> html.Section:
    return html.Section(
        html.Div([
            html.Div([
                html.Div(s["value"], className="public-stat-n"),
                html.Div(s["label"], className="public-stat-label"),
            ], className="public-stat-item")
            for s in STATS
        ], className="public-stats-inner"),
        className="public-stats")


# ---------------------------------------------------------------------------
# 4. Quiénes somos
# ---------------------------------------------------------------------------
def _about() -> html.Section:
    return html.Section([
        html.Div([
            html.Div([
                _section_eyebrow("¿Quiénes somos?"),
                html.H2(["Equipo profesional con ",
                         html.Em("alianzas internacionales")],
                        className="public-section-title"),
            ], className="public-section-header"),

            html.Div([
                html.Div([
                    html.P(p, className="public-about-paragraph")
                    for p in ABOUT_PARAGRAPHS
                ] + [
                    html.Div([
                        _value_pill("◌", "Producción agrícola"),
                        _value_pill("✦", "Desarrollo de productos"),
                        _value_pill("◈", "Comercialización"),
                        _value_pill("▲", "Ciencia, tecnología e innovación"),
                    ], className="public-about-pills"),
                ], className="public-about-text"),

                html.Div([
                    html.Img(src="/assets/equipo-terreno.jpg",
                             alt="Equipo Puro Finca preparando el terreno",
                             className="public-about-image"),
                    html.Div("Equipo Puro Finca · preparación inicial del terreno",
                             className="public-about-caption"),
                ], className="public-about-image-wrap"),
            ], className="public-about-grid"),
        ], className="public-section-inner"),
    ], className="public-section public-about-section", id="nosotros")


def _value_pill(icon: str, label: str) -> html.Div:
    return html.Div([
        html.Span(icon, className="public-pill-icon"),
        html.Span(label, className="public-pill-label"),
    ], className="public-value-pill")


# ---------------------------------------------------------------------------
# 5. Objetivo general
# ---------------------------------------------------------------------------
def _general_objective() -> html.Section:
    return html.Section([
        html.Div([
            html.Div([
                _section_eyebrow("Objetivo general"),
                html.H2([
                    html.Em("Potenciar"), " la agroexportación en Colombia"
                ], className="public-section-title"),
                html.P(OBJECTIVE_GENERAL,
                       className="public-objective-text"),
                html.P(
                    "Para posicionar a Colombia en una fuerte posición "
                    "agrícola, aprovechamos la experiencia y los sistemas "
                    "de los países de donde proviene nuestra empresa.",
                    className="public-objective-text small"),
            ], className="public-objective-content"),
        ], className="public-section-inner"),
    ], className="public-section public-objective-section")


# ---------------------------------------------------------------------------
# 6. Servicios
# ---------------------------------------------------------------------------
def _services() -> html.Section:
    cards = []
    for s in SERVICES:
        children = []
        if s.get("image"):
            children.append(
                html.Div(className="public-service-image",
                         style={"backgroundImage": f"url('{s['image']}')"})
            )
        else:
            children.append(
                html.Div(s["icon"], className="public-service-icon-large")
            )
        children.extend([
            html.Div([
                html.Span(s["icon"], className="public-service-icon"),
                html.H3(s["title"], className="public-service-title"),
                html.P(s["text"], className="public-service-text"),
            ], className="public-service-body"),
        ])
        cards.append(html.Div(children, className="public-service-card"))

    return html.Section([
        html.Div([
            html.Div([
                _section_eyebrow("Lo que hacemos"),
                html.H2("Servicios y líneas de negocio",
                        className="public-section-title"),
                html.P(
                    "Desde el cultivo en finca hasta la transformación en "
                    "valor agregado, integramos toda la cadena productiva "
                    "de la batata.",
                    className="public-section-subtitle"),
            ], className="public-section-header"),

            html.Div(cards, className="public-services-grid"),
        ], className="public-section-inner"),
    ], className="public-section public-services-section", id="servicios")


# ---------------------------------------------------------------------------
# 7. Proyecto líder
# ---------------------------------------------------------------------------
def _flagship_project() -> html.Section:
    return html.Section([
        html.Div([
            html.Div([
                html.Div([
                    _section_eyebrow("Proyecto líder"),
                    html.H2([
                        FLAGSHIP_PROJECT["name"].split("(")[0].strip(),
                        " — ", html.Em("nuestro proyecto bandera")
                    ], className="public-section-title"),
                    html.P(FLAGSHIP_PROJECT["text"],
                           className="public-flagship-text"),

                    html.Ul([
                        html.Li([
                            html.Span("✓", className="public-flagship-check"),
                            h
                        ], className="public-flagship-item")
                        for h in FLAGSHIP_PROJECT["highlights"]
                    ], className="public-flagship-list"),
                ], className="public-flagship-content"),

                html.Div([
                    html.Img(src="/assets/agricultor-campo.jpg",
                             alt="Cultivo de batata Puro Finca",
                             className="public-flagship-image"),
                    html.Div("Inspección de surcos en la finca",
                             className="public-flagship-caption"),
                ], className="public-flagship-visual"),
            ], className="public-flagship-grid"),
        ], className="public-section-inner"),
    ], className="public-section public-flagship-section", id="proyecto")


# ---------------------------------------------------------------------------
# 8. Misión y visión
# ---------------------------------------------------------------------------
def _mission_vision() -> html.Section:
    return html.Section([
        html.Div([
            html.Div([
                _section_eyebrow("Hacia dónde vamos", light=True),
                html.H2(["Misión y ",
                         html.Em("visión")],
                        className="public-section-title light"),
            ], className="public-section-header centered"),

            html.Div([
                # Misión
                html.Div([
                    html.Div([
                        html.Div("M", className="public-mv-letter"),
                        html.Div([
                            html.Div("Misión", className="public-mv-label"),
                            html.Div("Lo que hacemos hoy",
                                     className="public-mv-sub"),
                        ]),
                    ], className="public-mv-header"),
                    html.P(MISSION, className="public-mv-text"),
                ], className="public-mv-card"),

                # Visión
                html.Div([
                    html.Div([
                        html.Div("V", className="public-mv-letter accent"),
                        html.Div([
                            html.Div("Visión", className="public-mv-label"),
                            html.Div("A dónde proyectamos llegar",
                                     className="public-mv-sub"),
                        ]),
                    ], className="public-mv-header"),
                    html.P(VISION, className="public-mv-text"),
                ], className="public-mv-card"),
            ], className="public-mv-grid"),
        ], className="public-section-inner"),
    ], className="public-section public-mv-section", id="mision")


# ---------------------------------------------------------------------------
# 9. Objetivos específicos
# ---------------------------------------------------------------------------
def _specific_objectives() -> html.Section:
    cards = []
    for o in SPECIFIC_OBJECTIVES:
        cards.append(html.Div([
            html.Div(o["icon"], className="public-obj-icon"),
            html.H3(o["title"], className="public-obj-title"),
            html.P(o["text"], className="public-obj-text"),
        ], className="public-obj-card"))

    return html.Section([
        html.Div([
            html.Div([
                _section_eyebrow("Cómo lo hacemos"),
                html.H2("Objetivos específicos",
                        className="public-section-title"),
                html.P(
                    "Seis líneas de trabajo que articulan nuestra "
                    "operación y nuestra visión de país.",
                    className="public-section-subtitle"),
            ], className="public-section-header"),

            html.Div(cards, className="public-objectives-grid"),
        ], className="public-section-inner"),
    ], className="public-section public-objectives-section")


# ---------------------------------------------------------------------------
# 10. Beneficios
# ---------------------------------------------------------------------------
def _benefits() -> html.Section:
    items = []
    for i, b in enumerate(BENEFITS, start=1):
        items.append(html.Div([
            html.Div(f"0{i}", className="public-benefit-n"),
            html.H3(b["title"], className="public-benefit-title"),
            html.P(b["text"], className="public-benefit-text"),
        ], className="public-benefit-item"))

    return html.Section([
        html.Div([
            html.Div([
                _section_eyebrow("Por qué elegirnos", light=True),
                html.H2("Diferenciales que se traducen en operación",
                        className="public-section-title light"),
            ], className="public-section-header centered"),
            html.Div(items, className="public-benefits-grid"),
        ], className="public-section-inner"),
    ], className="public-section public-benefits-section",
    id="beneficios")


# ---------------------------------------------------------------------------
# 11. CTA al portal
# ---------------------------------------------------------------------------
def _cta_band() -> html.Section:
    return html.Section(
        html.Div([
            html.Div([
                _section_eyebrow("Para nuestro equipo"),
                html.H2("Acceso al portal interno",
                        className="public-section-title"),
                html.P(
                    "Si haces parte del equipo de Puro Finca, accede al "
                    "panel operativo para consultar indicadores en tiempo "
                    "real, generar reportes ejecutivos y monitorear cada "
                    "etapa del proceso productivo.",
                    className="public-section-subtitle"),
                html.A("Iniciar sesión →", href="/login",
                       className="public-cta-btn primary large"),
            ], className="public-cta-card"),
        ], className="public-section-inner"),
        className="public-section public-cta-section")


# ---------------------------------------------------------------------------
# 12. Footer
# ---------------------------------------------------------------------------
def _contact_footer() -> html.Footer:
    return html.Footer([
        html.Div([
            html.Div([
                html.Div([
                    html.Img(src="/assets/logo.png", alt="Puro Finca",
                             className="public-footer-logo"),
                    html.Div([
                        html.Div(COMPANY["name"], className="public-footer-name"),
                        html.Div(COMPANY["industry"],
                                 className="public-footer-tag"),
                    ]),
                ], className="public-footer-brand"),

                html.P(
                    "Empresa colombiana especializada en producción, "
                    "desarrollo y comercialización agrícola, articulada "
                    "con el área de ciencia, tecnología e innovación del "
                    "sector. Más de 5 años construyendo agroexportación "
                    "desde la Región Caribe.",
                    className="public-footer-about"),
            ], className="public-footer-col"),

            html.Div([
                html.H4("Contacto", className="public-footer-h"),
                html.Div([
                    html.Span("Email:  ", className="public-footer-key"),
                    html.A(COMPANY["email"], href=f"mailto:{COMPANY['email']}",
                           className="public-footer-link"),
                ]),
                html.Div([
                    html.Span("Tel.:   ", className="public-footer-key"),
                    html.A(COMPANY["phone"],
                           href=f"tel:{COMPANY['phone'].replace(' ', '')}",
                           className="public-footer-link"),
                ]),
                html.Div([
                    html.Span("Sede:   ", className="public-footer-key"),
                    html.Span(COMPANY["address"]),
                ]),
                html.Div([
                    html.Span("Web:    ", className="public-footer-key"),
                    html.Span(COMPANY["website"]),
                ]),
            ], className="public-footer-col", id="contacto"),

            html.Div([
                html.H4("Enlaces", className="public-footer-h"),
                html.A("¿Quiénes somos?", href="#nosotros",
                       className="public-footer-link"),
                html.A("Servicios",  href="#servicios",
                       className="public-footer-link"),
                html.A("Proyecto líder", href="#proyecto",
                       className="public-footer-link"),
                html.A("Misión y visión", href="#mision",
                       className="public-footer-link"),
                html.A("Portal interno →", href="/login",
                       className="public-footer-link strong"),
            ], className="public-footer-col"),
        ], className="public-footer-grid"),

        html.Div([
            html.Div(f"© 2026 {COMPANY['name']}. Todos los derechos reservados.",
                     className="public-footer-copy"),
            html.Div("Sitio web institucional · Versión 2026",
                     className="public-footer-mini"),
        ], className="public-footer-bottom"),
    ], className="public-footer")


# ---------------------------------------------------------------------------
# Layout completo
# ---------------------------------------------------------------------------
def layout() -> html.Div:
    return html.Div([
        _navbar(),
        _hero(),
        _stats_band(),
        _about(),
        _general_objective(),
        _services(),
        _flagship_project(),
        _mission_vision(),
        _specific_objectives(),
        _benefits(),
        _cta_band(),
        _contact_footer(),
    ], className="public-page")
