"""
pages/inicio.py
---------------
Página de Inicio — Resumen ejecutivo PURO FINCA.

Esta versión mantiene la lógica original de métricas, filtros y callbacks,
pero simplifica la pantalla de inicio para que sea más limpia, funcional
y enfocada en la operación.

Se conserva:
- Hero principal
- Botón de exportar PDF
- Volumen operativo consolidado
- Tablero de cumplimiento
- Alertas ejecutivas
- Lecturas rápidas

Se elimina:
- Resumen narrativo largo
- Índice visual de procesos
- Bloques de identidad operativa
- Contexto operativo editable
- Nota del analista
"""

from __future__ import annotations

from dash import Input, Output, callback, html

from config.settings import APP_DESCRIPTION, PROCESOS
from styles.theme import (
    empty_state,
    hero_section,
    section_header,
)
from components.ui import kpi_card, kpi_row, fmt_num, fmt_pct, pill
from pages._common import filter_panel
from components.sidebar import get_data_filtrada
from auth import current_role
from services.access_control import can_read_operational_data
from utils.metrics import (
    kpis_corte,
    kpis_siembra,
    kpis_cosecha,
    kpis_lavado,
    kpis_empaque,
    kpis_cargue,
)


# ---------------------------------------------------------------------------
# Bloque de instrucción inicial
# ---------------------------------------------------------------------------

def instruction_panel():
    return html.Div(
        [
            html.Div(
                [
                    html.Div("Inicio del análisis", className="section-eyebrow"),
                    html.H2(
                        "Conecta la base operativa de Supabase para comenzar.",
                        className="section-title",
                    ),
                    html.P(
                        "Desde el panel lateral puedes cargar el archivo Excel de la operación. "
                        "Una vez cargado, este inicio mostrará automáticamente el volumen "
                        "consolidado, el cumplimiento por proceso, las alertas ejecutivas "
                        "y las lecturas rápidas del periodo filtrado.",
                        className="section-subtitle",
                    ),
                ],
                style={"maxWidth": "760px"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div("01", className="step-number"),
                            html.Div(
                                [
                                    html.H4("Conecta Supabase", className="step-title"),
                                    html.P(
                                        "Verifica que Supabase esté conectado.",
                                        className="step-text",
                                    ),
                                ]
                            ),
                        ],
                        className="step-card",
                    ),
                    html.Div(
                        [
                            html.Div("02", className="step-number"),
                            html.Div(
                                [
                                    html.H4("Aplica filtros", className="step-title"),
                                    html.P(
                                        "Filtra por finca, lote, proyecto, cliente o destino.",
                                        className="step-text",
                                    ),
                                ]
                            ),
                        ],
                        className="step-card",
                    ),
                    html.Div(
                        [
                            html.Div("03", className="step-number"),
                            html.Div(
                                [
                                    html.H4("Analiza resultados", className="step-title"),
                                    html.P(
                                        "Consulta KPIs, cumplimiento, alertas y lecturas rápidas.",
                                        className="step-text",
                                    ),
                                ]
                            ),
                        ],
                        className="step-card",
                    ),
                ],
                className="instruction-steps",
            ),
        ],
        className="section-panel",
        style={
            "padding": "2rem",
            "marginTop": "1.5rem",
            "marginBottom": "1.5rem",
        },
    )


# ---------------------------------------------------------------------------
# Layout estático
# ---------------------------------------------------------------------------

def layout():
    return html.Div(
        [
            # ---------- HERO ----------
            hero_section(
                title="Cosecha con <em>datos</em>, decisiones con criterio.",
                subtitle=APP_DESCRIPTION,
                eyebrow="Panel Operativo · Puro Finca",
                meta=[
                    {"label": "Procesos", "value": "6 etapas"},
                    {"label": "Unidades", "value": "Campo + planta"},
                    {"label": "Actualizado", "value": "Tiempo real"},
                ],
                badge_number="06",
                badge_label="Procesos",
            ),

            filter_panel("Filtros del dashboard", compact=True),

            # ---------- Acciones rápidas ----------
            html.Div(
                [
                    html.Button(
                        [
                            html.Span("⬇ ", style={"fontWeight": "700"}),
                            "Exportar reporte PDF",
                        ],
                        id="btn-export-pdf",
                        className="btn-primary",
                        style={
                            "width": "auto",
                            "display": "inline-flex",
                            "alignItems": "center",
                            "gap": "4px",
                        },
                        n_clicks=0,
                    ),
                ],
                className="quick-actions",
            ),

            # ---------- Contenido dinámico ----------
            html.Div(id="inicio-contenido"),
        ],
        className="fade-in-up ops-page ops-home process-productividad",
    )


# ===========================================================================
# CALLBACK
# ===========================================================================

