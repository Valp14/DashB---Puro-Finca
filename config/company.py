"""
config/company.py
-----------------
Datos institucionales de Puro Finca S.A.S — extraídos del documento
corporativo oficial.

Las credenciales del portal interno se leen de variables de entorno;
si no están definidas se usan valores por defecto que se deben CAMBIAR
en producción. Para personalizar:
1. Copiar .env.example a .env
2. Definir PORTAL_USERS, SECRET_KEY y SESSION_LIFETIME
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Cargar .env si está presente
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Identidad de la empresa
# ---------------------------------------------------------------------------
COMPANY = {
    "name":         "Puro Finca S.A.S",
    "short_name":   "Puro Finca",
    "tagline":      "Agroexportación con ciencia, tecnología e innovación",
    "industry":     "Producción, transformación y comercialización agrícola",
    "founded":      "Más de 5 años de experiencia",
    "email":        "contacto@purofinca.co",
    "phone":        "+57 300 000 0000",
    "address":      "Región Caribe, Colombia",
    "website":      "www.purofinca.co",
    "logo_path":    "/assets/logo.png",
    "flagship":     "Batata (camote / boniato)",
    "products":     "Batata fresca · Harina Aurora · Batatas congeladas",
}


# ---------------------------------------------------------------------------
# Quiénes somos (textos del PDF oficial)
# ---------------------------------------------------------------------------
ABOUT_PARAGRAPHS = [
    "Somos un equipo profesional especializado en el desarrollo de "
    "proyectos de alto impacto en el sector agrícola, enfocados "
    "específicamente en producción, desarrollo de productos y "
    "comercialización.",

    "Estamos articulados con el área de ciencia, tecnología e innovación "
    "del sector. Contamos con más de 5 años de experiencia en el mercado "
    "y hemos establecido alianzas productivas a nivel nacional e "
    "internacional.",
]


# ---------------------------------------------------------------------------
# Misión y visión (texto literal del PDF)
# ---------------------------------------------------------------------------
MISSION = (
    "Establecer a Colombia como un país exportador de productos agrícolas, "
    "desarrollando el mercado económico y social, creando proyectos "
    "conectados con los mercados internacionales y contribuyendo a "
    "potenciar el sector agrícola a través del empleo, transferencia de "
    "conocimiento, tecnología e innovación, principalmente en la Región "
    "Caribe."
)

VISION = (
    "Ser una empresa líder de la agroexportación en Colombia en el año "
    "2025, impactando a más de 1.000 microempresarios del sector agro y "
    "convertir a la Región Caribe en la gran despensa de distribución de "
    "agroexportación del país, construyendo alianzas productivas sólidas "
    "e impulsando el desarrollo integral de las comunidades con las que "
    "trabajamos."
)


# ---------------------------------------------------------------------------
# Objetivo general (PDF, página 3)
# ---------------------------------------------------------------------------
OBJECTIVE_GENERAL = (
    "Potenciar la agroexportación en Colombia a través del mejoramiento "
    "de la productividad, la competitividad y la transformación total de "
    "los sistemas agroalimentarios mediante el desarrollo de cadenas de "
    "valor agregado intensivas en innovación y conocimiento."
)


# ---------------------------------------------------------------------------
# Objetivos específicos (PDF, páginas 4-5)
# ---------------------------------------------------------------------------
SPECIFIC_OBJECTIVES = [
    {
        "icon":  "◌",
        "title": "Fortalecimiento de cadenas productivas",
        "text":  "Promover la planificación y el fortalecimiento de la "
                 "competitividad en la cadena de producción de cultivos y "
                 "unidades de producción, conforme a las aptitudes y "
                 "potencialidades territoriales.",
    },
    {
        "icon":  "✦",
        "title": "Estándares para agroexportación",
        "text":  "Formular propuestas para fomentar la agroexportación a "
                 "través de directrices considerando ICA, Global Gap, BPA, "
                 "FDA y otros estándares internacionales.",
    },
    {
        "icon":  "◈",
        "title": "Cofinanciación e inversión",
        "text":  "Desarrollar incentivos y estrategias para atraer "
                 "matching grants e inversión del sector privado, "
                 "específicamente desde Europa.",
    },
    {
        "icon":  "▲",
        "title": "Asistencia técnica",
        "text":  "Establecer acuerdos estandarizados para productos "
                 "agropecuarios y brindar asistencia técnica de aliados "
                 "comerciales europeos a pequeños productores.",
    },
    {
        "icon":  "◇",
        "title": "Renovación de sistemas agroalimentarios",
        "text":  "Asesorar la transformación de la productividad y "
                 "competitividad del sector, guiando la transición hacia "
                 "cadenas de valor agregado intensivas en innovación.",
    },
    {
        "icon":  "★",
        "title": "Asociatividad y signos distintivos",
        "text":  "Asesorar a pequeños productores en sus procesos de "
                 "asociatividad u organización agroempresarial, así como "
                 "en la protección de signos distintivos y nuevas "
                 "creaciones.",
    },
]


# ---------------------------------------------------------------------------
# Servicios / líneas de negocio (basados en el proyecto líder del PDF)
# ---------------------------------------------------------------------------
SERVICES = [
    {
        "icon":  "◌",
        "title": "Producción agrícola tecnificada",
        "text":  "Cultivo de batata (camote) bajo estándares operativos "
                 "definidos por etapa: corte de esquejes, siembra, cosecha "
                 "y trazabilidad por finca, lote y proyecto.",
        "image": "/assets/hero-cultivo.jpg",
    },
    {
        "icon":  "✦",
        "title": "Batata fresca para exportación",
        "text":  "Boniato seleccionado y clasificado por calidad, "
                 "preparado para mercados internacionales con cumplimiento "
                 "de estándares ICA y Global Gap.",
        "image": "/assets/boniatos-fresco.jpg",
    },
    {
        "icon":  "◈",
        "title": "Transformación: Harina Aurora",
        "text":  "Transformación de la batata en harina de boniato bajo "
                 "nuestra marca Aurora, con valor agregado para el "
                 "mercado nacional e internacional.",
        "image": "/assets/harina-aurora.jpg",
    },
    {
        "icon":  "▲",
        "title": "Inteligencia operativa",
        "text":  "Panel de indicadores en tiempo real para gerencia: "
                 "cumplimiento, productividad por persona/día, calidad de "
                 "salida y desviaciones críticas.",
        "image": None,
    },
]


# ---------------------------------------------------------------------------
# Beneficios / propuesta de valor
# ---------------------------------------------------------------------------
BENEFITS = [
    {
        "title": "Articulación con CTeI",
        "text":  "Conectados con el área de ciencia, tecnología e "
                 "innovación del sector agrícola colombiano.",
    },
    {
        "title": "Alianzas internacionales",
        "text":  "Más de 5 años construyendo alianzas productivas a "
                 "nivel nacional e internacional, especialmente con "
                 "Europa.",
    },
    {
        "title": "Impacto comunitario",
        "text":  "Meta de impactar a más de 1.000 microempresarios "
                 "del sector agro en la Región Caribe.",
    },
    {
        "title": "Cadena completa",
        "text":  "Desde la producción hasta la comercialización, "
                 "incluyendo transformación en harina y producto "
                 "congelado.",
    },
]


# ---------------------------------------------------------------------------
# Stats destacadas (banda de cifras de la landing)
# ---------------------------------------------------------------------------
STATS = [
    {"value": "5+",     "label": "Años en el mercado"},
    {"value": "1.000",  "label": "Microempresarios objetivo"},
    {"value": "1.000",  "label": "Hectáreas proyectadas"},
    {"value": "06",     "label": "Procesos integrados"},
]


# ---------------------------------------------------------------------------
# Proyecto líder (PDF, página 8)
# ---------------------------------------------------------------------------
FLAGSHIP_PROJECT = {
    "name":  "Batata (camote / boniato)",
    "text":  "Nuestro proyecto líder es la batata, con la cual proyectamos "
             "alcanzar 1.000 hectáreas de producción para el mercado "
             "internacional dentro de 2 años, exportando producto en fresco, "
             "transformado en harina de batata y batatas congeladas.",
    "highlights": [
        "Exportación en fresco a mercados internacionales",
        "Transformación en harina de batata (Aurora)",
        "Producción de batatas congeladas",
        "Estándares ICA, Global Gap, BPA y FDA",
    ],
}


# ---------------------------------------------------------------------------
# Seguridad / credenciales del portal interno
# ---------------------------------------------------------------------------
def _parse_users(env_string: str) -> dict:
    """Parsea 'user1:hash,user2:hash2' a dict.

    Tambien acepta texto plano para compatibilidad local, pero auth.session
    bloquea las claves de ejemplo y recomienda hashes.
    """
    out = {}
    for pair in (env_string or "").split(","):
        pair = pair.strip()
        if ":" in pair:
            email, pwd = pair.split(":", 1)
            email, pwd = email.strip().lower(), pwd.strip()
            if email and pwd:
                out[email] = pwd
    return out

DEFAULT_PORTAL_PASSWORDS = {
    "purofinca2026",
    "gerencia2026",
    "jefe2026",
    "operador2026",
    "asociacion2026",
}


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "si", "sí"}


PORTAL_USERS = _parse_users(os.getenv("PORTAL_USERS", ""))
ALLOW_DEFAULT_PORTAL_PASSWORDS = _env_bool("ALLOW_DEFAULT_PORTAL_PASSWORDS", False)

APP_DEBUG = _env_bool("APP_DEBUG", False)
SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", False)
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
LOGIN_WINDOW_SECONDS = int(os.getenv("LOGIN_WINDOW_SECONDS", "900"))

# Generar SECRET_KEY segura por defecto si no está en entorno
if "SECRET_KEY" not in os.environ:
    try:
        import secrets
        SECRET_KEY = secrets.token_hex(32)
    except ImportError:
        # Fallback si secrets no está disponible
        import hashlib
        import time
        SECRET_KEY = hashlib.sha256(str(time.time()).encode()).hexdigest()
else:
    SECRET_KEY = os.getenv("SECRET_KEY")

SESSION_LIFETIME = int(os.getenv("SESSION_LIFETIME", "14400"))
