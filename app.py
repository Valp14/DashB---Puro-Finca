"""
app.py
------
Punto de entrada de la aplicación Puro Finca.

Arquitectura híbrida:
  - Flask vanilla maneja:
      /             → landing pública tomada de purofincaweb.com
      /login        → página de login
      /api/login    → POST de credenciales
      /logout       → cerrar sesión
      /api/report.pdf → descarga del reporte ejecutivo autenticada
  - Dash maneja:
      /portal/*     → dashboard interno protegido

La integración Flask + Dash se hace montando Dash sobre el Flask server
con routes_pathname_prefix="/portal/".
"""

from __future__ import annotations

import io
import time
from collections import defaultdict, deque
from datetime import timedelta
from urllib.parse import urlsplit

import dash
import dash_bootstrap_components as dbc
from flask import (
    Flask,
    redirect,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from flask_caching import Cache

from auth import (
    is_logged_in,
    login as auth_login,
    logout as auth_logout,
    current_user,
)
from config.company import COMPANY, SECRET_KEY, SESSION_LIFETIME
from config.company import (
    APP_DEBUG,
    LOGIN_MAX_ATTEMPTS,
    LOGIN_WINDOW_SECONDS,
    SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_SECURE,
)


# ---------------------------------------------------------------------------
# Flask server
# ---------------------------------------------------------------------------

server = Flask(__name__, static_folder="assets", static_url_path="/assets")

server.config.update(
    SECRET_KEY=SECRET_KEY,
    PERMANENT_SESSION_LIFETIME=timedelta(seconds=SESSION_LIFETIME),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE=SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_SECURE=SESSION_COOKIE_SECURE,
)

_login_failures: dict[str, deque[float]] = defaultdict(deque)


# ---------------------------------------------------------------------------
# Helpers para renderizar layouts Dash como HTML estático
# Se conservan porque el login todavía se genera desde pages/login.py
# ---------------------------------------------------------------------------

def _is_safe_next_url(candidate: str) -> bool:
    """Acepta solo rutas locales relativas al sitio."""
    if not candidate or not isinstance(candidate, str):
        return False

    if not candidate.startswith("/") or candidate.startswith(("//", "/\\")):
        return False

    parts = urlsplit(candidate)
    return not parts.scheme and not parts.netloc


def _login_throttle_key(email: str) -> str:
    remote = request.headers.get("X-Forwarded-For", request.remote_addr or "")
    ip = remote.split(",", 1)[0].strip()
    return f"{ip}:{email.strip().lower()}"


def _is_login_limited(email: str) -> bool:
    key = _login_throttle_key(email)
    attempts = _login_failures[key]
    now = time.time()

    while attempts and now - attempts[0] > LOGIN_WINDOW_SECONDS:
        attempts.popleft()

    return len(attempts) >= LOGIN_MAX_ATTEMPTS


def _record_login_failure(email: str) -> None:
    _login_failures[_login_throttle_key(email)].append(time.time())


def _clear_login_failures(email: str) -> None:
    _login_failures.pop(_login_throttle_key(email), None)


def _render_dash_component(component, title: str = "Puro Finca") -> str:
    """Convierte un componente Dash a HTML serializado dentro de un esqueleto."""
    return _component_to_html(component, title)


def _component_to_html(component, title: str) -> str:
    """Recursivamente convierte componentes Dash a HTML estático."""
    body_html = _render(component)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{COMPANY['tagline']}">
<link rel="icon" type="image/png" href="/assets/logo.png">
<link rel="stylesheet" href="/assets/style.css">
<link rel="stylesheet" href="/assets/public.css">
</head>
<body>
{body_html}
</body>
</html>"""


def _render(c) -> str:
    """Render recursivo de componentes Dash a HTML."""
    from dash.development.base_component import Component

    if c is None:
        return ""

    if isinstance(c, str):
        return _escape(c)

    if isinstance(c, (list, tuple)):
        return "".join(_render(x) for x in c)

    if isinstance(c, bool):
        return ""

    if isinstance(c, (int, float)):
        return _escape(str(c))

    if not isinstance(c, Component):
        return _escape(str(c))

    tag = _tag_name(c)

    if tag is None:
        return _render_special(c)

    attrs_str = ""
    children = ""
    self_closing = tag in {"img", "input", "br", "hr", "meta", "link"}

    for attr_name, html_attr in [
        ("id", "id"),
        ("className", "class"),
        ("href", "href"),
        ("src", "src"),
        ("alt", "alt"),
        ("type", "type"),
        ("name", "name"),
        ("value", "value"),
        ("placeholder", "placeholder"),
        ("htmlFor", "for"),
        ("method", "method"),
        ("action", "action"),
        ("style", "style"),
    ]:
        if hasattr(c, attr_name):
            v = getattr(c, attr_name, None)

            if v is None:
                continue

            if attr_name == "style" and isinstance(v, dict):
                v = "; ".join(
                    f"{_camel_to_kebab(k)}: {vv}"
                    for k, vv in v.items()
                )

            if v != "":
                attrs_str += f' {html_attr}="{_escape_attr(str(v))}"'

    for attr_name, html_attr in [
        ("required", "required"),
        ("autoFocus", "autofocus"),
    ]:
        if getattr(c, attr_name, None):
            attrs_str += f" {html_attr}"

    if self_closing:
        return f"<{tag}{attrs_str}>"

    if hasattr(c, "children") and c.children is not None:
        children = _render(c.children)

    return f"<{tag}{attrs_str}>{children}</{tag}>"


def _tag_name(c) -> str | None:
    """Mapea html.Div → div, html.H1 → h1, html.A → a, etc."""
    cls = type(c).__name__
    module = type(c).__module__

    if module.startswith("dash.html"):
        return cls.lower()

    return None


def _render_special(c) -> str:
    """Render de componentes dcc.* usados en el login."""
    cls = type(c).__name__

    if cls == "Input":
        attrs = ""

        for k, html_k in [
            ("id", "id"),
            ("name", "name"),
            ("type", "type"),
            ("placeholder", "placeholder"),
            ("value", "value"),
            ("className", "class"),
            ("style", "style"),
        ]:
            v = getattr(c, k, None)

            if k == "style" and isinstance(v, dict):
                v = "; ".join(
                    f"{_camel_to_kebab(kk)}: {vv}"
                    for kk, vv in v.items()
                )

            if v is not None and v != "":
                attrs += f' {html_k}="{_escape_attr(str(v))}"'

        if getattr(c, "required", None):
            attrs += " required"

        if getattr(c, "autoFocus", None):
            attrs += " autofocus"

        return f"<input{attrs}>"

    return ""


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _escape_attr(s: str) -> str:
    return s.replace('"', "&quot;").replace("\n", " ")


def _camel_to_kebab(s: str) -> str:
    out = []

    for ch in s:
        if ch.isupper():
            out.append("-")
            out.append(ch.lower())
        else:
            out.append(ch)

    return "".join(out)


# ---------------------------------------------------------------------------
# Ruta Flask: landing pública
# ---------------------------------------------------------------------------

@server.route("/")
def landing_view():
    """
    Muestra la landing pública original de purofincaweb.com.

    IMPORTANTE:
    Este archivo debe existir en:
        dashboard_v3/assets/puro-finca-v2.html

    Y las imágenes usadas por esa landing también deben estar en:
        dashboard_v3/assets/
    """
    return send_from_directory(server.static_folder, "puro-finca-v2.html")


# ---------------------------------------------------------------------------
# Rutas Flask: login / logout
# ---------------------------------------------------------------------------

@server.route("/login")
def login_view():
    from pages import login as login_page

    error = request.args.get("error", "")
    next_url = request.args.get("next", "/portal/")

    return _render_dash_component(
        login_page.layout(error=error, next_url=next_url),
        title=f"Acceso · {COMPANY['name']}",
    )


@server.route("/api/login", methods=["POST"])
def api_login():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    next_url = request.form.get("next", "/portal/")

    if not _is_safe_next_url(next_url):
        next_url = "/portal/"

    if _is_login_limited(email):
        return redirect(
            url_for(
                "login_view",
                error="Demasiados intentos fallidos. Espera unos minutos e intenta de nuevo.",
                next=next_url,
            )
        )

    if auth_login(email, password):
        _clear_login_failures(email)
        return redirect(next_url)

    _record_login_failure(email)
    return redirect(
        url_for(
            "login_view",
            error="Correo o contraseña incorrectos. Verificá los datos e intentá de nuevo.",
            next=next_url,
        )
    )


@server.route("/logout")
def logout_view():
    auth_logout()
    return redirect("/")


# ---------------------------------------------------------------------------
# Ruta protegida: descarga PDF
# ---------------------------------------------------------------------------

@server.route("/api/report.pdf")
def download_pdf():
    if not is_logged_in():
        return redirect(url_for("login_view", next="/portal/"))

    return _generate_demo_pdf()


@server.route("/api/report.pdf", methods=["POST"])
def download_pdf_post():
    if not is_logged_in():
        return redirect(url_for("login_view"))

    payload = request.get_json(silent=True) or {}

    from pathlib import Path
    from datetime import datetime
    from utils.pdf import build_executive_report

    logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"

    pdf_bytes = build_executive_report(
        kpis_corte=payload.get("kpis_corte", {}),
        kpis_siembra=payload.get("kpis_siembra", {}),
        kpis_cosecha=payload.get("kpis_cosecha", {}),
        kpis_lavado=payload.get("kpis_lavado", {}),
        kpis_empaque=payload.get("kpis_empaque", {}),
        kpis_cargue=payload.get("kpis_cargue", {}),
        filtros_aplicados=payload.get("filtros"),
        user_email=current_user(),
        logo_path=str(logo_path) if logo_path.exists() else None,
    )

    fname = f"puro_finca_reporte_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=fname,
    )


def _generate_demo_pdf():
    """Genera un PDF con datos vacíos si se accede vía GET sin payload."""
    from pathlib import Path
    from datetime import datetime
    from utils.pdf import build_executive_report

    logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"

    empty = {}

    pdf_bytes = build_executive_report(
        kpis_corte=empty,
        kpis_siembra=empty,
        kpis_cosecha=empty,
        kpis_lavado=empty,
        kpis_empaque=empty,
        kpis_cargue=empty,
        user_email=current_user(),
        logo_path=str(logo_path) if logo_path.exists() else None,
    )

    fname = f"puro_finca_reporte_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=fname,
    )


# ---------------------------------------------------------------------------
# Protección del portal
# ---------------------------------------------------------------------------

@server.before_request
def _protect_portal():
    """Bloquea /portal/* a usuarios sin sesión."""
    path = request.path or ""

    if not path.startswith("/portal/"):
        return None

    if not is_logged_in():
        if "/_dash-" in path or path.endswith("/_reload-hash"):
            return "", 401

        return redirect(url_for("login_view", next=path))

    return None


@server.after_request
def _security_headers(response):
    """Cabeceras defensivas para portal y API."""
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")

    path = request.path or ""
    if path.startswith("/portal/") or path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, private"

    return response


# ---------------------------------------------------------------------------
# Dash app montada en /portal/
# ---------------------------------------------------------------------------

app = dash.Dash(
    __name__,
    server=server,
    title=f"{COMPANY['name']} · Panel Operativo",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    update_title=None,
    routes_pathname_prefix="/portal/",
    requests_pathname_prefix="/portal/",
)


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

cache = Cache(
    server,
    config={
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 600,
    },
)


# ---------------------------------------------------------------------------
# Layout del portal
# ---------------------------------------------------------------------------

from layout_portal import serve_layout  # noqa: E402

app.layout = serve_layout


# ---------------------------------------------------------------------------
# Registrar callbacks y páginas internas
# ---------------------------------------------------------------------------

import callbacks  # noqa: E402,F401

from pages import (  # noqa: E402,F401
    inicio,
    productividad,
    corte,
    siembra,
    cosecha,
    lavado,
    empaque,
    cargue,
    calidad_perdidas,
    plan_vs_real,
    reportes,
    configuracion,
    calidad_datos,
    inventario,
    formularios,
    mis_registros,
)


# ---------------------------------------------------------------------------
# Ejecutar servidor
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8050, debug=APP_DEBUG)
