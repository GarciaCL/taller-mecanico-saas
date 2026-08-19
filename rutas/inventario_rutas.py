import os
import io
from flask import Blueprint, request, redirect, session, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
from modulos.ordenes import (
    crear_orden_recepcion_guiada, actualizar_estado_orden, 
    obtener_detalle_orden_por_token, actualizar_orden_trabajo, 
    finalizar_orden_trabajo, obtener_historial_vehiculo
)
from modulos.inventario import descontar_stock_orden
from modulos.generador_pdf import generar_pdf_ficha_recepcion

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
    orden = obtener_detalle_orden_por_token(token)
    if not orden:
        return render_template("seguimiento.html", error="Orden no encontrada"), 404
    return render_template("seguimiento.html", o=orden)

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