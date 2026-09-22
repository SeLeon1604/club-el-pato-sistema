"""
Capa de acceso a datos. Envuelve las llamadas a Supabase para que el
resto del codigo (blueprints) no dependa directamente del cliente.

En MODO_DEMO (sin credenciales de Supabase) devuelve datos de ejemplo
en memoria, para poder levantar el proyecto y ver las pantallas
funcionando sin tener la base configurada todavia.
"""
from datetime import datetime, timezone

import bcrypt
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

_GRUPOS_DEMO = [
    {"id": "g1", "nombre_grupo": "Familia Martinez", "responsable_socio_id": "1"},
]

_CUOTAS_DEMO = [
    {"id": "c1", "socio_id": "1", "periodo": "2026-08", "monto": 8500,
     "estado": "vencido", "fecha_vencimiento": "2026-08-31"},
    {"id": "c2", "socio_id": "1", "periodo": "2026-09", "monto": 8500,
     "estado": "pendiente", "fecha_vencimiento": "2026-09-30"},
]

def _hash_demo(clave):
    # rounds bajos: solo para arrancar rapido en modo demo
    return bcrypt.hashpw(clave.encode(), bcrypt.gensalt(rounds=4)).decode()


# Credenciales de demo: recepcion@elpato.local / 1234,
# comision@elpato.local / demo1234, socio DNI 30123456 / demo1234
_USUARIOS_DEMO = [
    {"id": "u1", "rol": "recepcion", "email": "recepcion@elpato.local",
     "dni_login": None, "socio_id": None, "activo": True,
     "pin_hash": _hash_demo("1234"), "password_hash": None},
    {"id": "u2", "rol": "comision", "email": "comision@elpato.local",
     "dni_login": None, "socio_id": None, "activo": True,
     "pin_hash": None, "password_hash": _hash_demo("demo1234")},
    {"id": "u3", "rol": "socio", "email": None,
     "dni_login": "30123456", "socio_id": "1", "activo": True,
     "pin_hash": None, "password_hash": _hash_demo("demo1234")},
    {"id": "u4", "rol": "admin", "email": "admin@elpato.local",
     "dni_login": None, "socio_id": None, "activo": True,
     "pin_hash": None, "password_hash": _hash_demo("demo1234")},
]

_ACTIVIDADES_DEMO = {"1": {"hockey"}, "2": {"hockey"}}

_TARIFAS_DEMO = [
    {"id": "t1", "tipo": "societaria", "clave": "activo", "monto": 5500,
     "vigente_desde": "2026-01-01", "anulada": False, "creado_por": None,
     "creado_en": "2026-01-01T00:00:00"},
    {"id": "t2", "tipo": "societaria", "clave": "activo", "monto": 6000,
     "vigente_desde": "2026-07-01", "anulada": False, "creado_por": None,
     "creado_en": "2026-06-20T00:00:00"},
    {"id": "t3", "tipo": "societaria", "clave": "cadete", "monto": 3500,
     "vigente_desde": "2026-01-01", "anulada": False, "creado_por": None,
     "creado_en": "2026-01-01T00:00:00"},
    {"id": "t4", "tipo": "societaria", "clave": "adherente", "monto": 4000,
     "vigente_desde": "2026-01-01", "anulada": False, "creado_por": None,
     "creado_en": "2026-01-01T00:00:00"},
    {"id": "t5", "tipo": "actividad", "clave": "hockey", "monto": 2500,
     "vigente_desde": "2026-01-01", "anulada": False, "creado_por": None,
     "creado_en": "2026-01-01T00:00:00"},
    {"id": "t6", "tipo": "actividad", "clave": "basquet", "monto": 2500,
     "vigente_desde": "2026-01-01", "anulada": False, "creado_por": None,
     "creado_en": "2026-01-01T00:00:00"},
    {"id": "t7", "tipo": "actividad", "clave": "futbol", "monto": 2000,
     "vigente_desde": "2026-01-01", "anulada": False, "creado_por": None,
     "creado_en": "2026-01-01T00:00:00"},
]

