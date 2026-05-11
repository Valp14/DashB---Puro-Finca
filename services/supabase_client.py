"""
services/supabase_client.py
---------------------------
Cliente centralizado de Supabase para el portal Puro Finca.

La aplicación usa la llave pública/publishable/anon desde .env. No usa service_role.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def get_supabase_config() -> dict[str, str | None]:
    """Devuelve configuración Supabase aceptando SUPABASE_KEY o SUPABASE_ANON_KEY."""
    return {
        "url": os.getenv("SUPABASE_URL"),
        "key": (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("SUPABASE_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
        ),
    }


@lru_cache(maxsize=1)
def get_supabase_client() -> Any:
    """Crea el cliente Supabase si la librería y las variables existen."""
    cfg = get_supabase_config()
    if not cfg["url"] or not cfg["key"]:
        raise RuntimeError(
            "Faltan SUPABASE_URL y/o una llave Supabase en el archivo .env."
        )

    try:
        from supabase import create_client
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "No está instalada la librería supabase. Ejecuta: pip install supabase"
        ) from exc

    return create_client(cfg["url"], cfg["key"])


def supabase_is_configured() -> bool:
    cfg = get_supabase_config()
    return bool(cfg["url"] and cfg["key"])
