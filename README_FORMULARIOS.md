# Purofinca · Formularios conectados a Supabase

Esta versión agrega el módulo **Formularios** para el operador y registra datos directamente en Supabase.

## Paso obligatorio antes de probar formularios

Ejecuta en Supabase SQL Editor el archivo:

```text
sql_formularios_rpc.sql
```

Ese archivo crea funciones RPC seguras para que la app pueda insertar formularios usando la `anon public key`, sin usar `service_role`.

## Cómo correr

```bash
pip install -r requirements.txt
python app.py
```

## Ruta nueva

```text
http://127.0.0.1:8050/portal/formularios
```

## Formularios incluidos

- Corte de esquejes: productividad, no mueve inventario.
- Siembra: productividad, no mueve inventario.
- Cosecha: mueve inventario hacia cuarto de curación, bodega o merma.
- Lavado: descuenta primera no lavada de cuarto de curación y reclasifica.
- Empaque: descuenta inventario origen y suma producto empacado.
- Despacho: descuenta producto empacado.

## Nota importante

El formulario de lavado requiere inventario disponible de:

```text
cuarto_curacion / primera / no_lavado / granel
```

El formulario de empaque permite seleccionar el inventario origen desde `v_inventario_actual`.

## Empaque transaccional

El empaque de varias lineas ahora usa `registrar_empaque_multi_app`, creado en
`sql_formularios_rpc.sql`. Si la app muestra que falta actualizar Supabase,
vuelve a ejecutar ese archivo en el SQL Editor.

Por el esquema actual, si hay descarte en varias lineas del mismo registro de
empaque, todas deben usar la misma causa de descarte.

## Mis registros por operador

Para que `/portal/mis-registros` muestre solo lo creado por el operador actual,
ejecuta una sola vez:

```text
sql_mis_registros_operador_only.sql
```

Ese script agrega la columna `creado_por_app` y la funcion `marcar_registro_app`
sin reemplazar los RPC existentes.
