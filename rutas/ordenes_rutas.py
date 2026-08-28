import os
import io
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


ordenes_bp = Blueprint('ordenes', __name__)

def guardar_foto(file, nombre_base):
    if not file or file.filename == '':
        return ''
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
    cliente = request.form.get("cliente", "Cliente General")
    telefono = request.form.get("telefono", "")
    marca = request.form.get("marca_input") or request.form.get("marca", "Marca")
    modelo = request.form.get("modelo_input") or request.form.get("modelo", "Modelo")
    sintomas = request.form["sintomas"]
    costo = float(request.form["costo"]) if request.form.get("costo") else 0.0
    km = int(request.form["km"]) if request.form.get("km") else 0
    combustible = request.form.get("combustible", "1/2")
    detalles = request.form.get("detalles", "")
    tiempo_horas = int(request.form.get("tiempo_estimado", 4))

    fotos = {
        'frontal': guardar_foto(request.files.get('foto_frontal'), f"{patente}_frontal"),
        'trasera': guardar_foto(request.files.get('foto_trasera'), f"{patente}_trasera"),
        'costado_izq': guardar_foto(request.files.get('foto_izq'), f"{patente}_izq"),
        'costado_der': guardar_foto(request.files.get('foto_der'), f"{patente}_der"),
        'tablero': guardar_foto(request.files.get('foto_tablero'), f"{patente}_tablero")
    }
    
    crear_orden_recepcion_guiada(
        session["taller_id"], patente, sintomas, costo, km, combustible, 
        detalles, fotos, tiempo_horas, cliente, telefono, marca, modelo
    )
    return redirect("/")

@ordenes_bp.route("/editar_ot", methods=["POST"])
def editar_ot_web():
    if "taller_id" not in session:
        return redirect("/login")
    
    orden_id = int(request.form["orden_id"])
    km = int(request.form["km"]) if request.form.get("km") else 0
    combustible = request.form.get("combustible", "1/2")
    tiempo_horas = int(request.form.get("tiempo_estimado", 4))
    sintomas = request.form.get("sintomas", "")
    costo = float(request.form["costo"]) if request.form.get("costo") else 0.0

    actualizar_orden_trabajo(session["taller_id"], orden_id, km, combustible, tiempo_horas, sintomas, costo)
    return redirect("/")

@ordenes_bp.route("/finalizar_ot", methods=["POST"])
def finalizar_ot_web():
    if "taller_id" not in session:
        return redirect("/login")
    
    orden_id = int(request.form["orden_id"])
    descontar_stock_orden(orden_id, session["taller_id"])
    finalizar_orden_trabajo(orden_id, session["taller_id"])
    return redirect("/")

@ordenes_bp.route("/cambiar_estado_ot", methods=["POST"])
def cambiar_estado_ot_web():
    if "taller_id" not in session:
        return jsonify({"success": False}), 401
    
    data = request.get_json()
    orden_id = data["orden_id"]
    nuevo_estado = data["nuevo_estado"]

    actualizar_estado_orden(orden_id, session["taller_id"], nuevo_estado)
    if nuevo_estado == 'entrega':
        descontar_stock_orden(orden_id, session["taller_id"])

    return jsonify({"success": True})

@ordenes_bp.route("/seguimiento/<token>")
def seguimiento_cliente(token):
    orden, repuestos = obtener_detalle_orden_por_token(token)
    if not orden:
        return render_template("seguimiento.html", error="Orden no encontrada"), 404
    return render_template("seguimiento.html", o=orden, repuestos=repuestos)

@ordenes_bp.route("/historial/<patente>")
def historial_vehiculo_web(patente):
    if "taller_id" not in session:
        return redirect("/login")
    
    historial = obtener_historial_vehiculo(session["taller_id"], patente)
    return render_template("historial.html", historial=historial, patente=patente.upper())

@ordenes_bp.route("/descargar_pdf/<token>")
def descargar_pdf_web(token):
    orden = obtener_detalle_orden_por_token(token)
    if not orden:
        return "Orden no encontrada", 404
    
    pdf_data = generar_pdf_ficha_recepcion(orden, request.host_url.rstrip('/'))
    return send_file(
        io.BytesIO(pdf_data),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Ficha_Recepcion_{orden[12]}.pdf"
    )

@ordenes_bp.route("/api/historial/<patente>")
def api_historial_vehiculo(patente):
    if "taller_id" not in session:
        return jsonify([]), 401
    
    try:
        historial = obtener_historial_vehiculo(session["taller_id"], patente)
        
        resultado = []
        for h in historial:
            fecha_val = h[7]
            if isinstance(fecha_val, datetime):
                fecha_str = fecha_val.strftime("%d/%m/%Y %H:%M")
            else:
                fecha_str = str(fecha_val) if fecha_val else "Fecha no disponible"

            resultado.append({
                "id": h[0],
                "estado": h[1],
                "sintomas": h[2] or "",
                "costo": h[3] or 0,
                "km": h[4] or 0,
                "combustible": h[5] or "1/2",
                "token": h[6] or "",
                "fecha": fecha_str,
                "patente": h[8],
                "marca": h[9] or "",
                "modelo": h[10] or "",
                "cliente": h[12] or "Cliente General",
                "telefono": h[13] or "",
                "archivada": h[14] if len(h) > 14 else False
            })
        return jsonify(resultado)
    except Exception as e:
        print(f"Error en API historial: {e}")
        return jsonify([])

@ordenes_bp.route("/archivar_ot", methods=["POST"])
def archivar_ot_ajax():
    if "taller_id" not in session:
        return jsonify({"status": "error", "mensaje": "Sesión expirada"}), 401

    try:
        datos = request.get_json()
        orden_id = datos.get("orden_id")

        if not orden_id:
            return jsonify({"status": "error", "mensaje": "ID de orden no proporcionado"}), 400

        taller_id = session["taller_id"]
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        p = obtener_placeholder()

        # Asegurar columna 'archivada' en la tabla
        try:
            cursor.execute("ALTER TABLE ordenes_trabajo ADD COLUMN IF NOT EXISTS archivada BOOLEAN DEFAULT FALSE")
            conexion.commit()
        except Exception:
            conexion.rollback()

        # Marcar la orden como archivada y estado 'entrega'
        cursor.execute(f"""
            UPDATE ordenes_trabajo 
            SET archivada = TRUE, estado = 'entrega' 
            WHERE id = {p} AND taller_id = {p}
        """, (orden_id, taller_id))

        conexion.commit()
        conexion.close()

        return jsonify({"status": "ok", "mensaje": "Orden archivada con éxito"})

    except Exception as e:
        print(f"Error al archivar OT: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500