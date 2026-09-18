"""
Capa de acceso a datos. Envuelve las llamadas a Supabase para que el
resto del codigo (blueprints) no dependa directamente del cliente.

En MODO_DEMO (sin credenciales de Supabase) devuelve datos de ejemplo
en memoria, para poder levantar el proyecto y ver las pantallas
funcionando sin tener la base configurada todavia.
"""
from config import Config

if not Config.MODO_DEMO:
    from supabase import create_client
    _client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
else:
    _client = None


# ---------------------------------------------------------------------
# Datos de ejemplo (solo se usan si MODO_DEMO = True)
# ---------------------------------------------------------------------
_SOCIOS_DEMO = [
    {
        "id": "1", "nro_socio": 231, "nombre": "Juan", "apellido": "Martinez",
        "dni": "30123456", "categoria": "activo", "disciplina_principal": "hockey",
        "estado": "activo", "grupo_familiar_id": "g1",
    },
    {
        "id": "2", "nro_socio": 232, "nombre": "Sofia", "apellido": "Martinez",
        "dni": "41987654", "categoria": "cadete", "disciplina_principal": "hockey",
        "estado": "activo", "grupo_familiar_id": "g1",
    },
]

_CUOTAS_DEMO = [
    {"id": "c1", "socio_id": "1", "periodo": "2026-08", "monto": 8500,
     "estado": "vencido", "fecha_vencimiento": "2026-08-31"},
    {"id": "c2", "socio_id": "1", "periodo": "2026-09", "monto": 8500,
     "estado": "pendiente", "fecha_vencimiento": "2026-09-30"},
]

_EVENTOS_DEMO = [
    {"id": "e1", "titulo": "Torneo interno de basquet", "disciplina": "basquet",
     "fecha_evento": "2026-09-27T15:00:00", "lugar": "gimnasio"},
    {"id": "e2", "titulo": "Asamblea anual de socios", "disciplina": None,
     "fecha_evento": "2026-10-02T19:00:00", "lugar": "sede social"},
]

_AUSPICIANTES_DEMO = [
    {"id": "a1", "nombre": "Autoservicio del barrio", "logo_url": None, "link": None},
    {"id": "a2", "nombre": "Farmacia central", "logo_url": None, "link": None},
]


# ---------------------------------------------------------------------
# Socios
# ---------------------------------------------------------------------
def buscar_socios(texto):
    if Config.MODO_DEMO:
        texto = texto.lower()
        return [
            s for s in _SOCIOS_DEMO
            if texto in s["nombre"].lower()
            or texto in s["apellido"].lower()
            or texto in s["dni"]
            or texto in str(s["nro_socio"])
        ]
    return (
        _client.table("socios")
        .select("*")
        .or_(f"nombre.ilike.%{texto}%,apellido.ilike.%{texto}%,dni.ilike.%{texto}%")
        .execute()
        .data
    )


def obtener_socio(socio_id):
    if Config.MODO_DEMO:
        return next((s for s in _SOCIOS_DEMO if s["id"] == socio_id), None)
    res = _client.table("socios").select("*").eq("id", socio_id).single().execute()
    return res.data


def crear_socio(datos):
    if Config.MODO_DEMO:
        nuevo = {**datos, "id": str(len(_SOCIOS_DEMO) + 1)}
        _SOCIOS_DEMO.append(nuevo)
        return nuevo
    return _client.table("socios").insert(datos).execute().data[0]


def dar_de_baja_socio(socio_id, motivo):
    if Config.MODO_DEMO:
        socio = obtener_socio(socio_id)
        if socio:
            socio["estado"] = "inactivo"
            socio["motivo_baja"] = motivo
        return socio
    return (
        _client.table("socios")
        .update({"estado": "inactivo", "motivo_baja": motivo})
        .eq("id", socio_id)
        .execute()
        .data
    )


# ---------------------------------------------------------------------
# Cuotas y pagos
# ---------------------------------------------------------------------
def cuotas_pendientes_de_socio(socio_id):
    if Config.MODO_DEMO:
        return [c for c in _CUOTAS_DEMO if c["socio_id"] == socio_id and c["estado"] != "pagado"]
    return (
        _client.table("cuotas")
        .select("*")
        .eq("socio_id", socio_id)
        .neq("estado", "pagado")
        .execute()
        .data
    )


def registrar_pago(cuota_ids, medio_pago, monto_total, registrado_por):
    """
    Crea un registro en `pagos` y vincula las cuotas cubiertas en
    `pagos_cuotas`. Marca esas cuotas como pagadas.
    """
    if Config.MODO_DEMO:
        for c in _CUOTAS_DEMO:
            if c["id"] in cuota_ids:
                c["estado"] = "pagado"
        return {"ok": True, "cuotas_pagadas": cuota_ids}

    pago = _client.table("pagos").insert({
        "monto_pagado": monto_total,
        "medio_pago": medio_pago,
        "registrado_por": registrado_por,
    }).execute().data[0]

    for cuota_id in cuota_ids:
        _client.table("pagos_cuotas").insert({
            "pago_id": pago["id"], "cuota_id": cuota_id,
        }).execute()
        _client.table("cuotas").update({"estado": "pagado"}).eq("id", cuota_id).execute()

    return pago


# ---------------------------------------------------------------------
# Novedades (panel de comision)
# ---------------------------------------------------------------------
def resumen_comision():
    if Config.MODO_DEMO:
        return {
            "cobrado_semana": 312400,
            "socios_activos": len([s for s in _SOCIOS_DEMO if s["estado"] == "activo"]),
            "morosos": [c for c in _CUOTAS_DEMO if c["estado"] == "vencido"],
        }
    # En produccion esto conviene resolverlo con una vista SQL o RPC
    # en Supabase en vez de traer todo y calcular en Python.
    raise NotImplementedError("Definir vista/RPC de resumen en Supabase")


# ---------------------------------------------------------------------
# Carnet / novedades / auspiciantes (app del socio)
# ---------------------------------------------------------------------
def eventos_para_socio(disciplina_socio):
    if Config.MODO_DEMO:
        return [
            e for e in _EVENTOS_DEMO
            if e["disciplina"] is None or e["disciplina"] == disciplina_socio
        ]
    return (
        _client.table("eventos_club")
        .select("*")
        .or_(f"disciplina.is.null,disciplina.eq.{disciplina_socio}")
        .order("fecha_evento")
        .execute()
        .data
    )


def auspiciantes_activos():
    if Config.MODO_DEMO:
        return _AUSPICIANTES_DEMO
    return (
        _client.table("auspiciantes")
        .select("*")
        .eq("activo", True)
        .order("orden")
        .execute()
        .data
    )
