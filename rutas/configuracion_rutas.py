from flask import Blueprint, request, redirect, session
from modulos.configuracion import actualizar_ajustes_taller

configuracion_bp = Blueprint('configuracion', __name__)

@configuracion_bp.route("/guardar_ajustes_taller", methods=["POST"])
def guardar_ajustes_web():
    if "taller_id" not in session:
        return redirect("/login")

    datos = {
        "nombre_taller": request.form["nombre_taller"],
        "logo_url": request.form.get("logo_url", "/static/logo_defecto.png"),
        "color_primario": request.form.get("color_primario", "#3b82f6"),
        "rut_taller": request.form.get("rut_taller", ""),
        "direccion_taller": request.form.get("direccion_taller", ""),
        "telefono_taller": request.form.get("telefono_taller", ""),
        "email_taller": request.form.get("email_taller", ""),
        "msg_whatsapp_listo": request.form.get("msg_whatsapp_listo", ""),
        "msg_whatsapp_cotizacion": request.form.get("msg_whatsapp_cotizacion", ""),
        "mecanico_puede_finalizar": "mecanico_puede_finalizar" in request.form,
        "mecanico_puede_rechazar": "mecanico_puede_rechazar" in request.form,
    }

    actualizar_ajustes_taller(session["taller_id"], datos)

    # Actualizar variables de sesión
    session["nombre_taller"] = datos["nombre_taller"]
    session["logo_url"] = datos["logo_url"]
    session["color_primario"] = datos["color_primario"]

    return redirect("/#ajustes")