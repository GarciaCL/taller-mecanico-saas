import sqlite3
import csv
import zipfile
import os
from datetime import datetime

DB_PATH = "base_datos/taller.db"

def validar_login(usuario, password):
    """Valida el usuario y contraseña, y retorna los datos del usuario y su taller."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT u.id, u.taller_id, u.usuario, u.rol, t.nombre_taller, t.logo_url, t.color_primario, 
               t.modulo_inventario, t.modulo_citas_web, t.modulo_correos
        FROM usuarios u
        JOIN talleres t ON u.taller_id = t.id
        WHERE u.usuario = ? AND u.password = ?
    """, (usuario, password))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

def agregar_cliente_y_vehiculo(taller_id, nombre, rut, telefono, correo, patente, marca, modelo, anio, km):
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO clientes (taller_id, nombre, rut, telefono, correo)
        VALUES (?, ?, ?, ?, ?)
    """, (taller_id, nombre, rut, telefono, correo))
    cliente_id = cursor.lastrowid
    
    cursor.execute("""
        INSERT INTO vehiculos (cliente_id, patente_vin, marca, modelo, anio, kilometraje)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (cliente_id, patente, marca, modelo, anio, km))
    conexion.commit()
    conexion.close()

def agregar_repuesto(taller_id, codigo, nombre, stock, costo, venta, mano_obra, compatibilidades):
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO inventario (taller_id, codigo, nombre, stock, precio_costo, precio_venta, mano_obra, modelos_compatibles)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (taller_id, codigo, nombre, stock, costo, venta, mano_obra, compatibilidades))
    conexion.commit()
    conexion.close()

def buscar_vehiculo_por_patente(patente):
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT v.id, v.patente_vin, v.marca, v.modelo, c.nombre, c.rut
        FROM vehiculos v
        JOIN clientes c ON v.cliente_id = c.id
        WHERE v.patente_vin = ?
    """, (patente,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

def crear_ficha_trabajo(vehiculo_id, observaciones, costo_total):
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO fichas_trabajo (vehiculo_id, observaciones_mecanico, costo_total)
        VALUES (?, ?, ?)
    """, (vehiculo_id, observaciones, costo_total))
    conexion.commit()
    conexion.close()

def crear_copia_seguridad_zip():
    carpeta_respaldos = "respaldos"
    if not os.path.exists(carpeta_respaldos):
        os.makedirs(carpeta_respaldos)
    fecha_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_zip = os.path.join(carpeta_respaldos, f"respaldo_taller_{fecha_str}.zip")
    with zipfile.ZipFile(nombre_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(DB_PATH, arcname="taller.db")
    return nombre_zip