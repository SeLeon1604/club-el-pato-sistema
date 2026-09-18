"""
App de comision (celular). Rol: comision.
Solo lectura: resumen, alertas de morosidad, ultimos movimientos.
"""
from flask import Blueprint, render_template, session, redirect, url_for
import db

comision_bp = Blueprint("comision", __name__)


@comision_bp.before_request
def proteger():
    if session.get("rol") != "comision":
        return redirect(url_for("auth.login"))


@comision_bp.route("/")
def novedades():
    resumen = db.resumen_comision()
    return render_template("comision/novedades.html", resumen=resumen)
