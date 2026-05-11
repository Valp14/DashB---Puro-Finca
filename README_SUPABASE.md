# Puro Finca · Versión migrada a Supabase

Esta versión usa `dashboard_v3` como base visual y migra la fuente principal de datos a Supabase.

## Qué quedó listo

- Conexión centralizada a Supabase en `services/supabase_client.py`.
- Carga de datos operativos desde Supabase en `services/supabase_data.py`.
- Conversión automática de las tablas nuevas al formato que ya usan los dashboards existentes.
- Navbar dinámico según rol: `admin`, `jefe`, `operador`, `asociacion`.
- Página nueva de inventario en `/portal/inventario`, consultando `v_inventario_actual` y `v_kpis_inventario_general`.
- El Excel queda como respaldo oculto, pero ya no es la fuente principal.

## Cómo correr

```bash
cd dashboard_v3
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

En Mac/Linux:

```bash
cd dashboard_v3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Luego abre:

```text
http://127.0.0.1:8050/login
```

## Usuarios de prueba incluidos

Estos usuarios están en `.env` y puedes cambiarlos:

| Rol | Correo | Contraseña |
|---|---|---|
| Admin | admin@empresa.com | hash generado |
| Jefe | jefe@empresa.com | hash generado |
| Operador | operador@empresa.com | hash generado |
| Asociacion | asociacion@empresa.com | hash generado |

## Variables Supabase

El archivo `.env` debe tener:

```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key-solo-en-el-servidor
```

No publiques la `service_role key`; debe quedarse solo en el backend Python.

## Rutas principales

- `/portal/` — Inicio.
- `/portal/productividad` — Productividad general.
- `/portal/inventario` — Inventario actual desde Supabase.
- `/portal/corte`, `/portal/siembra`, `/portal/cosecha`, `/portal/lavado`, `/portal/empaque`, `/portal/cargue` — páginas de proceso leyendo datos de Supabase.

## Siguiente fase

La siguiente fase es construir los formularios nuevos conectados directamente a Supabase. Esta versión primero deja el sistema leyendo desde Supabase como fuente principal.

## Si la app no muestra datos

Si el menú lateral aparece como `Revisar conexión Supabase`, puede ser por RLS/permisos de lectura. En ese caso ejecuta en Supabase SQL Editor el archivo:

```text
sql_politicas_lectura_app.sql
```

Esto habilita lectura con la llave publishable/anon para esta fase de desarrollo. Para producción, lo ideal será conectar el login con Supabase Auth o mover las lecturas a un backend con permisos controlados.
