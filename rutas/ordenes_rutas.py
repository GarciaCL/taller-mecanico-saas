import os
import io
import cloudinary
import cloudinary.uploader
from flask import Blueprint, request, redirect, session, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
from modulos.conexion import obtener_conexion, obtener_placeholder
from modulos.ordenes import (
    crear_orden_recepcion_guiada, actualizar_estado_orden, 
    obtener_detalle_orden_por_token, actualizar_orden_trabajo, 
    finalizar_orden_trabajo, obtener_historial_vehiculo
)
from modulos.inventario import descontar_stock_orden
from modulos.generador_pdf import generar_pdf_ficha_recepcion
from datetime import datetime

# Asumiendo Blueprint ordenes_bp
ordenes_bp = Blueprint('ordenes', __name__)

# Configuración de Cloudinary (Asegúrate de tener las variables de entorno)
cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET"),
    secure = True
)

def guardar_foto(file, nombre_base):
    if not file or file.filename == '':
        return ''
    
    try:
        # Subir directamente la imagen desde la memoria a Cloudinary
        upload_result = cloudinary.uploader.upload(
            file,
            public_id=f"taller_ot/{nombre_base}",
            overwrite=True,
            resource_type="image"
        )
        # Retorna la URL pública segura en la nube
        return upload_result.get("secure_url", "")
    except Exception as e:
        print(f"[CLOUDINARY ERROR]: {e}")
        # Caída de respaldo local (Efemero en Render, pero evita error 500)
        filename = secure_filename(f"{nombre_base}_{file.filename}")
        path = os.path.join('static', 'uploads', filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        file.save(path)
        return f"/static/uploads/{filename}"

@ordenes_bp.route("/crear_ot", methods=["POST"])
def crear_ot_web():
    if "taller_id" not in session:
        return redirect("/login")
    
    patente = request.form["patente"]
    # Obtener datos, usando get y valores por defecto para seguridad
    cliente = request.form.get("cliente", "Cliente General").strip()
    telefono = request.form.get("telefono", "").strip()
    # Soportar inputs datalist o texto libre para marca/modelo
    marca = request.form.get("marca_input") or request.form.get("marca", "Marca")
    modelo = request.form.get("modelo_input") or request.form.get("modelo", "Modelo")
    sintomas = request.form["sintomas"]
    costo = float(request.form["costo"]) if request.form.get("costo") else 0.0
    km = int(request.form["km"]) if request.form.get("km") else 0
    combustible = request.form.get("combustible", "1/2")
    detalles = request.form.get("detalles", "")
    tiempo_horas = int(request.form.get("tiempo_estimado", 4))

    # Procesar las 5 fotos obligatorias/opcionales con Cloudinary
    fotos = {
        'frontal': guardar_foto(request.files.get('foto_frontal'), f"{patente}_frontal"),
        'trasera': guardar_foto(request.files.get('foto_trasera'), f"{patente}_trasera"),
        'costado_izq': guardar_foto(request.files.get('foto_izq'), f"{patente}_izq"),
        'costado_der': guardar_foto(request.files.get('foto_der'), f"{patente}_der"),
        'tablero': guardar_foto(request.files.get('foto_tablero'), f"{patente}_tablero")
    }
    
    # Llamar lógica de negocio (creará cliente/vehículo si no existen)
    crear_orden_recepcion_guiada(
        session["taller_id"], patente, sintomas, costo, km, combustible, 
        detalles, fotos, tiempo_horas, cliente, telefono, marca, modelo
    )
    return redirect("/")

# ... (otras rutas editar_ot, finalizar_ot, cambiar_estado_ot permanecen igual) ...

@ordenes_bp.route("/api/buscar_vehiculo/<patente>")
def api_buscar_vehiculo(patente):
    """Búsqueda AJAX de patente existente para autocompletar datos"""
    if "taller_id" not in session:
        return jsonify({"encontrado": False}), 401

    patente_limpia = patente.strip().upper()
    taller_id = session["taller_id"]

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    # Buscar marca, modelo del vehículo y nombre, teléfono del último dueño registrado en este taller
    cursor.execute(f"""
        SELECT v.marca, v.modelo, c.nombre, c.telefono
        FROM vehiculos v
        JOIN clientes c ON v.cliente_id = c.id
        WHERE c.taller_id = {p} AND UPPER(v.patente_vin) = {p}
        ORDER BY v.id DESC LIMIT 1
    """, (taller_id, patente_limpia))

    res = cursor.fetchone()
    conexion.close()

    if res:
        return jsonify({
            "encontrado": True,
            "marca": res[0] or "",
            "modelo": res[1] or "",
            "cliente": res[2] or "",
            "telefono": res[3] or ""
        })
    else:
        return jsonify({"encontrado": False})

@ordenes_bp.route("/descargar_pdf/<token>")
def descargar_pdf_web(token):
    if "taller_id" not in session:
        return redirect("/login")
        
    # Usar la función existente que ya obtiene detalle y repuestos
    orden, repuestos = obtener_detalle_orden_por_token(token)
    if not orden:
        return "Orden no encontrada", 404
    
    try:
        # Pasar request.host_url para generar QR absoluto
        pdf_data = generar_pdf_ficha_recepcion(orden, request.host_url.rstrip('/'))
        
        # Retornar archivo PDF
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Ficha_Recepcion_{orden[12]}.pdf" # orden[12] es patente
        )
    except Exception as e:
        print(f"Error generando PDF para token {token}: {e}")
        return "Error interno al generar PDF", 500

@ordenes_bp.route("/cambiar_estado_ot", methods=["POST"])
@ordenes_bp.route("/ordenes/cambiar_estado_ot", methods=["POST"])
def cambiar_estado_ot_web():
    if "taller_id" not in session:
        return jsonify({"error": "No autorizado"}), 401

    # Detectar si los datos vienen en JSON (JavaScript fetch) o Formulario (Form HTML)
    if request.is_json:
        datos = request.get_json() or {}
        orden_id = datos.get("orden_id")
        nuevo_estado = datos.get("nuevo_estado")
    else:
        orden_id = request.form.get("orden_id")
        nuevo_estado = request.form.get("nuevo_estado")

    if not orden_id or not nuevo_estado:
        return jsonify({"error": "Faltan parámetros obrigatorios"}), 400

    try:
        # Llamar a la función que actualiza la BD y envía el correo automático al cliente
        actualizar_estado_orden(int(orden_id), session["taller_id"], nuevo_estado)
        return jsonify({"exito": True, "mensaje": "Estado actualizado correctamente"})
    except Exception as e:
        print(f"[ERROR CAMBIAR ESTADO OT]: {e}")
        return jsonify({"error": str(e)}), 500