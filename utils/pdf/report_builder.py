"""
utils/pdf/report_builder.py
---------------------------
Generación de reporte ejecutivo PDF para Puro Finca.

Estructura del informe:
  1. Portada con logo, fecha y filtros aplicados
  2. Resumen ejecutivo (volumen consolidado por etapa)
  3. Tablero de cumplimiento (KPI por proceso vs estándar)
  4. Distribución de calidad (gráfico de torta del lavado)
  5. Tendencia de cosecha (gráfico de líneas)
  6. Alertas y recomendaciones
  7. Footer con datos corporativos

Usa solo ReportLab para mantener consistencia (no dependemos de wkhtmltopdf
ni de un browser headless). Las gráficas se generan con matplotlib (a
través de utilidades simples) o se incluyen como tablas cuando el dataset
está vacío.
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Optional
from xml.sax.saxutils import escape as _xml_escape

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    PageBreak, KeepTogether, HRFlowable,
)
from reportlab.pdfgen import canvas

from config.settings import (
    ESTANDARES, UMBRAL_CUMPLIMIENTO_OK, UMBRAL_CUMPLIMIENTO_ALERTA,
    UMBRAL_PRIMERA_OK, UMBRAL_PRIMERA_ALERTA,
    UMBRAL_PERDIDA_OK, UMBRAL_PERDIDA_ALERTA,
)
from config.company import COMPANY


# ---------------------------------------------------------------------------
# Paleta de marca para PDF
# ---------------------------------------------------------------------------
BRAND_GREEN_DARK   = colors.HexColor("#14532D")
BRAND_GREEN        = colors.HexColor("#1F6B3A")
BRAND_GREEN_LIME   = colors.HexColor("#8FC93A")
BRAND_ORANGE       = colors.HexColor("#F18A1F")
BRAND_ORANGE_DARK  = colors.HexColor("#E8661A")
BRAND_CREAM        = colors.HexColor("#FBF7EE")
BRAND_INK          = colors.HexColor("#0E1A13")
BRAND_INK_SOFT     = colors.HexColor("#475A4F")
BRAND_INK_MUTE     = colors.HexColor("#94A39A")
BRAND_BORDER       = colors.HexColor("#E3E9E5")
BRAND_PANEL        = colors.HexColor("#F7F9F8")

LEVEL_COLORS = {
    "ok":      colors.HexColor("#2D8A4E"),
    "alerta":  colors.HexColor("#B5791F"),
    "critico": colors.HexColor("#B23A3A"),
    "na":      BRAND_INK_MUTE,
    "neutral": BRAND_GREEN,
}


# ---------------------------------------------------------------------------
# Estilos de párrafo
# ---------------------------------------------------------------------------
def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"],
            fontName="Helvetica-Bold", fontSize=22, leading=26,
            textColor=BRAND_GREEN_DARK, spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"],
            fontName="Helvetica", fontSize=11, leading=14,
            textColor=BRAND_INK_SOFT, spaceAfter=8),
        "h2": ParagraphStyle("h2", parent=base["Heading2"],
            fontName="Helvetica-Bold", fontSize=14, leading=18,
            textColor=BRAND_GREEN_DARK, spaceBefore=14, spaceAfter=6),
        "h3": ParagraphStyle("h3", parent=base["Heading3"],
            fontName="Helvetica-Bold", fontSize=11, leading=14,
            textColor=BRAND_INK, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["BodyText"],
            fontName="Helvetica", fontSize=10, leading=14,
            textColor=BRAND_INK, alignment=TA_JUSTIFY, spaceAfter=6),
        "small": ParagraphStyle("small", parent=base["BodyText"],
            fontName="Helvetica", fontSize=9, leading=12,
            textColor=BRAND_INK_SOFT, spaceAfter=4),
        "tag": ParagraphStyle("tag", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=8, leading=10,
            textColor=BRAND_GREEN, alignment=TA_LEFT),
        "kpi_label": ParagraphStyle("kpi_label", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=7.5, leading=9,
            textColor=BRAND_INK_SOFT, alignment=TA_LEFT),
        "kpi_value": ParagraphStyle("kpi_value", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=15, leading=18,
            textColor=BRAND_INK, alignment=TA_LEFT),
        "kpi_sub": ParagraphStyle("kpi_sub", parent=base["Normal"],
            fontName="Helvetica", fontSize=7.5, leading=9,
            textColor=BRAND_INK_MUTE, alignment=TA_LEFT),
        "footer": ParagraphStyle("footer", parent=base["Normal"],
            fontName="Helvetica", fontSize=8, leading=10,
            textColor=BRAND_INK_MUTE, alignment=TA_CENTER),
    }


# ---------------------------------------------------------------------------
# Helpers de formato
# ---------------------------------------------------------------------------
def _fmt_num(v, decimals: int = 0, suffix: str = "") -> str:
    if v is None:
        return "-"
    try:
        if pd.isna(v):
            return "-"
    except Exception:
        pass
    try:
        if decimals == 0:
            return f"{int(round(float(v))):,}{suffix}".replace(",", ".")
        formatted = f"{float(v):,.{decimals}f}"
        ent, _, dec = formatted.partition(".")
        ent = ent.replace(",", ".")
        return f"{ent},{dec}{suffix}" if dec else f"{ent}{suffix}"
    except Exception:
        return str(v)


def _fmt_pct(v, decimals: int = 1) -> str:
    if v is None:
        return "-"
    try:
        if pd.isna(v):
            return "-"
    except Exception:
        pass
    try:
        return f"{float(v) * 100:.{decimals}f}%".replace(".", ",")
    except Exception:
        return "-"


def _level_from_pct(value: Optional[float], ok_thr: float,
                    alert_thr: float, higher_is_better: bool = True) -> str:
    if value is None:
        return "na"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "na"
    if higher_is_better:
        if v >= ok_thr:
            return "ok"
        if v >= alert_thr:
            return "alerta"
        return "critico"
    else:
        if v <= ok_thr:
            return "ok"
        if v <= alert_thr:
            return "alerta"
        return "critico"


# ---------------------------------------------------------------------------
# Header / Footer del PDF
# ---------------------------------------------------------------------------
class _Header:
    """Renderiza el header y footer en cada página."""

    def __init__(self, logo_path: Optional[Path], generated_at: str):
        self.logo_path = logo_path
        self.generated_at = generated_at

    def __call__(self, canv: canvas.Canvas, doc):
        canv.saveState()
        page_w, page_h = A4

        # ----- Header -----
        # Banda decorativa superior
        canv.setFillColor(BRAND_GREEN_DARK)
        canv.rect(0, page_h - 6, page_w, 6, fill=1, stroke=0)
        canv.setFillColor(BRAND_ORANGE)
        canv.rect(0, page_h - 8, page_w * 0.25, 2, fill=1, stroke=0)

        # Logo (si existe)
        if self.logo_path and self.logo_path.exists():
            try:
                canv.drawImage(str(self.logo_path), 1.6 * cm, page_h - 2.5 * cm,
                               width=1.4 * cm, height=1.4 * cm,
                               preserveAspectRatio=True, mask="auto")
            except Exception:
                pass

        # Nombre + tagline
        canv.setFillColor(BRAND_GREEN_DARK)
        canv.setFont("Helvetica-Bold", 11)
        canv.drawString(3.4 * cm, page_h - 1.5 * cm, COMPANY["name"])
        canv.setFillColor(BRAND_INK_SOFT)
        canv.setFont("Helvetica", 8)
        canv.drawString(3.4 * cm, page_h - 1.95 * cm,
                        "Reporte ejecutivo · Panel Operativo")

        # Fecha (derecha)
        canv.setFillColor(BRAND_INK_MUTE)
        canv.setFont("Helvetica", 8)
        canv.drawRightString(page_w - 1.6 * cm, page_h - 1.5 * cm,
                             "Generado el")
        canv.setFillColor(BRAND_INK)
        canv.setFont("Helvetica-Bold", 9)
        canv.drawRightString(page_w - 1.6 * cm, page_h - 1.95 * cm,
                             self.generated_at)

        # ----- Footer -----
        canv.setStrokeColor(BRAND_BORDER)
        canv.setLineWidth(0.5)
        canv.line(1.6 * cm, 1.6 * cm, page_w - 1.6 * cm, 1.6 * cm)

        canv.setFillColor(BRAND_INK_MUTE)
        canv.setFont("Helvetica", 8)
        canv.drawString(1.6 * cm, 1.1 * cm,
                        f"{COMPANY['name']} · {COMPANY['email']}")
        canv.drawCentredString(page_w / 2, 1.1 * cm,
                               "Documento confidencial — uso interno")
        canv.drawRightString(page_w - 1.6 * cm, 1.1 * cm,
                             f"Página {doc.page}")
        canv.restoreState()


# ---------------------------------------------------------------------------
# Bloques visuales
# ---------------------------------------------------------------------------
def _hero_block(styles, title: str, subtitle: str, filters_summary: str,
                logo_path: Optional[Path]):
    """Bloque tipo portada con título y filtros aplicados."""
    inner = []
    inner.append(Paragraph(
        '<font color="#1F6B3A"><b>REPORTE EJECUTIVO</b></font>',
        styles["tag"]))
    inner.append(Spacer(1, 4))
    inner.append(Paragraph(title, styles["title"]))
    inner.append(Paragraph(subtitle, styles["subtitle"]))
    inner.append(HRFlowable(width="40%", thickness=2,
                            color=BRAND_GREEN_LIME, spaceBefore=4, spaceAfter=8))
    inner.append(Paragraph(
        f"<b>Filtros aplicados:</b> {filters_summary}",
        styles["small"]))
    return inner


def _kpi_grid(styles, kpis: list[dict]):
    """Grid 2x2 de KPIs como Table de ReportLab."""
    cells = []
    for k in kpis:
        nivel = k.get("nivel", "neutral")
        accent = LEVEL_COLORS.get(nivel, BRAND_GREEN)
        cell = [
            [Paragraph(f'<font color="{accent.hexval()}"><b>● {k["label"].upper()}</b></font>',
                       styles["kpi_label"])],
            [Paragraph(f"<b>{k['value']}</b>", styles["kpi_value"])],
            [Paragraph(k.get("sub", ""), styles["kpi_sub"])],
        ]
        cells.append(cell)

    # Convertir a tabla 2x2
    rows = []
    for i in range(0, len(cells), 2):
        chunk = cells[i:i+2]
        # Cada celda interior es una mini-tabla apilada vertical
        row = []
        for c in chunk:
            inner_t = Table(c, colWidths=[7.5 * cm])
            inner_t.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (0, 0), 10),
                ("TOPPADDING", (0, 1), (0, 1), 0),
                ("TOPPADDING", (0, 2), (0, 2), 2),
                ("BOTTOMPADDING", (0, 2), (0, 2), 10),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, BRAND_BORDER),
                ("LINEBEFORE", (0, 0), (0, -1), 3,
                 LEVEL_COLORS.get(kpis[i + len(row)].get("nivel", "neutral") if i + len(row) < len(kpis) else "neutral", BRAND_GREEN)),
            ]))
            row.append(inner_t)
        # Si la fila quedó incompleta (1 sola celda), añadir vacío
        while len(row) < 2:
            row.append("")
        rows.append(row)

    outer = Table(rows, colWidths=[7.7 * cm, 7.7 * cm])
    outer.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return outer


def _kpi_card_table(styles, label: str, value: str, sub: str,
                    nivel: str = "neutral", width_cm: float = 7.5):
    """Genera UNA tarjeta KPI como Table autocontenida."""
    accent = LEVEL_COLORS.get(nivel, BRAND_GREEN)
    data = [
        [Paragraph(f'<font color="{accent.hexval()}"><b>● {_safe_inline(label).upper()}</b></font>',
                   styles["kpi_label"])],
        [Paragraph(f"<b>{_safe_inline(value)}</b>", styles["kpi_value"])],
        [Paragraph(_safe_inline(sub), styles["kpi_sub"])],
    ]

    t = Table(data, colWidths=[width_cm * cm])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (0, 0), 9),
        ("TOPPADDING", (0, 1), (0, 1), 2),
        ("TOPPADDING", (0, 2), (0, 2), 4),
        ("BOTTOMPADDING", (0, 2), (0, 2), 9),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.5, BRAND_BORDER),
        ("LINEBEFORE", (0, 0), (0, -1), 3, accent),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _kpi_grid_layout(styles, kpis: list[dict], cols: int = 2):
    """Grid de tarjetas KPI con ancho dinámico y legible en A4."""
    if not kpis:
        return Spacer(1, 1)

    page_inner = A4[0] - 3.2 * cm
    col_w = page_inner / cols
    inner_width_cm = max(3.8, (col_w - 8) / cm)

    cells = [
        _kpi_card_table(
            styles,
            k["label"],
            k["value"],
            k.get("sub", ""),
            k.get("nivel", "neutral"),
            width_cm=inner_width_cm,
        )
        for k in kpis
    ]

    rows = []
    for i in range(0, len(cells), cols):
        row = cells[i:i+cols]
        while len(row) < cols:
            row.append("")
        rows.append(row)

    t = Table(rows, colWidths=[col_w] * cols)
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _safe_inline(value) -> str:
    """Texto seguro para Paragraph de ReportLab sin romper etiquetas permitidas."""
    if value is None:
        return "-"
    text = str(value)
    allowed = ("<font", "</font>", "<b>", "</b>", "<i>", "</i>", "<br", "<para", "</para>")
    if any(tag in text for tag in allowed):
        return text
    return _xml_escape(text)


def _paragraph_cell(value, style):
    """Convierte celdas de tabla en Paragraph para que el markup se renderice."""
    if isinstance(value, Paragraph):
        return value
    return Paragraph(_safe_inline(value), style)


def _data_table(headers: list[str], rows: list[list], col_widths=None):
    """Tabla de datos profesional con estilo Puro Finca."""
    base = getSampleStyleSheet()
    header_style = ParagraphStyle(
        "table_header",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=BRAND_INK_SOFT,
        alignment=TA_LEFT,
    )
    body_style = ParagraphStyle(
        "table_body",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=BRAND_INK,
        alignment=TA_LEFT,
    )

    data = [
        [_paragraph_cell(h, header_style) for h in headers]
    ] + [
        [_paragraph_cell(c, body_style) for c in row]
        for row in rows
    ]

    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PANEL),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, 0), 1, BRAND_BORDER),

        # Body
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, BRAND_PANEL]),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, BRAND_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _alert_block(styles, items: list[dict]):
    """Lista de alertas con iconos coloreados."""
    if not items:
        return Paragraph(
            '<para backColor="#E7F4D2" leftIndent="8" rightIndent="8" '
            'spaceBefore="4" spaceAfter="4">'
            '<font color="#2D8A4E"><b>✓ Sin alertas activas.</b> '
            'Todos los procesos operan dentro de los umbrales.</font></para>',
            styles["body"])

    flowables = []
    for it in items:
        nivel = it.get("nivel", "alerta")
        c = LEVEL_COLORS.get(nivel, LEVEL_COLORS["alerta"])
        bg = colors.HexColor("#FEF4E6") if nivel == "alerta" else \
             colors.HexColor("#F9E2E2") if nivel == "critico" else \
             colors.HexColor("#E7F4D2")
        text = it["text"]
        flowables.append(Paragraph(
            f'<para backColor="{bg.hexval()}" leftIndent="8" rightIndent="8" '
            f'spaceBefore="2" spaceAfter="2">'
            f'<font color="{c.hexval()}"><b>● {nivel.upper()}</b></font>  '
            f'{text}</para>',
            styles["body"]))
        flowables.append(Spacer(1, 2))
    return flowables


# ---------------------------------------------------------------------------
# Figuras (matplotlib opcional, fallback a tabla)
# ---------------------------------------------------------------------------
def _try_donut_image(labels: list[str], values: list[float],
                     width_cm: float = 8.0):
    """Intenta generar un donut con matplotlib. Si falla, devuelve None."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    if not values or sum(values) == 0:
        return None

    palette = ["#1F6B3A", "#F18A1F", "#8FC93A", "#2D8A4E", "#E8661A", "#6CBD6F"]
    fig, ax = plt.subplots(figsize=(width_cm / 2.54, width_cm / 2.54),
                            facecolor="white")
    wedges, _ = ax.pie(values, colors=palette[:len(values)],
                        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2))
    ax.set_aspect("equal")
    ax.legend(wedges, [f"{l} ({v/sum(values)*100:.1f}%)" for l, v in zip(labels, values)],
              loc="center left", bbox_to_anchor=(1.0, 0.5),
              frameon=False, fontsize=9)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    img = Image(buf, width=width_cm * cm, height=width_cm * cm,
                kind="proportional")
    return img


