from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from modulos.reservas import obtener_reservas, crear_reserva, actualizar_estado_reserva

reservas_bp = Blueprint('reservas', __name__)

@reservas_bp.route('/reservas')
def vista_reservas():
    """Ruta principal para cargar el panel con el calendario del taller."""
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    
    return render_template('reservas.html')

@reservas_bp.route('/api/reservas', methods=['GET'])
def api_obtener_reservas():
    """Endpoint que entrega las reservas en formato JSON compatible con FullCalendar."""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    taller_id = session.get('taller_id')
    reservas = obtener_reservas(taller_id)
    
    # Formatear datos para que FullCalendar los interprete como eventos
    eventos = []
    for r in reservas:
        color = '#ffc107' # Amarillo para pendiente
        if r['estado'] == 'confirmada':
            color = '#28a745' # Verde
        elif r['estado'] == 'cancelada':
            color = '#dc3545' # Rojo
        elif r['estado'] == 'convertida_ot':
            color = '#17a2b8' # Azul

        eventos.append({
            'id': r['id'],
            'title': f"{r['patente']} - {r['cliente_nombre']}",
            'start': r['fecha_inicio'].isoformat(),
            'end': r['fecha_fin'].isoformat(),
            'color': color,
            'extendedProps': {
                'telefono': r['cliente_telefono'],
                'modelo': r['vehiculo_modelo'],
                'servicio': r['servicio_requerido'],
                'estado': r['estado']
            }
        })
        
    return jsonify(eventos)

@reservas_bp.route('/api/reservas/crear', methods=['POST'])
def api_crear_reserva():
    """Endpoint para agendar una nueva reserva."""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    taller_id = session.get('taller_id')
    datos = request.json
    
    if not datos.get('patente') or not datos.get('cliente_nombre') or not datos.get('fecha_inicio'):
        return jsonify({'error': 'Faltan campos obligatorios'}), 400
        
    reserva_id = crear_reserva(taller_id, datos)
    return jsonify({'success': True, 'reserva_id': reserva_id})

@reservas_bp.route('/api/reservas/estado/<int:reserva_id>', methods=['POST'])
def api_cambiar_estado(reserva_id):
    """Endpoint para cambiar el estado de la reserva."""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
        
    taller_id = session.get('taller_id')
    datos = request.json
    nuevo_estado = datos.get('estado')
    
    actualizar_estado_reserva(reserva_id, taller_id, nuevo_estado)
    return jsonify({'success': True})