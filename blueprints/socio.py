"""
App del socio (celular). Rol: socio.
Carnet digital con QR + novedades filtradas por disciplina + auspiciantes.
"""
from flask import Blueprint, render_template, session, redirect, url_for
import db

socio_bp = Blueprint("socio", __name__)


@socio_bp.before_request
def proteger():
    if session.get("rol") != "socio":
        return redirect(url_for("auth.login"))


@socio_bp.route("/")
def carnet():
    # TODO: reemplazar por el socio_id real vinculado al usuario logueado
    socio = db.obtener_socio("1")
    eventos = db.eventos_para_socio(socio["disciplina_principal"]) if socio else []
    auspiciantes = db.auspiciantes_activos()
    return render_template(
        "socio/carnet.html", socio=socio, eventos=eventos, auspiciantes=auspiciantes
    )