CONFIG_POR_DEFECTO = {
    "dia_vencimiento": "10",
    "recargo_tipo": "porcentaje",  # 'porcentaje' o 'monto'
    "recargo_valor": "10",
}
_CONFIG_DEMO = dict(CONFIG_POR_DEFECTO)
_EVENTOS_SISTEMA_DEMO = []

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
# Usuarios (autenticacion)
# ---------------------------------------------------------------------
def obtener_usuario_para_login(identificador, rol):
    """Usuario activo con ese rol cuyo email (recepcion/comision) o
    dni_login (socio) coincide con `identificador`. None si no existe."""
    campo = "dni_login" if rol == "socio" else "email"
    identificador = identificador.strip()
    if campo == "email":
        identificador = identificador.lower()
    if Config.MODO_DEMO:
        return next(
            (u for u in _USUARIOS_DEMO
             if u["rol"] == rol and u["activo"] and u[campo] == identificador),
            None,
        )
    res = (
        _client.table("usuarios")
        .select("*")
        .eq("rol", rol)
        .eq("activo", True)
        .eq(campo, identificador)
        .limit(1)
        .execute()
        .data
    )
    return res[0] if res else None


def crear_usuario(rol, identificador, clave, socio_id=None):
    """Alta de usuario con hash bcrypt (PIN para recepcion, password para el resto)."""
    hash_ = bcrypt.hashpw(clave.encode(), bcrypt.gensalt()).decode()
    fila = {
        "rol": rol,
        "socio_id": socio_id,
        "pin_hash": hash_ if rol == "recepcion" else None,
        "password_hash": None if rol == "recepcion" else hash_,
        "activo": True,
    }
    if rol == "socio":
        fila["dni_login"] = identificador.strip()
    else:
        fila["email"] = identificador.strip().lower()
    if Config.MODO_DEMO:
        fila["id"] = f"u{len(_USUARIOS_DEMO) + 1}"
        _USUARIOS_DEMO.append(fila)
        return fila
    return _client.table("usuarios").insert(fila).execute().data[0]


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


def existe_dni(dni):
    if Config.MODO_DEMO:
        return any(s["dni"] == dni for s in _SOCIOS_DEMO)
    res = _client.table("socios").select("id").eq("dni", dni).limit(1).execute().data
    return bool(res)


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
# Grupos familiares
# ---------------------------------------------------------------------
def _con_miembros(grupos):
    """Agrega a cada grupo la lista `miembros` (nombres) para mostrarlos."""
    if not grupos:
        return grupos
    ids = [g["id"] for g in grupos]
    if Config.MODO_DEMO:
        socios = [s for s in _SOCIOS_DEMO if s.get("grupo_familiar_id") in ids]
    else:
        socios = (
            _client.table("socios")
            .select("nombre,apellido,grupo_familiar_id")
            .in_("grupo_familiar_id", ids)
            .execute()
            .data
        )
    for g in grupos:
        g["miembros"] = [
            f"{s['nombre']} {s['apellido']}"
            for s in socios if s["grupo_familiar_id"] == g["id"]
        ]
    return grupos


def buscar_grupos(texto, limite=10):
    """Grupos cuyo nombre, o el apellido de algun miembro, contiene `texto`."""
    if Config.MODO_DEMO:
        t = texto.lower()
        ids_por_miembro = {
            s["grupo_familiar_id"] for s in _SOCIOS_DEMO
            if s.get("grupo_familiar_id") and t in s["apellido"].lower()
        }
        grupos = [
            dict(g) for g in _GRUPOS_DEMO
            if t in (g["nombre_grupo"] or "").lower() or g["id"] in ids_por_miembro
        ]
        return _con_miembros(grupos[:limite])

    # los comodines del texto no deben alterar el patron ilike
    t = "".join(ch for ch in texto if ch not in ",()*%")
    ids = {
        g["id"] for g in
        _client.table("grupos_familiares").select("id")
        .ilike("nombre_grupo", f"%{t}%").limit(limite).execute().data
    }
    ids |= {
        s["grupo_familiar_id"] for s in
        _client.table("socios").select("grupo_familiar_id")
        .ilike("apellido", f"%{t}%").not_.is_("grupo_familiar_id", "null")
        .limit(limite).execute().data
    }
    if not ids:
        return []
    grupos = (
        _client.table("grupos_familiares").select("*")
        .in_("id", list(ids)[:limite]).execute().data
    )
    return _con_miembros(grupos)


