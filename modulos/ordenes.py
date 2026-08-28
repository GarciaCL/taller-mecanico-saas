import secrets
from datetime import datetime
from modulos.conexion import obtener_conexion, obtener_placeholder

def crear_orden_recepcion_guiada(taller_id, patente, sintomas, costo_estimado, km_ingreso, combustible, detalles, fotos, tiempo_horas=4, nombre_cliente="Cliente General", telefono_cliente="", marca="Marca", modelo="Modelo"):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    patente_limpia = patente.strip().upper()

    cursor.execute(f"SELECT id FROM vehiculos WHERE UPPER(patente_vin) = {p}", (patente_limpia,))
    vehiculo = cursor.fetchone()

    if not vehiculo:
        cursor.execute(f"SELECT id FROM clientes WHERE taller_id = {p} AND (telefono = {p} OR nombre = {p})", (taller_id, telefono_cliente, nombre_cliente))
        cliente = cursor.fetchone()
        
        if not cliente:
            cursor.execute(f"""
                INSERT INTO clientes (taller_id, nombre, rut, telefono)
                VALUES ({p}, {p}, 'N/A', {p})
            """, (taller_id, nombre_cliente, telefono_cliente))
            conexion.commit()
            cursor.execute(f"SELECT id FROM clientes WHERE taller_id = {p} ORDER BY id DESC LIMIT 1", (taller_id,))
            cliente = cursor.fetchone()

        cliente_id = cliente[0]

        cursor.execute(f"""
            INSERT INTO vehiculos (cliente_id, patente_vin, marca, modelo, kilometraje)
            VALUES ({p}, {p}, {p}, {p}, {p})
        """, (cliente_id, patente_limpia, marca, modelo, km_ingreso))
        conexion.commit()

        cursor.execute(f"SELECT id FROM vehiculos WHERE UPPER(patente_vin) = {p}", (patente_limpia,))
        vehiculo = cursor.fetchone()

    vehiculo_id = vehiculo[0]
    cursor.execute(f"UPDATE vehiculos SET kilometraje = {p} WHERE id = {p}", (km_ingreso, vehiculo_id))

    hash_unico = secrets.token_hex(3).upper()
    token_orden = f"{patente_limpia}-{hash_unico}"

    cursor.execute(f"""
        INSERT INTO ordenes_trabajo 
        (taller_id, vehiculo_id, token, estado, sintomas_cliente, costo_estimado, km_ingreso, nivel_combustible, detalles_carrocería, tiempo_estimado_horas,
         foto_frontal, foto_trasera, foto_costado_izq, foto_costado_der, foto_tablero)
        VALUES ({p}, {p}, {p}, 'recepcion', {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
    """, (
        taller_id, vehiculo_id, token_orden, sintomas, costo_estimado, km_ingreso, combustible, detalles, tiempo_horas,
        fotos.get('frontal', ''), fotos.get('trasera', ''), fotos.get('costado_izq', ''),
        fotos.get('costado_der', ''), fotos.get('tablero', '')
    ))

    conexion.commit()
    conexion.close()
    return True

