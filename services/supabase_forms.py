"""Servicios de formularios operativos contra Supabase.

La app usa RPC SECURITY DEFINER para registrar formularios sin exponer la
service_role key. Debes ejecutar primero sql_formularios_rpc.sql en Supabase.
"""

from __future__ import annotations

from typing import Any
from services.supabase_client import get_supabase_client


def _client():
    return get_supabase_client()


def _data(resp: Any):
    return getattr(resp, "data", None)


def fetch_catalog_options(table: str, label_col: str = "nombre", extra_cols: str = "") -> list[dict[str, Any]]:
    cols = f"id,{label_col}"
    if extra_cols:
        cols += "," + extra_cols
    rows = _data(_client().table(table).select(cols).range(0, 9999).execute()) or []
    opts = []
    for r in rows:
        label = r.get(label_col) or r.get("codigo") or r.get("nombre") or r.get("id")
        opts.append({"label": str(label), "value": str(r.get("id"))})
    return opts


def fetch_catalogs_for_forms() -> dict[str, list[dict[str, Any]]]:
    return {
        "fincas": fetch_catalog_options("fincas", "nombre"),
        "proyectos": fetch_catalog_options("proyectos", "nombre"),
        "lotes": fetch_catalog_options("lotes", "codigo"),
        "clientes": fetch_catalog_options("clientes", "nombre"),
        "destinos": fetch_catalog_options("destinos", "nombre"),
        "causas": fetch_catalog_options("causas_descarte", "nombre"),
    }


def fetch_inventory_options() -> list[dict[str, Any]]:
    rows = _data(_client().table("v_inventario_actual").select("*").range(0, 9999).execute()) or []
    options = []
    for r in rows:
        ubicacion = str(r.get("ubicacion") or "").replace("_", " ").title()
        clase = str(r.get("clase") or "").replace("_", " ").title()
        estado = str(r.get("estado") or "").replace("_", " ").title()
        pres = str(r.get("presentacion") or "").replace("_", " ").title()
        kg = float(r.get("kg_disponibles") or 0)
        value = "|".join([str(r.get("ubicacion")), str(r.get("clase")), str(r.get("estado")), str(r.get("presentacion"))])
        options.append({
            "label": f"{ubicacion} · {clase} · {estado} · {pres} · {kg:,.2f} kg",
            "value": value,
        })
    return options


def parse_inventory_value(value: str | None) -> dict[str, str | None]:
    if not value:
        return {"ubicacion": None, "clase": None, "estado": None, "presentacion": None}
    parts = str(value).split("|")
    parts += [None] * (4 - len(parts))
    return {"ubicacion": parts[0], "clase": parts[1], "estado": parts[2], "presentacion": parts[3]}


def rpc(name: str, params: dict[str, Any]) -> Any:
    resp = _client().rpc(name, params).execute()
    return _data(resp)


def _scalar_id(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, str):
            return first
        if isinstance(first, dict):
            return str(first.get("id") or first.get("registrar_empaque_multi_app") or first.get("registrar_empaque_app") or "") or None
    if isinstance(value, dict):
        return str(value.get("id") or "") or None
    return None


def mark_record_owner(table: str, record_id: Any, email: str | None) -> bool:
    rid = _scalar_id(record_id)
    if not rid or not email:
        return False
    try:
        rpc("marcar_registro_app", {
            "p_tabla": table,
            "p_id": rid,
            "p_correo": email,
        })
        return True
    except Exception:
        return False


def registrar_corte(params: dict[str, Any]):
    return rpc("registrar_corte_esquejes_app", params)


def registrar_siembra(params: dict[str, Any]):
    return rpc("registrar_siembra_app", params)


def registrar_cosecha(params: dict[str, Any]):
    return rpc("registrar_cosecha_app", params)


def registrar_lavado(params: dict[str, Any]):
    return rpc("registrar_lavado_app", params)


def registrar_empaque(params: dict[str, Any]):
    return rpc("registrar_empaque_app", params)


def registrar_empaque_multi(params: dict[str, Any]):
    return rpc("registrar_empaque_multi_app", params)


def registrar_despacho(params: dict[str, Any]):
    return rpc("registrar_despacho_app", params)


def registrar_despacho_multi(params: dict[str, Any]):
    return rpc("registrar_despacho_multi_app", params)
