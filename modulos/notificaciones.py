import os
import threading
import resend
from dotenv import load_dotenv

# Cargar las variables del archivo .env explícitamente
load_dotenv()

# Cargar configuración desde las variables de entorno (.env)
resend.api_key = os.getenv("RESEND_API_KEY")
SENDER = os.getenv("MAIL_DEFAULT_SENDER", "Mi Taller Online <onboarding@resend.dev>")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

def _enviar_async(params):
    """Envía el correo en segundo plano para no congelar la página web."""
    try:
        resend.Emails.send(params)
        print(f"[CORREO ENVIADO] A: {params['to']}")
    except Exception as e:
        print(f"[ERROR CORREO] No se pudo enviar el mensaje: {e}")

def enviar_correo(para, asunto, html_content):
    """Función principal para disparar correos asíncronos."""
    if not resend.api_key:
        print("[ALERTA CORREO] RESEND_API_KEY no está configurada en .env")
        return

    params = {
        "from": SENDER,
        "to": [para],
        "subject": asunto,
        "html": html_content
    }
    # Ejecuta el envío en un hilo secundario
    threading.Thread(target=_enviar_async, args=(params,)).start()


# ==========================================
# 1. CORREO DE BIENVENIDA AL USUARIO / CLIENTE
# ==========================================
def enviar_bienvenida_usuario(email_usuario, nombre_usuario):
    asunto = "¡Bienvenido a Mi Taller Online! 🛠️"
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 30px; margin: 0;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 16px; padding: 25px; border: 1px solid #334155;">
            <h2 style="color: #38bdf8; margin-top: 0;">¡Hola, {nombre_usuario}! 👋</h2>
            <p style="font-size: 15px; color: #cbd5e1; line-height: 1.6;">
                Te damos la bienvenida a <strong>Mi Taller Online</strong>. Tu cuenta ha sido creada exitosamente.
            </p>
            <p style="font-size: 15px; color: #cbd5e1; line-height: 1.6;">
                Desde tu panel podrás gestionar tus vehículos, ver el estado de tus órdenes de trabajo en tiempo real y agendar tus próximas mantenciones.
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://mitalleronline.cl/login" style="background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 10px; font-weight: bold; font-size: 14px; display: inline-block;">
                    Acceder a Mi Cuenta
                </a>
            </div>
            <hr style="border: 0; border-top: 1px solid #334155; margin: 20px 0;">
            <p style="font-size: 12px; color: #64748b; text-align: center; margin: 0;">
                Si no creaste esta cuenta, puedes ignorar este mensaje.
            </p>
        </div>
    </body>
    </html>
    """
    enviar_correo(email_usuario, asunto, html)


# ==========================================
# 2. AVISO DE NUEVO REGISTRO AL ADMINISTRADOR
# ==========================================
def enviar_aviso_registro_admin(nombre_taller, email_taller):
    if not ADMIN_EMAIL:
        return
        
    asunto = f"🚨 Nuevo Registro en la Plataforma: {nombre_taller}"
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f8fafc; color: #0f172a; padding: 20px;">
        <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0;">
            <h3 style="color: #0284c7; margin-top: 0;">Se ha registrado un nuevo usuario / taller</h3>
            <ul style="line-height: 1.8; color: #334155;">
                <li><strong>Nombre / Taller:</strong> {nombre_taller}</li>
                <li><strong>Correo Electrónico:</strong> {email_taller}</li>
            </ul>
            <p style="font-size: 13px; color: #64748b;">Puedes verificar sus detalles desde el panel SuperAdmin.</p>
        </div>
    </body>
    </html>
    """
    enviar_correo(ADMIN_EMAIL, asunto, html)


