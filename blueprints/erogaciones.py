"""
Carga de erogaciones (gastos del club). Accesible desde comision y
desde recepcion, por eso vive en su propio blueprint en vez de
duplicar la pantalla en los otros dos.
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, request, session, redirect, url_for, flash

import db

erogaciones_bp = Blueprint("erogaciones", __name__)

CATEGORIAS_SUGERIDAS = ["mantenimiento", "indumentaria", "servicios", "eventos", "sueldos"]


@erogaciones_bp.before_request
def proteger():
    if session.get("rol") not in ("comision", "recepcion"):
        return redirect(url_for("auth.login"))


@erogaciones_bp.route("/nueva", methods=["GET", "POST"])
def nueva():
    if request.method == "POST":
        concepto = request.form.get("concepto", "").strip()
        categoria = request.form.get("categoria", "").strip()
        fecha = request.form.get("fecha", "").strip()
        error = None

        if not concepto:
            error = "El concepto es obligatorio."
        else:
            try:
                monto = Decimal(request.form.get("monto", "").replace(",", "."))
                if not monto.is_finite() or monto < 0:
                    raise InvalidOperation
            except InvalidOperation:
                error = "El monto debe ser un numero mayor o igual a 0."

        if not error:
            try:
                date.fromisoformat(fecha)
            except ValueError:
                error = "La fecha no es valida."

        if error:
            flash(error, "error")
        else:
            db.crear_erogacion(concepto, categoria, monto, fecha, session["usuario_id"])
            db.registrar_evento(
                "erogacion",
                {"concepto": concepto, "categoria": categoria or None,
                 "monto": float(monto), "fecha": fecha},
                session["usuario_id"],
            )
            flash("Erogacion cargada.", "ok")
        return redirect(url_for("erogaciones.nueva"))

    volver = "comision.novedades" if session.get("rol") == "comision" else "recepcion.index"
    return render_template(
        "erogaciones/nueva.html", categorias=CATEGORIAS_SUGERIDAS,
        hoy=date.today().isoformat(), volver=url_for(volver),
    )
