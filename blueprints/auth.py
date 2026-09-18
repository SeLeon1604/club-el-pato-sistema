"""
Login unico para las 3 apps. Segun el rol del usuario autenticado,
redirige a la vista que le corresponde.

TODO produccion:
- reemplazar la verificacion de PIN/password por hash real (bcrypt)
  contra la tabla `usuarios`
- limitar intentos de PIN (la tablet queda en un lugar fisico accesible)
"""
from flask import Blueprint, render_template, request, redirect, url_for, session

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        rol = request.form.get("rol")
        credencial = request.form.get("credencial")

        # TODO: reemplazar por validacion real contra tabla `usuarios`
        if rol and credencial:
            session["rol"] = rol
            session["usuario_id"] = "demo-user"
            if rol == "recepcion":
                return redirect(url_for("recepcion.index"))
            if rol == "comision":
                return redirect(url_for("comision.novedades"))
            if rol == "socio":
                return redirect(url_for("socio.carnet"))

        return render_template("login.html", error="Credenciales invalidas")

    return render_template("login.html", error=None)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
