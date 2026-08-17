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

    cursor.execute(f"""
        SELECT ot.id, ot.estado, COALESCE(ot.sintomas_cliente, ''), COALESCE(ot.costo_estimado, 0),
               v.patente_vin, COALESCE(v.marca, ''), COALESCE(v.modelo, ''),
               c.nombre, COALESCE(c.telefono, ''),
               COALESCE(ot.km_ingreso, 0), COALESCE(ot.nivel_combustible, '1/2'),
               COALESCE(ot.token, v.patente_vin),
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

def obtener_historial_vehiculo(taller_id, patente):
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

# --- INVENTARIO & GESTIÓN DE STOCK ---

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

def agregar_repuesto(taller_id, codigo, categoria, nombre, stock, costo, venta, mano_obra, compatibilidades):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()
    cursor.execute(f"""
        INSERT INTO inventario (taller_id, codigo, categoria, nombre, stock, precio_costo, precio_venta, mano_obra, modelos_compatibles)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
    """, (taller_id, codigo, categoria, nombre, stock, costo, venta, mano_obra, compatibilidades))
    conexion.commit()
    conexion.close()

def agregar_repuestos_masivo(taller_id, lista_repuestos):
    """Inserta en lote una lista de repuestos enviada por carga masiva Excel/CSV."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    for item in lista_repuestos:
        codigo = str(item.get('codigo', '')).strip()
        nombre = str(item.get('nombre', '')).strip()
        categoria = str(item.get('categoria', 'General')).strip() or 'General'
        stock = int(item.get('stock', 0)) if str(item.get('stock', '')).isdigit() else 0
        costo = float(item.get('costo', 0)) if str(item.get('costo', '')).replace('.', '', 1).isdigit() else 0.0
        venta = float(item.get('venta', 0)) if str(item.get('venta', '')).replace('.', '', 1).isdigit() else 0.0
        compat = str(item.get('compatibilidades', 'Universal')).strip() or 'Universal'

        if codigo and nombre:
            cursor.execute(f"""
                INSERT INTO inventario (taller_id, codigo, categoria, nombre, stock, precio_costo, precio_venta, mano_obra, modelos_compatibles)
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, 0, {p})
            """, (taller_id, codigo, categoria, nombre, stock, costo, venta, compat))

    conexion.commit()
    conexion.close()
    return True

def agregar_repuesto_a_orden(orden_id, inventario_id, cantidad=1):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"SELECT precio_venta FROM inventario WHERE id = {p}", (inventario_id,))
    prod = cursor.fetchone()
    precio = prod[0] if prod else 0.0

    cursor.execute(f"""
        INSERT INTO ordenes_repuestos (orden_id, inventario_id, cantidad, precio_unidad)
        VALUES ({p}, {p}, {p}, {p})
    """, (orden_id, inventario_id, cantidad, precio))

    conexion.commit()
    conexion.close()
    return True

def obtener_repuestos_orden(orden_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    try:
        cursor.execute(f"""
            SELECT nr.id, i.nombre, nr.cantidad, nr.precio_unidad, nr.descontado
            FROM ordenes_repuestos nr
            JOIN inventario i ON nr.inventario_id = i.id
            WHERE nr.orden_id = {p}
        """, (orden_id,))
        items = cursor.fetchall()
    except Exception:
        items = []
    finally:
        conexion.close()
    return items

def descontar_stock_orden(orden_id, taller_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    try:
        cursor.execute(f"""
            SELECT id, inventario_id, cantidad 
            FROM ordenes_repuestos 
            WHERE orden_id = {p} AND (descontado IS FALSE OR descontado IS NULL OR descontado = 0)
        """, (orden_id,))
        items = cursor.fetchall()

        for item_id, inv_id, cant in items:
            cursor.execute(f"""
                UPDATE inventario 
                SET stock = GREATEST(0, stock - {p}) 
                WHERE id = {p} AND taller_id = {p}
            """, (cant, inv_id, taller_id))

            cursor.execute(f"""
                UPDATE ordenes_repuestos 
                SET descontado = TRUE 
                WHERE id = {p}
            """, (item_id,))

        conexion.commit()
    except Exception:
        conexion.rollback()
    finally:
        conexion.close()
    return True

# --- MARCAS Y MODELOS DINÁMICOS ---

def obtener_marcas_y_modelos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT DISTINCT COALESCE(marca, ''), COALESCE(modelo, '') FROM vehiculos WHERE marca IS NOT NULL AND marca != ''")
    filas = cursor.fetchall()
    conexion.close()

    marcas_dict = {}
    for m, mod in filas:
        m = m.strip().title()
        mod = mod.strip().title()
        if m not in marcas_dict:
            marcas_dict[m] = []
        if mod and mod not in marcas_dict[m]:
            marcas_dict[m].append(mod)

    return marcas_dict