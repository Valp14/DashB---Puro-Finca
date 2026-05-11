# Puro Finca S.A.S · Plataforma Web

> **Versión 3 (2026)** — Landing pública + Portal interno autenticado + Reportes PDF.
>
> Aplicación Python construida sobre **Flask + Dash** que combina la cara
> pública de la empresa (landing institucional) con el panel operativo
> interno protegido por login.

---

## Stack y framework

- **Flask 3.x** — sirve la landing pública, login, logout y endpoints de API.
- **Dash 2.x** (Plotly) — sirve el dashboard interactivo bajo `/portal/`.
- **ReportLab** — generación de reportes PDF.
- **matplotlib** — gráficas embebidas en el PDF.
- **pandas / openpyxl** — ingesta de Excel y cálculo de KPIs.

---

## Arquitectura

```
                        ┌──────────────────────────────────┐
                        │   Flask server (raíz)            │
                        │                                  │
GET  /              ────│─→ Landing pública                │
GET  /login         ────│─→ Página de login                │
POST /api/login     ────│─→ Validación credenciales        │
GET  /logout        ────│─→ Cerrar sesión                  │
GET  /assets/*      ────│─→ Archivos estáticos             │
                        │                                  │
                        │   Dash app (montada en /portal/) │
                        │   ┌──────────────────────────┐   │
GET  /portal/       ────│───│─→ Inicio                 │   │
GET  /portal/cosecha────│───│─→ Detalle de cosecha     │   │
GET  /portal/...    ────│───│─→ 13 vistas operativas   │   │
                        │   └──────────────────────────┘   │
                        │   Middleware: protección sesión  │
                        └──────────────────────────────────┘
```

El middleware `_protect_portal()` en `app.py` bloquea cualquier acceso a
`/portal/*` sin sesión activa y redirige a `/login?next=...`.

---

## Estructura del proyecto

```
puro_finca_dashboard_v3/
├── app.py                    # Punto de entrada (Flask + Dash)
├── layout_portal.py          # Layout del área autenticada
├── callbacks.py              # Callbacks globales (router, filtros, PDF)
├── requirements.txt
├── README.md
├── .env.example              # Plantilla de credenciales
│
├── auth/
│   ├── __init__.py
│   └── session.py            # login / logout / sesión Flask
│
├── assets/
│   ├── style.css             # Sistema de diseño (rediseño 2026)
│   ├── public.css            # Landing pública + login + responsive
│   ├── logo.png              # Logo Puro Finca
│   ├── hero-cultivo.jpg      # Cultivo de batata (hero landing)
│   ├── equipo-terreno.jpg    # Equipo en preparación de terreno
│   ├── agricultor-campo.jpg  # Agricultor inspeccionando surcos
│   ├── boniatos-fresco.jpg   # Producto fresco
│   └── harina-aurora.jpg     # Harina de batata Aurora
│
├── config/
│   ├── settings.py           # Paleta, estándares operativos
│   └── company.py            # Datos institucionales (PDF oficial)
│
├── components/
│   ├── sidebar.py            # Sidebar agrupada con filtros globales
│   ├── ui.py                 # kpi_card, pill, detail_table, etc.
│   └── charts.py             # Plotly con paleta corporativa
│
├── styles/
│   └── theme.py              # hero, narrative, exec_summary, etc.
│
├── utils/
│   ├── data_loader.py        # Lectura del Excel operativo
│   ├── filters.py            # Filtros globales
│   ├── metrics.py            # Cálculo de KPIs
│   └── pdf/
│       ├── __init__.py
│       └── report_builder.py # Generador de reporte PDF ejecutivo
│
└── pages/
    ├── landing.py            # Landing pública (12 secciones)
    ├── login.py              # Página de inicio de sesión
    ├── inicio.py             # Home del portal interno
    ├── productividad.py
    ├── corte.py · siembra.py · cosecha.py
    ├── lavado.py · empaque.py · cargue.py
    ├── calidad_perdidas.py · plan_vs_real.py
    ├── reportes.py · configuracion.py · calidad_datos.py
    └── _common.py
```

