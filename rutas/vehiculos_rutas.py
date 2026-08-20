from flask import Blueprint, jsonify, session, request
from modulos.vehiculos_crm import obtener_lista_vehiculos_crm

vehiculos_bp = Blueprint('vehiculos', __name__)

@vehiculos_bp.route("/obtener_vehiculos_crm")
def obtener_vehiculos_crm_web():
    if "taller_id" not in session:
        return jsonify([]), 401

    orden = request.args.get("orden", "visita")
    lista = obtener_lista_vehiculos_crm(session["taller_id"], orden)
    return jsonify(lista)