@callback(
    Output("inicio-contenido", "children"),
    Input("store-archivo", "data"),
    Input("store-data", "data"),
    Input("store-filtros", "data"),
)
def render_inicio(archivo_cargado, store_data, filtros):
    if not can_read_operational_data(current_role()):
        return html.Div(
            [
                section_header(
                    title="Panel de operador",
                    subtitle="Registra la operacion diaria desde formularios.",
                ),
                html.Div(
                    [
                        html.H2("Listo para registrar datos"),
                        html.P(
                            "Tu perfil puede crear registros operativos. Los historicos consolidados "
                            "quedan reservados para perfiles de consulta y administracion.",
                            className="muted",
                        ),
                        html.A("Ir a formularios", href="/portal/formularios", className="btn-primary"),
                    ],
                    className="section-panel",
                ),
            ]
        )

    if not archivo_cargado:
        return html.Div(
            [
                instruction_panel(),
                empty_state(
                    "Aún no hay datos cargados. Importa el archivo Excel operativo "
                    "desde el panel lateral para iniciar el análisis."
                ),
            ]
        )

    # -----------------------------------------------------------------------
    # Data filtrada por proceso
    # -----------------------------------------------------------------------

    data = {p: get_data_filtrada(store_data, filtros, p) for p in PROCESOS}

    corte = kpis_corte(data["Corte Esquejes"])
    siembra = kpis_siembra(data["Siembra"])
    cosecha = kpis_cosecha(data["Cosecha"])
    lavado = kpis_lavado(data["Lavado Clasificacion"])
    empaque = kpis_empaque(data["Empaque"])
    cargue = kpis_cargue(data["Cargue Vehiculo"])

    # -----------------------------------------------------------------------
    # Sección 1: Volumen operativo consolidado
    # -----------------------------------------------------------------------

    fila1 = kpi_row(
        [
            kpi_card(
                "Esquejes cortados",
                fmt_num(corte["total_esquejes"]),
                sub=f"{corte['dias_operativos']} días · {corte['registros']} registros",
                nivel="neutral",
            ),
            kpi_card(
                "Plantas sembradas",
                fmt_num(siembra["total_plantas"]),
                sub=f"{siembra['dias_operativos']} días · {siembra['registros']} registros",
                nivel="neutral",
            ),
            kpi_card(
                "Kilogramos cosechados",
                fmt_num(cosecha["total_kg"]),
                sub=f"{cosecha['dias_operativos']} días · {cosecha['registros']} registros",
                nivel="neutral",
            ),
            kpi_card(
                "Kg lavados",
                fmt_num(lavado["total_lavado"]),
                sub=f"{lavado['dias_operativos']} días · {lavado['registros']} registros",
                nivel="neutral",
            ),
        ]
    )

    fila2 = kpi_row(
        [
            kpi_card(
                "Kg empacados",
                fmt_num(empaque["total_empacado"]),
                sub=f"{empaque['dias_operativos']} días · {empaque['registros']} registros",
                nivel="neutral",
            ),
            kpi_card(
                "Toneladas despachadas",
                fmt_num(cargue["total_toneladas"], 2) + " t",
                sub=f"{cargue['despachos']} despachos · {cargue['dias_operativos']} días",
                nivel="neutral",
            ),
            kpi_card(
                "Primera calidad",
                fmt_pct(lavado["pct_1"]),
                sub="Sobre clasificado",
                nivel=lavado.get("nivel_primera", "na"),
            ),
            kpi_card(
                "Caja comercializable",
                fmt_pct(lavado["pct_comercial"]),
                sub="1ra + 2da + 3ra sobre salida total",
                nivel=lavado.get("nivel_comercial", "na"),
            ),
        ]
    )

    # -----------------------------------------------------------------------
    # Sección 2: Tablero de cumplimiento
    # -----------------------------------------------------------------------

    estado_tabla = [
        {
            "Proceso": "Corte de esquejes",
            "Cumplimiento": corte["cumpl_prod"],
            "Nivel": corte["nivel_cumpl"],
            "Base": f"{corte['dias_operativos']} días",
        },
        {
            "Proceso": "Siembra",
            "Cumplimiento": siembra["cumpl_prod"],
            "Nivel": siembra["nivel_cumpl"],
            "Base": f"{siembra['dias_operativos']} días",
        },
        {
            "Proceso": "Cosecha",
            "Cumplimiento": cosecha["cumpl_prod"],
            "Nivel": cosecha["nivel_cumpl"],
            "Base": f"{cosecha['dias_operativos']} días",
        },
        {
            "Proceso": "Lavado y clasificación",
            "Cumplimiento": lavado["cumpl_prod"],
            "Nivel": lavado["nivel_cumpl"],
            "Base": f"{lavado['dias_operativos']} días",
        },
        {
            "Proceso": "Empaque",
            "Cumplimiento": empaque.get("cumpl_empacado"),
            "Nivel": empaque["nivel_cumpl"],
            "Base": f"{empaque['dias_operativos']} días",
        },
        {
            "Proceso": "Cargue y despacho",
            "Cumplimiento": cargue["cumpl_ton"],
            "Nivel": cargue["nivel_cumpl"],
            "Base": f"{cargue['despachos']} despachos",
        },
    ]

    cards_cumpl = [
        kpi_card(
            it["Proceso"],
            fmt_pct(it["Cumplimiento"]) if it["Cumplimiento"] is not None else "-",
            sub=f"Cumplimiento vs estándar · {it['Base']}",
            nivel=it["Nivel"],
        )
        for it in estado_tabla
    ]

    cumpl_rows = [
        kpi_row(cards_cumpl[0:3]),
        kpi_row(cards_cumpl[3:6]),
    ]

    # -----------------------------------------------------------------------
    # Sección 3: Alertas ejecutivas
    # -----------------------------------------------------------------------

    alertas = []

    for it in estado_tabla:
        if it["Nivel"] == "critico" and it["Cumplimiento"] is not None:
            alertas.append(
                (
                    "critico",
                    f"{it['Proceso']}: cumplimiento en {fmt_pct(it['Cumplimiento'])}, "
                    f"por debajo del umbral aceptable.",
                )
            )
        elif it["Nivel"] == "alerta" and it["Cumplimiento"] is not None:
            alertas.append(
                (
                    "alerta",
                    f"{it['Proceso']}: cumplimiento en {fmt_pct(it['Cumplimiento'])}, "
                    f"requiere seguimiento.",
                )
            )

    if lavado.get("pct_perdida") is not None and lavado["nivel_perdida"] != "ok":
        alertas.append(
            (
                lavado["nivel_perdida"],
                f"Pérdidas en lavado: {fmt_pct(lavado['pct_perdida'])} del kg recibido.",
            )
        )

    if cosecha.get("pct_descarte") is not None and cosecha["nivel_descarte"] != "ok":
        alertas.append(
            (
                cosecha["nivel_descarte"],
                f"Descarte en cosecha: {fmt_pct(cosecha['pct_descarte'])} "
                f"sobre producción total.",
            )
        )

    if lavado.get("pct_1") is not None and lavado["nivel_primera"] != "ok":
        alertas.append(
            (
                lavado["nivel_primera"],
                f"Primera calidad en {fmt_pct(lavado['pct_1'])}: "
                f"por debajo del objetivo 60%.",
            )
        )

    if not alertas:
        alertas_panel = html.Div(
            "Sin alertas activas con los filtros actuales. Los procesos operan "
            "dentro de los umbrales establecidos.",
            className="section-panel ok-accent",
        )
    else:
        alertas_panel = html.Div(
            html.Ul(
                [
                    html.Li(
                        [pill(niv), " ", texto],
                        style={"marginBottom": "8px"},
                    )
                    for niv, texto in alertas
                ],
                style={"margin": "0", "paddingLeft": "1rem"},
            ),
            className="section-panel warn-accent",
        )

    # -----------------------------------------------------------------------
    # Sección 4: Lecturas rápidas
    # -----------------------------------------------------------------------

    insights = []

    if corte["prod_persona_dia"] is not None:
        insights.append(
            f"Productividad promedio de corte: {fmt_num(corte['prod_persona_dia'])} "
            f"esquejes por persona/día "
            f"(estándar {fmt_num(corte['estandar_persona'])})."
        )

    if cosecha["prod_persona_dia"] is not None:
        insights.append(
            f"Productividad promedio de cosecha: {fmt_num(cosecha['prod_persona_dia'])} "
            f"kg por persona/día "
            f"(estándar {fmt_num(cosecha['estandar_persona'])})."
        )

    if lavado["pct_1"] is not None:
        insights.append(
            f"Distribución de calidad: {fmt_pct(lavado['pct_1'])} primera, "
            f"{fmt_pct(lavado['pct_2'])} segunda, "
            f"{fmt_pct(lavado['pct_3'])} tercera."
        )

    if cargue["ton_promedio"] is not None:
        insights.append(
            f"Toneladas promedio por despacho: "
            f"{fmt_num(cargue['ton_promedio'], 2)} t "
            f"(estándar {fmt_num(cargue['estandar_ton'])} t)."
        )

    if insights:
        lecturas_panel = html.Div(
            html.Ul(
                [
                    html.Li(x, style={"marginBottom": "8px"})
                    for x in insights
                ],
                style={"margin": "0", "paddingLeft": "1rem"},
            ),
            className="section-panel",
        )
    else:
        lecturas_panel = html.Div(
            "Aún no hay suficientes datos para generar lecturas.",
            className="section-panel",
        )

    # -----------------------------------------------------------------------
    # Retorno final
    # -----------------------------------------------------------------------

    return html.Div(
        [
            section_header(
                title="Volumen operativo consolidado",
                subtitle="Totales acumulados del periodo filtrado, por etapa.",
            ),
            html.Div([fila1, fila2], className="stagger"),

            section_header(
                title="Tablero de cumplimiento",
                subtitle="Desempeño real frente al estándar definido para cada proceso.",
            ),
            html.Div(cumpl_rows, className="stagger"),

            section_header(
                title="Alertas ejecutivas",
                subtitle="Desviaciones que requieren revisión o seguimiento operativo.",
            ),
            alertas_panel,

            section_header(
                title="Lecturas rápidas",
                subtitle="Síntesis automática de productividad, calidad y despacho.",
            ),
            lecturas_panel,
        ]
    )
