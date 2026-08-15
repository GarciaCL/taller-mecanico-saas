import json
import random
from datetime import datetime

# Esta es nuestra "tarjeta de acceso VIP" secreta
API_KEY_VALIDA = "TALLER-SECRET-KEY-2026"

def simular_servidor_vps(api_key_recibida):
    """
    Simula el servidor en la nube.
    Verifica la API Key y entrega las reservas web pendientes.
    """
    # 1. Validación de seguridad con la API Key
    if api_key_recibida != API_KEY_VALIDA:
        return {"estado": "error", "mensaje": "⛔ API Key inválida. Acceso denegado."}

    # 2. Simulamos citas que agendaron los clientes en la página web
    citas_simuladas = [
        {
            "id_reserva": 101,
            "cliente": "María González",
            "telefono": "+56987654321",
            "patente": "BB345CC",
            "servicio": "Cambio de Aceite y Filtro",
            "fecha_cita": "2026-08-20 10:00"
        },
        {
            "id_reserva": 102,
            "cliente": "Carlos Tapia",
            "telefono": "+56912345678",
            "patente": "DD789EE",
            "servicio": "Revisión de Frenos",
            "fecha_cita": "2026-08-21 15:30"
        }
    ]

    return {
        "estado": "exito", 
        "mensaje": "✅ Conexión exitosa con la Nube VPS.",
        "reservas": citas_simuladas
    }

def simular_envio_correos_recordatorio(api_key_recibida):
    """
    Simula el envío masivo diferido de correos de recordatorio 
    para clientes con mantenciones vencidas por tiempo/kilometraje.
    """
    if api_key_recibida != API_KEY_VALIDA:
        return {"estado": "error", "mensaje": "⛔ API Key inválida."}

    correos_enviados = [
        "📧 Enviado a juan@email.com: Recordatorio de mantención 50.000 KM + Cupón 15% Descuento.",
        "📧 Enviado a maria@email.com: Recordatorio revisión anual de frenos + Cupón 10% Descuento."
    ]

    return {
        "estado": "exito",
        "mensaje": "✅ Correos automáticos diferidos procesados correctamente.",
        "envios": correos_enviados
    }