import os
import cloudinary
import cloudinary.uploader
from flask import Blueprint, request, redirect, session
from modulos.conexion import obtener_conexion, obtener_placeholder

cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "hylsaomw"),
    api_key = os.environ.get("CLOUDINARY_API_KEY", "342238895435546"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET", "WWzr1lNjdqEZVDD9BqcYPuOU4Is"),
    secure = True
)

configuracion_bp = Blueprint('configuracion', __name__)
# Función auxiliar para subir el logo a Cloudinary
def subir_logo_taller(file_logo, taller_id, url_actual=""):
    if not file_logo or file_logo.filename == '':
        return url_actual

    try:
        # Subir logo a una carpeta exclusiva en Cloudinary
        upload_result = cloudinary.uploader.upload(
            file_logo,
            public_id=f"logos_talleres/logo_taller_{taller_id}",
            overwrite=True,
            resource_type="image"
        )
        return upload_result.get("secure_url", url_actual)
    except Exception as e:
        print(f"[CLOUDINARY LOGO ERROR]: {e}")
        return url_actual

@ajustes_bp.route("/guardar_ajustes_taller", methods=["POST"])
def guardar_ajustes_taller_web():
    if "taller_id" not in session:
        return redirect("/login")

    taller_id = session["taller_id"]
    nombre_taller = request.form["nombre_taller"]
    rut_taller = request.form.get("rut_taller", "")
    color_primario = request.form.get("color_primario", "#3b82f6")
    logo_url_actual = request.form.get("logo_url_actual", "/static/logo_defecto.png")
    
    # Archivo enviado desde la vista HTML
    logo_archivo = request.files.get("logo_archivo")

    # Subir a Cloudinary o conservar la URL previa
    logo_final = subir_logo_taller(logo_archivo, taller_id, logo_url_actual)

    # Datos SMTP
    smtp_servidor = request.form.get("smtp_servidor", "smtp.gmail.com")
    smtp_puerto = int(request.form.get("smtp_puerto", 587))
    smtp_email = request.form.get("smtp_email", "")
    smtp_password = request.form.get("smtp_password", "")

    # Plantillas de correo
    msg_email_cotizacion = request.form.get("msg_email_cotizacion", "")
    msg_email_listo = request.form.get("msg_email_listo", "")

    # Actualizar en la BD del taller
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        UPDATE talleres
        SET nombre_taller = {p},
            logo_url = {p},
            color_primario = {p},
            rut_taller = {p},
            smtp_servidor = {p},
            smtp_puerto = {p},
            smtp_email = {p},
            smtp_password = {p},
            msg_email_cotizacion = {p},
            msg_email_listo = {p}
        WHERE id = {p}
    """, (
        nombre_taller, logo_final, color_primario, rut_taller,
        smtp_servidor, smtp_puerto, smtp_email, smtp_password,
        msg_email_cotizacion, msg_email_listo, taller_id
    ))

    conexion.commit()
    conexion.close()

    # Actualizar los datos reflejados en la sesión activa
    session["nombre_taller"] = nombre_taller
    session["logo_url"] = logo_final
    session["color_primario"] = color_primario

    return redirect("/#ajustes")