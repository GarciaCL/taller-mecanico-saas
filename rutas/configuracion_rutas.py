import os
from flask import Blueprint, request, redirect, session
from werkzeug.utils import secure_filename
from modulos.conexion import obtener_conexion, obtener_placeholder

configuracion_bp = Blueprint('configuracion', __name__)

@configuracion_bp.route("/guardar_ajustes_taller", methods=["POST"])
def guardar_ajustes_web():
    if "taller_id" not in session:
        return redirect("/login")

    taller_id = session["taller_id"]
    nombre = request.form["nombre_taller"]
    color = request.form.get("color_primario", "#3b82f6")
    
    # Manejo de la subida del Logo
    logo_file = request.files.get("logo_archivo")
    logo_url = request.form.get("logo_url_actual", "/static/logo_defecto.png")

    if logo_file and logo_file.filename != '':
        filename = f"logo_taller_{taller_id}_" + secure_filename(logo_file.filename)
        folder = os.path.join("static", "logos")
        os.makedirs(folder, exist_ok=True)
        path_guardado = os.path.join(folder, filename)
        logo_file.save(path_guardado)
        logo_url = f"/{path_guardado}"

    # Guardar en Base de Datos
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        UPDATE talleres
        SET nombre_taller = {p}, logo_url = {p}, color_primario = {p},
            rut_taller = {p}, direccion_taller = {p}, telefono_taller = {p}, email_taller = {p},
            msg_whatsapp_listo = {p}, msg_whatsapp_cotizacion = {p},
            smtp_servidor = {p}, smtp_puerto = {p}, smtp_email = {p}, smtp_password = {p},
            msg_email_cotizacion = {p}, msg_email_listo = {p},
            mecanico_puede_finalizar = {p}, mecanico_puede_rechazar = {p}
        WHERE id = {p}
    """, (
        nombre, logo_url, color,
        request.form.get("rut_taller", ""), request.form.get("direccion_taller", ""),
        request.form.get("telefono_taller", ""), request.form.get("email_taller", ""),
        request.form.get("msg_whatsapp_listo", ""), request.form.get("msg_whatsapp_cotizacion", ""),
        request.form.get("smtp_servidor", "smtp.gmail.com"), int(request.form.get("smtp_puerto", 587)),
        request.form.get("smtp_email", ""), request.form.get("smtp_password", ""),
        request.form.get("msg_email_cotizacion", ""), request.form.get("msg_email_listo", ""),
        "mecanico_puede_finalizar" in request.form, "mecanico_puede_rechazar" in request.form,
        taller_id
    ))

    conexion.commit()
    conexion.close()

    session["nombre_taller"] = nombre
    session["logo_url"] = logo_url
    session["color_primario"] = color

    return redirect("/#ajustes")