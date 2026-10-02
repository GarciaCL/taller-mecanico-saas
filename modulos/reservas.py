import psycopg2
import psycopg2.extras
import os

def obtener_conexion():
    """Obtiene la conexión a la base de datos PostgreSQL usando la variable de entorno."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL no está configurada en el entorno.")
    return psycopg2.connect(url)

def obtener_reservas(taller_id):
    """Obtiene todas las reservas asociadas a un taller para mostrarlas en FullCalendar."""
    conn = obtener_conexion()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    query = """
        SELECT id, cliente_nombre, cliente_telefono, patente, vehiculo_modelo, 
               servicio_requerido, fecha_inicio, fecha_fin, estado
        FROM reservas
        WHERE taller_id = %s
        ORDER BY fecha_inicio ASC;
    """
    cursor.execute(query, (taller_id,))
    reservas = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return reservas

def crear_reserva(taller_id, datos):
    """Inserta una nueva reserva de cupo en la base de datos."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    query = """
        INSERT INTO reservas (taller_id, cliente_nombre, cliente_rut, cliente_telefono, 
                             cliente_email, patente, vehiculo_modelo, servicio_requerido, 
                             fecha_inicio, fecha_fin, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """
    cursor.execute(query, (
        taller_id,
        datos.get('cliente_nombre'),
        datos.get('cliente_rut', ''),
        datos.get('cliente_telefono', ''),
        datos.get('cliente_email', ''),
        datos.get('patente'),
        datos.get('vehiculo_modelo', ''),
        datos.get('servicio_requerido', ''),
        datos.get('fecha_inicio'),
        datos.get('fecha_fin'),
        datos.get('estado', 'pendiente')
    ))
    
    reserva_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return reserva_id

def actualizar_estado_reserva(reserva_id, taller_id, nuevo_estado):
    """Actualiza el estado de una reserva (ej: 'confirmada', 'cancelada', 'convertida_ot')."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    query = """
        UPDATE reservas
        SET estado = %s
        WHERE id = %s AND taller_id = %s;
    """
    cursor.execute(query, (nuevo_estado, reserva_id, taller_id))
    conn.commit()
    cursor.close()
    conn.close()