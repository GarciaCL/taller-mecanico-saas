from flask import Blueprint, request, jsonify, redirect, session
from modulos.mecanicos import agregar_mecanico, asignar_mecanico_a_ot, obtener_lista_mecanicos

mecanicos_bp = Blueprint('mecanicos', __name__)

@mecanicos_bp.route("/agregar_mecanico", methods=["POST"])
def agregar_mecanico_web():
    if "taller_id" not in session:
        return redirect("/login")

    nombre = request.form["nombre"]
    especialidad = request.form.get("especialidad", "Mecánica General")
    telefono = request.form.get("telefono", "")

    agregar_mecanico(session["taller_id"], nombre, especialidad, telefono)
    return redirect("/#dash")

@mecanicos_bp.route("/asignar_mecanico_ot", methods=["POST"])
def asignar_mecanico_ot_web():
    if "taller_id" not in session:
        return jsonify({"success": False}), 401

    data = request.get_json()
    orden_id = int(data["orden_id"])
    mecanico_id = int(data["mecanico_id"]) if data.get("mecanico_id") else None

    asignar_mecanico_a_ot(orden_id, session["taller_id"], mecanico_id)
    return jsonify({"success": True})