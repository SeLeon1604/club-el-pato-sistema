import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "cambiar-en-produccion")

    # No hay tokens CSRF: Lax evita que otros sitios disparen POSTs con la sesion
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True

    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

    # Mientras no haya credenciales reales de Supabase, el modulo db.py
    # trabaja con datos de ejemplo en memoria para poder probar las
    # pantallas sin depender de la base.
    MODO_DEMO = not (SUPABASE_URL and SUPABASE_KEY)
