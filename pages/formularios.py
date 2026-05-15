"""Formularios operativos conectados a Supabase.

Esta pantalla es el punto de entrada del operador. Los formularios nuevos ya
registran directamente en Supabase. Cosecha, lavado, empaque y despacho mueven
inventario mediante triggers/RPC en la base de datos.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html, no_update

from services.supabase_forms import (
    fetch_catalogs_for_forms,
    fetch_inventory_options,
    parse_inventory_value,
    registrar_corte,
    registrar_siembra,
    registrar_cosecha,
    registrar_lavado,
    registrar_empaque_multi,
    registrar_despacho_multi,
    mark_record_owner,
)
from services.supabase_data import load_operational_store
from auth import current_role, current_user
from services.access_control import (
    can_read_operational_data,
    can_submit_forms,
    empty_operational_store,
)


CLASES = [
    {"label": "Primera", "value": "primera"},
    {"label": "Segunda", "value": "segunda"},
    {"label": "Tercera", "value": "tercera"},
    {"label": "Semilla", "value": "semilla"},
]

PRESENTACIONES = [
    {"label": "Caja", "value": "caja"},
    {"label": "Saco", "value": "saco"},
    {"label": "Bolsa", "value": "bolsa"},
    {"label": "Otra", "value": "otra"},
]

SI_NO = [
    {"label": "Sí", "value": "si"},
    {"label": "No", "value": "no"},
]


def _today():
    return date.today().isoformat()


def _field(label: str, component, note: str | None = None):
    return html.Div([
        html.Label(label, className="control-label"),
        component,
        html.Div(note, className="muted", style={"fontSize": "12px", "marginTop": "4px"}) if note else None,
    ], className="form-field")


def _input(id_: str, type_: str = "text", value: Any = None, placeholder: str = ""):
    return dcc.Input(id=id_, type=type_, value=value, placeholder=placeholder, className="form-control")


def _num(id_: str, value: Any = 0, step: str = "0.01"):
    return dcc.Input(id=id_, type="number", value=value, min=0, step=step, className="form-control")


def _dropdown(id_: str, options=None, value=None, placeholder="Seleccione..."):
    return dcc.Dropdown(id=id_, options=options or [], value=value, placeholder=placeholder, clearable=True)


def _textarea(id_: str, placeholder: str = "Observaciones"):
    return dcc.Textarea(id=id_, placeholder=placeholder, className="form-control", style={"minHeight": "86px"})


def _section(title: str, children, subtitle: str | None = None):
    return html.Div([
        html.Div(title, className="section-eyebrow"),
        html.P(subtitle, className="muted") if subtitle else None,
        html.Div(children, className="form-grid"),
    ], className="section-panel form-section")


def _msg(id_: str):
    return html.Div(id=id_, className="form-message")


def _button(id_: str, text: str):
    return html.Button(text, id=id_, n_clicks=0, className="btn-primary")


def _empaque_line(prefix: str, title: str, required: bool = False):
    badge = html.Span("Obligatorio" if required else "Opcional", className="form-line-badge" + (" required" if required else ""))
    return html.Div([
        html.Div([html.Div(title, className="form-line-title"), badge], className="form-line-header"),
        html.Div([
            _field("Clase empacada", _dropdown(f"{prefix}-clase", CLASES)),
            _field("Presentación", _dropdown(f"{prefix}-presentacion", PRESENTACIONES)),
            _field("Unidades", _num(f"{prefix}-unidades", 0, "1")),
            _field("Kg por unidad", _num(f"{prefix}-kg-unidad", 0)),
            _field("Kg empacados", _num(f"{prefix}-kg", 0)),
            _field("Kg sobrante", _num(f"{prefix}-sobrante", 0)),
            _field("Kg descarte", _num(f"{prefix}-descarte", 0)),
            _field("Causa de descarte", _dropdown(f"{prefix}-causa")),
        ], className="form-grid form-grid-line"),
    ], className="form-line-card")


def _despacho_sale_line(prefix: str, title: str, required: bool = False):
    badge = html.Span("Obligatoria" if required else "Opcional", className="form-line-badge" + (" required" if required else ""))
    header = [html.Div(title, className="form-line-title"), badge]
    if not required:
        header.append(html.Button("Eliminar venta", id=f"btn-limpiar-{prefix}", n_clicks=0, className="btn-secondary btn-line-clear"))
    return html.Div([
        html.Div(header, className="form-line-header"),
        html.Div([
            _field("Tipo de venta", _input(f"{prefix}-tipo-venta", placeholder="Ej: contado, crédito, exportación")),
            _field("Tratamiento", _input(f"{prefix}-tratamiento", placeholder="Ej: lavado, curado, seleccionado")),
            _field("Clase", _dropdown(f"{prefix}-clase", CLASES)),
            _field("Presentación", _dropdown(f"{prefix}-presentacion", PRESENTACIONES)),
            _field("Unidades", _num(f"{prefix}-unidades", 0, "1")),
            _field("Kg por unidad", _num(f"{prefix}-kg-unidad", 0)),
            _field("Kg despachados", _num(f"{prefix}-kg", 0)),
            _field("Precio unitario", _num(f"{prefix}-precio", 0)),
            _field("Observaciones de venta", _textarea(f"{prefix}-obs", "Observaciones de esta venta")),
        ], className="form-grid form-grid-line"),
    ], className="form-line-card")


def _catalog_stores():
    return [
        dcc.Store(id="forms-catalogs"),
        dcc.Store(id="forms-inventory-options"),
    ]


def form_corte():
    return html.Div([
        _section("Datos generales", [
            _field("Fecha", dcc.DatePickerSingle(id="corte-fecha", date=_today(), display_format="YYYY-MM-DD")),
            _field("Finca", _dropdown("corte-finca")),
            _field("Proyecto", _dropdown("corte-proyecto")),
            _field("Lote", _dropdown("corte-lote")),
        ]),
        _section("Productividad", [
            _field("Cantidad de esquejes cortados", _num("corte-cantidad", 0, "1")),
            _field("Número de trabajadores", _num("corte-trabajadores", 0, "1")),
            _field("Horas trabajadas", _num("corte-horas", 0, "0.25")),
        ]),
        _section("Observaciones", [_field("Observaciones", _textarea("corte-obs"))]),
        html.Div([_button("btn-guardar-corte", "Registrar corte de esquejes"), _msg("msg-corte")], className="form-actions"),
    ])


def form_siembra():
    return html.Div([
        _section("Datos generales", [
            _field("Fecha", dcc.DatePickerSingle(id="siembra-fecha", date=_today(), display_format="YYYY-MM-DD")),
            _field("Finca", _dropdown("siembra-finca")),
            _field("Proyecto", _dropdown("siembra-proyecto")),
            _field("Lote", _dropdown("siembra-lote")),
        ]),
        _section("Esquejes y siembra", [
            _field("Fecha de corte de esquejes", dcc.DatePickerSingle(id="siembra-fecha-corte", display_format="YYYY-MM-DD")),
            _field("Esquejes recibidos", _num("siembra-recibidos", 0, "1")),
            _field("Cantidad sembrada", _num("siembra-cantidad", 0, "1")),
            _field("Cantidad sobrante", _num("siembra-sobrante", 0, "1")),
            _field("Cantidad descartada", _num("siembra-descartada", 0, "1")),
        ]),
        _section("Productividad", [
            _field("Número de trabajadores", _num("siembra-trabajadores", 0, "1")),
            _field("Horas trabajadas", _num("siembra-horas", 0, "0.25")),
            _field("Actividad secundaria", _input("siembra-actividad", placeholder="Ej. selección, empaque, mantenimiento")),
        ]),
        _section("Observaciones", [_field("Observaciones", _textarea("siembra-obs"))]),
        html.Div([_button("btn-guardar-siembra", "Registrar siembra"), _msg("msg-siembra")], className="form-actions"),
    ])


def form_cosecha():
    return html.Div([
        _section("Datos generales", [
            _field("Fecha", dcc.DatePickerSingle(id="cosecha-fecha", date=_today(), display_format="YYYY-MM-DD")),
            _field("Finca", _dropdown("cosecha-finca")),
            _field("Proyecto", _dropdown("cosecha-proyecto")),
            _field("Lote", _dropdown("cosecha-lote")),
            _field("Surcos cosechados", _num("cosecha-surcos", 0)),
            _field("Número de trabajadores", _num("cosecha-trabajadores", 0, "1")),
            _field("Horas trabajadas", _num("cosecha-horas", 0, "0.25")),
            _field("¿Usó maquinaria?", _dropdown("cosecha-maquinaria", SI_NO, "no")),
        ]),
        _section("Producción y clasificación inicial", [
            _field("Producción total kg", _num("cosecha-total", 0)),
            _field("Kg primera clase", _num("cosecha-primera", 0)),
            _field("Kg segunda clase", _num("cosecha-segunda", 0)),
            _field("Kg tercera clase", _num("cosecha-tercera", 0)),
            _field("Kg semilla", _num("cosecha-semilla", 0)),
            _field("Kg descarte", _num("cosecha-descarte", 0)),
            _field("Causa de descarte", _dropdown("cosecha-causa"), "Solo aplica si hay descarte."),
        ], "Primera irá a cuarto de curación. Segunda, tercera y semilla irán a bodega grande."),
        html.Div(id="resumen-cosecha", className="form-summary"),
        _section("Observaciones", [_field("Observaciones", _textarea("cosecha-obs"))]),
        html.Div([_button("btn-guardar-cosecha", "Registrar cosecha y mover inventario"), _msg("msg-cosecha")], className="form-actions"),
    ])


def form_lavado():
    return html.Div([
        _section("Datos generales", [
            _field("Fecha", dcc.DatePickerSingle(id="lavado-fecha", date=_today(), display_format="YYYY-MM-DD")),
            _field("Finca", _dropdown("lavado-finca")),
            _field("Proyecto", _dropdown("lavado-proyecto")),
            _field("Lote origen", _dropdown("lavado-lote")),
            _field("Número de trabajadores", _num("lavado-trabajadores", 0, "1")),
            _field("Horas de proceso", _num("lavado-horas", 0, "0.25")),
        ]),
        _section("Origen desde cuarto de curación", [
            _field("Kg usados para lavado", _num("lavado-usados", 0), "Debe existir inventario de primera no lavada en cuarto de curación."),
            _field("Kg lavados", _num("lavado-lavados", 0)),
        ]),
        _section("Nueva clasificación después del lavado", [
            _field("Kg primera lavada", _num("lavado-primera", 0)),
            _field("Kg segunda", _num("lavado-segunda", 0)),
            _field("Kg tercera", _num("lavado-tercera", 0)),
            _field("Kg semilla", _num("lavado-semilla", 0)),
            _field("Kg descarte", _num("lavado-descarte", 0)),
            _field("Causa de descarte", _dropdown("lavado-causa")),
        ]),
        html.Div(id="resumen-lavado", className="form-summary"),
        _section("Observaciones", [_field("Observaciones", _textarea("lavado-obs"))]),
        html.Div([_button("btn-guardar-lavado", "Registrar lavado y reclasificación"), _msg("msg-lavado")], className="form-actions"),
    ])


def form_empaque():
    return html.Div([
        _section("Datos generales", [
            _field("Fecha", dcc.DatePickerSingle(id="empaque-fecha", date=_today(), display_format="YYYY-MM-DD")),
            _field("Finca", _dropdown("empaque-finca")),
            _field("Proyecto", _dropdown("empaque-proyecto")),
            _field("Lote origen", _dropdown("empaque-lote")),
            _field("Número de trabajadores", _num("empaque-trabajadores", 0, "1")),
            _field("Horas trabajadas", _num("empaque-horas", 0, "0.25")),
        ]),
        _section("Origen del producto", [
            _field("Inventario origen", _dropdown("empaque-origen-inv"), "Selecciona el saldo disponible que se va a empacar."),
            _field("Kg usados", _num("empaque-usados", 0)),
        ]),
        _section("Detalle de empaque", [
            html.Div("Registra una o varias combinaciones de clase y presentación en un solo envío.", className="form-helper-text"),
            _empaque_line("empaque", "Empaque 1", True),
            dbc.Accordion([
                dbc.AccordionItem(_empaque_line("empaque2", "Empaque 2"), title="Agregar otro empaquetado"),
                dbc.AccordionItem(_empaque_line("empaque3", "Empaque 3"), title="Agregar otro empaquetado adicional"),
                dbc.AccordionItem(_empaque_line("empaque4", "Empaque 4"), title="Agregar un cuarto empaquetado"),
            ], start_collapsed=True, className="form-accordion"),
        ]),
        html.Div(id="resumen-empaque", className="form-summary"),
        _section("Observaciones", [_field("Observaciones", _textarea("empaque-obs"))]),
        html.Div([_button("btn-guardar-empaque", "Registrar empaque y mover inventario"), _msg("msg-empaque")], className="form-actions"),
    ])


def form_despacho():
    return html.Div([
        _section("Datos del despacho", [
            _field("Fecha", dcc.DatePickerSingle(id="despacho-fecha", date=_today(), display_format="YYYY-MM-DD")),
            _field("Cliente", _dropdown("despacho-cliente")),
            _field("Cliente nuevo / texto", _input("despacho-cliente-texto", placeholder="Solo si no está en catálogo")),
            _field("Destino", _dropdown("despacho-destino")),
            _field("Destino texto", _input("despacho-destino-texto", placeholder="Solo si no está en catálogo")),
            _field("Placa vehículo", _input("despacho-placa")),
            _field("Conductor", _input("despacho-conductor")),
            _field("Remisión", _input("despacho-remision")),
        ]),
        _section("Ventas del despacho", [
            html.Div("Registra una o varias ventas dentro del mismo despacho.", className="form-helper-text"),
            _despacho_sale_line("despacho", "Venta 1", True),
            dbc.Accordion([
                dbc.AccordionItem(_despacho_sale_line("despacho2", "Venta 2"), title="Agregar otra venta"),
                dbc.AccordionItem(_despacho_sale_line("despacho3", "Venta 3"), title="Agregar otra venta adicional"),
                dbc.AccordionItem(_despacho_sale_line("despacho4", "Venta 4"), title="Agregar una cuarta venta"),
            ], start_collapsed=True, className="form-accordion"),
        ]),
        _section("Equipo operativo", [
            _field("Número de trabajadores", _num("despacho-trabajadores", 0, "1")),
            _field("Horas trabajadas", _num("despacho-horas", 0, "0.25")),
        ]),
        html.Div(id="resumen-despacho", className="form-summary"),
        _section("Observaciones", [_field("Observaciones generales", _textarea("despacho-obs-general"))]),
        html.Div([_button("btn-guardar-despacho", "Registrar despacho y descontar inventario"), _msg("msg-despacho")], className="form-actions"),
    ])


def layout():
    return html.Div([
        *_catalog_stores(),
        html.Div([
            html.Div("Operación", className="eyebrow"),
            html.H1("Formularios del operador"),
            html.P("Registra la información diaria. Los procesos de cosecha, lavado, empaque y despacho actualizan inventario desde Supabase.", className="lead"),
        ], className="page-hero"),
        html.Div([
            dbc.Tabs([
                dbc.Tab(form_corte(), label="Corte de esquejes", tab_id="tab-corte"),
                dbc.Tab(form_siembra(), label="Siembra", tab_id="tab-siembra"),
                dbc.Tab(form_cosecha(), label="Cosecha", tab_id="tab-cosecha"),
                dbc.Tab(form_lavado(), label="Lavado", tab_id="tab-lavado"),
                dbc.Tab(form_empaque(), label="Empaque", tab_id="tab-empaque"),
                dbc.Tab(form_despacho(), label="Despacho", tab_id="tab-despacho"),
            ], id="tabs-formularios", active_tab="tab-cosecha"),
        ], className="panel-card"),
    ], className="ops-page ops-process-page process-formularios")


# ---------------------------------------------------------------------------
# Carga de catálogos y opciones
# ---------------------------------------------------------------------------
@callback(
    Output("forms-catalogs", "data"),
    Output("forms-inventory-options", "data"),
    Input("url", "pathname"),
)
def load_form_options(pathname):
    if (pathname or "").rstrip("/") != "/portal/formularios":
        return no_update, no_update
    try:
        return fetch_catalogs_for_forms(), fetch_inventory_options()
    except Exception as exc:
        return {"_error": str(exc)}, []


@callback(
    # Corte
    Output("corte-finca", "options"), Output("corte-proyecto", "options"), Output("corte-lote", "options"),
    # Siembra
    Output("siembra-finca", "options"), Output("siembra-proyecto", "options"), Output("siembra-lote", "options"),
    # Cosecha
    Output("cosecha-finca", "options"), Output("cosecha-proyecto", "options"), Output("cosecha-lote", "options"), Output("cosecha-causa", "options"),
    # Lavado
    Output("lavado-finca", "options"), Output("lavado-proyecto", "options"), Output("lavado-lote", "options"), Output("lavado-causa", "options"),
    # Empaque
    Output("empaque-finca", "options"), Output("empaque-proyecto", "options"), Output("empaque-lote", "options"), Output("empaque-causa", "options"), Output("empaque2-causa", "options"), Output("empaque3-causa", "options"), Output("empaque4-causa", "options"), Output("empaque-origen-inv", "options"),
    # Despacho
    Output("despacho-cliente", "options"), Output("despacho-destino", "options"),
    Input("forms-catalogs", "data"),
    Input("forms-inventory-options", "data"),
)
def populate_options(catalogs, inv_options):
    c = catalogs or {}
    fincas = c.get("fincas", [])
    proyectos = c.get("proyectos", [])
    lotes = c.get("lotes", [])
    causas = c.get("causas", [])
    clientes = c.get("clientes", [])
    destinos = c.get("destinos", [])
    inv = inv_options or []
    return (
        fincas, proyectos, lotes,
        fincas, proyectos, lotes,
        fincas, proyectos, lotes, causas,
        fincas, proyectos, lotes, causas,
        fincas, proyectos, lotes, causas, causas, causas, causas, inv,
        clientes, destinos,
    )


# ---------------------------------------------------------------------------
# Resúmenes automáticos
# ---------------------------------------------------------------------------
def _f(v):
    try:
        return float(v or 0)
    except Exception:
        return 0.0


def _summary_line(label, value):
    return html.Div([html.Span(label), html.B(value)])


@callback(Output("resumen-cosecha", "children"), Input("cosecha-total", "value"), Input("cosecha-primera", "value"), Input("cosecha-segunda", "value"), Input("cosecha-tercera", "value"), Input("cosecha-semilla", "value"), Input("cosecha-descarte", "value"))
def resumen_cosecha(total, primera, segunda, tercera, semilla, descarte):
    clasificado = sum(map(_f, [primera, segunda, tercera, semilla, descarte]))
    diff = _f(total) - clasificado
    nivel = "#2E7D4F" if abs(diff) < 0.01 else "#A33A3A"
    return html.Div([
        _summary_line("Producción total", f"{_f(total):,.2f} kg"),
        _summary_line("Total clasificado", f"{clasificado:,.2f} kg"),
        html.Div([html.Span("Diferencia"), html.B(f"{diff:,.2f} kg", style={"color": nivel})]),
        html.Div("Destino: primera a cuarto de curación; segunda, tercera y semilla a bodega grande; descarte a merma.", className="muted"),
    ])


@callback(Output("resumen-lavado", "children"), Input("lavado-usados", "value"), Input("lavado-lavados", "value"), Input("lavado-primera", "value"), Input("lavado-segunda", "value"), Input("lavado-tercera", "value"), Input("lavado-semilla", "value"), Input("lavado-descarte", "value"))
def resumen_lavado(usados, lavados, primera, segunda, tercera, semilla, descarte):
    clasificado = sum(map(_f, [primera, segunda, tercera, semilla, descarte]))
    diff = _f(lavados) - clasificado
    return html.Div([
        _summary_line("Kg usados", f"{_f(usados):,.2f} kg"),
        _summary_line("Kg lavados", f"{_f(lavados):,.2f} kg"),
        _summary_line("Total reclasificado", f"{clasificado:,.2f} kg"),
        html.Div([html.Span("Diferencia"), html.B(f"{diff:,.2f} kg", style={"color": "#2E7D4F" if abs(diff)<0.01 else "#A33A3A"})]),
    ])


@callback(
    Output("resumen-empaque", "children"),
    Input("empaque-usados", "value"),
    Input("empaque-kg", "value"), Input("empaque-sobrante", "value"), Input("empaque-descarte", "value"),
    Input("empaque2-kg", "value"), Input("empaque2-sobrante", "value"), Input("empaque2-descarte", "value"),
    Input("empaque3-kg", "value"), Input("empaque3-sobrante", "value"), Input("empaque3-descarte", "value"),
    Input("empaque4-kg", "value"), Input("empaque4-sobrante", "value"), Input("empaque4-descarte", "value"),
)
def resumen_empaque(usados, kg, sobrante, descarte, kg2, sobrante2, descarte2, kg3, sobrante3, descarte3, kg4, sobrante4, descarte4):
    lineas = [
        _f(kg)+_f(sobrante)+_f(descarte),
        _f(kg2)+_f(sobrante2)+_f(descarte2),
        _f(kg3)+_f(sobrante3)+_f(descarte3),
        _f(kg4)+_f(sobrante4)+_f(descarte4),
    ]
    salida = sum(lineas)
    diff = _f(usados)-salida
    activas = sum(1 for v in lineas if v > 0)
    return html.Div([
        _summary_line("Kg usados", f"{_f(usados):,.2f} kg"),
        _summary_line("Líneas de empaque activas", str(activas)),
        _summary_line("Empacado + sobrante + descarte", f"{salida:,.2f} kg"),
        html.Div([html.Span("Diferencia"), html.B(f"{diff:,.2f} kg", style={"color": "#2E7D4F" if abs(diff)<0.01 else "#A33A3A"})]),
    ])

@callback(
    Output("resumen-despacho", "children"),
    Input("despacho-kg", "value"), Input("despacho-unidades", "value"), Input("despacho-kg-unidad", "value"), Input("despacho-precio", "value"),
    Input("despacho2-kg", "value"), Input("despacho2-unidades", "value"), Input("despacho2-kg-unidad", "value"), Input("despacho2-precio", "value"),
    Input("despacho3-kg", "value"), Input("despacho3-unidades", "value"), Input("despacho3-kg-unidad", "value"), Input("despacho3-precio", "value"),
    Input("despacho4-kg", "value"), Input("despacho4-unidades", "value"), Input("despacho4-kg-unidad", "value"), Input("despacho4-precio", "value"),
)
def resumen_despacho(kg, unidades, kg_unidad, precio, kg2, unidades2, kg_unidad2, precio2, kg3, unidades3, kg_unidad3, precio3, kg4, unidades4, kg_unidad4, precio4):
    lineas = [
        (_f(kg), _f(unidades), _f(kg_unidad), _f(precio)),
        (_f(kg2), _f(unidades2), _f(kg_unidad2), _f(precio2)),
        (_f(kg3), _f(unidades3), _f(kg_unidad3), _f(precio3)),
        (_f(kg4), _f(unidades4), _f(kg_unidad4), _f(precio4)),
    ]
    total_kg = sum(line[0] for line in lineas)
    estimado = sum(line[1] * line[2] for line in lineas)
    valor = sum(line[0] * line[3] for line in lineas if line[3] > 0)
    activas = sum(1 for line in lineas if line[0] > 0 or line[1] > 0 or line[2] > 0)
    return html.Div([
        _summary_line("Ventas activas", str(activas)),
        _summary_line("Kg despachados", f"{total_kg:,.2f} kg"),
        _summary_line("Kg estimados por unidades", f"{estimado:,.2f} kg"),
        _summary_line("Valor estimado", f"{valor:,.2f}" if valor > 0 else "-"),
    ])


# ---------------------------------------------------------------------------
# Guardado de formularios
# ---------------------------------------------------------------------------
def _ok(text):
    return html.Div([html.B("Formulario enviado exitosamente. "), html.Span(text)], className="alert alert-success")


def _err(text):
    return html.Div(str(text), className="alert alert-danger")


def _refresh():
    if can_read_operational_data(current_role()):
        return load_operational_store()
    return empty_operational_store()


def _can_write_forms():
    return can_submit_forms(current_role())


def _forbidden_write():
    return _err("Tu perfil no tiene permiso para registrar formularios."), no_update


def _mark_owner(table: str, record_id: Any) -> None:
    mark_record_owner(table, record_id, current_user())


def _missing_fields(fields: list[tuple[str, Any]]) -> list[str]:
    missing = []
    for label, value in fields:
        if value is None or str(value).strip() == "":
            missing.append(label)
    return missing


def _invalid_date(value: Any) -> bool:
    if value is None or str(value).strip() == "":
        return True
    try:
        date.fromisoformat(str(value)[:10])
        return False
    except Exception:
        return True


def _missing_error(fields: list[str]):
    return _err("Completa estos campos: " + ", ".join(fields) + "."), no_update


def _positive_error(fields: list[str]):
    return _err("Estos valores deben ser mayores a cero: " + ", ".join(fields) + "."), no_update


def _nonnegative_error(fields: list[str]):
    return _err("Estos valores no pueden ser negativos: " + ", ".join(fields) + "."), no_update


def _approx_equal(a: Any, b: Any, tolerance: float = 0.01) -> bool:
    return abs(_f(a) - _f(b)) <= tolerance


def _validate_common(fecha, finca, proyecto, lote=None, lote_label="Lote"):
    fields = [("Fecha", fecha), ("Finca", finca), ("Proyecto", proyecto)]
    if lote_label:
        fields.append((lote_label, lote))
    missing = _missing_fields(fields)
    if fecha and _invalid_date(fecha):
        missing.append("Fecha valida")
    if missing:
        return _missing_error(missing)
    return None


@callback(Output("msg-corte", "children"), Output("store-data", "data", allow_duplicate=True), Input("btn-guardar-corte", "n_clicks"), State("corte-fecha", "date"), State("corte-finca", "value"), State("corte-proyecto", "value"), State("corte-lote", "value"), State("corte-cantidad", "value"), State("corte-trabajadores", "value"), State("corte-horas", "value"), State("corte-obs", "value"), prevent_initial_call=True)
def submit_corte(n, fecha, finca, proyecto, lote, cantidad, trabajadores, horas, obs):
    if not n: return no_update, no_update
    if not _can_write_forms(): return _forbidden_write()
    common_error = _validate_common(fecha, finca, proyecto, lote)
    if common_error: return common_error
    if _f(cantidad) <= 0 or _f(trabajadores) <= 0 or _f(horas) <= 0:
        return _err("Cantidad, trabajadores y horas deben ser mayores a cero."), no_update
    try:
        record_id = registrar_corte({"p_fecha": fecha, "p_finca_id": finca, "p_proyecto_id": proyecto, "p_lote_id": lote, "p_cantidad_esquejes": int(_f(cantidad)), "p_numero_trabajadores": int(_f(trabajadores)), "p_horas_trabajadas": _f(horas), "p_observaciones": obs})
        _mark_owner("form_corte_esquejes", record_id)
        return _ok("Corte de esquejes registrado correctamente."), _refresh()
    except Exception as exc:
        return _err(exc), no_update


@callback(Output("msg-siembra", "children"), Output("store-data", "data", allow_duplicate=True), Input("btn-guardar-siembra", "n_clicks"), State("siembra-fecha", "date"), State("siembra-finca", "value"), State("siembra-proyecto", "value"), State("siembra-lote", "value"), State("siembra-fecha-corte", "date"), State("siembra-recibidos", "value"), State("siembra-cantidad", "value"), State("siembra-sobrante", "value"), State("siembra-descartada", "value"), State("siembra-trabajadores", "value"), State("siembra-horas", "value"), State("siembra-actividad", "value"), State("siembra-obs", "value"), prevent_initial_call=True)
def submit_siembra(n, fecha, finca, proyecto, lote, fecha_corte, recibidos, cantidad, sobrante, descartada, trabajadores, horas, actividad, obs):
    if not n: return no_update, no_update
    if not _can_write_forms(): return _forbidden_write()
    common_error = _validate_common(fecha, finca, proyecto, lote)
    if common_error: return common_error
    missing = _missing_fields([("Fecha de corte de esquejes", fecha_corte)])
    if fecha_corte and _invalid_date(fecha_corte):
        missing.append("Fecha de corte valida")
    if missing: return _missing_error(missing)
    if _f(cantidad) <= 0 or _f(trabajadores) <= 0 or _f(horas) <= 0:
        return _err("Cantidad sembrada, trabajadores y horas deben ser mayores a cero."), no_update
    if _f(recibidos) <= 0:
        return _positive_error(["Esquejes recibidos"])
    negative = []
    if _f(sobrante) < 0: negative.append("Cantidad sobrante")
    if _f(descartada) < 0: negative.append("Cantidad descartada")
    if negative: return _nonnegative_error(negative)
    if not _approx_equal(recibidos, _f(cantidad) + _f(sobrante) + _f(descartada)):
        return _err("Esquejes recibidos debe coincidir con sembrados + sobrante + descartada."), no_update
    try:
        record_id = registrar_siembra({"p_fecha": fecha, "p_finca_id": finca, "p_proyecto_id": proyecto, "p_lote_id": lote, "p_fecha_corte_esquejes": fecha_corte, "p_cantidad_esquejes_recibidos": int(_f(recibidos)), "p_cantidad_sembrada": int(_f(cantidad)), "p_cantidad_sobrante": int(_f(sobrante)), "p_cantidad_descartada": int(_f(descartada)), "p_numero_trabajadores": int(_f(trabajadores)), "p_horas_trabajadas": _f(horas), "p_actividad_secundaria": actividad, "p_observaciones": obs})
        _mark_owner("form_siembra", record_id)
        return _ok("Siembra registrada correctamente."), _refresh()
    except Exception as exc:
        return _err(exc), no_update


@callback(Output("msg-cosecha", "children"), Output("store-data", "data", allow_duplicate=True), Input("btn-guardar-cosecha", "n_clicks"), State("cosecha-fecha", "date"), State("cosecha-finca", "value"), State("cosecha-proyecto", "value"), State("cosecha-lote", "value"), State("cosecha-surcos", "value"), State("cosecha-trabajadores", "value"), State("cosecha-horas", "value"), State("cosecha-maquinaria", "value"), State("cosecha-total", "value"), State("cosecha-primera", "value"), State("cosecha-segunda", "value"), State("cosecha-tercera", "value"), State("cosecha-semilla", "value"), State("cosecha-descarte", "value"), State("cosecha-causa", "value"), State("cosecha-obs", "value"), prevent_initial_call=True)
def submit_cosecha(n, fecha, finca, proyecto, lote, surcos, trabajadores, horas, maq, total, primera, segunda, tercera, semilla, descarte, causa, obs):
    if not n: return no_update, no_update
    if not _can_write_forms(): return _forbidden_write()
    common_error = _validate_common(fecha, finca, proyecto, lote)
    if common_error: return common_error
    positive = []
    if _f(surcos) <= 0: positive.append("Surcos cosechados")
    if _f(trabajadores) <= 0: positive.append("Trabajadores")
    if _f(horas) <= 0: positive.append("Horas")
    if positive: return _positive_error(positive)
    clasificado = sum(map(_f, [primera, segunda, tercera, semilla, descarte]))
    negative = []
    for label, value in [
        ("Kg primera", primera),
        ("Kg segunda", segunda),
        ("Kg tercera", tercera),
        ("Kg semilla", semilla),
        ("Kg descarte", descarte),
    ]:
        if _f(value) < 0:
            negative.append(label)
    if negative: return _nonnegative_error(negative)
    if _f(total) <= 0 or abs(_f(total) - clasificado) >= 0.01:
        return _err("La producción total debe ser mayor a cero y coincidir con la clasificación."), no_update
    try:
        record_id = registrar_cosecha({"p_fecha": fecha, "p_finca_id": finca, "p_proyecto_id": proyecto, "p_lote_id": lote, "p_surcos_cosechados": _f(surcos), "p_numero_trabajadores": int(_f(trabajadores)), "p_horas_trabajadas": _f(horas), "p_uso_maquinaria": maq == "si", "p_produccion_total_kg": _f(total), "p_kg_primera": _f(primera), "p_kg_segunda": _f(segunda), "p_kg_tercera": _f(tercera), "p_kg_semilla": _f(semilla), "p_kg_descarte": _f(descarte), "p_causa_descarte_id": causa, "p_observaciones": obs})
        _mark_owner("form_cosecha", record_id)
        return _ok("Cosecha registrada. El inventario fue actualizado automáticamente."), _refresh()
    except Exception as exc:
        return _err(exc), no_update


@callback(Output("msg-lavado", "children"), Output("store-data", "data", allow_duplicate=True), Input("btn-guardar-lavado", "n_clicks"), State("lavado-fecha", "date"), State("lavado-finca", "value"), State("lavado-proyecto", "value"), State("lavado-lote", "value"), State("lavado-usados", "value"), State("lavado-lavados", "value"), State("lavado-primera", "value"), State("lavado-segunda", "value"), State("lavado-tercera", "value"), State("lavado-semilla", "value"), State("lavado-descarte", "value"), State("lavado-trabajadores", "value"), State("lavado-horas", "value"), State("lavado-causa", "value"), State("lavado-obs", "value"), prevent_initial_call=True)
def submit_lavado(n, fecha, finca, proyecto, lote, usados, lavados, primera, segunda, tercera, semilla, descarte, trabajadores, horas, causa, obs):
    if not n: return no_update, no_update
    if not _can_write_forms(): return _forbidden_write()
    common_error = _validate_common(fecha, finca, proyecto, lote, "Lote origen")
    if common_error: return common_error
    positive = []
    if _f(usados) <= 0: positive.append("Kg usados")
    if _f(lavados) <= 0: positive.append("Kg lavados")
    if _f(trabajadores) <= 0: positive.append("Trabajadores")
    if _f(horas) <= 0: positive.append("Horas")
    if positive: return _positive_error(positive)
    clasificado = sum(map(_f, [primera, segunda, tercera, semilla, descarte]))
    negative = []
    for label, value in [
        ("Kg primera lavada", primera),
        ("Kg segunda", segunda),
        ("Kg tercera", tercera),
        ("Kg semilla", semilla),
        ("Kg descarte", descarte),
    ]:
        if _f(value) < 0:
            negative.append(label)
    if negative: return _nonnegative_error(negative)
    if _f(lavados) <= 0 or abs(_f(lavados)-clasificado) >= 0.01 or abs(_f(usados)-_f(lavados)) >= 0.01:
        return _err("Kg usados, kg lavados y suma reclasificada deben coincidir."), no_update
    try:
        record_id = registrar_lavado({"p_fecha": fecha, "p_finca_id": finca, "p_proyecto_id": proyecto, "p_lote_origen_id": lote, "p_kg_usados": _f(usados), "p_kg_lavados": _f(lavados), "p_kg_primera_lavada": _f(primera), "p_kg_segunda": _f(segunda), "p_kg_tercera": _f(tercera), "p_kg_semilla": _f(semilla), "p_kg_descarte": _f(descarte), "p_numero_trabajadores": int(_f(trabajadores)), "p_horas_proceso": _f(horas), "p_causa_descarte_id": causa, "p_observaciones": obs})
        _mark_owner("form_lavado_clasificacion", record_id)
        return _ok("Lavado registrado. El inventario fue actualizado automáticamente."), _refresh()
    except Exception as exc:
        return _err(exc), no_update


@callback(
    Output("msg-empaque", "children"),
    Output("store-data", "data", allow_duplicate=True),
    Input("btn-guardar-empaque", "n_clicks"),
    State("empaque-fecha", "date"), State("empaque-finca", "value"), State("empaque-proyecto", "value"), State("empaque-lote", "value"),
    State("empaque-origen-inv", "value"), State("empaque-usados", "value"),
    State("empaque-clase", "value"), State("empaque-presentacion", "value"), State("empaque-unidades", "value"), State("empaque-kg-unidad", "value"), State("empaque-kg", "value"), State("empaque-sobrante", "value"), State("empaque-descarte", "value"), State("empaque-causa", "value"),
    State("empaque2-clase", "value"), State("empaque2-presentacion", "value"), State("empaque2-unidades", "value"), State("empaque2-kg-unidad", "value"), State("empaque2-kg", "value"), State("empaque2-sobrante", "value"), State("empaque2-descarte", "value"), State("empaque2-causa", "value"),
    State("empaque3-clase", "value"), State("empaque3-presentacion", "value"), State("empaque3-unidades", "value"), State("empaque3-kg-unidad", "value"), State("empaque3-kg", "value"), State("empaque3-sobrante", "value"), State("empaque3-descarte", "value"), State("empaque3-causa", "value"),
    State("empaque4-clase", "value"), State("empaque4-presentacion", "value"), State("empaque4-unidades", "value"), State("empaque4-kg-unidad", "value"), State("empaque4-kg", "value"), State("empaque4-sobrante", "value"), State("empaque4-descarte", "value"), State("empaque4-causa", "value"),
    State("empaque-trabajadores", "value"), State("empaque-horas", "value"), State("empaque-obs", "value"),
    prevent_initial_call=True,
)
def submit_empaque(n, fecha, finca, proyecto, lote, inv_value, usados,
                    clase, pres, unidades, kg_unidad, kg, sobrante, descarte, causa,
                    clase2, pres2, unidades2, kg_unidad2, kg2, sobrante2, descarte2, causa2,
                    clase3, pres3, unidades3, kg_unidad3, kg3, sobrante3, descarte3, causa3,
                    clase4, pres4, unidades4, kg_unidad4, kg4, sobrante4, descarte4, causa4,
                    trabajadores, horas, obs):
    if not n: return no_update, no_update
    if not _can_write_forms(): return _forbidden_write()
    common_error = _validate_common(fecha, finca, proyecto, lote, "Lote origen")
    if common_error: return common_error
    inv = parse_inventory_value(inv_value)
    if not inv.get("ubicacion"):
        return _err("Selecciona inventario origen."), no_update
    positive = []
    if _f(usados) <= 0: positive.append("Kg usados")
    if _f(trabajadores) <= 0: positive.append("Trabajadores")
    if _f(horas) <= 0: positive.append("Horas")
    if positive: return _positive_error(positive)

    lineas = [
        (clase, pres, unidades, kg_unidad, kg, sobrante, descarte, causa),
        (clase2, pres2, unidades2, kg_unidad2, kg2, sobrante2, descarte2, causa2),
        (clase3, pres3, unidades3, kg_unidad3, kg3, sobrante3, descarte3, causa3),
        (clase4, pres4, unidades4, kg_unidad4, kg4, sobrante4, descarte4, causa4),
    ]
    activas = []
    for i, (cl, pr, un, kgu, kge, sob, des, cau) in enumerate(lineas, start=1):
        total_linea = _f(kge) + _f(sob) + _f(des)
        tiene_datos = total_linea > 0 or bool(cl or pr or _f(un) or _f(kgu))
        if not tiene_datos:
            continue
        negative = []
        if _f(sob) < 0: negative.append("Kg sobrante")
        if _f(des) < 0: negative.append("Kg descarte")
        if negative: return _nonnegative_error([f"Empaque {i}: {x}" for x in negative])
        if not cl or not pr or _f(kge) <= 0:
            return _err(f"En Empaque {i}, clase, presentación y kg empacados son obligatorios."), no_update
        if _f(un) <= 0 or _f(kgu) <= 0:
            return _err(f"En Empaque {i}, unidades y kg por unidad deben ser mayores a cero."), no_update
        if not _approx_equal(_f(un) * _f(kgu), kge, tolerance=0.05):
            return _err(f"En Empaque {i}, unidades por kg por unidad debe coincidir con kg empacados."), no_update
        activas.append({
            "clase": cl,
            "presentacion": pr,
            "unidades": int(_f(un)),
            "kg_por_unidad": _f(kgu),
            "kg_empacados": _f(kge),
            "kg_sobrante": _f(sob),
            "kg_descarte": _f(des),
            "causa_descarte_id": cau,
        })

    if not activas:
        return _err("Registra al menos una línea de empaque con kg empacados."), no_update

    salida = sum(_f(line["kg_empacados"])+_f(line["kg_sobrante"])+_f(line["kg_descarte"]) for line in activas)
    if abs(_f(usados) - salida) >= 0.01:
        return _err("Kg usados debe coincidir con la suma de todas las líneas: kg empacados + sobrante + descarte."), no_update
    if _f(trabajadores) <= 0 or _f(horas) <= 0:
        return _err("Trabajadores y horas deben ser mayores a cero."), no_update

    try:
        record_id = registrar_empaque_multi({"p_fecha": fecha, "p_finca_id": finca, "p_proyecto_id": proyecto, "p_lote_origen_id": lote, "p_ubicacion_origen": inv["ubicacion"], "p_clase_origen": inv["clase"], "p_estado_origen": inv["estado"], "p_presentacion_origen": inv["presentacion"], "p_kg_usados": _f(usados), "p_numero_trabajadores": int(_f(trabajadores)), "p_horas_trabajadas": _f(horas), "p_lineas": activas, "p_observaciones": obs})
        _mark_owner("form_empaque", record_id)
        return _ok(f"Se registraron {len(activas)} línea(s) de empaque y el inventario fue actualizado automáticamente."), _refresh()
    except Exception as exc:
        if "registrar_empaque_multi_app" in str(exc):
            return _err("Falta actualizar Supabase: ejecuta sql_formularios_rpc.sql para habilitar el registro transaccional de empaque."), no_update
        return _err(exc), no_update

@callback(
    Output("msg-despacho", "children"),
    Output("store-data", "data", allow_duplicate=True),
    Input("btn-guardar-despacho", "n_clicks"),
    State("despacho-fecha", "date"), State("despacho-cliente", "value"), State("despacho-cliente-texto", "value"), State("despacho-destino", "value"), State("despacho-destino-texto", "value"), State("despacho-placa", "value"), State("despacho-conductor", "value"), State("despacho-remision", "value"),
    State("despacho-tipo-venta", "value"), State("despacho-tratamiento", "value"), State("despacho-clase", "value"), State("despacho-presentacion", "value"), State("despacho-unidades", "value"), State("despacho-kg-unidad", "value"), State("despacho-kg", "value"), State("despacho-precio", "value"), State("despacho-obs", "value"),
    State("despacho2-tipo-venta", "value"), State("despacho2-tratamiento", "value"), State("despacho2-clase", "value"), State("despacho2-presentacion", "value"), State("despacho2-unidades", "value"), State("despacho2-kg-unidad", "value"), State("despacho2-kg", "value"), State("despacho2-precio", "value"), State("despacho2-obs", "value"),
    State("despacho3-tipo-venta", "value"), State("despacho3-tratamiento", "value"), State("despacho3-clase", "value"), State("despacho3-presentacion", "value"), State("despacho3-unidades", "value"), State("despacho3-kg-unidad", "value"), State("despacho3-kg", "value"), State("despacho3-precio", "value"), State("despacho3-obs", "value"),
    State("despacho4-tipo-venta", "value"), State("despacho4-tratamiento", "value"), State("despacho4-clase", "value"), State("despacho4-presentacion", "value"), State("despacho4-unidades", "value"), State("despacho4-kg-unidad", "value"), State("despacho4-kg", "value"), State("despacho4-precio", "value"), State("despacho4-obs", "value"),
    State("despacho-trabajadores", "value"), State("despacho-horas", "value"), State("despacho-obs-general", "value"),
    prevent_initial_call=True,
)
def submit_despacho(n, fecha, cliente, cliente_texto, destino, destino_texto, placa, conductor, remision,
                    tipo, tratamiento, clase, pres, unidades, kg_unidad, kg, precio, obs_linea,
                    tipo2, tratamiento2, clase2, pres2, unidades2, kg_unidad2, kg2, precio2, obs_linea2,
                    tipo3, tratamiento3, clase3, pres3, unidades3, kg_unidad3, kg3, precio3, obs_linea3,
                    tipo4, tratamiento4, clase4, pres4, unidades4, kg_unidad4, kg4, precio4, obs_linea4,
                    trabajadores, horas, obs):
    if not n: return no_update, no_update
    if not _can_write_forms(): return _forbidden_write()
    missing = _missing_fields([("Fecha", fecha), ("Placa vehiculo", placa)])
    if fecha and _invalid_date(fecha):
        missing.append("Fecha valida")
    if missing: return _missing_error(missing)
    if not (cliente or cliente_texto):
        return _err("Selecciona o escribe un cliente."), no_update
    if not (destino or destino_texto):
        return _err("Selecciona o escribe un destino."), no_update
    positive = []
    if _f(trabajadores) <= 0: positive.append("Trabajadores")
    if _f(horas) <= 0: positive.append("Horas")
    if positive: return _positive_error(positive)

    lineas_raw = [
        (tipo, tratamiento, clase, pres, unidades, kg_unidad, kg, precio, obs_linea),
        (tipo2, tratamiento2, clase2, pres2, unidades2, kg_unidad2, kg2, precio2, obs_linea2),
        (tipo3, tratamiento3, clase3, pres3, unidades3, kg_unidad3, kg3, precio3, obs_linea3),
        (tipo4, tratamiento4, clase4, pres4, unidades4, kg_unidad4, kg4, precio4, obs_linea4),
    ]
    ventas = []
    for i, (tip, trat, cl, pr, un, kgu, kge, pre, obs_v) in enumerate(lineas_raw, start=1):
        tiene_datos = bool(tip or trat or cl or pr or obs_v) or _f(un) > 0 or _f(kgu) > 0 or _f(kge) > 0 or _f(pre) > 0
        if not tiene_datos:
            continue
        if not cl or not pr or _f(kge) <= 0:
            return _err(f"En Venta {i}, clase, presentación y kg despachados son obligatorios."), no_update
        if _f(un) <= 0 or _f(kgu) <= 0:
            return _err(f"En Venta {i}, unidades y kg por unidad deben ser mayores a cero."), no_update
        if _f(pre) < 0:
            return _err(f"En Venta {i}, el precio no puede ser negativo."), no_update
        if not _approx_equal(_f(un) * _f(kgu), kge, tolerance=0.05):
            return _err(f"En Venta {i}, unidades por kg por unidad debe coincidir con kg despachados."), no_update
        ventas.append({
            "tipo_venta": tip,
            "tratamiento": trat,
            "clase": cl,
            "presentacion": pr,
            "unidades": int(_f(un)),
            "kg_por_unidad": _f(kgu),
            "kg_despachados": _f(kge),
            "precio_unitario": _f(pre),
            "observaciones": obs_v,
        })

    if not ventas:
        return _err("Registra al menos una venta con kg despachados."), no_update

    try:
        record_id = registrar_despacho_multi({"p_fecha": fecha, "p_cliente_id": cliente, "p_cliente_texto": cliente_texto, "p_destino_id": destino, "p_destino_texto": destino_texto, "p_placa_vehiculo": placa, "p_conductor": conductor, "p_numero_remision": remision, "p_numero_trabajadores": int(_f(trabajadores)), "p_horas_trabajadas": _f(horas), "p_ventas": ventas, "p_observaciones": obs})
        _mark_owner("form_despacho", record_id)
        return _ok(f"Despacho registrado con {len(ventas)} venta(s). El inventario fue descontado automáticamente."), _refresh()
    except Exception as exc:
        if "registrar_despacho_multi_app" in str(exc):
            return _err("Falta actualizar Supabase: ejecuta sql_formularios_rpc.sql para habilitar ventas múltiples en despacho."), no_update
        return _err(exc), no_update


# ---------------------------------------------------------------------------
# Limpieza automática después de envíos exitosos
# ---------------------------------------------------------------------------
def _is_success_msg(children):
    return "Formulario enviado exitosamente" in str(children or "")

@callback(
    Output("corte-cantidad", "value"), Output("corte-trabajadores", "value"), Output("corte-horas", "value"), Output("corte-obs", "value"),
    Input("msg-corte", "children"), prevent_initial_call=True,
)
def reset_corte_form(msg):
    if not _is_success_msg(msg): return no_update, no_update, no_update, no_update
    return 0, 0, 0, ""

@callback(
    Output("siembra-fecha-corte", "date"), Output("siembra-recibidos", "value"), Output("siembra-cantidad", "value"), Output("siembra-sobrante", "value"), Output("siembra-descartada", "value"), Output("siembra-trabajadores", "value"), Output("siembra-horas", "value"), Output("siembra-actividad", "value"), Output("siembra-obs", "value"),
    Input("msg-siembra", "children"), prevent_initial_call=True,
)
def reset_siembra_form(msg):
    if not _is_success_msg(msg): return (no_update,)*9
    return None, 0, 0, 0, 0, 0, 0, "", ""

@callback(
    Output("cosecha-surcos", "value"), Output("cosecha-trabajadores", "value"), Output("cosecha-horas", "value"), Output("cosecha-maquinaria", "value"), Output("cosecha-total", "value"), Output("cosecha-primera", "value"), Output("cosecha-segunda", "value"), Output("cosecha-tercera", "value"), Output("cosecha-semilla", "value"), Output("cosecha-descarte", "value"), Output("cosecha-causa", "value"), Output("cosecha-obs", "value"),
    Input("msg-cosecha", "children"), prevent_initial_call=True,
)
def reset_cosecha_form(msg):
    if not _is_success_msg(msg): return (no_update,)*12
    return 0, 0, 0, "no", 0, 0, 0, 0, 0, 0, None, ""

@callback(
    Output("lavado-usados", "value"), Output("lavado-lavados", "value"), Output("lavado-primera", "value"), Output("lavado-segunda", "value"), Output("lavado-tercera", "value"), Output("lavado-semilla", "value"), Output("lavado-descarte", "value"), Output("lavado-trabajadores", "value"), Output("lavado-horas", "value"), Output("lavado-causa", "value"), Output("lavado-obs", "value"),
    Input("msg-lavado", "children"), prevent_initial_call=True,
)
def reset_lavado_form(msg):
    if not _is_success_msg(msg): return (no_update,)*11
    return 0, 0, 0, 0, 0, 0, 0, 0, 0, None, ""

@callback(
    Output("empaque-origen-inv", "value"), Output("empaque-usados", "value"),
    Output("empaque-clase", "value"), Output("empaque-presentacion", "value"), Output("empaque-unidades", "value"), Output("empaque-kg-unidad", "value"), Output("empaque-kg", "value"), Output("empaque-sobrante", "value"), Output("empaque-descarte", "value"), Output("empaque-causa", "value"),
    Output("empaque2-clase", "value"), Output("empaque2-presentacion", "value"), Output("empaque2-unidades", "value"), Output("empaque2-kg-unidad", "value"), Output("empaque2-kg", "value"), Output("empaque2-sobrante", "value"), Output("empaque2-descarte", "value"), Output("empaque2-causa", "value"),
    Output("empaque3-clase", "value"), Output("empaque3-presentacion", "value"), Output("empaque3-unidades", "value"), Output("empaque3-kg-unidad", "value"), Output("empaque3-kg", "value"), Output("empaque3-sobrante", "value"), Output("empaque3-descarte", "value"), Output("empaque3-causa", "value"),
    Output("empaque4-clase", "value"), Output("empaque4-presentacion", "value"), Output("empaque4-unidades", "value"), Output("empaque4-kg-unidad", "value"), Output("empaque4-kg", "value"), Output("empaque4-sobrante", "value"), Output("empaque4-descarte", "value"), Output("empaque4-causa", "value"),
    Output("empaque-trabajadores", "value"), Output("empaque-horas", "value"), Output("empaque-obs", "value"),
    Input("msg-empaque", "children"), prevent_initial_call=True,
)
def reset_empaque_form(msg):
    if not _is_success_msg(msg): return (no_update,)*37
    return (None, 0, None, None, 0, 0, 0, 0, 0, None, None, None, 0, 0, 0, 0, 0, None, None, None, 0, 0, 0, 0, 0, None, None, None, 0, 0, 0, 0, 0, None, 0, 0, "")

@callback(
    Output("despacho-cliente", "value"), Output("despacho-cliente-texto", "value"), Output("despacho-destino", "value"), Output("despacho-destino-texto", "value"), Output("despacho-placa", "value"), Output("despacho-conductor", "value"), Output("despacho-remision", "value"),
    Output("despacho-tipo-venta", "value"), Output("despacho-tratamiento", "value"), Output("despacho-clase", "value"), Output("despacho-presentacion", "value"), Output("despacho-unidades", "value"), Output("despacho-kg-unidad", "value"), Output("despacho-kg", "value"), Output("despacho-precio", "value"), Output("despacho-obs", "value"),
    Output("despacho2-tipo-venta", "value"), Output("despacho2-tratamiento", "value"), Output("despacho2-clase", "value"), Output("despacho2-presentacion", "value"), Output("despacho2-unidades", "value"), Output("despacho2-kg-unidad", "value"), Output("despacho2-kg", "value"), Output("despacho2-precio", "value"), Output("despacho2-obs", "value"),
    Output("despacho3-tipo-venta", "value"), Output("despacho3-tratamiento", "value"), Output("despacho3-clase", "value"), Output("despacho3-presentacion", "value"), Output("despacho3-unidades", "value"), Output("despacho3-kg-unidad", "value"), Output("despacho3-kg", "value"), Output("despacho3-precio", "value"), Output("despacho3-obs", "value"),
    Output("despacho4-tipo-venta", "value"), Output("despacho4-tratamiento", "value"), Output("despacho4-clase", "value"), Output("despacho4-presentacion", "value"), Output("despacho4-unidades", "value"), Output("despacho4-kg-unidad", "value"), Output("despacho4-kg", "value"), Output("despacho4-precio", "value"), Output("despacho4-obs", "value"),
    Output("despacho-trabajadores", "value"), Output("despacho-horas", "value"), Output("despacho-obs-general", "value"),
    Input("msg-despacho", "children"), prevent_initial_call=True,
)
def reset_despacho_form(msg):
    if not _is_success_msg(msg): return (no_update,)*46
    empty_line = ("", "", None, None, 0, 0, 0, 0, "")
    return (None, "", None, "", "", "", "", *empty_line, *empty_line, *empty_line, *empty_line, 0, 0, "")


def _clear_despacho_line_outputs(prefix: str):
    return (
        Output(f"{prefix}-tipo-venta", "value", allow_duplicate=True),
        Output(f"{prefix}-tratamiento", "value", allow_duplicate=True),
        Output(f"{prefix}-clase", "value", allow_duplicate=True),
        Output(f"{prefix}-presentacion", "value", allow_duplicate=True),
        Output(f"{prefix}-unidades", "value", allow_duplicate=True),
        Output(f"{prefix}-kg-unidad", "value", allow_duplicate=True),
        Output(f"{prefix}-kg", "value", allow_duplicate=True),
        Output(f"{prefix}-precio", "value", allow_duplicate=True),
        Output(f"{prefix}-obs", "value", allow_duplicate=True),
    )


def _clear_despacho_line(n):
    if not n:
        return (no_update,) * 9
    return "", "", None, None, 0, 0, 0, 0, ""


@callback(*_clear_despacho_line_outputs("despacho2"), Input("btn-limpiar-despacho2", "n_clicks"), prevent_initial_call=True)
def clear_despacho2(n):
    return _clear_despacho_line(n)


@callback(*_clear_despacho_line_outputs("despacho3"), Input("btn-limpiar-despacho3", "n_clicks"), prevent_initial_call=True)
def clear_despacho3(n):
    return _clear_despacho_line(n)


@callback(*_clear_despacho_line_outputs("despacho4"), Input("btn-limpiar-despacho4", "n_clicks"), prevent_initial_call=True)
def clear_despacho4(n):
    return _clear_despacho_line(n)
