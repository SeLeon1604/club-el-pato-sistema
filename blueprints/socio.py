"""
App del socio (celular). Rol: socio.
3 pestañas: Carnet (QR + auspiciante random), Novedades (partidos +
eventos + beneficio de la semana) y Beneficios (todos los auspiciantes).
"""
import random
from datetime import date

from flask import Blueprint, render_template, session, redirect, url_for
import db

socio_bp = Blueprint("socio", __name__)


@socio_bp.before_request
def proteger():
    if session.get("rol") != "socio":
        return redirect(url_for("auth.login"))


def _beneficio_de_la_semana(auspiciantes):
    """Mismo auspiciante para todos los socios durante toda la semana:
    se elige por el numero de semana ISO del año, no al azar."""
    if not auspiciantes:
        return None
    semana = date.today().isocalendar()[1]
    return auspiciantes[semana % len(auspiciantes)]


@socio_bp.route("/")
def carnet():
    socio = db.obtener_socio(session.get("socio_id"))
    auspiciantes = db.auspiciantes_activos()
    auspiciante_random = random.choice(auspiciantes) if auspiciantes else None
    return render_template(
        "socio/carnet.html", socio=socio, auspiciante=auspiciante_random, tab_activa="carnet"
    )


@socio_bp.route("/novedades")
def novedades():
    socio = db.obtener_socio(session.get("socio_id"))
    disciplina = socio["disciplina_principal"] if socio else None
    partidos = db.fixture_proximos(disciplina) if disciplina and disciplina != "ninguna" else []
    eventos = db.eventos_para_socio(disciplina) if socio else []
    beneficio = _beneficio_de_la_semana(db.auspiciantes_activos())
    return render_template(
        "socio/novedades.html", partidos=partidos, eventos=eventos,
        beneficio=beneficio, tab_activa="novedades",
    )


@socio_bp.route("/beneficios")
def beneficios():
    auspiciantes = db.auspiciantes_activos()
    agrupados = {}
    for a in auspiciantes:
        cat = a.get("categoria_comercio") or "otros"
        agrupados.setdefault(cat, []).append(a)
    return render_template(
        "socio/beneficios.html", agrupados=sorted(agrupados.items()), tab_activa="beneficios"
    )
