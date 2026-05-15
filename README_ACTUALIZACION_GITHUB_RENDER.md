# Actualización del despliegue Puro Finca en GitHub y Render

Este paquete corresponde a la versión **Correcciones 1** preparada para actualizar el proyecto ya desplegado en Render, conservando el mismo servicio y, por tanto, el mismo enlace público.

## 1. Qué se debe subir a GitHub

Sube el contenido de esta carpeta al mismo repositorio de GitHub que ya está conectado con Render.

No subas estos elementos:

- `.env`
- Carpetas `__pycache__`
- Archivos `.pyc`
- Entornos virtuales como `.venv`, `venv` o `env`

Este ZIP final ya fue limpiado para no incluir `.env` ni archivos de caché de Python.

## 2. Archivos importantes para Render

El proyecto ya incluye los archivos necesarios para el despliegue:

- `requirements.txt`: dependencias del proyecto.
- `runtime.txt`: versión de Python recomendada.
- `render.yaml`: configuración base para Render.
- `app.py`: punto de entrada.

Configuración esperada en Render:

```bash
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:server --bind 0.0.0.0:$PORT
```

## 3. Variables de entorno que deben estar en Render

En el servicio existente de Render, revisa la sección **Environment** y confirma que existan estas variables:

```env
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
SECRET_KEY=...
PORTAL_USERS=...
PORTAL_ROLES=...
ALLOW_DEFAULT_PORTAL_PASSWORDS=false
APP_DEBUG=false
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=Lax
SESSION_LIFETIME=14400
LOGIN_MAX_ATTEMPTS=5
LOGIN_WINDOW_SECONDS=900
```

Notas:

- En Render, `SESSION_COOKIE_SECURE` debe quedar en `true` porque Render usa HTTPS.
- `SECRET_KEY` debe ser una clave larga y segura.
- `PORTAL_USERS` debe llevar los usuarios con contraseña hasheada.
- `SUPABASE_SERVICE_ROLE_KEY` nunca debe subirse a GitHub.

## 4. Cómo actualizar conservando el mismo enlace

Para conservar el mismo enlace, no crees un nuevo Web Service en Render.

Debes usar el mismo repositorio y la misma rama que ya están conectados al servicio actual de Render. Normalmente la rama es `main`.

Flujo recomendado:

1. Descomprime este ZIP en tu computador.
2. Copia el contenido de la carpeta del proyecto.
3. Reemplaza los archivos del repositorio local o súbelos al mismo repositorio en GitHub.
4. Haz commit de los cambios en la misma rama conectada a Render.
5. Render detectará el cambio y hará el nuevo deploy automáticamente si Auto-Deploy está activado.
6. Si Auto-Deploy está desactivado, entra al servicio existente en Render y usa **Manual Deploy**.

## 5. Verificación después del deploy

Cuando Render termine el despliegue, revisa:

- Que el estado del deploy diga `Live`.
- Que el login cargue correctamente.
- Que el usuario operador vea formularios e inventario.
- Que los formularios guarden en Supabase.
- Que las visualizaciones cambien después de registrar información.
- Que no aparezcan errores en la pestaña **Logs** de Render.

## 6. Si aparece error

Revisa primero:

- Que todas las variables de entorno estén completas.
- Que el Start Command sea exactamente: `gunicorn app:server --bind 0.0.0.0:$PORT`.
- Que `gunicorn` esté en `requirements.txt`.
- Que la llave de Supabase no esté vencida o mal copiada.
- Que las tablas/RPC necesarias existan en Supabase.
