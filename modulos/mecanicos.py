from modulos.conexion import obtener_conexion, obtener_placeholder

def obtener_lista_mecanicos(taller_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        SELECT m.id, m.nombre, COALESCE(m.especialidad, 'General'), COALESCE(m.telefono, ''),
               COUNT(CASE WHEN ot.estado != 'finalizado' THEN 1 END) AS ots_activas,
               COUNT(CASE WHEN ot.estado = 'finalizado' THEN 1 END) AS ots_cerradas,
               COALESCE(SUM(CASE WHEN ot.estado = 'finalizado' THEN ot.costo_estimado ELSE 0 END), 0) AS total_generado
        FROM mecanicos m
        LEFT JOIN ordenes_trabajo ot ON ot.mecanico_id = m.id
        WHERE m.taller_id = {p} AND m.activo IS TRUE
        GROUP BY m.id, m.nombre, m.especialidad, m.telefono
        ORDER BY m.nombre ASC
    """, (taller_id,))

    filas = cursor.fetchall()
    conexion.close()
    return filas

def agregar_mecanico(taller_id, nombre, especialidad="Mecánica General", telefono=""):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        INSERT INTO mecanicos (taller_id, nombre, especialidad, telefono)
        VALUES ({p}, {p}, {p}, {p})
    """, (taller_id, nombre.strip(), especialidad.strip(), telefono.strip()))

    conexion.commit()
    conexion.close()
    return True

def asignar_mecanico_a_ot(orden_id, taller_id, mecanico_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        UPDATE ordenes_trabajo
        SET mecanico_id = {p}
        WHERE id = {p} AND taller_id = {p}
    """, (mecanico_id if mecanico_id else None, orden_id, taller_id))

    conexion.commit()
    conexion.close()
    return True