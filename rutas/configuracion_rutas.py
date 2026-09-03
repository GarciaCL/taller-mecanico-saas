import os
import cloudinary
import cloudinary.uploader
from flask import Blueprint, request, redirect, session, jsonify
from modulos.conexion import obtener_conexion, obtener_placeholder

# Asumiendo que este es el Blueprint correcto para este archivo
configuracion_bp = Blueprint('configuracion', __name__)

# Configuración de Cloudinary (Asegúrate de tener las variables de entorno configuradas en Render)
cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET"),
    secure = True
)

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

@configuracion_bp.route("/guardar_ajustes_taller", methods=["POST"])
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

@configuracion_bp.route("/crear_mecanico_ajax", methods=["POST"])
def crear_mecanico_ajax():
    """Registra un mecánico vía AJAX evitando duplicados"""
    if "taller_id" not in session:
        return jsonify({"status": "error", "mensaje": "Sesión expirada"}), 401

    try:
        data = request.get_json()
        nombre = data.get("nombre", "").strip()
        especialidad = data.get("especialidad", "").strip()

        if not nombre:
            return jsonify({"status": "error", "mensaje": "El nombre es obligatorio"}), 400

        taller_id = session["taller_id"]
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        p = obtener_placeholder()

        # 1. Verificar si ya existe un mecánico con el mismo nombre en el taller (case insensitive)
        cursor.execute(f"""
            SELECT id FROM mecanicos 
            WHERE taller_id = {p} AND LOWER(nombre) = LOWER({p})
        """, (taller_id, nombre))
        existe = cursor.fetchone()

        if existe:
            conexion.close()
            # Si existe, retornamos el ID existente indicando éxito para asignarlo
            return jsonify({
                "status": "ok", 
                "id": existe[0], 
                "nombre": nombre, 
                "mensaje": "El mecánico ya estaba registrado, se ha seleccionado automáticamente."
            })

        # 2. Si no existe, insertar
        cursor.execute(f"""
            INSERT INTO mecanicos (taller_id, nombre, especialidad)
            VALUES ({p}, {p}, {p})
        """, (taller_id, nombre, especialidad))
        conexion.commit()

        # Obtener el ID generado
        cursor.execute(f"SELECT id FROM mecanicos WHERE taller_id = {p} ORDER BY id DESC LIMIT 1", (taller_id,))
        nuevo_id = cursor.fetchone()[0]
        conexion.close()

        return jsonify({
            "status": "ok", 
            "id": nuevo_id, 
            "nombre": nombre,
            "mensaje": "Mecánico registrado y seleccionado."
        })

    except Exception as e:
        print(f"Error en crear_mecanico_ajax: {e}")
        if 'conexion' in locals() and conexion:
            conexion.rollback()
            conexion.close()
        return jsonify({"status": "error", "mensaje": "Error interno del servidor"}), 500