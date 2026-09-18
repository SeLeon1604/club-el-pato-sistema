"""
App de recepcion (tablet). Rol: recepcion.
Pantallas: menu principal, busqueda, ficha+cobro, alta de socio.
"""
from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
import db

recepcion_bp = Blueprint("recepcion", __name__)


def _requiere_rol_recepcion():
    return session.get("rol") == "recepcion"


@recepcion_bp.before_request
def proteger():
    if not _requiere_rol_recepcion():
        return redirect(url_for("auth.login"))


@recepcion_bp.route("/")
def index():
    return render_template("recepcion/index.html")


@recepcion_bp.route("/buscar")
def buscar():
    texto = request.args.get("q", "")
    resultados = db.buscar_socios(texto) if texto else []
    return render_template("recepcion/busqueda.html", resultados=resultados, texto=texto)


@recepcion_bp.route("/socio/<socio_id>")
def ficha_socio(socio_id):
    socio = db.obtener_socio(socio_id)
    cuotas = db.cuotas_pendientes_de_socio(socio_id)
    total = sum(c["monto"] for c in cuotas)
    return render_template("recepcion/ficha_cobro.html", socio=socio, cuotas=cuotas, total=total)


@recepcion_bp.route("/socio/<socio_id>/cobrar", methods=["POST"])
def cobrar(socio_id):
    cuota_ids = request.form.getlist("cuota_id")
    medio_pago = request.form.get("medio_pago")
    monto_total = float(request.form.get("monto_total", 0))

    resultado = db.registrar_pago(
        cuota_ids=cuota_ids,
        medio_pago=medio_pago,
        monto_total=monto_total,
        registrado_por=session.get("usuario_id"),
    )
    return jsonify(resultado)


@recepcion_bp.route("/socio/nuevo", methods=["GET", "POST"])
def alta_socio():
    if request.method == "POST":
        datos = {
            "nombre": request.form.get("nombre"),
            "apellido": request.form.get("apellido"),
            "dni": request.form.get("dni"),
            "categoria": request.form.get("categoria"),
            "disciplina_principal": request.form.get("disciplina_principal"),
            "estado": "activo",
        }
        socio = db.crear_socio(datos)
        return redirect(url_for("recepcion.ficha_socio", socio_id=socio["id"]))

    return render_template("recepcion/alta_socio.html")


@recepcion_bp.route("/socio/<socio_id>/baja", methods=["POST"])
def baja_socio(socio_id):
    motivo = request.form.get("motivo", "")
    db.dar_de_baja_socio(socio_id, motivo)
    return redirect(url_for("recepcion.index"))
