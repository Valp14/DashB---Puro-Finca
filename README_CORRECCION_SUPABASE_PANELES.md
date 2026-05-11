# Corrección Supabase como fuente principal

Esta versión corrige el problema de que algunas páginas seguían mostrando mensajes de “Importar Excel” aunque Supabase ya estuviera conectado.

Cambios aplicados:

- `store-data` y `store-archivo` ahora usan almacenamiento `memory`, para cargar el estado real de Supabase en cada ejecución y evitar estados antiguos guardados en el navegador.
- Se reemplazaron mensajes de Excel por mensajes de Supabase.
- El importador de Excel queda oculto como respaldo, pero no es el flujo principal.

Después de reemplazar el proyecto:

```bash
pip install -r requirements.txt
python app.py
```

Si antes abriste la versión anterior, haz una recarga dura del navegador con `Ctrl + F5`.
