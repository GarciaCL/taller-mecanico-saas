from flask import Blueprint, jsonify, session
from modulos.metricas import obtener_metricas_estimadas

metricas_bp = Blueprint('metricas', __name__)

@metricas_bp.route("/api/metricas_estimadas")
def obtener_metricas_web():
    if "taller_id" not in session:
        return jsonify(None), 401

    data = obtener_metricas_estimadas(session["taller_id"])
    return jsonify(data)