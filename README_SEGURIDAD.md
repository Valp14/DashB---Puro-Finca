# Seguridad del portal

## Cambios aplicados

- El portal ya no trae usuarios por defecto desde el codigo.
- Las contrasenas conocidas de ejemplo quedan bloqueadas por defecto.
- `PORTAL_USERS` acepta hashes generados con Werkzeug.
- `APP_DEBUG` controla el modo debug y viene desactivado por defecto.
- El login tiene limite de intentos por IP + correo.
- Las rutas `/portal/*` y `/api/*` responden con cabeceras de no cache.
- Se agrega `sql_seguridad_produccion.sql` para revocar permisos `anon` en Supabase.

## Crear contrasenas seguras

Genera un hash por cada usuario:

```bash
python scripts/hash_password.py "una-contrasena-larga-y-unica"
```

Luego configura `.env` asi:

```env
PORTAL_USERS=admin@empresa.com:scrypt:hash-generado,operador@empresa.com:scrypt:hash-generado
PORTAL_ROLES=admin@empresa.com:admin,operador@empresa.com:operador
ALLOW_DEFAULT_PORTAL_PASSWORDS=false
APP_DEBUG=false
```

## Produccion con Supabase

Para produccion, usa `SUPABASE_SERVICE_ROLE_KEY` solo en el servidor Python y
ejecuta `sql_seguridad_produccion.sql` en Supabase. Eso evita que la llave
`anon` pueda leer tablas operativas o ejecutar RPC de escritura directamente.

No publiques `SUPABASE_SERVICE_ROLE_KEY` en frontend, repositorios, capturas ni
documentacion compartida.
