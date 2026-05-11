"""Reglas centralizadas de acceso del portal."""

from __future__ import annotations

from config.settings import PROCESOS


PAGE_ACCESS = {
    "operador": {"/portal", "/portal/formularios"},
    "asociacion": {"/portal", "/portal/productividad", "/portal/reportes"},
    "jefe": {
        "/portal",
        "/portal/inventario",
        "/portal/productividad",
        "/portal/formularios",
        "/portal/corte",
        "/portal/siembra",
        "/portal/cosecha",
        "/portal/lavado",
        "/portal/empaque",
        "/portal/cargue",
        "/portal/calidad-perdidas",
        "/portal/calidad-datos",
        "/portal/reportes",
    },
    "admin": {
        "/portal",
        "/portal/inventario",
        "/portal/formularios",
        "/portal/mis-registros",
        "/portal/productividad",
        "/portal/corte",
        "/portal/siembra",
        "/portal/cosecha",
        "/portal/lavado",
        "/portal/empaque",
        "/portal/cargue",
        "/portal/calidad-perdidas",
        "/portal/plan-vs-real",
        "/portal/reportes",
        "/portal/configuracion",
        "/portal/calidad-datos",
    },
}

DATA_ROLES = {"admin", "jefe", "asociacion"}
FORM_WRITE_ROLES = {"admin", "jefe", "operador"}


def normalize_role(role: str | None) -> str:
    return role if role in PAGE_ACCESS else "operador"


def allowed_pages(role: str | None) -> set[str]:
    return PAGE_ACCESS[normalize_role(role)]


def can_access_page(role: str | None, path: str) -> bool:
    return path in allowed_pages(role)


def can_read_operational_data(role: str | None) -> bool:
    return normalize_role(role) in DATA_ROLES


def can_submit_forms(role: str | None) -> bool:
    return normalize_role(role) in FORM_WRITE_ROLES


def empty_operational_store() -> dict[str, list]:
    return {p: [] for p in PROCESOS}
