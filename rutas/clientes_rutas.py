from flask import Blueprint, request, jsonify, redirect, session
from modulos.clientes import actualizar_cliente, obtener_detalle_cliente, agregar_vehiculo_a_cliente

clientes_bp = Blueprint('clientes', __name__)

@clientes_bp.route("/actualizar_cliente", methods=["POST"])
def actualizar_cliente_web():
    if "taller_id" not in session:
        return redirect("/login")

    cliente_id = int(request.form["cliente_id"])
    nombre = request.form["nombre"]
    rut = request.form.get("rut", "N/A")
    telefono = request.form.get("telefono", "")
    email = request.form.get("email", "")

    actualizar_cliente(session["taller_id"], cliente_id, nombre, rut, telefono, email)
    return redirect("/")

@clientes_bp.route("/obtener_cliente/<int:cliente_id>")
def obtener_cliente_web(cliente_id):
    if "taller_id" not in session:
        return jsonify(None), 401

    detalle = obtener_detalle_cliente(session["taller_id"], cliente_id)
    return jsonify(detalle)

@clientes_bp.route("/agregar_vehiculo_cliente", methods=["POST"])
def agregar_vehiculo_cliente_web():
    if "taller_id" not in session:
        return redirect("/login")

    cliente_id = int(request.form["cliente_id"])
    patente = request.form["patente"]
    marca = request.form.get("marca", "")
    modelo = request.form.get("modelo", "")
    anio = int(request.form.get("anio", 2020)) if request.form.get("anio") else 2020
    km = int(request.form.get("km", 0)) if request.form.get("km") else 0

    agregar_vehiculo_a_cliente(cliente_id, patente, marca, modelo, anio, km)
    return redirect("/")