def obtener_grupo(grupo_id):
    if Config.MODO_DEMO:
        return next((g for g in _GRUPOS_DEMO if g["id"] == grupo_id), None)
    res = _client.table("grupos_familiares").select("*").eq("id", grupo_id).limit(1).execute().data
    return res[0] if res else None


def crear_grupo(nombre_grupo):
    if Config.MODO_DEMO:
        nuevo = {"id": f"g{len(_GRUPOS_DEMO) + 1}", "nombre_grupo": nombre_grupo,
                 "responsable_socio_id": None}
        _GRUPOS_DEMO.append(nuevo)
        return nuevo
    return _client.table("grupos_familiares").insert({"nombre_grupo": nombre_grupo}).execute().data[0]


def asignar_responsable_grupo(grupo_id, socio_id):
    if Config.MODO_DEMO:
        g = obtener_grupo(grupo_id)
        if g:
            g["responsable_socio_id"] = socio_id
        return
    _client.table("grupos_familiares").update({"responsable_socio_id": socio_id}).eq("id", grupo_id).execute()


def eliminar_grupo(grupo_id):
    if Config.MODO_DEMO:
        _GRUPOS_DEMO[:] = [g for g in _GRUPOS_DEMO if g["id"] != grupo_id]
        return
    _client.table("grupos_familiares").delete().eq("id", grupo_id).execute()


# ---------------------------------------------------------------------
# Cuotas y pagos
# ---------------------------------------------------------------------
def cuotas_pendientes_de_socio(socio_id):
    if Config.MODO_DEMO:
        return [c for c in _CUOTAS_DEMO
                if c["socio_id"] == socio_id and c["estado"] in ("pendiente", "vencido")]
    return (
        _client.table("cuotas")
        .select("*")
        .eq("socio_id", socio_id)
        .in_("estado", ["pendiente", "vencido"])
        .order("periodo")
        .execute()
        .data
    )


def _paginado(armar_consulta, tam=1000):
    """PostgREST corta en 1000 filas: recorre todas las paginas.
    `armar_consulta` devuelve una consulta nueva en cada llamada."""
    filas, desde = [], 0
    while True:
        pagina = armar_consulta().range(desde, desde + tam - 1).execute().data
        filas += pagina
        if len(pagina) < tam:
            return filas
        desde += tam


def socios_activos_hasta(fecha_fin):
    """Socios activos dados de alta hasta `fecha_fin` (ISO)."""
    if Config.MODO_DEMO:
        return [s for s in _SOCIOS_DEMO
                if s["estado"] == "activo" and s.get("fecha_alta", "0000-00-00") <= fecha_fin]
    return _paginado(lambda: (
        _client.table("socios").select("id,categoria,fecha_alta")
        .eq("estado", "activo").lte("fecha_alta", fecha_fin).order("id")
    ))


def actividades_por_socio():
    """{socio_id: {disciplinas}}"""
    if Config.MODO_DEMO:
        return {k: set(v) for k, v in _ACTIVIDADES_DEMO.items()}
    filas = _paginado(lambda: (
        _client.table("socios_actividades").select("socio_id,disciplina")
        .order("socio_id").order("disciplina")
    ))
    res = {}
    for f in filas:
        res.setdefault(f["socio_id"], set()).add(f["disciplina"])
    return res


def guardar_actividades(socio_id, disciplinas):
    disciplinas = sorted(set(disciplinas))
    if Config.MODO_DEMO:
        _ACTIVIDADES_DEMO[socio_id] = set(disciplinas)
        return
    if disciplinas:
        _client.table("socios_actividades").upsert(
            [{"socio_id": socio_id, "disciplina": d} for d in disciplinas]
        ).execute()


def socio_ids_con_cuota(periodo):
    if Config.MODO_DEMO:
        return {c["socio_id"] for c in _CUOTAS_DEMO if c["periodo"] == periodo}
    filas = _paginado(lambda: (
        _client.table("cuotas").select("socio_id").eq("periodo", periodo).order("socio_id")
    ))
    return {f["socio_id"] for f in filas}


