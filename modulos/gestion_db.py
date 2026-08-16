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

# --- CONSULTAS PARA LISTADOS ---

def obtener_clientes_y_vehiculos(taller_id):
    """Obtiene el listado de clientes junto con sus vehículos asociados."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()
    cursor.execute(f"""
        SELECT c.id, c.nombre, c.rut, c.telefono, c.correo,
               v.patente_vin, v.marca, v.modelo, v.anio, v.kilometraje
        FROM clientes c
        LEFT JOIN vehiculos v ON c.id = v.cliente_id
        WHERE c.taller_id = {p}
        ORDER BY c.id DESC
    """, (taller_id,))
    filas = cursor.fetchall()
    conexion.close()
    return filas

def obtener_inventario(taller_id):
    """Obtiene el listado completo de repuestos."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()
    cursor.execute(f"""
        SELECT id, codigo, categoria, nombre, stock, precio_costo, precio_venta, mano_obra, modelos_compatibles
        FROM inventario
        WHERE taller_id = {p}
        ORDER BY id DESC
    """, (taller_id,))
    filas = cursor.fetchall()
    conexion.close()
    return filas

# --- REGISTROS ---

def agregar_cliente_y_vehiculo(taller_id, nombre, rut, telefono, correo, patente, marca, modelo, anio, km):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    if DATABASE_URL:
        cursor.execute(f"""
            INSERT INTO clientes (taller_id, nombre, rut, telefono, correo)
            VALUES ({p}, {p}, {p}, {p}, {p}) RETURNING id
        """, (taller_id, nombre, rut, telefono, correo))
        cliente_id = cursor.fetchone()[0]
    else:
        cursor.execute(f"""
            INSERT INTO clientes (taller_id, nombre, rut, telefono, correo)
            VALUES ({p}, {p}, {p}, {p}, {p})
        """, (taller_id, nombre, rut, telefono, correo))
        cliente_id = cursor.lastrowid

    cursor.execute(f"""
        INSERT INTO vehiculos (cliente_id, patente_vin, marca, modelo, anio, kilometraje)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p})
    """, (cliente_id, patente, marca, modelo, anio, km))

    conexion.commit()
    conexion.close()

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

def buscar_vehiculo_por_patente(patente):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()
    
    cursor.execute(f"""
        SELECT v.id, v.patente_vin, v.marca, v.modelo, c.nombre, c.rut
        FROM vehiculos v
        JOIN clientes c ON v.cliente_id = c.id
        WHERE v.patente_vin = {p}
    """, (patente,))
    
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

def crear_ficha_trabajo(vehiculo_id, observaciones, costo_total):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()
    
    cursor.execute(f"""
        INSERT INTO fichas_trabajo (vehiculo_id, observaciones_mecanico, costo_total)
        VALUES ({p}, {p}, {p})
    """, (vehiculo_id, observaciones, costo_total))
    
    conexion.commit()
    conexion.close()

def crear_copia_seguridad_zip():
    carpeta_respaldos = "respaldos"
    if not os.path.exists(carpeta_respaldos):
        os.makedirs(carpeta_respaldos)
    fecha_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_zip = os.path.join(carpeta_respaldos, f"respaldo_taller_{fecha_str}.zip")
    
    db_local = "base_datos/taller.db"
    if os.path.exists(db_local):
        with zipfile.ZipFile(nombre_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(db_local, arcname="taller.db")
    return nombre_zip