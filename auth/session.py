"""
auth/session.py
---------------
Gestión de la sesión de usuario para el portal interno.

Usa flask.session (cookie firmada con SECRET_KEY) para mantener al usuario
autenticado entre requests. No persiste contraseñas ni información sensible
del usuario más allá del email.
"""

from __future__ import annotations

from typing import Optional

from flask import session
from werkzeug.security import check_password_hash

from config.company import (
    ALLOW_DEFAULT_PORTAL_PASSWORDS,
    DEFAULT_PORTAL_PASSWORDS,
    PORTAL_USERS,
)


_SESSION_KEY = "_pf_user"
_SESSION_ROLE_KEY = "_pf_role"


def login(email: str, password: str) -> bool:
    """Valida credenciales y deja al usuario autenticado en la sesión.

    Returns
    -------
    True si las credenciales son válidas; False en caso contrario.
    """
    if not email or not password:
        return False

    email_norm = email.strip().lower()
    stored_password = PORTAL_USERS.get(email_norm)
    if stored_password is None:
        return False

    # Comparación constante en tiempo (evita timing attacks)
    if not ALLOW_DEFAULT_PORTAL_PASSWORDS and password in DEFAULT_PORTAL_PASSWORDS:
        return False

    if not _verify_password(stored_password, password):
        return False

    session.permanent = True
    session[_SESSION_KEY] = email_norm

    try:
        from services.auth_roles import get_role_for_email
        session[_SESSION_ROLE_KEY] = get_role_for_email(email_norm)
    except Exception:
        session[_SESSION_ROLE_KEY] = "operador"

    return True


def logout() -> None:
    """Cierra la sesión del usuario actual."""
    session.pop(_SESSION_KEY, None)
    session.pop(_SESSION_ROLE_KEY, None)


def is_logged_in() -> bool:
    """¿Hay un usuario autenticado en esta sesión?"""
    try:
        return bool(session.get(_SESSION_KEY))
    except RuntimeError:
        # Fuera de un contexto de request
        return False


def current_user() -> Optional[str]:
    """Email del usuario activo, o None."""
    try:
        return session.get(_SESSION_KEY)
    except RuntimeError:
        return None



def current_role() -> str:
    """Rol del usuario activo: admin, jefe, operador o asociacion."""
    try:
        role = session.get(_SESSION_ROLE_KEY)
        if role:
            return role
        email = session.get(_SESSION_KEY)
        if not email:
            return "operador"
        from services.auth_roles import get_role_for_email
        role = get_role_for_email(email)
        session[_SESSION_ROLE_KEY] = role
        return role
    except RuntimeError:
        return "operador"
    except Exception:
        return "operador"

def require_login(func):
    """
    Decorador para rutas Flask que requieren sesión.
    Redirige a /login si no hay usuario autenticado.
    """
    from functools import wraps
    from flask import redirect, url_for, request

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for("login_view", next=request.path))
        return func(*args, **kwargs)
    return wrapper


def _safe_compare(a: str, b: str) -> bool:
    """Comparación de strings resistente a timing attacks."""
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


def _verify_password(stored_password: str, candidate: str) -> bool:
    """Valida hashes de Werkzeug y conserva compatibilidad con texto plano."""
    if not stored_password:
        return False

    hash_prefixes = ("scrypt:", "pbkdf2:", "argon2:")
    if stored_password.startswith(hash_prefixes):
        try:
            return check_password_hash(stored_password, candidate)
        except Exception:
            return False

    return _safe_compare(stored_password, candidate)
