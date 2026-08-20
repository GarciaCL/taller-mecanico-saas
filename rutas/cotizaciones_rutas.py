from flask import Blueprint, request, jsonify, redirect, session
from modulos.cotizaciones import (
    crear_cotizacion, obtener_lista_cotizaciones,
    obtener_detalle_cotizacion, agregar_item_cotizacion,
    convertir_cotizacion_a_ot
)

cotizaciones_bp = Blueprint('cotizaciones', __name__)

@cotizaciones_bp.route("/crear_cotizacion", methods=["POST"])
def crear_cotizacion_web():
    if "taller_id" not in session:
        return redirect("/login")

    cliente = request.form["cliente"]
    telefono = request.form.get("telefono", "")
    patente = request.form["patente"]
    marca = request.form.get("marca", "")
    modelo = request.form.get("modelo", "")
    sintomas = request.form.get("sintomas", "Presupuesto General")

    crear_cotizacion(session["taller_id"], cliente, telefono, patente, marca, modelo, sintomas)
    return redirect("/")

@cotizaciones_bp.route("/vincular_item_cotizacion", methods=["POST"])
def vincular_item_cotizacion_web():
    if "taller_id" not in session:
        return jsonify({"success": False}), 401

    cot_id = int(request.form["cotizacion_id"])
    inventario_id = int(request.form["inventario_id"]) if request.form.get("inventario_id") else None
    descripcion = request.form.get("descripcion", "")
    cantidad = int(request.form.get("cantidad", 1))
    precio = float(request.form.get("precio_unidad", 0.0))

    nuevo_total = agregar_item_cotizacion(cot_id, inventario_id, descripcion, cantidad, precio)
    return jsonify({"success": True, "nuevo_total": nuevo_total})

@cotizaciones_bp.route("/convertir_cotizacion_ot/<int:cot_id>", methods=["POST"])
def convertir_cotizacion_ot_web(cot_id):
    if "taller_id" not in session:
        return jsonify({"success": False}), 401

    exito = convertir_cotizacion_a_ot(cot_id, session["taller_id"])
    return jsonify({"success": exito})