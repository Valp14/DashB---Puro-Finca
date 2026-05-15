"""
services/supabase_data.py
-------------------------
Capa de lectura de Supabase.

Convierte las tablas operativas reales de Supabase al formato legacy que ya
usan los dashboards actuales. De esta forma el sistema migra a Supabase sin
romper las páginas existentes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from config.settings import PROCESOS
from services.supabase_client import get_supabase_client, supabase_is_configured


TABLE_MAP = {
    "Corte Esquejes": "form_corte_esquejes",
    "Siembra": "form_siembra",
    "Cosecha": "form_cosecha",
    "Lavado Clasificacion": "form_lavado_clasificacion",
    "Empaque": "form_empaque",
    "Cargue Vehiculo": "form_despacho",
}


def _empty_store() -> dict[str, list[dict[str, Any]]]:
    return {p: [] for p in PROCESOS}


def _safe_response_data(resp: Any) -> list[dict[str, Any]]:
    data = getattr(resp, "data", None)
    return data if isinstance(data, list) else []


def _fetch_table(table: str, columns: str = "*") -> list[dict[str, Any]]:
    client = get_supabase_client()
    # Rango amplio para evitar el límite por defecto si crecen los registros.
    resp = client.table(table).select(columns).range(0, 9999).execute()
    return _safe_response_data(resp)


def _catalog_lookup(table: str, label_col: str) -> dict[str, str]:
    try:
        rows = _fetch_table(table, f"id,{label_col}")
    except Exception:
        return {}
    return {str(r.get("id")): str(r.get(label_col) or "") for r in rows if r.get("id")}


def load_catalogs() -> dict[str, dict[str, str]]:
    """Trae catálogos básicos para reemplazar IDs por nombres legibles."""
    return {
        "fincas": _catalog_lookup("fincas", "nombre"),
        "proyectos": _catalog_lookup("proyectos", "nombre"),
        "lotes": _catalog_lookup("lotes", "codigo"),
        "clientes": _catalog_lookup("clientes", "nombre"),
        "destinos": _catalog_lookup("destinos", "nombre"),
    }


def _name(catalogs: dict[str, dict[str, str]], catalog: str, value: Any) -> str:
    if value is None:
        return ""
    return catalogs.get(catalog, {}).get(str(value), str(value))


def _base_row(row: dict[str, Any], catalogs: dict[str, dict[str, str]]) -> dict[str, Any]:
    return {
        "Timestamp": row.get("creado_en") or row.get("fecha"),
        "Fecha": row.get("fecha"),
        "Finca": _name(catalogs, "fincas", row.get("finca_id")),
        "Proyecto": _name(catalogs, "proyectos", row.get("proyecto_id")),
        "Lote": _name(catalogs, "lotes", row.get("lote_id")),
        "Observaciones": row.get("observaciones") or "",
        "Estado Validacion": row.get("estado_validacion") or "",
        "Requiere Revision": row.get("requiere_revision"),
        "Fuente": row.get("fuente_carga") or "Supabase",
    }


def _records_to_legacy(proceso: str, rows: list[dict[str, Any]], catalogs: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in rows:
        item = _base_row(r, catalogs)

        if proceso == "Corte Esquejes":
            item.update({
                "Esquejes": r.get("cantidad_esquejes"),
                "Numero Trabajadores": r.get("numero_trabajadores"),
                "Horas": r.get("horas_trabajadas"),
            })

        elif proceso == "Siembra":
            item.update({
                "Plantas": r.get("cantidad_sembrada"),
                "Numero Trabajadores": r.get("numero_trabajadores"),
                "Horas": r.get("horas_trabajadas"),
            })

        elif proceso == "Cosecha":
            item.update({
                "Surcos": r.get("surcos_cosechados"),
                "Numero Trabajadores": r.get("numero_trabajadores"),
                "Horas": r.get("horas_trabajadas"),
                "Maquinaria": "Sí" if r.get("uso_maquinaria") else "No",
                "Horas Maquina": r.get("horas_maquina"),
                "Produccion Kg": r.get("produccion_total_kg"),
                "Descarte Kg": r.get("kg_descarte"),
                "Kg 1ra": r.get("kg_primera"),
                "Kg 2da": r.get("kg_segunda"),
                "Kg 3ra": r.get("kg_tercera"),
                "Kg Semilla": r.get("kg_semilla"),
            })

        elif proceso == "Lavado Clasificacion":
            item.update({
                "Kg Recibidos": r.get("kg_recibidos"),
                "Kg Lavados": r.get("kg_lavados"),
                "Kg 1ra": r.get("kg_primera_lavada"),
                "Kg 2da": r.get("kg_segunda"),
                "Kg 3ra": r.get("kg_tercera"),
                "Kg Semilla": r.get("kg_semilla"),
                "Kg Descarte Lavado": r.get("kg_descarte"),
                "Numero Trabajadores": r.get("numero_trabajadores"),
                "Horas": r.get("horas_proceso"),
            })

        elif proceso == "Empaque":
            item.update({
                "Kg Recibidos": r.get("kg_recibidos_total"),
                "Kg Empacados": r.get("kg_empacados_total"),
                "Kg Cajas": r.get("kg_cajas"),
                "Kg Sacos": r.get("kg_sacos"),
                "Kg Bolsas": r.get("kg_bolsas"),
                "Cajas": r.get("unidades_cajas"),
                "Numero Trabajadores": r.get("numero_trabajadores"),
                "Horas": r.get("horas_trabajadas"),
            })

        elif proceso == "Cargue Vehiculo":
            raw = r.get("toneladas_o_kg") or 0
            try:
                raw_num = float(raw)
            except Exception:
                raw_num = 0.0
            # La base actual registró valores en kg aunque la columna histórica diga toneladas.
            toneladas = raw_num / 1000 if raw_num > 100 else raw_num
            item.update({
                "Cliente": _name(catalogs, "clientes", r.get("cliente_id")) or r.get("cliente_texto") or "",
                "Destino": _name(catalogs, "destinos", r.get("destino_id")) or r.get("destino_texto") or "",
                "Placa": r.get("placa_vehiculo"),
                "Toneladas": toneladas,
                "Kg Despachados": raw_num,
                "Cajas": r.get("cajas"),
                "Sacos": r.get("sacos"),
                "Bolsas": r.get("bolsas"),
                "Numero Trabajadores": r.get("numero_trabajadores"),
                "Horas": r.get("horas_trabajadas"),
            })

        out.append(item)
    return out


def _attach_despacho_totals(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return rows

    ids = [str(r.get("id")) for r in rows if r.get("id")]
    if not ids:
        return rows

    try:
        client = get_supabase_client()
        resp = (
            client
            .table("form_despacho_detalle")
            .select("despacho_id,presentacion,unidades,kg_despachados")
            .in_("despacho_id", ids)
            .range(0, 9999)
            .execute()
        )
        detalles = _safe_response_data(resp)
    except Exception:
        return rows

    totals: dict[str, dict[str, float]] = {}
    for d in detalles:
        did = str(d.get("despacho_id") or "")
        if not did:
            continue
        acc = totals.setdefault(did, {"kg": 0.0, "cajas": 0.0, "sacos": 0.0, "bolsas": 0.0})
        try:
            kg = float(d.get("kg_despachados") or 0)
        except Exception:
            kg = 0.0
        try:
            unidades = float(d.get("unidades") or 0)
        except Exception:
            unidades = 0.0
        acc["kg"] += kg
        presentacion = str(d.get("presentacion") or "").lower()
        if presentacion == "caja":
            acc["cajas"] += unidades
        elif presentacion == "saco":
            acc["sacos"] += unidades
        elif presentacion == "bolsa":
            acc["bolsas"] += unidades

    enriched = []
    for row in rows:
        item = dict(row)
        total = totals.get(str(row.get("id") or ""))
        if total:
            item["toneladas_o_kg"] = total["kg"]
            item["cajas"] = total["cajas"]
            item["sacos"] = total["sacos"]
            item["bolsas"] = total["bolsas"]
        enriched.append(item)
    return enriched


def load_operational_store() -> dict[str, list[dict[str, Any]]]:
    """Carga todas las tablas operativas de Supabase en formato dcc.Store."""
    if not supabase_is_configured():
        return _empty_store()

    try:
        catalogs = load_catalogs()
        store = _empty_store()
        for proceso, table in TABLE_MAP.items():
            rows = _fetch_table(table)
            if proceso == "Cargue Vehiculo":
                rows = _attach_despacho_totals(rows)
            store[proceso] = _records_to_legacy(proceso, rows, catalogs)
        return store
    except Exception as exc:
        # La UI usa este mensaje para mostrar el estado sin romper la app.
        store = _empty_store()
        store["_supabase_error"] = str(exc)
        return store


def load_user_operational_store(email: str | None) -> dict[str, list[dict[str, Any]]]:
    """Carga solo registros creados por el usuario de la app."""
    if not supabase_is_configured() or not email:
        return _empty_store()

    try:
        catalogs = load_catalogs()
        store = _empty_store()
        normalized_email = email.strip().lower()

        for proceso, table in TABLE_MAP.items():
            resp = (
                get_supabase_client()
                .table(table)
                .select("*")
                .eq("creado_por_app", normalized_email)
                .order("creado_en", desc=True)
                .range(0, 199)
                .execute()
            )
            rows = _safe_response_data(resp)
            if proceso == "Cargue Vehiculo":
                rows = _attach_despacho_totals(rows)
            store[proceso] = _records_to_legacy(proceso, rows, catalogs)

        return store
    except Exception as exc:
        store = _empty_store()
        store["_supabase_error"] = str(exc)
        return store


def get_inventory_rows() -> list[dict[str, Any]]:
    try:
        return _fetch_table("v_inventario_actual")
    except Exception:
        return []


def get_inventory_kpis() -> dict[str, Any]:
    try:
        rows = _fetch_table("v_kpis_inventario_general")
        return rows[0] if rows else {}
    except Exception:
        return {}


def get_connection_status(store_data: dict[str, Any] | None = None) -> dict[str, Any]:
    configured = supabase_is_configured()
    error = (store_data or {}).get("_supabase_error") if isinstance(store_data, dict) else None
    total_records = 0
    if isinstance(store_data, dict):
        total_records = sum(len(store_data.get(p, [])) for p in PROCESOS)
    return {
        "configured": configured,
        "ok": configured and not error,
        "error": error,
        "total_records": total_records,
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
