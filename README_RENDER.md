# Despliegue en Render — Puro Finca

Este paquete está preparado para desplegar el portal interno en Render como **Web Service**.

## Configuración recomendada en Render

- **Service type:** Web Service
- **Runtime / Language:** Python
- **Branch:** main
- **Build Command:**

```bash
pip install -r requirements.txt
```

- **Start Command:**

```bash
gunicorn app:server --bind 0.0.0.0:$PORT
```

El archivo `runtime.txt` fija Python 3.11.9 para evitar que Render use una versión demasiado nueva de Python y aumente el riesgo de incompatibilidades.

## Variables de entorno obligatorias

Configúralas en Render en la sección **Environment**:

```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key
SECRET_KEY=clave-larga-segura
PORTAL_USERS=admin@empresa.com:scrypt:hash_generado
PORTAL_ROLES=admin@empresa.com:admin
ALLOW_DEFAULT_PORTAL_PASSWORDS=false
APP_DEBUG=false
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=Lax
SESSION_LIFETIME=14400
LOGIN_MAX_ATTEMPTS=5
LOGIN_WINDOW_SECONDS=900
```

Para generar hashes de contraseña:

```bash
python scripts/hash_password.py "tu-contrasena-segura"
```

## Notas

- No subas `.env` al repositorio.
- En Render Free, la aplicación puede dormir después de un tiempo sin uso y tardar en abrir la primera vez.
- Si Render muestra `Exited with status 127`, revisa que `gunicorn` esté en `requirements.txt` y que el Start Command sea el indicado.
