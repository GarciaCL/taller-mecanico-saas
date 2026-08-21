import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from modulos.conexion import obtener_conexion, obtener_placeholder

def enviar_correo_taller(taller_id, destinatario, asunto, cuerpo_texto, archivo_pdf_bytes=None, nombre_pdf="Documento.pdf"):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        SELECT smtp_servidor, smtp_puerto, smtp_email, smtp_password, nombre_taller
        FROM talleres WHERE id = {p}
    """, (taller_id,))

    config = cursor.fetchone()
    conexion.close()

    if not config or not config[2] or not config[3]:
        print("⚠️ Correo no enviado: Falta configurar servidor SMTP en Ajustes del Taller.")
        return False

    smtp_servidor, smtp_puerto, smtp_email, smtp_password, nombre_taller = config

    try:
        msg = MIMEMultipart()
        msg['From'] = f"{nombre_taller} <{smtp_email}>"
        msg['To'] = destinatario
        msg['Subject'] = asunto

        msg.attach(MIMEText(cuerpo_texto, 'plain', 'utf-8'))

        if archivo_pdf_bytes:
            adjunto = MIMEApplication(archivo_pdf_bytes.read(), _subtype="pdf")
            adjunto.add_header('Content-Disposition', 'attachment', filename=nombre_pdf)
            msg.attach(adjunto)

        server = smtplib.SMTP(smtp_servidor, smtp_puerto)
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False