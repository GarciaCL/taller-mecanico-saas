from modulos.conexion import obtener_conexion, obtener_placeholder

def obtener_lista_clientes(taller_id):
    """Obtiene el listado de clientes con la cantidad de vehículos y OTs asociadas."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        SELECT c.id, c.nombre, COALESCE(c.rut, 'N/A'), COALESCE(c.telefono, ''),
               COUNT(DISTINCT v.id) AS total_vehiculos,
               COUNT(DISTINCT ot.id) AS total_ordenes,
               STRING_AGG(DISTINCT v.patente_vin, ', ') AS patentes
        FROM clientes c
        LEFT JOIN vehiculos v ON v.cliente_id = c.id
        LEFT JOIN ordenes_trabajo ot ON ot.vehiculo_id = v.id
        WHERE c.taller_id = {p}
        GROUP BY c.id, c.nombre, c.rut, c.telefono
        ORDER BY c.id DESC
    """, (taller_id,))

    filas = cursor.fetchall()
    conexion.close()
    return filas

def actualizar_cliente(taller_id, cliente_id, nombre, rut, telefono):
    """Actualiza la ficha de datos de un cliente."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        UPDATE clientes
        SET nombre = {p}, rut = {p}, telefono = {p}
        WHERE id = {p} AND taller_id = {p}
    """, (nombre.strip(), rut.strip(), telefono.strip(), cliente_id, taller_id))

    conexion.commit()
    conexion.close()
    return True

def obtener_detalle_cliente(taller_id, cliente_id):
    """Obtiene los datos del cliente y sus vehículos asociados."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"SELECT id, nombre, rut, telefono FROM clientes WHERE id = {p} AND taller_id = {p}", (cliente_id, taller_id))
    cliente = cursor.fetchone()

    if not cliente:
        conexion.close()
        return None

    cursor.execute(f"SELECT id, patente_vin, marca, modelo, kilometraje FROM vehiculos WHERE cliente_id = {p}", (cliente_id,))
    vehiculos = cursor.fetchall()

    conexion.close()
    return {"cliente": cliente, "vehiculos": vehiculos}