---

## Instalación

```bash
# 1. Descomprimir el proyecto
unzip puro_finca_dashboard_v3.zip
cd puro_finca_dashboard_v3/

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate     # Linux / macOS
# .venv\Scripts\activate       # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar credenciales (recomendado para producción)
cp .env.example .env
# Editar .env: definir PORTAL_USERS, SECRET_KEY, SESSION_LIFETIME
```

## Ejecución

### Desarrollo

```bash
python app.py
```

Abrir `http://localhost:8050` para la landing, o `http://localhost:8050/login`
para entrar al portal.

### Producción (Gunicorn)

```bash
pip install gunicorn
gunicorn app:server -b 0.0.0.0:8050 -w 4 --timeout 60
```

### Producción (Docker — opcional)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
ENV PYTHONUNBUFFERED=1
EXPOSE 8050
CMD ["gunicorn", "app:server", "-b", "0.0.0.0:8050", "-w", "4"]
```

---

## Credenciales del portal

Por defecto (modo demo, **cambiar en producción**):

| Email                       | Contraseña       |
|-----------------------------|------------------|
| Define usuarios reales en `.env` | Usa hashes, no texto plano |

Para crear un hash: `python scripts/hash_password.py "contrasena-larga-y-unica"`.

Para personalizar, edita `.env`:

```env
PORTAL_USERS=usuario1@empresa.com:scrypt:hash-generado,usuario2@empresa.com:scrypt:hash-generado
SECRET_KEY=clave-aleatoria-larga-generada-con-secrets-token-hex
SESSION_LIFETIME=14400
```

Generá una `SECRET_KEY` segura con:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Mapa de rutas

| Ruta                  | Método | Auth | Descripción                             |
|-----------------------|--------|------|-----------------------------------------|
| `/`                   | GET    | No   | Landing pública                         |
| `/login`              | GET    | No   | Página de inicio de sesión              |
| `/api/login`          | POST   | No   | Validación de credenciales              |
| `/logout`             | GET    | Sí   | Cerrar sesión y redirigir a `/`         |
| `/portal/`            | GET    | Sí   | Inicio del dashboard                    |
| `/portal/cosecha`     | GET    | Sí   | Detalle de cosecha (y 12 vistas más)    |
| `/api/report.pdf`     | GET    | Sí   | Reporte PDF (también vía botón en UI)   |
| `/assets/<archivo>`   | GET    | No   | Archivos estáticos (logo, CSS, fotos)   |

---

## Generación de PDF

Desde la página de inicio del portal, hacé clic en **"Exportar reporte
PDF"**. El generador incluye:

- Header corporativo con logo en cada página
- Portada con filtros aplicados
- Sección 1 — Volumen consolidado (8 KPIs)
- Sección 2 — Cumplimiento vs estándar (tabla con badges)
- Sección 3 — Distribución de calidad (donut)
- Sección 4 — Tendencia de cosecha (gráfico de líneas)
- Sección 5 — Alertas ejecutivas
- Sección 6 — Recomendaciones automáticas
- Footer con datos corporativos y paginación

---

## Bugs corregidos en esta versión

1. **`dotacion_block`** mezclaba `signo` con `fmt_pct()` produciendo
   `"++12,5%"`. Corregido con manejo de excepciones.
2. **`detail_table`** usaba fuente de sistema (`-apple-system`) en lugar
   de Plus Jakarta Sans. Migrado al sistema tipográfico unificado, con
   `font-variant-numeric: tabular-nums` para alinear cifras.
3. **`donut_composicion`** crasheaba con listas vacías o sumas en cero.
   Ahora valida input antes de renderizar.
4. **`barh_ranking`** tenía altura fija (320 px) que distorsionaba
   gráficas con muchas categorías. Ahora calcula altura dinámica:
   `max(220, 60 + 28 × n_barras)`.
5. **`html.Input`** no existe en Dash — la página de login usaba esta
   referencia incorrecta para el campo hidden. Corregido a `dcc.Input`
   con `type="hidden"`.

---

## Mejoras realizadas

### Auditoría y refactor
- Validación de inputs en charts (vacíos, NaN, sumas en cero)
- DataTable con styling consistente
- Manejo robusto de excepciones en formateadores

### Adaptación responsive
- Topbar con menú hamburguesa para móvil/tablet (≤1024px)
- Sidebar con drawer animado y backdrop
- Breakpoints en 1024 / 720 / 480 px
- Imágenes con `aspect-ratio` para evitar layout shifts
- Stats band se reorganiza de 4 cols → 2 cols → 1 col

### Landing pública
- 12 secciones con información oficial extraída del PDF corporativo
- 5 imágenes reales del PDF (cultivo, equipo, agricultor, producto, harina)
- Hero con bg-image difuminada y card glassmorphism
- Misión y Visión literal de la empresa
- 6 objetivos específicos
- Proyecto líder (batata) con checklist de exportación
- CTA al portal interno

### Portal interno (login)
- Sistema de autenticación con flask.session firmada
- Comparación de contraseñas resistente a timing attacks
- Sesiones de 4 horas (configurable)
- Validación de redirects (anti open-redirect)
- Middleware de protección automática para `/portal/*`
- Página de login split 50/50 con feedback de errores

### Generación de reportes PDF
- Reporte ejecutivo profesional con ReportLab
- 6 secciones, gráficas embebidas, paginación
- Datos del usuario y filtros aplicados
- Recomendaciones automáticas según niveles de cumplimiento

---

## Recomendaciones finales

### Antes de desplegar a producción

1. **Cambiar credenciales por defecto** — editar `.env`.
2. **Generar SECRET_KEY aleatoria** — no usar la del repo.
3. **Servir detrás de HTTPS** — agregar `SESSION_COOKIE_SECURE=True` en
   `app.py` cuando uses TLS.
4. **Usar Gunicorn** — el servidor Flask de desarrollo no es para
   producción.
5. **Configurar reverse proxy** (Nginx / Caddy) para terminación TLS,
   compresión y caching de assets.

### Mejoras futuras sugeridas

- Migrar el archivo `.env` con credenciales planas a un sistema de hash
  (bcrypt) y/o un proveedor de identidad (OAuth, SSO).
- Persistencia de datos: hoy el upload del Excel queda solo en
  `dcc.Store` por sesión. Para producción real, persistir en una BD
  (PostgreSQL + SQLAlchemy).
- Logs estructurados con `structlog` o `python-json-logger`.
- Tests unitarios sobre `utils/metrics.py` y `utils/pdf/report_builder.py`.
- CI/CD con GitHub Actions para correr tests + lint en cada push.
- Métricas de uso (Prometheus / Grafana) para monitorear la operación
  del panel en producción.

### Mantenimiento del contenido

Los textos de la landing están en `config/company.py` como constantes
Python. Para actualizarlos no necesitás tocar HTML — solo editar las
listas y diccionarios:

- `COMPANY` — nombre, email, teléfono, sede.
- `ABOUT_PARAGRAPHS` — sección "¿Quiénes somos?".
- `MISSION` / `VISION` — texto oficial.
- `OBJECTIVE_GENERAL` — objetivo general.
- `SPECIFIC_OBJECTIVES` — lista de 6 tarjetas (con icono, título, texto).
- `SERVICES` — 4 servicios (con imagen opcional).
- `BENEFITS` — 4 diferenciales.
- `STATS` — banda de cifras destacadas.
- `FLAGSHIP_PROJECT` — proyecto líder con highlights.

Los textos del portal interno están en `pages/inicio.py` como
constantes al inicio del archivo (`EXEC_SUMMARY_PARAGRAPHS`,
`NARRATIVE_CARDS`, etc.).
