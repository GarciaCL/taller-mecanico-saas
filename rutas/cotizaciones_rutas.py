from flask import Blueprint, request, jsonify, redirect, session, send_file
from modulos.cotizaciones import (
    crear_cotizacion, obtener_lista_cotizaciones,
    buscar_vehiculo_o_cliente_por_patente, cambiar_estado_cotizacion,
    revalidar_cotizacion_vencida, convertir_cotizacion_a_ot, generar_pdf_cotizacion
)
import json

cotizaciones_bp = Blueprint('cotizaciones', __name__)

@cotizaciones_bp.route("/buscar_patente_cotizacion/<patente>")
def buscar_patente_cotizacion_web(patente):
    if "taller_id" not in session:
        return jsonify({"encontrado": False}), 401
    
    datos = buscar_vehiculo_o_cliente_por_patente(session["taller_id"], patente)
    return jsonify(datos)

@cotizaciones_bp.route("/crear_cotizacion", methods=["POST"])
def crear_cotizacion_web():
    if "taller_id" not in session:
        return redirect("/login")

    cliente = request.form["cliente"]
    telefono = request.form.get("telefono", "")
    patente = request.form["patente"]
    marca = request.form.get("marca_input") or request.form.get("marca", "Marca")
    modelo = request.form.get("modelo_input") or "Modelo"
    sintomas = request.form.get("sintomas", "Presupuesto General")

    raw_items = request.form.get("items_cotizacion_json", "[]")
    try:
        items_json = json.loads(raw_items)
    except Exception:
        items_json = []

    crear_cotizacion_completa(session["taller_id"], cliente, telefono, patente, marca, modelo, sintomas, items_json)
    return redirect("/#cot")

@cotizaciones_bp.route("/rechazar_cotizacion/<int:cot_id>", methods=["POST"])
def rechazar_cotizacion_web(cot_id):
    if "taller_id" not in session:
        return jsonify({"success": False}), 401

    cambiar_estado_cotizacion(cot_id, session["taller_id"], "rechazada")
    return jsonify({"success": True})

@cotizaciones_bp.route("/revalidar_cotizacion/<int:cot_id>", methods=["POST"])
def revalidar_cotizacion_web(cot_id):
    if "taller_id" not in session:
        return jsonify({"success": False}), 401

    revalidar_cotizacion_vencida(cot_id, session["taller_id"])
    return jsonify({"success": True})

@cotizaciones_bp.route("/convertir_cotizacion_ot/<int:cot_id>", methods=["POST"])
def convertir_cotizacion_ot_web(cot_id):
    if "taller_id" not in session:
        return jsonify({"success": False}), 401

    exito = convertir_cotizacion_a_ot(cot_id, session["taller_id"])
    return jsonify({"success": exito})

@cotizaciones_bp.route("/descargar_pdf_cotizacion/<int:cot_id>")
def descargar_pdf_cotizacion_web(cot_id):
    pdf = generar_pdf_cotizacion(cot_id)
    if not pdf:
        return "Cotización no encontrada", 404
    return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name=f'Presupuesto_{cot_id}.pdf')