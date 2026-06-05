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
# IMPORTANTE:
# Se conservan los nombres internos originales para no afectar callbacks,
# filtros, carga de hojas, graficas ni componentes del dashboard.
PROCESOS = [
    "Corte Esquejes",
    "Siembra",
    "Cosecha",
    "Lavado Clasificacion",
    "Empaque",
    "Cargue Vehiculo",
]

# Etiquetas visibles ajustadas al Manual Operativo CAM.
PROCESOS_LABEL = {
    "Corte Esquejes":       "Corte de semillas / esquejes",
    "Siembra":              "Siembra",
    "Cosecha":              "Cosecha mecanizada",
    "Lavado Clasificacion": "Lavado",
    "Empaque":              "Clasificación y empaque",
    "Cargue Vehiculo":      "Carga al camión",
}

SHEET_ALIASES = {
    "Corte Esquejes": [
        "Corte Esquejes",
        "Corte de Esquejes",
        "Corte",
        "Corte de semillas",
        "Corte Semillas",
        "Corte de semillas (esquejes)",
    ],
    "Siembra": [
        "Siembra",
        "Siembras",
    ],
    "Cosecha": [
        "Cosecha",
        "Cosechas",
        "Cosecha mecanizada",
        "Cosecha Mecanizada",
    ],
    "Lavado Clasificacion": [
        "Lavado Clasificacion",
        "Lavado  Clasificación",
        "Lavado Clasificación",
        "Lavado y Clasificacion",
        "Lavado y Clasificación",
        "Lavado",
    ],
    "Empaque": [
        "Empaque",
        "Empaques",
        "Clasificacion Empaque",
        "Clasificación Empaque",
        "Clasificacion y Empaque",
        "Clasificación y Empaque",
        "Clasificación y empaque",
    ],
    "Cargue Vehiculo": [
        "Cargue Vehiculo",
        "Cargue Vehículo",
        "Cargue",
        "Despacho",
        "Cargue y Despacho",
        "Carga al Camion",
        "Carga al Camión",
        "Carga Camion",
        "Carga Camión",
    ],
}

