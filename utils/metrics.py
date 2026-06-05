"""
utils/metrics.py
----------------
[MIGRACION Streamlit -> Dash]
Este modulo NO depende de Streamlit. Se copia tal cual del proyecto original.

Calculos de KPIs con correcciones aplicadas:
- Comercializable = 1ra + 2da + 3ra (3ra SI es comercializable)
- Cumplimiento de cargue basado en promedio por despacho vs estandar 17 t
- Analisis de dotacion: personas requeridas vs asignadas
- Analisis de rentabilidad de maquinaria con factor tiempo
- Deteccion de inconsistencias para pagina de Calidad de Datos

AJUSTE APLICADO:
- dias_operativos ahora cuenta el periodo calendario completo entre la fecha
  mínima y máxima del dataframe filtrado.
- promedio_diario_kpi ahora puede calcular promedios sobre todo el periodo
  calendario, incluyendo días intermedios sin registro como 0, salvo columnas
  configuradas para excluir ceros en ZEROS_EXCLUIDOS_EN_KPI.
- Se corrige normalizacion de Maquinaria para reconocer valores como:
  Si, Sí, si, sí, True, 1, tractor, con maquinaria, mecanizada.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from config.settings import (
    ZEROS_EXCLUIDOS_EN_KPI,
    ESTANDARES,
    DOTACION_ESTANDAR,
    NUMERIC_COLUMNS,
    UMBRAL_CUMPLIMIENTO_OK,
    UMBRAL_CUMPLIMIENTO_ALERTA,
    UMBRAL_PRIMERA_OK,
    UMBRAL_PRIMERA_ALERTA,
    UMBRAL_COMERCIAL_OK,
    UMBRAL_COMERCIAL_ALERTA,
    UMBRAL_PERDIDA_OK,
    UMBRAL_PERDIDA_ALERTA,
    UMBRAL_DOTACION_OK,
    UMBRAL_DOTACION_ALERTA,
    CARGUE_UMBRAL_KG_A_T,
)


# ---------------------------------------------------------------------------
# Helpers numericos
# ---------------------------------------------------------------------------
def safe_div(a, b) -> Optional[float]:
    try:
        if a is None or b is None:
            return None
        if pd.isna(a) or pd.isna(b) or b == 0:
            return None
        return float(a) / float(b)
    except Exception:
        return None


def _normalizar_texto(valor) -> str:
    """
    Normaliza texto para comparaciones robustas:
    - Convierte a minusculas.
    - Elimina espacios extremos.
    - Quita tildes comunes.
    """
    if valor is None or pd.isna(valor):
        return ""

    texto = str(valor).strip().lower()

    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
    }

    for original, nuevo in reemplazos.items():
        texto = texto.replace(original, nuevo)

    return texto


def normalizar_maquinaria(valor) -> str:
    """
    Normaliza el uso de maquinaria.

    Retorna:
        "si" cuando el registro indica uso de maquinaria.
        "no" cuando no hay maquinaria o el valor no es reconocible.

    Esta funcion evita el problema de comparar "Sí" contra "si".
    """
    texto = _normalizar_texto(valor)

    positivos = {
        "si",
        "s",
        "yes",
        "true",
        "1",
        "con maquinaria",
        "maquinaria",
        "maquina",
        "uso maquinaria",
        "usa maquinaria",
        "utilizo maquinaria",
        "utiliza maquinaria",
        "tractor",
        "con tractor",
        "mecanizada",
        "cosecha mecanizada",
    }

    negativos = {
        "no",
        "n",
        "false",
        "0",
        "sin maquinaria",
        "manual",
        "no aplica",
        "na",
        "n/a",
        "",
        "none",
        "nan",
    }

    if texto in positivos:
        return "si"

    if texto in negativos:
        return "no"

    if texto.startswith("si"):
        return "si"

    if texto.startswith("no"):
        return "no"

    if "tractor" in texto:
        return "si"

    if "maquinaria" in texto and "sin" not in texto and "no" not in texto:
        return "si"

    if "mecanizada" in texto:
        return "si"

    return "no"


def promedio_kpi(df: pd.DataFrame, col: str, sheet: str) -> Optional[float]:
    if df is None or df.empty or col not in df.columns:
        return None

    excluir = col in ZEROS_EXCLUIDOS_EN_KPI.get(sheet, [])
    serie = pd.to_numeric(df[col], errors="coerce").dropna()

    if excluir:
        serie = serie.loc[serie != 0]

    if serie.empty:
        return None

    return float(serie.mean())


def suma_kpi(df: pd.DataFrame, col: str) -> float:
    if df is None or df.empty or col not in df.columns:
        return 0.0

    return float(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())


def count_registros(df: pd.DataFrame) -> int:
    if df is None:
        return 0

    return int(len(df))


def count_dias_operativos(df: pd.DataFrame) -> int:
    """
    Cuenta los dias calendario del periodo analizado.

    Antes:
        Contaba unicamente las fechas con registros.

    Ahora:
        Cuenta todos los dias entre la fecha minima y la fecha maxima del
        dataframe filtrado.

    Ejemplo:
        Si hay registros entre el 1 y el 16 de abril, retorna 16 dias,
        aunque solo existan registros en 14 fechas.
    """
    if df is None or df.empty or "Fecha" not in df.columns:
        return 0

    fechas = pd.to_datetime(df["Fecha"], errors="coerce").dropna()

    if fechas.empty:
        return 0

    fecha_min = fechas.dt.normalize().min()
    fecha_max = fechas.dt.normalize().max()

    if pd.isna(fecha_min) or pd.isna(fecha_max):
        return 0

    return int((fecha_max - fecha_min).days + 1)


def _prepare_daily(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    if df is None or df.empty or "Fecha" not in df.columns:
        return pd.DataFrame()

    tmp = df.copy()
    tmp["Fecha"] = pd.to_datetime(tmp["Fecha"], errors="coerce")
    tmp = tmp.dropna(subset=["Fecha"])

    if tmp.empty:
        return tmp

    for col in cols:
        if col in tmp.columns:
            tmp[col] = pd.to_numeric(tmp[col], errors="coerce")

    tmp["_FechaDia"] = tmp["Fecha"].dt.normalize()

    return tmp


def promedio_diario_kpi(df: pd.DataFrame, col: str, sheet: str) -> Optional[float]:
    """
    Calcula el promedio diario sobre el periodo calendario completo.

    Antes:
        Promediaba solo los dias con registros.

    Ahora:
        Construye el rango completo entre fecha minima y fecha maxima,
        rellena dias sin registro con 0 y calcula el promedio sobre
        todo ese periodo.

    Nota:
        Si una columna esta configurada en ZEROS_EXCLUIDOS_EN_KPI,
        se mantiene la regla de excluir ceros para evitar distorsiones.
    """
    tmp = _prepare_daily(df, [col])

    if tmp.empty or col not in tmp.columns:
        return promedio_kpi(df, col, sheet)

    serie = tmp.groupby("_FechaDia")[col].sum()
    serie = pd.to_numeric(serie, errors="coerce").fillna(0)

    if serie.empty:
        return None

    fecha_min = serie.index.min()
    fecha_max = serie.index.max()

    if pd.isna(fecha_min) or pd.isna(fecha_max):
        return None

    rango_completo = pd.date_range(start=fecha_min, end=fecha_max, freq="D")
    serie = serie.reindex(rango_completo, fill_value=0)

    if col in ZEROS_EXCLUIDOS_EN_KPI.get(sheet, []):
        serie = serie.loc[serie != 0]

    if serie.empty:
        return None

    return float(serie.mean())


def productividad_persona_dia(df: pd.DataFrame, value_col: str) -> Optional[float]:
    if df is None or df.empty or {"Fecha", value_col, "Numero Trabajadores"} - set(df.columns):
        return None

    tmp = _prepare_daily(df, [value_col, "Numero Trabajadores"])

    if tmp.empty:
        return None

    tmp = tmp[(tmp[value_col] > 0) & (tmp["Numero Trabajadores"] > 0)]

    if tmp.empty:
        return None

    daily = (
        tmp.groupby("_FechaDia", as_index=False)
        .agg(
            **{
                value_col: (value_col, "sum"),
                "Numero Trabajadores": ("Numero Trabajadores", "sum"),
            }
        )
    )

    daily = daily[daily["Numero Trabajadores"] > 0]

    if daily.empty:
        return None

    ratios = daily[value_col] / daily["Numero Trabajadores"]
    ratios = ratios.replace([np.inf, -np.inf], np.nan).dropna()

    if ratios.empty:
        return None

    return float(ratios.mean())


# ---------------------------------------------------------------------------
# Semaforizacion
# ---------------------------------------------------------------------------
def nivel_cumplimiento(pct: Optional[float]) -> str:
    if pct is None or pd.isna(pct):
        return "na"

    if pct >= UMBRAL_CUMPLIMIENTO_OK:
        return "ok"

    if pct >= UMBRAL_CUMPLIMIENTO_ALERTA:
        return "alerta"

    return "critico"


def nivel_primera(pct: Optional[float]) -> str:
    if pct is None or pd.isna(pct):
        return "na"

    if pct >= UMBRAL_PRIMERA_OK:
        return "ok"

    if pct >= UMBRAL_PRIMERA_ALERTA:
        return "alerta"

    return "critico"


def nivel_comercial(pct: Optional[float]) -> str:
    if pct is None or pd.isna(pct):
        return "na"

    if pct >= UMBRAL_COMERCIAL_OK:
        return "ok"

    if pct >= UMBRAL_COMERCIAL_ALERTA:
        return "alerta"

    return "critico"


def nivel_perdida(pct: Optional[float]) -> str:
    if pct is None or pd.isna(pct):
        return "na"

    if pct <= UMBRAL_PERDIDA_OK:
        return "ok"

    if pct <= UMBRAL_PERDIDA_ALERTA:
        return "alerta"

    return "critico"


def nivel_dotacion(desviacion_pct: Optional[float]) -> str:
    if desviacion_pct is None or pd.isna(desviacion_pct):
        return "na"

    abs_desv = abs(desviacion_pct)

    if abs_desv <= UMBRAL_DOTACION_OK:
        return "ok"

    if abs_desv <= UMBRAL_DOTACION_ALERTA:
        return "alerta"

    return "critico"


# ---------------------------------------------------------------------------
# KPIs por proceso
# ---------------------------------------------------------------------------
def kpis_corte(df: pd.DataFrame) -> dict:
    sheet = "Corte Esquejes"

    total_esquejes = suma_kpi(df, "Esquejes")
    total_horas = suma_kpi(df, "Horas")
    registros = count_registros(df)
    dias_operativos = count_dias_operativos(df)
    esquejes_prom_dia = promedio_diario_kpi(df, "Esquejes", sheet)

    prod_persona_dia = productividad_persona_dia(df, "Esquejes")

    estandar = ESTANDARES[sheet]["esquejes_persona_dia"]
    cumpl_prod = safe_div(prod_persona_dia, estandar)

    return {
        "total_esquejes": total_esquejes,
        "total_horas": total_horas,
        "esquejes_prom_dia": esquejes_prom_dia,
        "prod_persona_dia": prod_persona_dia,
        "estandar_persona": estandar,
        "cumpl_prod": cumpl_prod,
        "nivel_cumpl": nivel_cumplimiento(cumpl_prod),
        "dias_operativos": dias_operativos,
        "registros": registros,
        "jornadas": dias_operativos,
    }


def kpis_siembra(df: pd.DataFrame) -> dict:
    sheet = "Siembra"

    total_plantas = suma_kpi(df, "Plantas")
    total_horas = suma_kpi(df, "Horas")
    registros = count_registros(df)
    dias_operativos = count_dias_operativos(df)
    plantas_prom = promedio_diario_kpi(df, "Plantas", sheet)

    prod_persona_dia = productividad_persona_dia(df, "Plantas")

    estandar = ESTANDARES[sheet]["plantas_persona_dia"]
    cumpl_prod = safe_div(prod_persona_dia, estandar)

    return {
        "total_plantas": total_plantas,
        "total_horas": total_horas,
        "plantas_prom_dia": plantas_prom,
        "prod_persona_dia": prod_persona_dia,
        "estandar_persona": estandar,
        "cumpl_prod": cumpl_prod,
        "nivel_cumpl": nivel_cumplimiento(cumpl_prod),
        "dias_operativos": dias_operativos,
        "registros": registros,
        "jornadas": dias_operativos,
    }


def kpis_cosecha(df: pd.DataFrame) -> dict:
    sheet = "Cosecha"

    total_kg = suma_kpi(df, "Produccion Kg")
    total_descarte = suma_kpi(df, "Descarte Kg")
    total_horas = suma_kpi(df, "Horas")
    registros = count_registros(df)
    dias_operativos = count_dias_operativos(df)

    prom_kg_jornada = promedio_diario_kpi(df, "Produccion Kg", sheet)
    prod_persona_dia = productividad_persona_dia(df, "Produccion Kg")

    estandar = ESTANDARES[sheet]["kg_persona_dia"]
    cumpl_prod = safe_div(prod_persona_dia, estandar)

    meta_ton_dia = ESTANDARES[sheet]["toneladas_objetivo_dia"]
    meta_ton_periodo = (meta_ton_dia * dias_operativos) if dias_operativos > 0 else None
    cumplimiento_meta_periodo = safe_div(total_kg / 1000.0, meta_ton_periodo)

    pct_descarte = (
        safe_div(total_descarte, total_kg + total_descarte)
        if (total_kg + total_descarte) > 0
        else None
    )

    return {
        "total_kg": total_kg,
        "total_descarte": total_descarte,
        "pct_descarte": pct_descarte,
        "total_horas": total_horas,
        "prom_kg_jornada": prom_kg_jornada,
        "prod_persona_dia": prod_persona_dia,
        "estandar_persona": estandar,
        "meta_ton_dia": meta_ton_dia,
        "meta_ton_periodo": meta_ton_periodo,
        "cumpl_meta_periodo": cumplimiento_meta_periodo,
        "cumpl_prod": cumpl_prod,
        "nivel_cumpl": nivel_cumplimiento(cumpl_prod),
        "nivel_descarte": nivel_perdida(pct_descarte),
        "dias_operativos": dias_operativos,
        "registros": registros,
        "jornadas": dias_operativos,
    }


def analisis_maquinaria(df: pd.DataFrame) -> dict:
    """
    Rentabilidad de maquinaria: 3 lentes de comparacion.
    - kg promedio por jornada
    - kg por hora trabajada
    - kg por hora-persona

    Correccion aplicada:
    Normaliza Maquinaria para reconocer Si, Sí, True, 1, tractor,
    con maquinaria, mecanizada, etc.
    """
    vacio = {
        "kg_promedio": None,
        "kg_por_hora": None,
        "kg_por_hora_persona": None,
        "jornadas": 0,
        "total_kg": 0.0,
    }

    resultado = {
        "con_maq": dict(vacio),
        "sin_maq": dict(vacio),
    }

    if df is None or df.empty or "Maquinaria" not in df.columns:
        return resultado

    d = df.copy()

    if "Produccion Kg" not in d.columns:
        return resultado

    for c in ("Produccion Kg", "Horas", "Numero Trabajadores"):
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")

    if "Horas" not in d.columns:
        d["Horas"] = 0.0

    if "Numero Trabajadores" not in d.columns:
        d["Numero Trabajadores"] = 0.0

    d = d[d["Produccion Kg"].fillna(0) > 0]

    if d.empty:
        return resultado

    d["_MaquinariaNorm"] = d["Maquinaria"].apply(normalizar_maquinaria)

    for valor_maq, key in (("si", "con_maq"), ("no", "sin_maq")):
        sub = d[d["_MaquinariaNorm"] == valor_maq]

        if sub.empty:
            resultado[key] = dict(vacio)
            continue

        if "Fecha" in sub.columns:
            daily = _prepare_daily(sub, ["Produccion Kg", "Horas", "Numero Trabajadores"])
        else:
            daily = pd.DataFrame()

        if not daily.empty and {"Produccion Kg", "Horas", "Numero Trabajadores"}.issubset(daily.columns):
            daily["Horas"] = pd.to_numeric(daily["Horas"], errors="coerce").fillna(0)
            daily["Numero Trabajadores"] = pd.to_numeric(
                daily["Numero Trabajadores"], errors="coerce"
            ).fillna(0)
            daily["Produccion Kg"] = pd.to_numeric(
                daily["Produccion Kg"], errors="coerce"
            ).fillna(0)

            daily["HoraPersona"] = daily["Horas"] * daily["Numero Trabajadores"]

            grouped = (
                daily.groupby("_FechaDia", as_index=False)
                .agg(
                    **{
                        "Produccion Kg": ("Produccion Kg", "sum"),
                        "Horas": ("Horas", "sum"),
                        "HoraPersona": ("HoraPersona", "sum"),
                    }
                )
            )

            kg_total = float(grouped["Produccion Kg"].sum())
            kg_prom = float(grouped["Produccion Kg"].mean())
            horas_tot = float(grouped["Horas"].sum())
            hp = float(grouped["HoraPersona"].sum())
            jornadas = int(len(grouped))

        else:
            kg_total = float(pd.to_numeric(sub["Produccion Kg"], errors="coerce").fillna(0).sum())
            kg_prom = float(pd.to_numeric(sub["Produccion Kg"], errors="coerce").fillna(0).mean())
            horas_tot = float(pd.to_numeric(sub["Horas"], errors="coerce").fillna(0).sum())
            hp = float(
                (
                    pd.to_numeric(sub["Horas"], errors="coerce").fillna(0)
                    * pd.to_numeric(sub["Numero Trabajadores"], errors="coerce").fillna(0)
                ).sum()
            )
            jornadas = int(len(sub))

        kg_hora = (kg_total / horas_tot) if horas_tot > 0 else None
        kg_hp = float(kg_total / hp) if hp > 0 else None

        resultado[key] = {
            "kg_promedio": kg_prom,
            "kg_por_hora": float(kg_hora) if kg_hora is not None else None,
            "kg_por_hora_persona": kg_hp,
            "jornadas": jornadas,
            "total_kg": kg_total,
        }

    return resultado


def kpis_lavado(df: pd.DataFrame) -> dict:
    sheet = "Lavado Clasificacion"

    total_recibido = suma_kpi(df, "Kg Recibidos")
    total_lavado = suma_kpi(df, "Kg Lavados")
    total_1 = suma_kpi(df, "Kg 1ra")
    total_2 = suma_kpi(df, "Kg 2da")
    total_3 = suma_kpi(df, "Kg 3ra")
    total_semilla = suma_kpi(df, "Kg Semilla")
    total_descarte = suma_kpi(df, "Kg Descarte Lavado")
    registros = count_registros(df)
    dias_operativos = count_dias_operativos(df)

    total_clasif = total_1 + total_2 + total_3 + total_semilla
    total_salida = total_clasif + total_descarte

    pct_1 = safe_div(total_1, total_clasif)
    pct_2 = safe_div(total_2, total_clasif)
    pct_3 = safe_div(total_3, total_clasif)
    pct_semilla = safe_div(total_semilla, total_clasif)

    pct_comercial = safe_div(total_1 + total_2 + total_3, total_salida)

    pct_perdida = safe_div(total_descarte, total_recibido) if total_recibido > 0 else None

    prod_persona_dia = productividad_persona_dia(df, "Kg Lavados")

    estandar = ESTANDARES[sheet]["kg_persona_dia"]
    cumpl_prod = safe_div(prod_persona_dia, estandar)

    return {
        "total_recibido": total_recibido,
        "total_lavado": total_lavado,
        "total_1": total_1,
        "total_2": total_2,
        "total_3": total_3,
        "total_semilla": total_semilla,
        "total_descarte": total_descarte,
        "pct_1": pct_1,
        "pct_2": pct_2,
        "pct_3": pct_3,
        "pct_semilla": pct_semilla,
        "pct_comercial": pct_comercial,
        "pct_perdida": pct_perdida,
        "prod_persona_dia": prod_persona_dia,
        "estandar_persona": estandar,
        "cumpl_prod": cumpl_prod,
        "nivel_cumpl": nivel_cumplimiento(cumpl_prod),
        "nivel_primera": nivel_primera(pct_1),
        "nivel_comercial": nivel_comercial(pct_comercial),
        "nivel_perdida": nivel_perdida(pct_perdida),
        "dias_operativos": dias_operativos,
        "registros": registros,
        "jornadas": dias_operativos,
    }


def kpis_empaque(df: pd.DataFrame) -> dict:
    total_recibido = suma_kpi(df, "Kg Recibidos")
    total_empacado = suma_kpi(df, "Kg Empacados")
    total_cajas = suma_kpi(df, "Kg Cajas")
    total_sacos = suma_kpi(df, "Kg Sacos")
    total_bolsas = suma_kpi(df, "Kg Bolsas")
    registros = count_registros(df)
    dias_operativos = count_dias_operativos(df)

    pct_empacado = safe_div(total_empacado, total_recibido) if total_recibido > 0 else None

    estandar_pct = ESTANDARES["Empaque"]["pct_empacado_objetivo"]
    cumpl_empacado = safe_div(pct_empacado, estandar_pct)

    total_tipos = total_cajas + total_sacos + total_bolsas
    pct_cajas = safe_div(total_cajas, total_tipos)
    pct_sacos = safe_div(total_sacos, total_tipos)
    pct_bolsas = safe_div(total_bolsas, total_tipos)

    return {
        "total_recibido": total_recibido,
        "total_empacado": total_empacado,
        "pct_empacado": pct_empacado,
        "total_cajas": total_cajas,
        "total_sacos": total_sacos,
        "total_bolsas": total_bolsas,
        "pct_cajas": pct_cajas,
        "pct_sacos": pct_sacos,
        "pct_bolsas": pct_bolsas,
        "estandar_pct": estandar_pct,
        "cumpl_empacado": cumpl_empacado,
        "nivel_cumpl": nivel_cumplimiento(cumpl_empacado),
        "dias_operativos": dias_operativos,
        "registros": registros,
        "jornadas": dias_operativos,
    }


def kpis_cargue(df: pd.DataFrame) -> dict:
    """
    Despues de _sanear_cargue, la columna Toneladas ya esta en t.
    Cumplimiento: promedio de t por despacho vs estandar 17 t.
    """
    sheet = "Cargue Vehiculo"

    total_ton = suma_kpi(df, "Toneladas")
    total_cajas = suma_kpi(df, "Cajas")
    total_sacos = suma_kpi(df, "Sacos")
    total_bolsas = suma_kpi(df, "Bolsas")
    total_horas = suma_kpi(df, "Horas")
    despachos = count_registros(df)
    dias_operativos = count_dias_operativos(df)

    ton_prom = promedio_kpi(df, "Toneladas", sheet)

    estandar_ton = ESTANDARES[sheet]["toneladas"]
    cumpl_ton = safe_div(ton_prom, estandar_ton)

    return {
        "total_toneladas": total_ton,
        "total_cajas": total_cajas,
        "total_sacos": total_sacos,
        "total_bolsas": total_bolsas,
        "total_horas": total_horas,
        "despachos": despachos,
        "dias_operativos": dias_operativos,
        "ton_promedio": ton_prom,
        "estandar_ton": estandar_ton,
        "cumpl_ton": cumpl_ton,
        "nivel_cumpl": nivel_cumplimiento(cumpl_ton),
    }


# ---------------------------------------------------------------------------
# Analisis de dotacion
# ---------------------------------------------------------------------------
def analisis_dotacion(df: pd.DataFrame, proceso: str) -> dict:
    vacio = {
        "estandar": DOTACION_ESTANDAR.get(proceso),
        "promedio_real": None,
        "desviacion_pct": None,
        "desviacion_abs": None,
        "jornadas_sub": 0,
        "jornadas_sobre": 0,
        "jornadas_ok": 0,
        "total_jornadas": 0,
        "nivel": "na",
        "diagnostico": "sin_datos",
    }

    if df is None or df.empty or "Numero Trabajadores" not in df.columns:
        return vacio

    estandar = DOTACION_ESTANDAR.get(proceso)

    if estandar is None:
        return vacio

    if "Fecha" in df.columns:
        tmp = _prepare_daily(df, ["Numero Trabajadores"])

        if not tmp.empty:
            serie = (
                tmp.loc[tmp["Numero Trabajadores"] > 0]
                .groupby("_FechaDia")["Numero Trabajadores"]
                .sum()
            )
        else:
            serie = pd.Series(dtype="float64")
    else:
        serie = pd.to_numeric(df["Numero Trabajadores"], errors="coerce").dropna()
        serie = serie[serie > 0]

    if serie.empty:
        return vacio

    promedio_real = float(serie.mean())
    desv_abs = promedio_real - estandar
    desv_pct = desv_abs / estandar

    tol_inf = estandar * 0.80
    tol_sup = estandar * 1.20

    jornadas_sub = int((serie < tol_inf).sum())
    jornadas_sobre = int((serie > tol_sup).sum())
    jornadas_ok = int(((serie >= tol_inf) & (serie <= tol_sup)).sum())

    nvl = nivel_dotacion(desv_pct)

    if desv_pct < -UMBRAL_DOTACION_OK:
        diag = "subcontratacion"
    elif desv_pct > UMBRAL_DOTACION_OK:
        diag = "sobrecontratacion"
    else:
        diag = "alineado"

    return {
        "estandar": estandar,
        "promedio_real": promedio_real,
        "desviacion_pct": desv_pct,
        "desviacion_abs": desv_abs,
        "jornadas_sub": jornadas_sub,
        "jornadas_sobre": jornadas_sobre,
        "jornadas_ok": jornadas_ok,
        "total_jornadas": int(len(serie)),
        "nivel": nvl,
        "diagnostico": diag,
    }


def interpretacion_dotacion(dot: dict, proceso: str) -> str:
    """Genera el texto ejecutivo sobre el estado de la dotacion."""
    if dot is None or dot.get("promedio_real") is None:
        return (
            "Aún no hay suficientes registros para evaluar la asignación "
            "de personal en este proceso."
        )

    dp = dot["desviacion_pct"]

    if dp is None:
        return "Sin datos comparables."

    if dp < -0.10:
        return (
            f"Se está operando con menos personas de las requeridas "
            f"({dp * 100:.1f}% por debajo del estándar de {dot['estandar']} personas). "
            f"Riesgo de <b>subcontratación</b>: posible extensión de jornadas, "
            f"retrasos y presión sobre el equipo. Evaluar refuerzo de cuadrilla."
        )

    if dp > 0.10:
        return (
            f"Se está operando con más personas de las requeridas "
            f"(+{dp * 100:.1f}% por encima del estándar de {dot['estandar']} personas). "
            f"Riesgo de <b>sobrecontratación</b>: sobrecosto de mano de obra sin "
            f"ganancia proporcional en productividad. Revisar si responde a "
            f"complejidad real o a planeación conservadora."
        )

    return (
        f"La asignación está alineada con el estándar ({dp * 100:+.1f}% de "
        f"desviación respecto a {dot['estandar']} personas). Dotación eficiente."
    )


# ---------------------------------------------------------------------------
# Deteccion de inconsistencias
# ---------------------------------------------------------------------------
def detectar_inconsistencias(data: dict) -> pd.DataFrame:
    """Barrido de reglas de validacion sobre todas las hojas."""
    flags = []

    # 0. Reglas genericas por proceso: fecha invalida / valores negativos
    for proceso, df in (data or {}).items():
        if df is None or df.empty:
            continue

        if "Fecha" in df.columns:
            fechas = pd.to_datetime(df["Fecha"], errors="coerce")
            mask = fechas.isna()

            for idx in df[mask].index:
                flags.append(
                    {
                        "Proceso": proceso,
                        "Fecha": None,
                        "Severidad": "Media",
                        "Regla": "Fecha faltante o invalida",
                        "Valor": "No se pudo interpretar la fecha del registro",
                        "Accion sugerida": "Corregir fecha para habilitar filtros y analisis temporales",
                    }
                )

        for col in NUMERIC_COLUMNS.get(proceso, []):
            if col not in df.columns:
                continue

            serie = pd.to_numeric(df[col], errors="coerce")
            mask = serie < 0

            for idx in df[mask].index:
                flags.append(
                    {
                        "Proceso": proceso,
                        "Fecha": df.loc[idx, "Fecha"] if "Fecha" in df.columns else None,
                        "Severidad": "Alta",
                        "Regla": f"Valor negativo en {col}",
                        "Valor": f"{serie[idx]:.2f}",
                        "Accion sugerida": "Revisar captura; el proceso no admite valores negativos",
                    }
                )

    # 1. Lavado: kg lavados > kg recibidos
    df = data.get("Lavado Clasificacion", pd.DataFrame())

    if not df.empty and {"Kg Recibidos", "Kg Lavados"}.issubset(df.columns):
        rec = pd.to_numeric(df["Kg Recibidos"], errors="coerce")
        lav = pd.to_numeric(df["Kg Lavados"], errors="coerce")

        mask = (lav > rec * 1.01) & rec.notna() & lav.notna()

        for idx in df[mask].index:
            flags.append(
                {
                    "Proceso": "Lavado",
                    "Fecha": df.loc[idx, "Fecha"] if "Fecha" in df.columns else None,
                    "Severidad": "Alta",
                    "Regla": "Kg lavados excede kg recibidos",
                    "Valor": f"Recibidos: {rec[idx]:.1f} | Lavados: {lav[idx]:.1f}",
                    "Accion sugerida": "Revisar captura del formulario",
                }
            )

    # 2. Lavado: clasificado > lavado
    if not df.empty and {"Kg Lavados", "Kg 1ra", "Kg 2da", "Kg 3ra", "Kg Semilla"}.issubset(df.columns):
        lav = pd.to_numeric(df["Kg Lavados"], errors="coerce").fillna(0)

        clas = (
            pd.to_numeric(df["Kg 1ra"], errors="coerce").fillna(0)
            + pd.to_numeric(df["Kg 2da"], errors="coerce").fillna(0)
            + pd.to_numeric(df["Kg 3ra"], errors="coerce").fillna(0)
            + pd.to_numeric(df["Kg Semilla"], errors="coerce").fillna(0)
        )

        mask = (clas > lav * 1.01) & (lav > 0)

        for idx in df[mask].index:
            flags.append(
                {
                    "Proceso": "Lavado",
                    "Fecha": df.loc[idx, "Fecha"] if "Fecha" in df.columns else None,
                    "Severidad": "Alta",
                    "Regla": "Suma clasificada excede kg lavados",
                    "Valor": f"Lavados: {lav[idx]:.1f} | Clasificado: {clas[idx]:.1f}",
                    "Accion sugerida": "Revisar distribucion de calidades",
                }
            )

    # 3. Cargue: valor en t sospechosamente alto
    df = data.get("Cargue Vehiculo", pd.DataFrame())

    if not df.empty and "Unidad Origen" in df.columns:
        mask = df["Unidad Origen"].astype(str).str.contains("kg", na=False)

        for idx in df[mask].index:
            flags.append(
                {
                    "Proceso": "Cargue",
                    "Fecha": (
                        df.loc[idx, "Fecha"]
                        if "Fecha" in df.columns
                        else df.loc[idx, "Timestamp"]
                        if "Timestamp" in df.columns
                        else None
                    ),
                    "Severidad": "Media",
                    "Regla": "Valor digitado en kg convertido a t automaticamente",
                    "Valor": f"{df.loc[idx, 'Toneladas']:.3f} t",
                    "Accion sugerida": "Ajustar formulario: etiquetar como 'Kilogramos'",
                }
            )

    # 4. Cosecha: trabajadores = 0 con produccion > 0
    df = data.get("Cosecha", pd.DataFrame())

    if not df.empty and {"Numero Trabajadores", "Produccion Kg"}.issubset(df.columns):
        trab = pd.to_numeric(df["Numero Trabajadores"], errors="coerce").fillna(0)
        prod = pd.to_numeric(df["Produccion Kg"], errors="coerce").fillna(0)

        mask = (trab == 0) & (prod > 0)

        for idx in df[mask].index:
            flags.append(
                {
                    "Proceso": "Cosecha",
                    "Fecha": df.loc[idx, "Fecha"] if "Fecha" in df.columns else None,
                    "Severidad": "Media",
                    "Regla": "Produccion registrada sin trabajadores",
                    "Valor": f"{prod[idx]:.1f} kg con 0 personas",
                    "Accion sugerida": "Completar numero de trabajadores",
                }
            )

    # 5. Cosecha: produccion > 0 con horas = 0
    if not df.empty and {"Horas", "Produccion Kg"}.issubset(df.columns):
        hs = pd.to_numeric(df["Horas"], errors="coerce").fillna(0)
        pr = pd.to_numeric(df["Produccion Kg"], errors="coerce").fillna(0)

        mask = (hs == 0) & (pr > 0)

        for idx in df[mask].index:
            flags.append(
                {
                    "Proceso": "Cosecha",
                    "Fecha": df.loc[idx, "Fecha"] if "Fecha" in df.columns else None,
                    "Severidad": "Media",
                    "Regla": "Produccion registrada sin horas trabajadas",
                    "Valor": f"{pr[idx]:.1f} kg en 0 horas",
                    "Accion sugerida": "Completar horas en proceso",
                }
            )

    # 6. Cosecha: maquinaria = Si con horas maquina = 0
    if not df.empty and {"Maquinaria", "Horas Maquina"}.issubset(df.columns):
        maq = df["Maquinaria"].apply(normalizar_maquinaria)
        hm = pd.to_numeric(df["Horas Maquina"], errors="coerce").fillna(0)

        mask = (maq == "si") & (hm == 0)

        for idx in df[mask].index:
            flags.append(
                {
                    "Proceso": "Cosecha",
                    "Fecha": df.loc[idx, "Fecha"] if "Fecha" in df.columns else None,
                    "Severidad": "Baja",
                    "Regla": "Uso de maquinaria declarado sin horas maquina",
                    "Valor": "Maquinaria: Si, Horas maquina: 0",
                    "Accion sugerida": "Completar horas efectivas de maquina",
                }
            )

    # 7. Empaque: kg empacados > kg recibidos
    df = data.get("Empaque", pd.DataFrame())

    if not df.empty and {"Kg Recibidos", "Kg Empacados"}.issubset(df.columns):
        rec = pd.to_numeric(df["Kg Recibidos"], errors="coerce")
        emp = pd.to_numeric(df["Kg Empacados"], errors="coerce")

        mask = (emp > rec * 1.01) & rec.notna() & emp.notna()

        for idx in df[mask].index:
            flags.append(
                {
                    "Proceso": "Empaque",
                    "Fecha": df.loc[idx, "Fecha"] if "Fecha" in df.columns else None,
                    "Severidad": "Alta",
                    "Regla": "Kg empacados excede kg recibidos",
                    "Valor": f"Recibidos: {rec[idx]:.1f} | Empacados: {emp[idx]:.1f}",
                    "Accion sugerida": "Revisar captura del formulario",
                }
            )

    if not flags:
        return pd.DataFrame(
            columns=[
                "Proceso",
                "Fecha",
                "Severidad",
                "Regla",
                "Valor",
                "Accion sugerida",
            ]
        )

    return pd.DataFrame(flags)
