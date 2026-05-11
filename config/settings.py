"""
config/settings.py
------------------
Configuracion central del dashboard Puro Finca.

[MIGRACION Streamlit -> Dash]
Este modulo NO cambia en la migracion: no depende de Streamlit.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Marca
# ---------------------------------------------------------------------------
APP_NAME     = "Puro Finca"
APP_SUBTITLE = "Seguimiento de productividad, calidad y cumplimiento operativo"
APP_DESCRIPTION = (
    "Panel de control integral del proceso productivo de batata — desde el "
    "corte de esquejes hasta el despacho. Visibilidad en tiempo real sobre "
    "rendimiento, calidad, cumplimiento y trazabilidad por finca, lote y "
    "proyecto."
)

# ---------------------------------------------------------------------------
# Procesos
# ---------------------------------------------------------------------------
PROCESOS = [
    "Corte Esquejes",
    "Siembra",
    "Cosecha",
    "Lavado Clasificacion",
    "Empaque",
    "Cargue Vehiculo",
]

PROCESOS_LABEL = {
    "Corte Esquejes":       "Corte de esquejes",
    "Siembra":              "Siembra",
    "Cosecha":              "Cosecha",
    "Lavado Clasificacion": "Lavado y clasificación",
    "Empaque":              "Empaque",
    "Cargue Vehiculo":      "Cargue y despacho",
}

SHEET_ALIASES = {
    "Corte Esquejes":       ["Corte Esquejes", "Corte de Esquejes", "Corte"],
    "Siembra":              ["Siembra", "Siembras"],
    "Cosecha":              ["Cosecha", "Cosechas"],
    "Lavado Clasificacion": ["Lavado Clasificacion", "Lavado  Clasificación",
                             "Lavado Clasificación", "Lavado y Clasificacion",
                             "Lavado y Clasificación", "Lavado"],
    "Empaque":              ["Empaque", "Empaques"],
    "Cargue Vehiculo":      ["Cargue Vehiculo", "Cargue Vehículo", "Cargue",
                             "Despacho", "Cargue y Despacho"],
}

COLUMN_ALIASES = {
    "timestamp": "Timestamp",
    "fecha": "Fecha",
    "finca": "Finca",
    "lote": "Lote",
    "proyecto": "Proyecto",
    "observaciones": "Observaciones",

    "numero de trabajadores": "Numero Trabajadores",
    "numero trabajadores": "Numero Trabajadores",
    "n de trabajadores": "Numero Trabajadores",
    "horas trabajadas": "Horas",
    "horas en proceso": "Horas",
    "horas de proceso": "Horas",

    "esquejes cortados": "Esquejes",
    "plantas sembradas": "Plantas",

    "surcos cosechados": "Surcos",
    "se utilizo maquinaria": "Maquinaria",
    "horas efectivas de maquina": "Horas Maquina",
    "produccion total kg": "Produccion Kg",
    "descarte kg": "Descarte Kg",

    "kg recibidos": "Kg Recibidos",
    "kg lavados": "Kg Lavados",
    "kg 1ra clase": "Kg 1ra",
    "kg 2da clase": "Kg 2da",
    "kg 3ra clase": "Kg 3ra",
    "kg semilla": "Kg Semilla",
    "kg descartados en lavado": "Kg Descarte Lavado",

    "kg empacados": "Kg Empacados",
    "kg empacados en cajas": "Kg Cajas",
    "kg empacados en sacos": "Kg Sacos",
    "kg empacados en bolsas": "Kg Bolsas",

    "toneladas": "Toneladas",
    "cajas": "Cajas",
    "sacos": "Sacos",
    "bolsas": "Bolsas",
    "cliente": "Cliente",
    "destino": "Destino",
    "placa": "Placa",
}

NUMERIC_COLUMNS = {
    "Corte Esquejes":       ["Horas", "Numero Trabajadores", "Esquejes"],
    "Siembra":              ["Horas", "Numero Trabajadores", "Plantas"],
    "Cosecha":              ["Surcos", "Numero Trabajadores", "Horas",
                             "Horas Maquina", "Produccion Kg", "Descarte Kg"],
    "Lavado Clasificacion": ["Kg Recibidos", "Kg Lavados", "Kg 1ra", "Kg 2da",
                             "Kg 3ra", "Kg Semilla", "Kg Descarte Lavado",
                             "Numero Trabajadores", "Horas"],
    "Empaque":              ["Kg Recibidos", "Kg Empacados", "Kg Cajas",
                             "Kg Sacos", "Kg Bolsas", "Numero Trabajadores",
                             "Horas"],
    "Cargue Vehiculo":      ["Toneladas", "Cajas", "Sacos", "Bolsas",
                             "Numero Trabajadores", "Horas"],
}

# ---------------------------------------------------------------------------
# Estandares operativos (manual Puro Finca)
# ---------------------------------------------------------------------------
ESTANDARES = {
    "Corte Esquejes": {
        "personas":            10,
        "dias":                1,
        "jornales":            10,
        "esquejes_total":      30000,
        "esquejes_persona_dia": 3500,
    },
    "Siembra": {
        "personas":            8,
        "jornales":            15,
        "dias":                2,
        "plantas_total":       30000,
        "plantas_persona_dia": 3000,
    },
    "Cosecha": {
        "personas":            10,
        "toneladas_objetivo_dia": 8,
        "kg_objetivo_dia":     8000,
        "jornales":            46,
        "dias":                2.5,
        "kg_persona_dia":      800,
        "pct_primera":         0.60,
        "pct_segunda":         0.25,
        "pct_tercera":         0.15,
        "pct_comercializable": 0.90,
    },
    "Lavado Clasificacion": {
        "personas":       10,
        "dias":           2,
        "jornales":       20,
        "kg_persona_dia": 735,
    },
    "Empaque": {
        "personas":              17,
        "dias":                  2,
        "jornales":              34,
        "pct_empacado_objetivo": 0.95,
    },
    "Cargue Vehiculo": {
        "personas":  3,
        "horas":     3,
        "toneladas": 17,
        "jornales":  3,
    },
}

DOTACION_ESTANDAR = {
    "Corte Esquejes":       10,
    "Siembra":              8,
    "Cosecha":              10,
    "Lavado Clasificacion": 10,
    "Empaque":              17,
    "Cargue Vehiculo":      3,
}

# ---------------------------------------------------------------------------
# Tratamiento de ceros distorsionantes
# ---------------------------------------------------------------------------
ZEROS_EXCLUIDOS_EN_KPI = {
    "Corte Esquejes":       ["Esquejes", "Horas", "Numero Trabajadores"],
    "Siembra":              ["Plantas", "Horas", "Numero Trabajadores"],
    "Cosecha":              ["Produccion Kg", "Horas", "Numero Trabajadores", "Surcos"],
    "Lavado Clasificacion": ["Kg Lavados", "Kg Recibidos", "Horas", "Numero Trabajadores"],
    "Empaque":              ["Kg Empacados", "Kg Recibidos", "Horas", "Numero Trabajadores"],
    "Cargue Vehiculo":      ["Toneladas", "Horas", "Numero Trabajadores"],
}

ZEROS_INFORMATIVOS = {
    "Cosecha":              ["Descarte Kg"],
    "Lavado Clasificacion": ["Kg Descarte Lavado", "Kg 2da", "Kg 3ra", "Kg Semilla"],
    "Empaque":              ["Kg Cajas", "Kg Sacos", "Kg Bolsas"],
    "Cargue Vehiculo":      ["Cajas", "Sacos", "Bolsas"],
}

# ---------------------------------------------------------------------------
# Umbrales de alerta
# ---------------------------------------------------------------------------
UMBRAL_CUMPLIMIENTO_OK     = 0.95
UMBRAL_CUMPLIMIENTO_ALERTA = 0.80

UMBRAL_PRIMERA_OK     = 0.55
UMBRAL_PRIMERA_ALERTA = 0.45

UMBRAL_COMERCIAL_OK     = 0.90
UMBRAL_COMERCIAL_ALERTA = 0.80

UMBRAL_PERDIDA_OK     = 0.05
UMBRAL_PERDIDA_ALERTA = 0.10

UMBRAL_DOTACION_OK     = 0.10
UMBRAL_DOTACION_ALERTA = 0.25

# ---------------------------------------------------------------------------
# Normalizacion unidad cargue (regla auto kg -> t)
# ---------------------------------------------------------------------------
CARGUE_UMBRAL_KG_A_T = 100.0

# ---------------------------------------------------------------------------
# Paleta corporativa — PURO FINCA (derivada del logo)
# ---------------------------------------------------------------------------
#   Verde bosque profundo   #1F6B3A  (primario)
#   Verde lima vibrante     #8FC93A  (del logo)
#   Naranja calido          #F18A1F  (texto del logo)
# Se conservan los mismos keys que el dashboard original consume.
COLOR = {
    "bg":           "#FFFFFF",
    "panel":        "#F7F9F8",
    "panel_soft":   "#FAFCFB",
    "border":       "#E3E9E5",
    "border_soft":  "#F0F4F1",
    "text":         "#0E1A13",
    "text_soft":    "#475A4F",
    "text_mute":    "#94A39A",
    "primary":      "#1F6B3A",
    "primary_2":    "#2D8A4E",
    "primary_soft": "#E7F4D2",
    "accent":       "#F18A1F",
    "ok":           "#2D8A4E",
    "ok_soft":      "#E7F4D2",
    "warn":         "#B5791F",
    "warn_soft":    "#FEF4E6",
    "critical":     "#B23A3A",
    "critical_soft":"#F9E2E2",
    "neutral":      "#6B7D72",
    "grid":         "#F0F4F1",
}

# Paleta categorica: alterna verdes, naranja del logo y neutros terrosos.
CATEGORICAL_COLORS = [
    "#1F6B3A",  # verde bosque
    "#F18A1F",  # naranja logo
    "#8FC93A",  # verde lima
    "#2D8A4E",  # verde medio
    "#E8661A",  # naranja tostado
    "#6CBD6F",  # verde claro
    "#B5791F",  # ocre tierra
    "#475A4F",  # verde oscuro neutro
]

# ---------------------------------------------------------------------------
# Historico
# ---------------------------------------------------------------------------
HISTORICO_COLUMNAS_MINIMAS = ["Fecha", "Proceso", "Finca", "Lote", "Valor"]
COL_ORIGEN = "Origen Datos"
ORIGEN_ACTUAL    = "Actual"
ORIGEN_HISTORICO = "Historico"