def obtener_ordenes_kanban(taller_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    # Asegurar que la columna 'archivada' exista en la tabla ordenes_trabajo
    try:
        cursor.execute("ALTER TABLE ordenes_trabajo ADD COLUMN IF NOT EXISTS archivada BOOLEAN DEFAULT FALSE")
        conexion.commit()
    except Exception:
        conexion.rollback()

    cursor.execute(f"""
        SELECT ot.id, ot.estado, COALESCE(ot.sintomas_cliente, ''), COALESCE(ot.costo_estimado, 0),
               v.patente_vin, COALESCE(v.marca, ''), COALESCE(v.modelo, ''),
               c.nombre, COALESCE(c.telefono, ''),
               COALESCE(ot.km_ingreso, 0), COALESCE(ot.nivel_combustible, '1/2'),
               COALESCE(ot.token, v.patente_vin),
               ot.fecha_creacion, COALESCE(ot.tiempo_estimado_horas, 4),
               ot.mecanico_id, COALESCE(m.nombre, 'Sin Asignar')
        FROM ordenes_trabajo ot
        JOIN vehiculos v ON ot.vehiculo_id = v.id
        JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN mecanicos m ON ot.mecanico_id = m.id
        WHERE ot.taller_id = {p} 
          AND ot.estado != 'finalizado'
          AND (ot.archivada IS FALSE OR ot.archivada IS NULL)
        ORDER BY ot.id DESC
    """, (taller_id,))

    filas = cursor.fetchall()
    conexion.close()

    resultado = []
    for f in filas:
        f_list = list(f)
        if isinstance(f_list[12], datetime):
            f_list[12] = f_list[12].isoformat()
        else:
            f_list[12] = str(f_list[12])
        resultado.append(f_list)

    return resultado

def actualizar_estado_orden(orden_id, taller_id, nuevo_estado):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        UPDATE ordenes_trabajo
        SET estado = {p}
        WHERE id = {p} AND taller_id = {p}
    """, (nuevo_estado, orden_id, taller_id))

    conexion.commit()
    conexion.close()

def finalizar_orden_trabajo(orden_id, taller_id):
    return actualizar_estado_orden(orden_id, taller_id, 'finalizado')

def obtener_detalle_orden_por_token(token_o_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        SELECT ot.id, ot.estado, COALESCE(ot.sintomas_cliente, ''), COALESCE(ot.costo_estimado, 0),
               COALESCE(ot.km_ingreso, 0), COALESCE(ot.nivel_combustible, '1/2'), COALESCE(ot.detalles_carrocería, ''),
               COALESCE(ot.foto_frontal, ''), COALESCE(ot.foto_trasera, ''), COALESCE(ot.foto_costado_izq, ''),
               COALESCE(ot.foto_costado_der, ''), COALESCE(ot.foto_tablero, ''),
               v.patente_vin, COALESCE(v.marca, ''), COALESCE(v.modelo, ''), COALESCE(v.anio, 0),
               c.nombre, COALESCE(c.telefono, ''),
               t.nombre_taller, COALESCE(t.logo_url, '/static/logo_defecto.png'), COALESCE(t.color_primario, '#3b82f6'),
               COALESCE(ot.token, ''), ot.fecha_creacion, COALESCE(m.nombre, 'Sin Asignar')
        FROM ordenes_trabajo ot
        JOIN vehiculos v ON ot.vehiculo_id = v.id
        JOIN clientes c ON v.cliente_id = c.id
        JOIN talleres t ON ot.taller_id = t.id
        LEFT JOIN mecanicos m ON ot.mecanico_id = m.id
        WHERE ot.token = {p} OR CAST(ot.id AS TEXT) = {p}
    """, (str(token_o_id), str(token_o_id)))

    resultado = cursor.fetchone()
    if not resultado:
        conexion.close()
        return None, []

    cursor.execute(f"""
        SELECT i.nombre, nr.cantidad, nr.precio_unidad
        FROM ordenes_repuestos nr
        JOIN inventario i ON nr.inventario_id = i.id
        WHERE nr.orden_id = {p}
    """, (resultado[0],))
    repuestos = cursor.fetchall()

    conexion.close()
    return resultado, repuestos

def actualizar_orden_trabajo(taller_id, orden_id, km, combustible, tiempo_horas, sintomas, costo):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        UPDATE ordenes_trabajo
        SET km_ingreso = {p},
            nivel_combustible = {p},
            tiempo_estimado_horas = {p},
            sintomas_cliente = {p},
            costo_estimado = {p}
        WHERE id = {p} AND taller_id = {p}
    """, (km, combustible, tiempo_horas, sintomas, costo, orden_id, taller_id))

    conexion.commit()
    conexion.close()
    return True

def obtener_historial_vehiculo(taller_id, patente):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        SELECT ot.id, ot.estado, COALESCE(ot.sintomas_cliente, ''), COALESCE(ot.costo_estimado, 0),
               COALESCE(ot.km_ingreso, 0), COALESCE(ot.nivel_combustible, '1/2'), ot.token, ot.fecha_creacion,
               v.patente_vin, COALESCE(v.marca, ''), COALESCE(v.modelo, ''), COALESCE(v.anio, 0),
               c.nombre, COALESCE(c.telefono, ''), COALESCE(ot.archivada, FALSE) as archivada
        FROM ordenes_trabajo ot
        JOIN vehiculos v ON ot.vehiculo_id = v.id
        JOIN clientes c ON v.cliente_id = c.id
        WHERE ot.taller_id = {p} AND UPPER(v.patente_vin) = UPPER({p})
        ORDER BY ot.id DESC
    """, (taller_id, patente.strip()))

    filas = cursor.fetchall()
    conexion.close()
    return filas