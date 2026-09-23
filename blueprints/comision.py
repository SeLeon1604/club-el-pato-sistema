"""
App de comision (celular). Rol: comision.
Solo lectura: caja del periodo (cobrado, altas/bajas, erogaciones).
"""
from flask import Blueprint, render_template, request, session, redirect, url_for, flash

import resumen as resumen_service

comision_bp = Blueprint("comision", __name__)


@comision_bp.before_request
def proteger():
    if session.get("rol") != "comision":
        return redirect(url_for("auth.login"))


@comision_bp.route("/")
def novedades():
    periodo = request.args.get("periodo", "mes")
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")
    try:
        datos = resumen_service.resumen(periodo, desde, hasta)
    except ValueError as e:
        flash(str(e), "error")
        periodo = "mes"
        datos = resumen_service.resumen(periodo)
    return render_template(
        "comision/novedades.html", resumen=datos, periodo=periodo, desde=desde, hasta=hasta
    )
