"""Roles de navegación para el portal."""

from __future__ import annotations

import os
from functools import lru_cache

from services.supabase_client import supabase_is_configured, get_supabase_client

VALID_ROLES = {"admin", "jefe", "operador", "asociacion"}


def _parse_env_roles() -> dict[str, str]:
    raw = os.getenv("PORTAL_ROLES", "")
    out: dict[str, str] = {}
    for pair in raw.split(","):
        if ":" not in pair:
            continue
        email, role = pair.split(":", 1)
        email = email.strip().lower()
        role = role.strip().lower()
        if email and role in VALID_ROLES:
            out[email] = role
    return out


@lru_cache(maxsize=256)
def get_role_for_email(email: str | None) -> str:
    if not email:
        return "operador"
    email = email.strip().lower()

    env_roles = _parse_env_roles()
    if email in env_roles:
        return env_roles[email]

    # Si existe en Supabase, usar perfiles. Si no, caer al default.
    if supabase_is_configured():
        try:
            client = get_supabase_client()
            resp = client.table("perfiles").select("rol,activo").eq("correo", email).limit(1).execute()
            data = getattr(resp, "data", None) or []
            if data and data[0].get("activo") is not False:
                role = str(data[0].get("rol") or "").lower()
                if role in VALID_ROLES:
                    return role
        except Exception:
            pass

    if email.startswith("admin") or "gerencia" in email:
        return "admin"
    return "operador"
