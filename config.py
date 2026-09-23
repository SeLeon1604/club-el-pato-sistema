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

    # Datos del club para la constancia de pago (PDF)
    CLUB_NOMBRE = os.environ.get("CLUB_NOMBRE", "Club El Pato")
    CLUB_DIRECCION = os.environ.get("CLUB_DIRECCION", "")
    CLUB_CUIT = os.environ.get("CLUB_CUIT", "")

    # Envio del recibo por email: "resend" o "smtp". Sin configurar,
    # el boton de enviar por email queda oculto en recepcion.
    EMAIL_PROVIDER = os.environ.get("EMAIL_PROVIDER", "")
    EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() != "false"
