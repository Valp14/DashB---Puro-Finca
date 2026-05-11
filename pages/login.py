"""
pages/login.py
--------------
Página de autenticación del portal interno.

El submit del formulario se hace contra una ruta Flask /api/login para
manejar la sesión correctamente (Dash callbacks no pueden setear cookies
de Flask de forma fiable). Tras login exitoso, redirige a /portal/.
"""

from __future__ import annotations

from dash import html, dcc

from config.company import COMPANY


def _hidden_input(name: str, value: str):
    """Renderiza un input oculto. Usa dcc.Input que sí soporta type=hidden."""
    return dcc.Input(type="hidden", name=name, value=value)


def layout(error: str = "", next_url: str = "/portal/") -> html.Div:
    error_block = (
        html.Div([
            html.Span("⚠ ", className="login-error-icon"),
            error,
        ], className="login-error")
        if error else html.Div(style={"display": "none"})
    )

    return html.Div([
        # Lado izquierdo: branding
        html.Div([
            html.Div([
                html.Img(src="/assets/logo.png", alt="Puro Finca",
                         className="login-side-logo"),
                html.Div([
                    html.H1("Puro Finca", className="login-side-name"),
                    html.Div("Panel Operativo", className="login-side-tag"),
                ]),
            ], className="login-side-brand"),

            html.Div([
                html.Span("Portal Interno", className="login-side-eyebrow"),
                html.H2(["Indicadores en tiempo real para el ",
                         html.Em("equipo de operaciones")],
                        className="login-side-title"),
                html.P(
                    "Acceso restringido para personal autorizado de Puro Finca. "
                    "Cargá el archivo operativo y consultá KPIs, alertas y "
                    "reportes generados automáticamente.",
                    className="login-side-text"),
            ], className="login-side-message"),

            html.Div([
                html.A("← Volver al sitio público", href="/",
                       className="login-side-back"),
            ]),
        ], className="login-side"),

        # Lado derecho: formulario
        html.Div([
            html.Form([
                html.Div([
                    html.Span("Acceso", className="login-form-eyebrow"),
                    html.H2("Inicia sesión", className="login-form-title"),
                    html.P("Usá las credenciales que te entregó la dirección.",
                           className="login-form-subtitle"),
                ], className="login-form-header"),

                error_block,

                html.Div([
                    html.Label("Correo electrónico",
                               htmlFor="login-email",
                               className="login-form-label"),
                    dcc.Input(
                        id="login-email",
                        name="email",
                        type="email",
                        placeholder="tunombre@purofinca.co",
                        required=True,
                        autoFocus=True,
                        className="login-form-input",
                    ),
                ], className="login-form-field"),

                html.Div([
                    html.Label("Contraseña",
                               htmlFor="login-password",
                               className="login-form-label"),
                    dcc.Input(
                        id="login-password",
                        name="password",
                        type="password",
                        placeholder="••••••••",
                        required=True,
                        className="login-form-input",
                    ),
                ], className="login-form-field"),

                # Campo oculto "next" — implementado con un componente
                # personalizado que el renderer convierte a <input type=hidden>
                _hidden_input("next", next_url),

                html.Button("Iniciar sesión →",
                            type="submit",
                            className="login-form-submit"),

                html.Div([
                    html.Span("¿Problemas para acceder? "),
                    html.A(f"Escribinos a {COMPANY['email']}",
                           href=f"mailto:{COMPANY['email']}",
                           className="login-form-help"),
                ], className="login-form-help-text"),
            ],
            method="POST",
            action="/api/login",
            className="login-form"),
        ], className="login-form-side"),
    ], className="login-page")
