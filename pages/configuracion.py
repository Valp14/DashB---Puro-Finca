"""
pages/configuracion.py
----------------------
Configuracion: estandares, dotacion, reglas de ceros, umbrales y metodologia.
Solo lectura, auditable.
[Equivalente a pages/11_Configuracion.py de Streamlit]
"""

from __future__ import annotations

import pandas as pd
from dash import html

from styles.theme import page_header
from components.ui import fmt_pct, pill, detail_table
from config.settings import (
    ESTANDARES, DOTACION_ESTANDAR, PROCESOS_LABEL,
    ZEROS_EXCLUIDOS_EN_KPI, ZEROS_INFORMATIVOS,
    UMBRAL_CUMPLIMIENTO_OK, UMBRAL_CUMPLIMIENTO_ALERTA,
    UMBRAL_PRIMERA_OK, UMBRAL_PRIMERA_ALERTA,
    UMBRAL_COMERCIAL_OK, UMBRAL_COMERCIAL_ALERTA,
    UMBRAL_PERDIDA_OK, UMBRAL_PERDIDA_ALERTA,
    UMBRAL_DOTACION_OK, UMBRAL_DOTACION_ALERTA,
    CARGUE_UMBRAL_KG_A_T,
)


def layout():
    # ---------- Estandares ----------
    est_rows = []
    for proc, cfg in ESTANDARES.items():
        for k, v in cfg.items():
            est_rows.append({
                "Proceso":   PROCESOS_LABEL[proc],
                "Parámetro": k.replace("_", " "),
                "Valor":     v,
            })

    # ---------- Dotacion ----------
    dot_rows = [{"Proceso": PROCESOS_LABEL[p],
                 "Personas requeridas por jornada": v}
                for p, v in DOTACION_ESTANDAR.items()]

    # ---------- Umbrales ----------
    umb = pd.DataFrame([
        {"Indicador": "Cumplimiento general",
         "Cumple": f">= {fmt_pct(UMBRAL_CUMPLIMIENTO_OK)}",
         "Alerta": f">= {fmt_pct(UMBRAL_CUMPLIMIENTO_ALERTA)}",
         "Crítico": f"< {fmt_pct(UMBRAL_CUMPLIMIENTO_ALERTA)}"},
        {"Indicador": "Primera calidad",
         "Cumple": f">= {fmt_pct(UMBRAL_PRIMERA_OK)}",
         "Alerta": f">= {fmt_pct(UMBRAL_PRIMERA_ALERTA)}",
         "Crítico": f"< {fmt_pct(UMBRAL_PRIMERA_ALERTA)}"},
        {"Indicador": "Caja comercializable (1ra+2da+3ra)",
         "Cumple": f">= {fmt_pct(UMBRAL_COMERCIAL_OK)}",
         "Alerta": f">= {fmt_pct(UMBRAL_COMERCIAL_ALERTA)}",
         "Crítico": f"< {fmt_pct(UMBRAL_COMERCIAL_ALERTA)}"},
        {"Indicador": "Pérdida operativa (menor es mejor)",
         "Cumple": f"<= {fmt_pct(UMBRAL_PERDIDA_OK)}",
         "Alerta": f"<= {fmt_pct(UMBRAL_PERDIDA_ALERTA)}",
         "Crítico": f"> {fmt_pct(UMBRAL_PERDIDA_ALERTA)}"},
        {"Indicador": "Dotación (desviación vs estándar)",
         "Cumple":  f"±{fmt_pct(UMBRAL_DOTACION_OK)}",
         "Alerta":  f"±{fmt_pct(UMBRAL_DOTACION_ALERTA)}",
         "Crítico": f"> ±{fmt_pct(UMBRAL_DOTACION_ALERTA)}"},
    ])

    # ---------- Tratamiento de ceros ----------
    ceros_rows = []
    for proc, cols in ZEROS_EXCLUIDOS_EN_KPI.items():
        for c in cols:
            ceros_rows.append({"Proceso": PROCESOS_LABEL[proc], "Columna": c,
                               "Tratamiento": "Excluir ceros en KPIs de desempeño"})
    for proc, cols in ZEROS_INFORMATIVOS.items():
        for c in cols:
            ceros_rows.append({"Proceso": PROCESOS_LABEL[proc], "Columna": c,
                               "Tratamiento": "Mantener ceros (informativos)"})

    return html.Div([
        page_header("Configuración y metodología",
                    subtitle="Reglas de negocio, estándares, umbrales y tratamiento metodológico"),

        html.Div(["Las reglas aquí documentadas se aplican a todas las páginas. "
                  "Para modificarlas, editar ", html.Code("config/settings.py"), "."],
                 className="muted"),

        html.H2("Estándares operativos"),
        detail_table(pd.DataFrame(est_rows), id="tbl-estandares"),

        html.H2("Dotación estándar de personal"),
        detail_table(pd.DataFrame(dot_rows), id="tbl-dotacion-config"),

        html.H2("Umbrales de semaforización"),
        detail_table(umb, id="tbl-umbrales"),

        html.Div([pill("ok"), " Cumple    ",
                  pill("alerta"), " Alerta    ",
                  pill("critico"), " Crítico"],
                 className="muted", style={"marginTop": "6px"}),

        html.H2("Normalización de unidades en Cargue"),
        html.Div([
            html.B("Regla automática. "),
            "En la hoja de Cargue, si un registro individual tiene \"Toneladas\" "
            "mayor a ", html.B(f"{CARGUE_UMBRAL_KG_A_T:.0f}"),
            ", el sistema asume que el valor fue digitado en kilogramos y lo "
            "convierte a toneladas dividiendo por 1000. La columna ",
            html.Code("Unidad Origen"),
            " registra si el valor vino originalmente en t o fue convertido "
            "desde kg. Esta regla evita que un error de captura produzca "
            "indicadores absurdos.",
            html.Br(), html.Br(),
            html.B("Recomendación. "),
            "Modificar el formulario para etiquetar el campo como \"Kilogramos\" "
            "y así eliminar la necesidad de conversión automática.",
        ], className="section-panel"),

        html.H2("Definición de caja comercializable"),
        html.Div([
            "Se considera producto ", html.B("comercializable"),
            " la suma de ", html.B("primera, segunda y tercera calidad"),
            ". La semilla y el descarte son ", html.B("no comercializables"),
            ". Esta definición se aplica en todas las páginas y en las "
            "exportaciones consolidadas.",
        ], className="section-panel"),

        html.H2("Tratamiento de ceros distorsionantes"),
        html.Div([
            html.B("Criterio. "),
            "En indicadores de desempeño (promedios, productividad, eficiencia) "
            "se excluyen los ceros que representan ausencia de captura, no "
            "aplicación o dato no comparable. En totales (sumas) nunca se "
            "excluyen. Los ceros informativos (ejemplo: descarte = 0 significa "
            "\"no hubo pérdida\") nunca se excluyen de ningún cálculo. Todos "
            "los registros permanecen visibles en las tablas de detalle.",
        ], className="section-panel"),

        detail_table(pd.DataFrame(ceros_rows), id="tbl-ceros"),

        html.H2("Estado actual de captura"),
        html.Div([
            html.B("Base en construcción. "),
            "Mientras la recolección de datos sigue madurando, el sistema "
            "preserva los valores en cero y los campos no disponibles sin "
            "forzar imputaciones. La prioridad actual es mantener trazabilidad "
            "del dato capturado y separar claramente cero real de ausencia de "
            "cálculo cuando corresponda.",
            html.Br(), html.Br(),
            html.B("Siguiente etapa sugerida. "),
            "Cuando exista una base más completa, conviene incorporar reglas "
            "adicionales para tratar ", html.Code("NA"), ", valores faltantes, "
            "outliers y consistencia temporal de forma más estricta.",
        ], className="section-panel"),

        html.H2("Robustez del sistema"),
        html.Div([
            html.B("Tolerancias. "),
            "El dashboard acepta variaciones en nombres de hojas (mayúsculas, "
            "acentos, dobles espacios) y en encabezados de columnas (signos "
            "de puntuación, espacios finales). Las hojas faltantes se tratan "
            "como vacías. Las columnas faltantes no producen errores; los "
            "KPIs que no puedan calcularse muestran un guion. Las divisiones "
            "por cero devuelven vacío en lugar de error. Los filtros que "
            "dejan un proceso sin registros muestran un mensaje explícito.",
        ], className="section-panel"),
    ], className="ops-page ops-process-page process-configuracion")
