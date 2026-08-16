import os
import zipfile
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

# --- RECEPCIÓN GUIADA Y ÓRDENES KANBAN ---

def crear_orden_recepcion_guiada(taller_id, patente, sintomas, costo_estimado, km_ingreso, combustible, detalles, fotos):
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

    cursor.execute(f"""
        INSERT INTO ordenes_trabajo 
        (taller_id, vehiculo_id, estado, sintomas_cliente, costo_estimado, km_ingreso, nivel_combustible, detalles_carrocería,
         foto_frontal, foto_trasera, foto_costado_izq, foto_costado_der, foto_tablero)
        VALUES ({p}, {p}, 'recepcion', {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
    """, (
        taller_id, vehiculo_id, sintomas, costo_estimado, km_ingreso, combustible, detalles,
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

    cursor.execute(f"""
        SELECT ot.id, ot.estado, ot.sintomas_cliente, COALESCE(ot.costo_estimado, 0),
               v.patente_vin, COALESCE(v.marca, ''), COALESCE(v.modelo, ''),
               c.nombre, COALESCE(c.telefono, ''),
               COALESCE(ot.km_ingreso, 0), COALESCE(ot.nivel_combustible, '1/2'),
               COALESCE(ot.foto_frontal, ''), COALESCE(ot.foto_tablero, ''),
               COALESCE(ot.detalles_carrocería, '')
        FROM ordenes_trabajo ot
        JOIN vehiculos v ON ot.vehiculo_id = v.id
        JOIN clientes c ON v.cliente_id = c.id
        WHERE ot.taller_id = {p}
        ORDER BY ot.id DESC
    """, (taller_id,))

    filas = cursor.fetchall()
    conexion.close()
    return filas

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

def obtener_detalle_orden_publico(orden_id):
    """Obtiene el detalle completo de una orden para la vista pública del cliente."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        SELECT ot.id, ot.estado, COALESCE(ot.sintomas_cliente, ''), COALESCE(ot.costo_estimado, 0),
               COALESCE(ot.km_ingreso, 0), COALESCE(ot.nivel_combustible, '1/2'), COALESCE(ot.detalles_carrocería, ''),
               COALESCE(ot.foto_frontal, ''), COALESCE(ot.foto_trasera, ''), COALESCE(ot.foto_costado_izq, ''),
               COALESCE(ot.foto_costado_der, ''), COALESCE(ot.foto_tablero, ''), ot.fecha_creacion,
               v.patente_vin, COALESCE(v.marca, ''), COALESCE(v.modelo, ''), COALESCE(v.anio, 0),
               c.nombre, COALESCE(c.telefono, ''),
               t.nombre_taller, COALESCE(t.logo_url, '/static/logo_defecto.png'), COALESCE(t.color_primario, '#3b82f6')
        FROM ordenes_trabajo ot
        JOIN vehiculos v ON ot.vehiculo_id = v.id
        JOIN clientes c ON v.cliente_id = c.id
        JOIN talleres t ON ot.taller_id = t.id
        WHERE ot.id = {p}
    """, (orden_id,))

    resultado = cursor.fetchone()
    conexion.close()
    return resultado

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