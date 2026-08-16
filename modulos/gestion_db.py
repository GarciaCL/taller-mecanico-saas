import os
import zipfile
from datetime import datetime

# Detectar la URL de la base de datos (PostgreSQL en Render o SQLite local)
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def obtener_conexion():
    """Devuelve una conexión a PostgreSQL si existe DATABASE_URL, de lo contrario a SQLite."""
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    else:
        import sqlite3
        return sqlite3.connect("base_datos/taller.db")

def obtener_placeholder():
    """Devuelve %s para PostgreSQL y ? para SQLite."""
    return "%s" if DATABASE_URL else "?"

# --- AUTENTICACIÓN ---

def validar_login(usuario, password):
    """Valida las credenciales de un usuario y retorna sus datos y los de su taller."""
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

# --- CONSULTAS Y LISTADOS ---

def obtener_clientes_y_vehiculos(taller_id):
    """Obtiene todos los clientes y sus vehículos para el taller especificado."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()
    
    cursor.execute(f"""
        SELECT c.id, c.nombre, c.rut, COALESCE(c.telefono, ''), COALESCE(c.correo, ''),
               COALESCE(v.patente_vin, 'Sin Vehículo'), COALESCE(v.marca, ''), 
               COALESCE(v.modelo, ''), COALESCE(v.anio, 0), COALESCE(v.kilometraje, 0)
        FROM clientes c
        LEFT JOIN vehiculos v ON c.id = v.cliente_id
        WHERE c.taller_id = {p}
        ORDER BY c.id DESC
    """, (taller_id,))
    
    filas = cursor.fetchall()
    conexion.close()
    return filas

def obtener_inventario(taller_id):
    """Obtiene todos los repuestos registrados con sus categorías y compatibilidad."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()
    
    cursor.execute(f"""
        SELECT id, codigo, COALESCE(categoria, 'General'), nombre, COALESCE(stock, 0), 
               COALESCE(precio_costo, 0), COALESCE(precio_venta, 0), COALESCE(mano_obra, 0), 
               COALESCE(modelos_compatibles, 'Universal')
        FROM inventario
        WHERE taller_id = {p}
        ORDER BY id DESC
    """, (taller_id,))
    
    filas = cursor.fetchall()
    conexion.close()
    return filas

# --- REGISTRAR DATOS ---

def agregar_cliente_y_vehiculo(taller_id, nombre, rut, telefono, correo, patente, marca, modelo, anio, km):
    """Registra un cliente y su vehículo asociado."""
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
    """Agrega un nuevo repuesto al inventario del taller."""
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
    """Busca un vehículo y su cliente dueño por la patente."""
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
    """Crea una nueva ficha de trabajo asociada a un vehículo."""
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
    """Genera un archivo .zip de respaldo."""
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

def obtener_historial_por_patente(taller_id, patente):
    """Consulta todas las mantenciones realizadas a una patente específica dentro del taller."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()
    
    cursor.execute(f"""
        SELECT f.id, f.fecha, COALESCE(f.observaciones_mecanico, ''), COALESCE(f.costo_total, 0),
               v.patente_vin, COALESCE(v.marca, ''), COALESCE(v.modelo, ''), COALESCE(v.anio, 0), COALESCE(v.kilometraje, 0),
               c.nombre, c.rut, COALESCE(c.telefono, '')
        FROM fichas_trabajo f
        JOIN vehiculos v ON f.vehiculo_id = v.id
        JOIN clientes c ON v.cliente_id = c.id
        WHERE c.taller_id = {p} AND UPPER(v.patente_vin) = UPPER({p})
        ORDER BY f.fecha DESC
    """, (taller_id, patente.strip()))
    
    filas = cursor.fetchall()
    conexion.close()
    return filas