def insertar_cuotas(cuotas):
    """Inserta cuotas nuevas; si (socio, periodo) ya existe la ignora,
    asi correr la generacion dos veces (o en paralelo) no duplica."""
    if Config.MODO_DEMO:
        existentes = {(c["socio_id"], c["periodo"]) for c in _CUOTAS_DEMO}
        for c in cuotas:
            if (c["socio_id"], c["periodo"]) not in existentes:
                _CUOTAS_DEMO.append({**c, "id": f"c{len(_CUOTAS_DEMO) + 1}"})
        return
    for i in range(0, len(cuotas), 500):
        _client.table("cuotas").upsert(
            cuotas[i:i + 500], on_conflict="socio_id,periodo", ignore_duplicates=True
        ).execute()


def cuotas_para_recargo(hoy_iso, socio_id=None):
    """Cuotas 'pendiente' cuyo vencimiento ya paso. Devuelve id y monto."""
    if Config.MODO_DEMO:
        return [{"id": c["id"], "monto": c["monto"]} for c in _CUOTAS_DEMO
                if c["estado"] == "pendiente" and c["fecha_vencimiento"] < hoy_iso
                and (socio_id is None or c["socio_id"] == socio_id)]

    def consulta():
        q = (_client.table("cuotas").select("id,monto")
             .eq("estado", "pendiente").lt("fecha_vencimiento", hoy_iso).order("id"))
        return q.eq("socio_id", socio_id) if socio_id else q
    return _paginado(consulta)


def marcar_cuotas_vencidas(ids, recargo):
    if not ids:
        return
    if Config.MODO_DEMO:
        for c in _CUOTAS_DEMO:
            if c["id"] in ids:
                c["estado"], c["monto_recargo"] = "vencido", recargo
        return
    for i in range(0, len(ids), 100):
        (_client.table("cuotas")
         .update({"estado": "vencido", "monto_recargo": recargo})
         .in_("id", ids[i:i + 100]).execute())


# ---------------------------------------------------------------------
# Tarifas (con historial), configuracion y auditoria
# ---------------------------------------------------------------------
def listar_tarifas():
    """Todas las filas, incluidas las anuladas, mas nuevas primero."""
    if Config.MODO_DEMO:
        return sorted((dict(t) for t in _TARIFAS_DEMO),
                      key=lambda t: t["vigente_desde"], reverse=True)
    return (_client.table("tarifas").select("*")
            .order("vigente_desde", desc=True).order("creado_en", desc=True)
            .execute().data)


def crear_tarifa(tipo, clave, monto, vigente_desde, creado_por):
    fila = {"tipo": tipo, "clave": clave, "monto": float(monto),
            "vigente_desde": vigente_desde, "creado_por": creado_por}
    if Config.MODO_DEMO:
        nueva = {**fila, "id": f"t{len(_TARIFAS_DEMO) + 1}", "anulada": False,
                 "creado_en": "demo"}
        _TARIFAS_DEMO.append(nueva)
        return nueva
    return _client.table("tarifas").insert(fila).execute().data[0]


def obtener_tarifa(tarifa_id):
    if Config.MODO_DEMO:
        return next((t for t in _TARIFAS_DEMO if t["id"] == tarifa_id), None)
    res = _client.table("tarifas").select("*").eq("id", tarifa_id).limit(1).execute().data
    return res[0] if res else None


def anular_tarifa(tarifa_id):
    if Config.MODO_DEMO:
        t = obtener_tarifa(tarifa_id)
        if t:
            t["anulada"] = True
        return
    _client.table("tarifas").update({"anulada": True}).eq("id", tarifa_id).execute()


def obtener_configuracion():
    if Config.MODO_DEMO:
        return dict(_CONFIG_DEMO)
    cfg = dict(CONFIG_POR_DEFECTO)
    for f in _client.table("configuracion").select("clave,valor").execute().data:
        cfg[f["clave"]] = f["valor"]
    return cfg


def guardar_configuracion(clave, valor, usuario_id):
    if Config.MODO_DEMO:
        _CONFIG_DEMO[clave] = valor
        return
    _client.table("configuracion").upsert({
        "clave": clave, "valor": valor, "actualizado_por": usuario_id,
        "actualizado_en": datetime.now(timezone.utc).isoformat(),
    }).execute()


def registrar_evento(tipo, detalle, usuario_id, socio_id=None):
    fila = {"tipo": tipo, "detalle": detalle, "usuario_id": usuario_id, "socio_id": socio_id}
    if Config.MODO_DEMO:
        _EVENTOS_SISTEMA_DEMO.append(fila)
        return
    _client.table("eventos_sistema").insert(fila).execute()


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
