"""
Logica de negocio de cuotas: tarifas vigentes, generacion mensual y
recargo por vencimiento. Accede a los datos solo a traves de db.py.

cuota = tarifa societaria de la categoria
        + suma de las tarifas de cada actividad del socio
Lo que no tiene tarifa vale 0; si el total es 0 no se genera cuota.
"""
import calendar
import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

import db

CATEGORIAS = ["activo", "cadete", "vitalicio", "honorario", "adherente"]
ACTIVIDADES = ["basquet", "futbol", "hockey"]

_CENTAVOS = Decimal("0.01")


def dinero(valor):
    return Decimal(str(valor)).quantize(_CENTAVOS, rounding=ROUND_HALF_UP)


def periodo_valido(periodo):
    m = re.fullmatch(r"(\d{4})-(0[1-9]|1[0-2])", periodo or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def periodo_de(fecha):
    return f"{fecha.year:04d}-{fecha.month:02d}"


def tarifas_vigentes(tarifas, fecha_iso):
    """{(tipo, clave): fila} con la tarifa no anulada mas reciente cuya
    vigencia empezo en `fecha_iso` o antes."""
    vigentes = {}
    for t in tarifas:
        if t.get("anulada") or t["vigente_desde"] > fecha_iso:
            continue
        k = (t["tipo"], t["clave"])
        if k not in vigentes or t["vigente_desde"] > vigentes[k]["vigente_desde"]:
            vigentes[k] = t
    return vigentes


def calcular_recargo(monto, cfg):
    tipo, valor = cfg["recargo_tipo"], dinero(cfg["recargo_valor"])
    if tipo == "porcentaje":
        return dinero(dinero(monto) * valor / 100)
    return valor


def generar_cuotas(periodo, usuario_id=None):
    """Crea la cuota de `periodo` ('AAAA-MM') para cada socio activo que
    todavia no la tenga. Es idempotente. Usa las tarifas vigentes al dia 1
    del periodo, asi el resultado no depende del dia en que se corra."""
    parsed = periodo_valido(periodo)
    if not parsed:
        raise ValueError("Periodo invalido, usar AAAA-MM")
    anio, mes = parsed
    inicio = date(anio, mes, 1)
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    fin = date(anio, mes, ultimo_dia)

    cfg = db.obtener_configuracion()
    vencimiento = date(anio, mes, min(int(cfg["dia_vencimiento"]), ultimo_dia))

    vigentes = tarifas_vigentes(db.listar_tarifas(), inicio.isoformat())
    actividades = db.actividades_por_socio()
    existentes = db.socio_ids_con_cuota(periodo)

    def tarifa(tipo, clave):
        t = vigentes.get((tipo, clave))
        return dinero(t["monto"]) if t else Decimal(0)

    nuevas = []
    ya_tenian = sin_importe = 0
    for s in db.socios_activos_hasta(fin.isoformat()):
        if s["id"] in existentes:
            ya_tenian += 1
            continue
        societaria = tarifa("societaria", s["categoria"])
        actividad = sum((tarifa("actividad", a) for a in actividades.get(s["id"], ())),
                        Decimal(0))
        total = societaria + actividad
        if total <= 0:
            sin_importe += 1
            continue
        nuevas.append({
            "socio_id": s["id"],
            "periodo": periodo,
            "monto": float(total),
            "monto_societaria": float(societaria),
            "monto_actividad": float(actividad),
            "fecha_vencimiento": vencimiento.isoformat(),
            "estado": "pendiente",
        })

    db.insertar_cuotas(nuevas)
    resultado = {"periodo": periodo, "creadas": len(nuevas),
                 "ya_tenian": ya_tenian, "sin_importe": sin_importe,
                 "vencimiento": vencimiento.isoformat()}
    db.registrar_evento("generacion_cuotas", resultado, usuario_id)
    return resultado


def aplicar_recargos(socio_id=None, hoy=None):
    """Pasa a 'vencido' las cuotas pendientes cuyo vencimiento ya paso y
    les fija el recargo vigente. Se aplica una sola vez: cambiar la
    configuracion despues no altera cuotas que ya vencieron."""
    hoy = hoy or date.today()
    cfg = db.obtener_configuracion()
    por_monto = {}
    for c in db.cuotas_para_recargo(hoy.isoformat(), socio_id):
        por_monto.setdefault(dinero(c["monto"]), []).append(c["id"])
    total = 0
    for monto, ids in por_monto.items():
        db.marcar_cuotas_vencidas(ids, float(calcular_recargo(monto, cfg)))
        total += len(ids)
    return total
