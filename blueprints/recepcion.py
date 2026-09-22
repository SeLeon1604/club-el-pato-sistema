"""
App de recepcion (tablet). Rol: recepcion.
Pantallas: menu principal, busqueda, ficha+cobro, alta de socio.
"""
from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
import cuotas as cuotas_service
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
    cuotas_service.aplicar_recargos(socio_id=socio_id)  # vencidas al dia, con su recargo
    cuotas = db.cuotas_pendientes_de_socio(socio_id)
    total = sum(c["monto"] + (c.get("monto_recargo") or 0) for c in cuotas)
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


@recepcion_bp.route("/grupos")
def buscar_grupos():
    texto = request.args.get("q", "").strip()
    if len(texto) < 2:
        return jsonify([])
    return jsonify(db.buscar_grupos(texto))


@recepcion_bp.route("/socio/nuevo", methods=["GET", "POST"])
def alta_socio():
    if request.method == "GET":
        return render_template("recepcion/alta_socio.html", form={}, error=None)

    form = request.form
    datos = {
        "nombre": form.get("nombre", "").strip(),
        "apellido": form.get("apellido", "").strip(),
        "dni": form.get("dni", "").strip(),
        "categoria": form.get("categoria"),
        "disciplina_principal": form.get("disciplina_principal"),
        "estado": "activo",
    }

    def con_error(msg):
        return render_template("recepcion/alta_socio.html", form=form, error=msg)

    if not (datos["nombre"] and datos["apellido"] and datos["dni"]):
        return con_error("Nombre, apellido y DNI son obligatorios.")
    if db.existe_dni(datos["dni"]):
        return con_error("Ya existe un socio con ese DNI.")

    modo_grupo = form.get("grupo_modo", "ninguno")
    grupo_nuevo = None
    if modo_grupo == "existente":
        grupo_id = form.get("grupo_familiar_id", "")
        if not grupo_id or not db.obtener_grupo(grupo_id):
            return con_error("Elegi un grupo familiar de la lista.")
        datos["grupo_familiar_id"] = grupo_id
    elif modo_grupo == "nuevo":
        nombre = form.get("nombre_grupo", "").strip() or f"Familia {datos['apellido']}"
        grupo_nuevo = db.crear_grupo(nombre)
        datos["grupo_familiar_id"] = grupo_nuevo["id"]

    try:
        socio = db.crear_socio(datos)
    except Exception:
        if grupo_nuevo:  # no dejar un grupo huerfano si falla el alta
            db.eliminar_grupo(grupo_nuevo["id"])
        raise

    # la disciplina principal siempre cuenta como actividad
    actividades = {a for a in form.getlist("actividades") if a in cuotas_service.ACTIVIDADES}
    if datos["disciplina_principal"] in cuotas_service.ACTIVIDADES:
        actividades.add(datos["disciplina_principal"])
    db.guardar_actividades(socio["id"], actividades)

    if grupo_nuevo:  # el primer socio del grupo nuevo queda como responsable
        db.asignar_responsable_grupo(grupo_nuevo["id"], socio["id"])

    return redirect(url_for("recepcion.ficha_socio", socio_id=socio["id"]))


@recepcion_bp.route("/socio/<socio_id>/baja", methods=["POST"])
def baja_socio(socio_id):
    motivo = request.form.get("motivo", "")
    db.dar_de_baja_socio(socio_id, motivo)
    return redirect(url_for("recepcion.index"))