def _try_line_image(dates, values, ylabel: str = "",
                    width_cm: float = 16.0, height_cm: float = 6.0):
    """Línea temporal simple."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    if not dates or not values or len(dates) != len(values):
        return None

    fig, ax = plt.subplots(figsize=(width_cm / 2.54, height_cm / 2.54),
                            facecolor="white")
    ax.plot(dates, values, color="#1F6B3A", linewidth=2, marker="o",
            markersize=4, markerfacecolor="#F18A1F",
            markeredgecolor="#F18A1F")
    ax.fill_between(dates, values, alpha=0.08, color="#1F6B3A")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#E3E9E5")
    ax.spines["bottom"].set_color("#E3E9E5")
    ax.tick_params(colors="#475A4F", labelsize=8)
    ax.grid(True, axis="y", linestyle="-", linewidth=0.4, color="#F0F4F1")
    ax.set_axisbelow(True)
    if ylabel:
        ax.set_ylabel(ylabel, color="#475A4F", fontsize=9)
    fig.autofmt_xdate(rotation=0, ha="center")
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width_cm * cm, height=height_cm * cm)


# ---------------------------------------------------------------------------
# Constructor principal
# ---------------------------------------------------------------------------
def build_executive_report(
    *,
    kpis_corte: dict, kpis_siembra: dict, kpis_cosecha: dict,
    kpis_lavado: dict, kpis_empaque: dict, kpis_cargue: dict,
    cosecha_serie: Optional[pd.DataFrame] = None,
    filtros_aplicados: Optional[dict] = None,
    user_email: Optional[str] = None,
    logo_path: Optional[str] = None,
) -> bytes:
    """
    Construye el reporte ejecutivo en bytes (PDF).

    Parameters
    ----------
    kpis_*  : dicts retornados por utils.metrics.kpis_*
    cosecha_serie : DataFrame con columnas ["Fecha", "Produccion Kg"] (opcional)
    filtros_aplicados : dict con los filtros activos para mostrar en portada
    user_email : email del usuario que generó el reporte
    logo_path : ruta absoluta al PNG del logo (opcional)
    """
    styles = _styles()
    buf = io.BytesIO()

    generated_at = datetime.now().strftime("%d / %m / %Y · %H:%M")

    logo_p = None
    if logo_path:
        p = Path(logo_path)
        if p.exists():
            logo_p = p

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.6 * cm, rightMargin=1.6 * cm,
        topMargin=2.8 * cm, bottomMargin=2.0 * cm,
        title=f"{COMPANY['name']} · Reporte ejecutivo",
        author=COMPANY["name"],
    )

    story = []

    # ====== Portada / hero ======
    filt_str = _format_filters(filtros_aplicados)
    story.extend(_hero_block(
        styles,
        title="Resumen ejecutivo de operación",
        subtitle=("Indicadores consolidados del ciclo productivo de batata: "
                  "corte de esquejes, siembra, cosecha, lavado, empaque y "
                  "despacho."),
        filters_summary=filt_str,
        logo_path=logo_p,
    ))
    story.append(Spacer(1, 14))

    # ====== Sección 1: Volumen consolidado ======
    story.append(Paragraph("1. Volumen operativo consolidado", styles["h2"]))
    story.append(Paragraph(
        "Totales acumulados del periodo filtrado, por etapa del proceso "
        "productivo.", styles["small"]))
    story.append(Spacer(1, 6))

    kpis_vol = [
        {"label": "Esquejes cortados",
         "value": _fmt_num(kpis_corte.get("total_esquejes")),
         "sub": f"{kpis_corte.get('dias_operativos', 0)} días operativos"},
        {"label": "Plantas sembradas",
         "value": _fmt_num(kpis_siembra.get("total_plantas")),
         "sub": f"{kpis_siembra.get('dias_operativos', 0)} días operativos"},
        {"label": "Kg cosechados",
         "value": _fmt_num(kpis_cosecha.get("total_kg")),
         "sub": f"{kpis_cosecha.get('dias_operativos', 0)} días operativos"},
        {"label": "Kg lavados",
         "value": _fmt_num(kpis_lavado.get("total_lavado")),
         "sub": f"{kpis_lavado.get('dias_operativos', 0)} días operativos"},
        {"label": "Kg empacados",
         "value": _fmt_num(kpis_empaque.get("total_empacado")),
         "sub": f"{kpis_empaque.get('dias_operativos', 0)} días operativos"},
        {"label": "Toneladas despachadas",
         "value": _fmt_num(kpis_cargue.get("total_toneladas"), 2) + " t",
         "sub": f"{kpis_cargue.get('despachos', 0)} despachos · {kpis_cargue.get('dias_operativos', 0)} días"},
        {"label": "Primera calidad",
         "value": _fmt_pct(kpis_lavado.get("pct_1")),
         "sub": "Sobre clasificado",
         "nivel": kpis_lavado.get("nivel_primera", "na")},
        {"label": "Caja comercializable",
         "value": _fmt_pct(kpis_lavado.get("pct_comercial")),
         "sub": "1ra + 2da + 3ra sobre salida total",
         "nivel": kpis_lavado.get("nivel_comercial", "na")},
    ]
    story.append(_kpi_grid_layout(styles, kpis_vol, cols=2))
    story.append(Spacer(1, 14))

    # ====== Sección 2: Cumplimiento por proceso ======
    story.append(Paragraph("2. Cumplimiento vs estándar", styles["h2"]))
    story.append(Paragraph(
        "Desempeño real de cada proceso comparado con el estándar operativo "
        "del manual Puro Finca.", styles["small"]))
    story.append(Spacer(1, 6))

    cumpl_rows = [
        ["Proceso", "Cumplimiento", "Nivel", "Base"],
        ["Corte de esquejes",
         _fmt_pct(kpis_corte.get("cumpl_prod")),
         _level_badge(kpis_corte.get("nivel_cumpl")),
         f"{kpis_corte.get('dias_operativos', 0)} días"],
        ["Siembra",
         _fmt_pct(kpis_siembra.get("cumpl_prod")),
         _level_badge(kpis_siembra.get("nivel_cumpl")),
         f"{kpis_siembra.get('dias_operativos', 0)} días"],
        ["Cosecha",
         _fmt_pct(kpis_cosecha.get("cumpl_prod")),
         _level_badge(kpis_cosecha.get("nivel_cumpl")),
         f"{kpis_cosecha.get('dias_operativos', 0)} días"],
        ["Lavado y clasificación",
         _fmt_pct(kpis_lavado.get("cumpl_prod")),
         _level_badge(kpis_lavado.get("nivel_cumpl")),
         f"{kpis_lavado.get('dias_operativos', 0)} días"],
        ["Empaque",
         _fmt_pct(kpis_empaque.get("cumpl_empacado")),
         _level_badge(kpis_empaque.get("nivel_cumpl")),
         f"{kpis_empaque.get('dias_operativos', 0)} días"],
        ["Cargue y despacho",
         _fmt_pct(kpis_cargue.get("cumpl_ton")),
         _level_badge(kpis_cargue.get("nivel_cumpl")),
         str(kpis_cargue.get("despachos", 0))],
    ]
    story.append(_data_table(cumpl_rows[0], cumpl_rows[1:],
                              col_widths=[6.2 * cm, 3.5 * cm, 3.5 * cm, 3.0 * cm]))
    story.append(Spacer(1, 14))

    # ====== Sección 3: Distribución de calidad (donut) ======
    story.append(Paragraph("3. Distribución de calidad — lavado",
                            styles["h2"]))
    story.append(Paragraph(
        "Composición total de salida del proceso, incluyendo calidad, semilla y descarte.",
        styles["small"]))
    story.append(Spacer(1, 6))

    cal_labels = []
    cal_values = []
    for k, lbl in [("total_1", "Primera"), ("total_2", "Segunda"),
                    ("total_3", "Tercera"), ("total_semilla", "Semilla"),
                    ("total_descarte", "Descarte")]:
        v = kpis_lavado.get(k)
        if v is not None and not _isnan(v) and float(v) > 0:
            cal_labels.append(lbl)
            cal_values.append(float(v))

    donut = _try_donut_image(cal_labels, cal_values, width_cm=8.0)
    if donut is not None:
        # Centrar el donut
        story.append(Table([[donut]], colWidths=[doc.width],
                            style=[("ALIGN", (0,0), (-1,-1), "CENTER")]))
    else:
        # Fallback: tabla
        rows = [["Categoría", "Kilogramos"]]
        for l, v in zip(cal_labels, cal_values):
            rows.append([l, _fmt_num(v, 1)])
        if not cal_labels:
            rows.append(["Sin datos", "-"])
        story.append(_data_table(rows[0], rows[1:],
                                  col_widths=[10 * cm, 5 * cm]))
    story.append(Spacer(1, 14))

    # ====== Sección 4: Tendencia de cosecha ======
    if cosecha_serie is not None and not cosecha_serie.empty:
        story.append(Paragraph("4. Tendencia de cosecha (kg / día)",
                                styles["h2"]))
        story.append(Spacer(1, 6))
        try:
            dates = pd.to_datetime(cosecha_serie["Fecha"]).dt.date.tolist()
            vals = cosecha_serie["Produccion Kg"].fillna(0).astype(float).tolist()
            line = _try_line_image(dates, vals, ylabel="kg",
                                    width_cm=16.0, height_cm=6.0)
            if line is not None:
                story.append(line)
            else:
                story.append(Paragraph(
                    "(Gráfico no disponible en este entorno — instale "
                    "matplotlib para incluirlo)", styles["small"]))
        except Exception as e:
            story.append(Paragraph(f"(Error generando gráfico: {e})",
                                    styles["small"]))
        story.append(Spacer(1, 14))

    # ====== Sección 5: Alertas ======
    story.append(Paragraph("5. Alertas ejecutivas", styles["h2"]))
    story.append(Paragraph(
        "Desviaciones detectadas durante el periodo analizado.",
        styles["small"]))
    story.append(Spacer(1, 6))

    alerts = _build_alerts(kpis_corte, kpis_siembra, kpis_cosecha,
                            kpis_lavado, kpis_empaque, kpis_cargue)
    al = _alert_block(styles, alerts)
    if isinstance(al, list):
        story.extend(al)
    else:
        story.append(al)
    story.append(Spacer(1, 14))

    # ====== Sección 6: Recomendaciones ======
    story.append(Paragraph("6. Recomendaciones", styles["h2"]))
    recs = _build_recommendations(alerts, kpis_lavado, kpis_cosecha)
    for r in recs:
        story.append(Paragraph(f"• {r}", styles["body"]))
    story.append(Spacer(1, 12))

    # ====== Pie ======
    story.append(HRFlowable(width="100%", thickness=0.5, color=BRAND_BORDER,
                             spaceBefore=10, spaceAfter=8))
    story.append(Paragraph(
        f"Reporte generado por <b>{user_email or 'Sistema'}</b> el "
        f"{generated_at}.", styles["small"]))
    story.append(Paragraph(
        f"{COMPANY['name']} · {COMPANY['address']} · {COMPANY['email']} · "
        f"{COMPANY['phone']}",
        styles["footer"]))

    # ====== Render con header/footer en cada página ======
    header = _Header(logo_p, generated_at)
    doc.build(story, onFirstPage=header, onLaterPages=header)

    return buf.getvalue()


def _isnan(v) -> bool:
    try:
        return pd.isna(v)
    except Exception:
        return False


def _level_badge(nivel: Optional[str]) -> str:
    if not nivel:
        return "-"
    color_map = {
        "ok":      "#2D8A4E",
        "alerta":  "#B5791F",
        "critico": "#B23A3A",
        "na":      "#94A39A",
    }
    label_map = {"ok": "Cumple", "alerta": "Alerta", "critico": "Crítico", "na": "S/D"}
    c = color_map.get(nivel, "#94A39A")
    label = label_map.get(nivel, nivel)
    return f'<font color="{c}"><b>● {label}</b></font>'


def _format_filters(f: Optional[dict]) -> str:
    if not f:
        return "Sin filtros aplicados — datos consolidados completos"

    parts = []
    fi, ff = f.get("fecha_inicio"), f.get("fecha_fin")
    if fi or ff:
        parts.append(f"Periodo {_safe_inline(fi or '...')} → {_safe_inline(ff or '...')}")

    for key, label in [("fincas", "Fincas"), ("lotes", "Lotes"),
                        ("proyectos", "Proyectos"),
                        ("clientes", "Clientes"), ("destinos", "Destinos")]:
        v = f.get(key)
        if v:
            values = ", ".join(_safe_inline(x) for x in v[:5])
            extra = f" (+{len(v)-5} más)" if len(v) > 5 else ""
            parts.append(f"{label}: {values}{extra}")

    return " · ".join(parts) if parts else "Sin filtros aplicados"


def _build_alerts(corte, siembra, cosecha, lavado, empaque, cargue) -> list[dict]:
    alerts = []
    procesos = [
        ("Corte de esquejes", corte.get("cumpl_prod"), corte.get("nivel_cumpl")),
        ("Siembra",            siembra.get("cumpl_prod"), siembra.get("nivel_cumpl")),
        ("Cosecha",            cosecha.get("cumpl_prod"), cosecha.get("nivel_cumpl")),
        ("Lavado",             lavado.get("cumpl_prod"),  lavado.get("nivel_cumpl")),
        ("Empaque",            empaque.get("cumpl_empacado"), empaque.get("nivel_cumpl")),
        ("Cargue",             cargue.get("cumpl_ton"),    cargue.get("nivel_cumpl")),
    ]
    for nombre, val, niv in procesos:
        if niv == "critico" and val is not None:
            alerts.append({"nivel": "critico",
                "text": f"<b>{nombre}</b>: cumplimiento en "
                        f"{_fmt_pct(val)}, por debajo del umbral aceptable."})
        elif niv == "alerta" and val is not None:
            alerts.append({"nivel": "alerta",
                "text": f"<b>{nombre}</b>: cumplimiento en "
                        f"{_fmt_pct(val)}, requiere seguimiento."})

    if (lavado.get("pct_perdida") is not None
            and lavado.get("nivel_perdida") and lavado["nivel_perdida"] != "ok"):
        alerts.append({"nivel": lavado["nivel_perdida"],
            "text": f"<b>Pérdidas en lavado</b>: "
                    f"{_fmt_pct(lavado['pct_perdida'])} del kg recibido."})

    if (cosecha.get("pct_descarte") is not None
            and cosecha.get("nivel_descarte") and cosecha["nivel_descarte"] != "ok"):
        alerts.append({"nivel": cosecha["nivel_descarte"],
            "text": f"<b>Descarte en cosecha</b>: "
                    f"{_fmt_pct(cosecha['pct_descarte'])} sobre producción total."})

    return alerts


def _to_float_or_none(value):
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _build_recommendations(alerts: list[dict], lavado: dict, cosecha: dict) -> list[str]:
    recs = []
    criticos = [a for a in alerts if a["nivel"] == "critico"]
    alertas = [a for a in alerts if a["nivel"] == "alerta"]

    if criticos:
        recs.append("Atender de manera prioritaria los procesos en estado "
                    "<b>crítico</b>: revisar dotación de personal, condiciones "
                    "de campo y tiempos efectivos de jornada.")
    if alertas:
        recs.append("Programar seguimiento semanal a los procesos en "
                    "<b>alerta</b> hasta retornar al rango ≥ 95% de "
                    "cumplimiento estándar.")

    pct1 = _to_float_or_none(lavado.get("pct_1"))
    if pct1 is not None and pct1 < UMBRAL_PRIMERA_OK:
        recs.append("La proporción de <b>primera calidad</b> está por debajo "
                    "del 55%. Revisar prácticas de cosecha y manipulación "
                    "post-cosecha para mejorar la clasificación.")

    pct_p = _to_float_or_none(lavado.get("pct_perdida"))
    if pct_p is not None and pct_p > UMBRAL_PERDIDA_OK:
        recs.append("Las <b>pérdidas en lavado</b> superan el 5% objetivo. "
                    "Auditar el proceso de selección y tipificar las causas "
                    "(daño mecánico, sobre-tamaño, sub-tamaño).")

    pct_d = _to_float_or_none(cosecha.get("pct_descarte"))
    if pct_d is not None and pct_d > 0.10:
        recs.append("El <b>descarte en cosecha</b> es elevado. Evaluar "
                    "calendario de siembra, riego y prevención fitosanitaria "
                    "del lote correspondiente.")

    if not recs:
        recs.append("La operación se mantiene dentro de los umbrales "
                    "establecidos. Mantener las prácticas actuales y "
                    "documentar los factores de éxito del periodo.")
        recs.append("Considerar iniciar análisis comparativos contra "
                    "periodos anteriores para identificar tendencias y "
                    "oportunidades de mejora marginal.")
    return recs
