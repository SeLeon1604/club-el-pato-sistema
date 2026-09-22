"""
Club El Pato - sistema de administracion
Punto de entrada Flask. Sirve las 3 PWA (recepcion, comision, socio)
desde un mismo backend, cada una con su manifest y su vista segun rol.
"""
from flask import Flask, session, redirect, url_for
from config import Config

from blueprints.auth import auth_bp
from blueprints.recepcion import recepcion_bp
from blueprints.comision import comision_bp
from blueprints.socio import socio_bp
from blueprints.admin import admin_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(auth_bp)
    app.register_blueprint(recepcion_bp, url_prefix="/recepcion")
    app.register_blueprint(comision_bp, url_prefix="/comision")
    app.register_blueprint(socio_bp, url_prefix="/carnet")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.route("/")
    def home():
        # redirige segun el rol logueado; si no hay sesion, va al login
        rol = session.get("rol")
        if rol == "recepcion":
            return redirect(url_for("recepcion.index"))
        if rol == "comision":
            return redirect(url_for("comision.novedades"))
        if rol == "socio":
            return redirect(url_for("socio.carnet"))
        if rol == "admin":
            return redirect(url_for("admin.index"))
        return redirect(url_for("auth.login"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
