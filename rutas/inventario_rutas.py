from flask import Blueprint, request, jsonify, redirect, session
from modulos.inventario import (
    agregar_repuesto, agregar_repuestos_masivo,
    eliminar_repuesto, eliminar_repuestos_masivo,
    agregar_repuesto_a_orden, obtener_repuestos_orden,
    eliminar_repuesto_orden, actualizar_repuesto_orden
)

# Declaracion explicita para solucionar el ImportError en Render
inventario_bp = Blueprint('inventario', __name__)

@inventario_bp.route("/guardar_repuesto", methods=["POST"])
def guardar_repuesto_web():
    if "taller_id" not in session:
        return redirect("/login")
    
    codigo = request.form.get("codigo", "").strip()
    categoria = request.form.get("categoria", "General").strip()
    nombre = request.form.get("nombre", "").strip()
    stock = int(request.form["stock"]) if request.form.get("stock") and request.form.get("stock").isdigit() else 0
    compat = request.form.get("compatabilidades_final", "Universal").strip() or "Universal"

    agregar_repuesto(session["taller_id"], codigo, categoria, nombre, stock, 0, 0, 0, compat)
    return redirect("/")

@inventario_bp.route("/carga_masiva_repuestos", methods=["POST"])
def carga_masiva_repuestos_web():
    if "taller_id" not in session:
        return jsonify({"success": False}), 401
    
    data = request.get_json()
    repuestos = data.get("repuestos", [])
    if repuestos:
        agregar_repuestos_masivo(session["taller_id"], repuestos)
        return jsonify({"success": True, "count": len(repuestos)})
    return jsonify({"success": False}), 400

@inventario_bp.route("/eliminar_repuesto/<int:repuesto_id>", methods=["POST"])
def eliminar_repuesto_web(repuesto_id):
    if "taller_id" not in session:
        return jsonify({"success": False}), 401
    eliminar_repuesto(session["taller_id"], repuesto_id)
    return jsonify({"success": True})

@inventario_bp.route("/eliminar_repuestos_masivo", methods=["POST"])
def eliminar_repuestos_masivo_web():
    if "taller_id" not in session:
        return jsonify({"success": False}), 401
    data = request.get_json()
    ids = data.get("ids", [])
    if ids:
        eliminar_repuestos_masivo(session["taller_id"], ids)
        return jsonify({"success": True, "count": len(ids)})
    return jsonify({"success": False}), 400

@inventario_bp.route("/vincular_repuesto_ot", methods=["POST"])
def vincular_repuesto_ot_web():
    if "taller_id" not in session:
        return jsonify({"success": False}), 401
    orden_id = int(request.form["orden_id"])
    inventario_id = int(request.form["inventario_id"])
    cantidad = int(request.form.get("cantidad", 1))
    precio_unidad = float(request.form.get("precio_unidad", 0.0)) if request.form.get("precio_unidad") else 0.0

    agregar_repuesto_a_orden(orden_id, inventario_id, cantidad, precio_unidad)
    return redirect("/")

@inventario_bp.route("/obtener_repuestos_ot/<int:orden_id>")
def obtener_repuestos_ot_web(orden_id):
    if "taller_id" not in session:
        return jsonify([])
    items = obtener_repuestos_orden(orden_id)
    return jsonify([{"id": i[0], "nombre": i[1], "cantidad": i[2], "precio": i[3], "descontado": i[4]} for i in items])

@inventario_bp.route("/eliminar_repuesto_ot/<int:item_id>", methods=["POST"])
def eliminar_repuesto_ot_web(item_id):
    if "taller_id" not in session:
        return jsonify({"success": False}), 401
    eliminar_repuesto_orden(item_id)
    return jsonify({"success": True})

@inventario_bp.route("/actualizar_repuesto_ot", methods=["POST"])
def actualizar_repuesto_ot_web():
    if "taller_id" not in session:
        return jsonify({"success": False}), 401
    data = request.get_json()
    actualizar_repuesto_orden(int(data["item_id"]), int(data.get("cantidad", 1)), float(data.get("precio", 0.0)))
    return jsonify({"success": True})