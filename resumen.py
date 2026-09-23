"""
Calculo de rangos de fecha y agregados para el panel de comision.
Logica de negocio separada de la capa de datos, igual que cuotas.py.
"""
from datetime import date, timedelta

import db

PERIODOS = ("hoy", "semana", "mes", "mes_anterior", "rango")


def rango_periodo(periodo, desde=None, hasta=None):
    """(date, date) del rango pedido. Lanza ValueError si es invalido."""
    hoy = date.today()
    if periodo == "hoy":
        d = h = hoy
    elif periodo == "semana":
        d, h = hoy - timedelta(days=hoy.weekday()), hoy
    elif periodo == "mes":
        d, h = hoy.replace(day=1), hoy
    elif periodo == "mes_anterior":
        h = hoy.replace(day=1) - timedelta(days=1)
        d = h.replace(day=1)
    elif periodo == "rango":
        try:
            d, h = date.fromisoformat(desde), date.fromisoformat(hasta)
        except (TypeError, ValueError):
            raise ValueError("Las fechas del rango no son validas.")
    else:
        raise ValueError("Periodo invalido.")
    if d > h:
        raise ValueError("La fecha 'desde' no puede ser posterior a 'hasta'.")
    return d, h


def resumen(periodo, desde=None, hasta=None):
    """Cobrado (con desglose efectivo/transferencia), altas, bajas y
    erogaciones (con desglose por categoria) del periodo pedido."""
    d, h = rango_periodo(periodo, desde, hasta)
    d_iso, h_iso = d.isoformat(), h.isoformat()

    pagos = db.pagos_en_periodo(d_iso, h_iso)
    total = sum(p["monto_pagado"] for p in pagos)
    efectivo = sum(p["monto_pagado"] for p in pagos if p["medio_pago"] == "efectivo")
    transferencia = sum(p["monto_pagado"] for p in pagos if p["medio_pago"] == "transferencia")
    otros = total - efectivo - transferencia

    erogaciones = db.erogaciones_en_periodo(d_iso, h_iso)
    erogaciones_total = sum(e["monto"] for e in erogaciones)
    por_categoria = {}
    for e in erogaciones:
        cat = e.get("categoria") or "sin categoria"
        por_categoria[cat] = por_categoria.get(cat, 0) + e["monto"]

    def pct(parte):
        return (parte / total * 100) if total else 0

    return {
        "periodo": periodo, "desde": d_iso, "hasta": h_iso,
        "total_cobrado": total,
        "efectivo": efectivo, "efectivo_pct": pct(efectivo),
        "transferencia": transferencia, "transferencia_pct": pct(transferencia),
        "otros": otros, "otros_pct": pct(otros),
        "altas": db.altas_en_periodo(d_iso, h_iso),
        "bajas": db.bajas_en_periodo(d_iso, h_iso),
        "erogaciones_total": erogaciones_total,
        "erogaciones_por_categoria": sorted(por_categoria.items()),
    }