# ==========================================
# 3. COMPROBANTE DE PAGO CONFIRMADO
# ==========================================
def enviar_notificacion_pago(email_usuario, monto, detalle_pago):
    asunto = "Comprobante de Pago Recibido - Mi Taller Online 💳"
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 30px; margin: 0;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 16px; padding: 25px; border: 1px solid #334155;">
            <h2 style="color: #4ade80; margin-top: 0;">¡Pago Recibido con Éxito! 🎉</h2>
            <p style="font-size: 15px; color: #cbd5e1;">Hemos procesado correctamente tu pago en la plataforma.</p>
            <div style="background-color: #0f172a; padding: 15px; border-radius: 10px; margin: 20px 0; border: 1px solid #334155;">
                <p style="margin: 5px 0; color: #94a3b8; font-size: 13px;">Concepto: <strong style="color: #f8fafc;">{detalle_pago}</strong></p>
                <p style="margin: 5px 0; color: #94a3b8; font-size: 13px;">Monto Total: <strong style="color: #4ade80; font-size: 18px;">${monto}</strong></p>
            </div>
            <p style="font-size: 14px; color: #cbd5e1;">Tu suscripción / servicio se encuentra 100% activo.</p>
        </div>
    </body>
    </html>
    """
    enviar_correo(email_usuario, asunto, html)


# ==========================================
# 4. AVISO DE VENCIMIENTO DE SUSCRIPCIÓN
# ==========================================
def enviar_aviso_vencimiento(email_usuario, fecha_vencimiento):
    asunto = "⚠️ Recordatorio: Tu suscripción está por vencer"
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 30px; margin: 0;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 16px; padding: 25px; border: 1px solid #334155;">
            <h2 style="color: #fbbf24; margin-top: 0;">Aviso de Vencimiento Próximo</h2>
            <p style="font-size: 15px; color: #cbd5e1;">Te recordamos que tu plan vence el día: <strong style="color: #f59e0b;">{fecha_vencimiento}</strong>.</p>
            <p style="font-size: 14px; color: #cbd5e1;">Para no perder el acceso a la gestión de tu taller, renueva tu suscripción desde el panel.</p>
            <div style="text-align: center; margin: 25px 0;">
                <a href="https://mitalleronline.cl/superadmin" style="background-color: #d97706; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 10px; font-weight: bold; font-size: 14px; display: inline-block;">
                    Renovar Suscripción
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    enviar_correo(email_usuario, asunto, html)

    # ==========================================
# 5. AVISO DE CAMBIO DE ESTADO EN ORDEN DE TRABAJO
# ==========================================
def enviar_aviso_estado_ot(email_cliente, nombre_cliente, patente, nuevo_estado, nombre_taller):
    asunto = f"🚗 Actualización de tu Vehículo [{patente}] - {nombre_taller}"
    
    # Mensaje o estilo personalizado según el estado
    color_banner = "#3b82f6" # Azul por defecto
    if nuevo_estado.lower() in ["listo", "listo para retiro", "completado"]:
        color_banner = "#22c55e" # Verde
    elif nuevo_estado.lower() in ["en proceso", "en reparacion"]:
        color_banner = "#f59e0b" # Naranja

    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 30px; margin: 0;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 16px; padding: 25px; border: 1px solid #334155;">
            <h2 style="color: {color_banner}; margin-top: 0;">¡Hola, {nombre_cliente}! 👋</h2>
            <p style="font-size: 15px; color: #cbd5e1; line-height: 1.6;">
                Te informamos que tu vehículo con patente <strong style="color: #f8fafc; font-size: 16px;">{patente}</strong> en <strong>{nombre_taller}</strong> ha actualizado su estado a:
            </p>
            <div style="text-align: center; background-color: #0f172a; padding: 15px; border-radius: 10px; margin: 20px 0; border: 1px solid #334155;">
                <span style="color: {color_banner}; font-weight: bold; font-size: 18px; text-transform: uppercase;">
                    {nuevo_estado}
                </span>
            </div>
            <p style="font-size: 14px; color: #94a3b8; text-align: center;">
                Si tienes dudas o necesitas coordinar el retiro, por favor ponte en contacto directo con el taller.
            </p>
        </div>
    </body>
    </html>
    """
    enviar_correo(email_cliente, asunto, html)