"""
Panel de administracion. Rol: admin.
Tarifas con historial, configuracion (vencimiento y recargo) y
generacion mensual de cuotas.
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, request, session, redirect, url_for, flash

import cuotas
import db

admin_bp = Blueprint("admin", __name__)


@admin_bp.before_request
def proteger():
    if session.get("rol") != "admin":
        return redirect(url_for("auth.login"))


@admin_bp.route("/")
def index():
    return render_template("admin/index.html")


# ---------------------------------------------------------------------
# Tarifas
# ---------------------------------------------------------------------
def _claves_validas(tipo):
    return {"societaria": cuotas.CATEGORIAS, "actividad": cuotas.ACTIVIDADES}.get(tipo)


@admin_bp.route("/tarifas", methods=["GET", "POST"])
def tarifas():
    hoy = date.today().isoformat()

    if request.method == "POST":
        tipo = request.form.get("tipo", "")
        clave = request.form.get("clave", "")
        vigente_desde = request.form.get("vigente_desde", "")
        error = None
        try:
            monto = cuotas.dinero(Decimal(request.form.get("monto", "").replace(",", ".")))
            if not monto.is_finite() or monto < 0 or monto >= Decimal("100000000"):
                raise InvalidOperation
        except InvalidOperation:
            monto, error = None, "El monto debe ser un numero mayor o igual a 0."
        try:
            date.fromisoformat(vigente_desde)
        except ValueError:
            error = "La fecha de vigencia no es valida."
        if not error and clave not in (_claves_validas(tipo) or []):
            error = "Tipo o clave invalidos."
        if not error and any(
            t["tipo"] == tipo and t["clave"] == clave
            and t["vigente_desde"] == vigente_desde and not t["anulada"]
            for t in db.listar_tarifas()
        ):
            error = "Ya hay una tarifa con esa vigencia; anulala o elegi otra fecha."

        if error:
            flash(error, "error")
        else:
            nueva = db.crear_tarifa(tipo, clave, monto, vigente_desde, session["usuario_id"])
            db.registrar_evento(
                "cambio_tarifa",
                {"accion": "alta", "tarifa_id": nueva["id"], "tipo": tipo, "clave": clave,
                 "monto": float(monto), "vigente_desde": vigente_desde},
                session["usuario_id"],
            )
            flash("Tarifa cargada.", "ok")
        return redirect(url_for("admin.tarifas"))

    todas = db.listar_tarifas()
    vigentes = cuotas.tarifas_vigentes(todas, hoy)
    return render_template(
        "admin/tarifas.html",
        tarifas=todas,
        vigentes=vigentes,
        vigentes_ids={t["id"] for t in vigentes.values()},
        categorias=cuotas.CATEGORIAS,
        actividades=cuotas.ACTIVIDADES,
        hoy=hoy,
    )


@admin_bp.route("/tarifas/<tarifa_id>/anular", methods=["POST"])
def anular_tarifa(tarifa_id):
    t = db.obtener_tarifa(tarifa_id)
    if t and not t["anulada"]:
        db.anular_tarifa(tarifa_id)
        db.registrar_evento(
            "cambio_tarifa",
            {"accion": "anulacion", "tarifa_id": tarifa_id, "tipo": t["tipo"],
             "clave": t["clave"], "monto": float(t["monto"]),
             "vigente_desde": t["vigente_desde"]},
            session["usuario_id"],
        )
        flash("Tarifa anulada.", "ok")
    return redirect(url_for("admin.tarifas"))


# ---------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------
@admin_bp.route("/configuracion", methods=["GET", "POST"])
def configuracion():
    if request.method == "POST":
        nueva = {
            "dia_vencimiento": request.form.get("dia_vencimiento", "").strip(),
            "recargo_tipo": request.form.get("recargo_tipo", ""),
            "recargo_valor": request.form.get("recargo_valor", "").strip().replace(",", "."),
        }
        error = None
        if not (nueva["dia_vencimiento"].isdigit() and 1 <= int(nueva["dia_vencimiento"]) <= 28):
            error = "El dia de vencimiento debe estar entre 1 y 28."
        elif nueva["recargo_tipo"] not in ("porcentaje", "monto"):
            error = "Tipo de recargo invalido."
        else:
            try:
                valor = Decimal(nueva["recargo_valor"])
                limite = Decimal(100) if nueva["recargo_tipo"] == "porcentaje" else Decimal("100000000")
                if not valor.is_finite() or valor < 0 or valor > limite:
                    raise InvalidOperation
                nueva["recargo_valor"] = str(cuotas.dinero(valor))
            except InvalidOperation:
                error = "El recargo debe ser un numero valido (porcentaje: 0 a 100)."

        if error:
            flash(error, "error")
        else:
            actual = db.obtener_configuracion()
            for clave, valor in nueva.items():
                if actual.get(clave) != valor:
                    db.guardar_configuracion(clave, valor, session["usuario_id"])
                    db.registrar_evento(
                        "cambio_config",
                        {"clave": clave, "anterior": actual.get(clave), "nuevo": valor},
                        session["usuario_id"],
                    )
            flash("Configuracion guardada. Rige para las cuotas que se generen o venzan desde ahora.", "ok")
        return redirect(url_for("admin.configuracion"))

    return render_template("admin/configuracion.html", cfg=db.obtener_configuracion())


# ---------------------------------------------------------------------
# Generacion mensual de cuotas
# ---------------------------------------------------------------------
@admin_bp.route("/cuotas/generar", methods=["GET", "POST"])
def generar_cuotas():
    resultado = None
    periodo = request.form.get("periodo") or cuotas.periodo_de(date.today())
    if request.method == "POST":
        if not cuotas.periodo_valido(periodo):
            flash("Periodo invalido.", "error")
        else:
            resultado = cuotas.generar_cuotas(periodo, session["usuario_id"])
            resultado["recargos"] = cuotas.aplicar_recargos()
    return render_template("admin/generar_cuotas.html", periodo=periodo, resultado=resultado)