COLUMN_ALIASES = {
    "timestamp": "Timestamp",
    "fecha": "Fecha",
    "finca": "Finca",
    "lote": "Lote",
    "proyecto": "Proyecto",
    "observaciones": "Observaciones",

    "numero de trabajadores": "Numero Trabajadores",
    "número de trabajadores": "Numero Trabajadores",
    "numero trabajadores": "Numero Trabajadores",
    "número trabajadores": "Numero Trabajadores",
    "n de trabajadores": "Numero Trabajadores",
    "no trabajadores": "Numero Trabajadores",
    "trabajadores": "Numero Trabajadores",
    "personas": "Numero Trabajadores",
    "recurso humano": "Numero Trabajadores",

    "horas trabajadas": "Horas",
    "horas en proceso": "Horas",
    "horas de proceso": "Horas",
    "horas": "Horas",

    "esquejes cortados": "Esquejes",
    "corte de esquejes": "Esquejes",
    "corte de semillas": "Esquejes",
    "produccion estimada esquejes": "Esquejes",
    "producción estimada esquejes": "Esquejes",

    "plantas sembradas": "Plantas",
    "plantas": "Plantas",

    "surcos cosechados": "Surcos",
    "surcos": "Surcos",
    "se utilizo maquinaria": "Maquinaria",
    "se utilizó maquinaria": "Maquinaria",
    "maquinaria": "Maquinaria",
    "horas efectivas de maquina": "Horas Maquina",
    "horas efectivas de máquina": "Horas Maquina",
    "horas maquina": "Horas Maquina",
    "horas máquina": "Horas Maquina",
    "produccion total kg": "Produccion Kg",
    "producción total kg": "Produccion Kg",
    "produccion kg": "Produccion Kg",
    "producción kg": "Produccion Kg",
    "descarte kg": "Descarte Kg",

    "kg recibidos": "Kg Recibidos",
    "kg lavados": "Kg Lavados",
    "kg 1ra clase": "Kg 1ra",
    "kg primera clase": "Kg 1ra",
    "kg 1ra": "Kg 1ra",
    "kg 2da clase": "Kg 2da",
    "kg segunda clase": "Kg 2da",
    "kg 2da": "Kg 2da",
    "kg 3ra clase": "Kg 3ra",
    "kg tercera clase": "Kg 3ra",
    "kg 3ra": "Kg 3ra",
    "kg semilla": "Kg Semilla",
    "kg descartados en lavado": "Kg Descarte Lavado",
    "kg descarte lavado": "Kg Descarte Lavado",

    "kg empacados": "Kg Empacados",
    "kg empacados en cajas": "Kg Cajas",
    "kg cajas": "Kg Cajas",
    "kg empacados en sacos": "Kg Sacos",
    "kg sacos": "Kg Sacos",
    "kg empacados en bolsas": "Kg Bolsas",
    "kg bolsas": "Kg Bolsas",

    "toneladas": "Toneladas",
    "toneladas cargadas": "Toneladas",
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
# Estandares operativos
# Manual Operativo CAM - Produccion de Batata - 1 Hectarea
# Version 1.0 - 12 de mayo de 2026
# ---------------------------------------------------------------------------
# NOTA:
# Se mantienen las mismas llaves internas para evitar romper calculos existentes.
# Se agregan llaves adicionales descriptivas donde aplica.

ESTANDARES = {
    "Corte Esquejes": {
        # Manual: 10 personas, 1 dia, 10 jornales, 30.000 esquejes.
        "personas":            10,
        "dias":                1,
        "jornales":            10,
        "esquejes_total":      30000,
        "esquejes_persona_dia": 3000,
        "jornales_maximos":    10,
    },

    "Siembra": {
        # Manual:
        # Ahoyado: 2 personas x 1 dia = 2 jornales.
        # Siembra: 10 personas x 1 dia = 10 jornales.
        # Total: 12 jornales en 1 dia.
        "personas":              12,
        "personas_ahoyado":      2,
        "personas_siembra":      10,
        "dias":                  1,
        "jornales":              12,
        "jornales_ahoyado":      2,
        "jornales_siembra":      10,
        "plantas_total":         30000,
        "plantas_persona_dia":   3000,
    },

    "Cosecha": {
        # Manual:
        # Produccion objetivo: 20 toneladas/ha.
        # Producto comercializable: 17 toneladas.
        # Pre-cosecha: 10 jornales.
        # Cosecha y apoyo: 44 jornales.
        # Total cosecha mecanizada: 54 jornales.
        "personas":                 15,
        "dias":                     2.5,
        "jornales":                 54,
        "jornales_precosecha":      10,
        "jornales_cosecha_apoyo":   44,

        "toneladas_objetivo_dia":   8,
        "kg_objetivo_dia":          8000,

        "produccion_total_ton":      20,
        "produccion_total_kg":       20000,
        "producto_comercial_ton":    17,
        "producto_comercial_kg":     17000,

        "kg_persona_dia":           530,

        "pct_primera":              0.60,
        "pct_segunda":              0.25,
        "pct_tercera":              0.15,
        "pct_comercializable":      0.85,

        # Datos operativos del manual.
        "tractor_dias":             1,
        "tractor_costo_dia":        135000,
        "apoyo_recoleccion_personas": 2,
        "apoyo_recoleccion_dias":     2,
        "apoyo_recoleccion_jornales": 4,
        "seleccion_campo_personas":   10,
        "seleccion_campo_dias":       2.5,
        "seleccion_campo_jornales":   25,
    },

    "Lavado Clasificacion": {
        # En el codigo se conserva el proceso "Lavado Clasificacion",
        # pero el estandar corresponde al proceso de LAVADO del manual.
        # Manual: 17 toneladas comercializables, 13 personas, 2 dias, 26 jornales.
        "personas":                 13,
        "dias":                     2,
        "jornales":                 26,
        "kg_persona_dia":           655,
        "toneladas_base":           17,
        "kg_base":                  17000,

        # Ejemplos del manual.
        "ejemplo_kg_dia_1":          2600,
        "ejemplo_jornales_1":        4,
        "ejemplo_kg_dia_2":          2000,
        "ejemplo_jornales_2":        3,
    },

    "Empaque": {
        # En el codigo se conserva "Empaque",
        # pero el estandar corresponde a CLASIFICACION Y EMPAQUE del manual.
        # Manual: cada jornal empaca 2.700 kg/dia; 3 personas x 1 dia = 3 jornales.
        # Volumen estimado de empaque: 8 toneladas.
        "personas":                 3,
        "dias":                     1,
        "jornales":                 3,
        "kg_persona_dia":           2700,
        "kg_jornal_dia":            2700,
        "volumen_estimado_ton":     8,
        "volumen_estimado_kg":      8000,

        # Se mantiene esta llave para no afectar calculos existentes.
        "pct_empacado_objetivo":    0.95,
    },

    "Cargue Vehiculo": {
        # En el codigo se conserva "Cargue Vehiculo",
        # pero la etiqueta visible corresponde a CARGA AL CAMION.
        # Manual: 880 kg/hora/jornal, equivalente a 44 cajas/hora.
        # Recurso humano: 3 personas x 3 horas = 3 jornales.
        "personas":                 3,
        "horas":                    3,
        "jornales":                 3,
        "kg_hora_jornal":           880,
        "cajas_hora_jornal":        44,

        # Se conserva la referencia de 17 toneladas comercializables del manual
        # para compatibilidad con vistas que usan la llave "toneladas".
        "toneladas":                17,
        "kg_base":                  17000,
    },
}

DOTACION_ESTANDAR = {
    "Corte Esquejes":       10,
    "Siembra":              12,
    "Cosecha":              15,
    "Lavado Clasificacion": 13,
    "Empaque":              3,
    "Cargue Vehiculo":      3,
}

# ---------------------------------------------------------------------------
# Resumen operativo por hectarea
# ---------------------------------------------------------------------------
# Llaves adicionales para que puedan usarse en tarjetas, resumenes o validaciones.
RESUMEN_MANUAL_HA = {
    "produccion_total_ton":       20,
    "produccion_total_kg":        20000,
    "producto_comercial_ton":     17,
    "producto_comercial_kg":      17000,
    "jornales_total":            108,
    "jornales_por_tonelada":     5.4,
    "pct_primera":               0.60,
    "pct_segunda":               0.25,
    "pct_tercera":               0.15,
    "pct_comercializable":       0.85,
}

JORNALES_POR_HECTAREA = {
    "Corte Esquejes":       10,
    "Siembra":              12,
    "Cosecha":              54,
    "Lavado Clasificacion": 26,
    "Empaque":              3,
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

# Manual: producto comercializable = 85%.
UMBRAL_COMERCIAL_OK     = 0.85
UMBRAL_COMERCIAL_ALERTA = 0.75

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
