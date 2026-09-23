"""
Constancia de pago: arma el PDF del recibo y lo manda por email.
Logica de negocio separada de la capa de datos, igual que cuotas.py.
Accede a los datos solo a traves de db.py.
"""
import smtplib
from email.message import EmailMessage

from fpdf import FPDF

from config import Config


def _cuotas_por_socio(cuotas):
    """[(socio_nombre, socio_nro, [periodo, ...]), ...] agrupando las
    cuotas por socio (un pago puede cubrir a varios integrantes de un
    mismo grupo familiar), en el orden en que aparecen."""
    orden, grupos = [], {}
    for c in cuotas:
        clave = (c["socio_nombre"], c["socio_nro"])
        if clave not in grupos:
            orden.append(clave)
            grupos[clave] = []
        grupos[clave].append(c["periodo"])
    return [(nombre, nro, sorted(periodos)) for nombre, nro in orden
            for periodos in [grupos[(nombre, nro)]]]


def generar_pdf(detalle):
    """Bytes del PDF de la constancia de pago."""
    pago, cuotas = detalle["pago"], detalle["cuotas"]

    pdf = FPDF(format="A5")
    pdf.set_auto_page_break(True, margin=12)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, Config.CLUB_NOMBRE, ln=True)
    pdf.set_font("Helvetica", "", 9)
    for linea in (Config.CLUB_DIRECCION, f"CUIT {Config.CLUB_CUIT}" if Config.CLUB_CUIT else ""):
        if linea:
            pdf.cell(0, 5, linea, ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Constancia de pago", ln=True)
    pdf.set_font("Helvetica", "", 10)
    numero = pago.get("numero")
    pdf.cell(0, 6, f"Recibo N° {numero:06d}" if numero else f"Recibo {pago['id']}", ln=True)
    fecha = (pago.get("fecha_pago") or "")[:16].replace("T", " ")
    pdf.cell(0, 6, f"Fecha: {fecha}", ln=True)
    pdf.cell(0, 6, f"Medio de pago: {pago['medio_pago']}", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Detalle", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for nombre, nro, periodos in _cuotas_por_socio(cuotas):
        # ln=True: sin esto fpdf2 deja el cursor pegado a la derecha y la
        # siguiente linea se queda sin ancho disponible.
        pdf.multi_cell(0, 6, f"{nombre} (Socio N° {nro}): {', '.join(periodos)}", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Total pagado: ${pago['monto_pagado']:.2f}", ln=True)

    return bytes(pdf.output())


def enviar_email(destinatario, pdf_bytes, detalle):
    """Manda el PDF adjunto al destinatario con el proveedor configurado
    en EMAIL_PROVIDER ('resend' o 'smtp'). Lanza RuntimeError si no hay
    ninguno configurado."""
    numero = detalle["pago"].get("numero")
    asunto = (f"{Config.CLUB_NOMBRE} - Recibo N° {numero:06d}" if numero
              else f"{Config.CLUB_NOMBRE} - Recibo de pago")
    cuerpo = "Hola! Te adjuntamos la constancia de tu pago. Gracias."

    if Config.EMAIL_PROVIDER == "resend":
        import resend
        resend.api_key = Config.RESEND_API_KEY
        resend.Emails.send({
            "from": Config.EMAIL_FROM,
            "to": [destinatario],
            "subject": asunto,
            "text": cuerpo,
            "attachments": [{"filename": "recibo.pdf", "content": list(pdf_bytes)}],
        })
        return

    if Config.EMAIL_PROVIDER == "smtp":
        msg = EmailMessage()
        msg["Subject"] = asunto
        msg["From"] = Config.EMAIL_FROM
        msg["To"] = destinatario
        msg.set_content(cuerpo)
        msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename="recibo.pdf")
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as smtp:
            if Config.SMTP_USE_TLS:
                smtp.starttls()
            if Config.SMTP_USER:
                smtp.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            smtp.send_message(msg)
        return

    raise RuntimeError("No hay un proveedor de email configurado (EMAIL_PROVIDER).")
