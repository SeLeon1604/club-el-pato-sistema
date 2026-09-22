"""
Login unico para las 3 apps. Segun el rol del usuario autenticado,
redirige a la vista que le corresponde.

Identificador: email (recepcion, comision) o DNI (socio).
Credencial: PIN por persona (recepcion) o contrasena (comision, socio),
verificada con bcrypt contra `usuarios`.

TODO produccion:
- limitar intentos de PIN (la tablet queda en un lugar fisico accesible)
"""
import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, session

import db

auth_bp = Blueprint("auth", __name__)

# Hash descartable para gastar el mismo tiempo cuando el usuario no existe
_HASH_FALSO = bcrypt.hashpw(b"x", bcrypt.gensalt()).decode()

_DESTINO = {
    "recepcion": "recepcion.index",
    "comision": "comision.novedades",
    "socio": "socio.carnet",
    "admin": "admin.index",
}


def _credencial_valida(usuario, credencial):
    hash_ = None
    if usuario:
        hash_ = usuario["pin_hash"] if usuario["rol"] == "recepcion" else usuario["password_hash"]
    try:
        ok = bcrypt.checkpw(credencial.encode(), (hash_ or _HASH_FALSO).encode())
    except ValueError:  # hash mal formado en la base
        return False
    return ok and bool(hash_)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        rol = request.form.get("rol", "")
        identificador = request.form.get("identificador", "")
        credencial = request.form.get("credencial", "")

        if rol in _DESTINO and identificador.strip() and credencial:
            usuario = db.obtener_usuario_para_login(identificador, rol)
            if _credencial_valida(usuario, credencial):
                session.clear()
                session["usuario_id"] = usuario["id"]
                session["rol"] = usuario["rol"]
                session["socio_id"] = usuario.get("socio_id")
                return redirect(url_for(_DESTINO[rol]))

        return render_template("login.html", error="Credenciales invalidas")

    return render_template("login.html", error=None)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
