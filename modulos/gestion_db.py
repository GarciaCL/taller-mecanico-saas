import os
import secrets
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def obtener_conexion():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    else:
        import sqlite3
        return sqlite3.connect("base_datos/taller.db")

def obtener_placeholder():
    return "%s" if DATABASE_URL else "?"

def validar_login(usuario, password):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()
    query = f"""
        SELECT u.id, u.taller_id, u.usuario, u.rol, t.nombre_taller, t.logo_url, t.color_primario, 
               t.modulo_inventario, t.modulo_citas_web, t.modulo_correos
        FROM usuarios u
        JOIN talleres t ON u.taller_id = t.id
        WHERE u.usuario = {p} AND u.password = {p}
    """
    cursor.execute(query, (usuario, password))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

# --- RECEPCIÓN Y ÓRDENES KANBAN ---

def crear_orden_recepcion_guiada(taller_id, patente, sintomas, costo_estimado, km_ingreso, combustible, detalles, fotos, tiempo_horas=4):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"SELECT id FROM vehiculos WHERE UPPER(patente_vin) = UPPER({p})", (patente.strip(),))
    vehiculo = cursor.fetchone()
    
    if not vehiculo:
        conexion.close()
        return False

    vehiculo_id = vehiculo[0]
    cursor.execute(f"UPDATE vehiculos SET kilometraje = {p} WHERE id = {p}", (km_ingreso, vehiculo_id))

    # Generar Token Único: PATENTE-HASH (ej. PTBR56-A8F9X2)
    hash_unico = secrets.token_hex(3).upper()
    token_orden = f"{patente.strip().upper()}-{hash_unico}"

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

    # 1. Parche preventivo: asignar token a cualquier orden antigua que no lo tenga
    cursor.execute(f"""
        SELECT ot.id, v.patente_vin 
        FROM ordenes_trabajo ot 
        JOIN vehiculos v ON ot.vehiculo_id = v.id 
        WHERE ot.taller_id = {p} AND (ot.token IS NULL OR ot.token = '')
    """, (taller_id,))
    ordenes_sin_token = cursor.fetchall()
    
    for ot_id, patente in ordenes_sin_token:
        h = secrets.token_hex(3).upper()
        nuevo_token = f"{patente.strip().upper()}-{h}"
        cursor.execute(f"UPDATE ordenes_trabajo SET token = {p} WHERE id = {p}", (nuevo_token, ot_id))
    if ordenes_sin_token:
        conexion.commit()

    # 2. Consultar solo órdenes activas en el taller (excluyendo 'finalizado')
    cursor.execute(f"""
        SELECT ot.id, ot.estado, COALESCE(ot.sintomas_cliente, ''), COALESCE(ot.costo_estimado, 0),
               v.patente_vin, COALESCE(v.marca, ''), COALESCE(v.modelo, ''),
               c.nombre, COALESCE(c.telefono, ''),
               COALESCE(ot.km_ingreso, 0), COALESCE(ot.nivel_combustible, '1/2'),
               ot.token,
               ot.fecha_creacion, COALESCE(ot.tiempo_estimado_horas, 4)
        FROM ordenes_trabajo ot
        JOIN vehiculos v ON ot.vehiculo_id = v.id
        JOIN clientes c ON v.cliente_id = c.id
        WHERE ot.taller_id = {p} AND ot.estado != 'finalizado'
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
    """Marca una orden de trabajo como finalizada para archivarla del Kanban."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        UPDATE ordenes_trabajo
        SET estado = 'finalizado'
        WHERE id = {p} AND taller_id = {p}
    """, (orden_id, taller_id))

    conexion.commit()
    conexion.close()
    return True

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
               COALESCE(ot.token, '')
        FROM ordenes_trabajo ot
        JOIN vehiculos v ON ot.vehiculo_id = v.id
        JOIN clientes c ON v.cliente_id = c.id
        JOIN talleres t ON ot.taller_id = t.id
        WHERE ot.token = {p} OR CAST(ot.id AS TEXT) = {p}
    """, (str(token_o_id), str(token_o_id)))

    resultado = cursor.fetchone()
    conexion.close()
    return resultado

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

# --- INVENTARIO ---

def obtener_inventario(taller_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()
    cursor.execute(f"""
        SELECT id, codigo, COALESCE(categoria, 'General'), nombre, COALESCE(stock, 0), 
               COALESCE(precio_costo, 0), COALESCE(precio_venta, 0), COALESCE(mano_obra, 0), 
               COALESCE(modelos_compatibles, 'Universal')
        FROM inventario WHERE taller_id = {p} ORDER BY id DESC
    """, (taller_id,))
    filas = cursor.fetchall()
    conexion.close()
    return filas

def agregar_repuesto(taller_id, codigo, categoria, nombre, stock, costo, venta, mano_obra, compatabilidades):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()
    cursor.execute(f"""
        INSERT INTO inventario (taller_id, codigo, categoria, nombre, stock, precio_costo, precio_venta, mano_obra, modelos_compatibles)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
    """, (taller_id, codigo, categoria, nombre, stock, costo, venta, mano_obra, compatabilidades))
    conexion.commit()
    conexion.close()

    def obtener_historial_vehiculo(taller_id, patente):
        """Obtiene todas las órdenes de trabajo (activas e históricas/finalizadas) asociadas a una patente."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        SELECT ot.id, ot.estado, COALESCE(ot.sintomas_cliente, ''), COALESCE(ot.costo_estimado, 0),
               COALESCE(ot.km_ingreso, 0), COALESCE(ot.nivel_combustible, '1/2'), ot.token, ot.fecha_creacion,
               v.patente_vin, COALESCE(v.marca, ''), COALESCE(v.modelo, ''), COALESCE(v.anio, 0),
               c.nombre, COALESCE(c.telefono, '')
        FROM ordenes_trabajo ot
        JOIN vehiculos v ON ot.vehiculo_id = v.id
        JOIN clientes c ON v.cliente_id = c.id
        WHERE ot.taller_id = {p} AND UPPER(v.patente_vin) = UPPER({p})
        ORDER BY ot.id DESC
    """, (taller_id, patente.strip()))

    filas = cursor.fetchall()
    conexion.close()
    return filas