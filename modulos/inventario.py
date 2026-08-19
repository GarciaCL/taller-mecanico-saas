from modulos.conexion import obtener_conexion, obtener_placeholder

def obtener_inventario(taller_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()
    cursor.execute(f"""
        SELECT id, codigo, COALESCE(categoria, 'General'), nombre, COALESCE(stock, 0), 
               0, 0, 0, COALESCE(modelos_compatibles, 'Universal')
        FROM inventario WHERE taller_id = {p} ORDER BY id DESC
    """, (taller_id,))
    filas = cursor.fetchall()
    conexion.close()
    return filas

def agregar_repuesto(taller_id, codigo, categoria, nombre, stock, costo, venta, mano_obra, compatabilidades):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()
    
    categoria_clean = categoria.strip() if categoria else 'General'
    compat_clean = compatabilidades.strip() if compatabilidades else 'Universal'

    cursor.execute(f"""
        INSERT INTO inventario (taller_id, codigo, categoria, nombre, stock, precio_costo, precio_venta, mano_obra, modelos_compatibles)
        VALUES ({p}, {p}, {p}, {p}, {p}, 0, 0, 0, {p})
    """, (taller_id, codigo.strip(), categoria_clean, nombre.strip(), stock, compat_clean))
    
    conexion.commit()
    conexion.close()
    return True

def agregar_repuestos_masivo(taller_id, lista_repuestos):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    for item in lista_repuestos:
        codigo = str(item.get('codigo', '')).strip()
        nombre = str(item.get('nombre', '')).strip()
        categoria = str(item.get('categoria', 'General')).strip() or 'General'
        stock = int(item.get('stock', 0)) if str(item.get('stock', '')).isdigit() else 0
        compat = str(item.get('compatabilidades', 'Universal')).strip() or 'Universal'

        if codigo and nombre:
            cursor.execute(f"""
                INSERT INTO inventario (taller_id, codigo, categoria, nombre, stock, precio_costo, precio_venta, mano_obra, modelos_compatibles)
                VALUES ({p}, {p}, {p}, {p}, {p}, 0, 0, 0, {p})
            """, (taller_id, codigo, categoria, nombre, stock, compat))

    conexion.commit()
    conexion.close()
    return True

def eliminar_repuesto(taller_id, repuesto_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"DELETE FROM inventario WHERE id = {p} AND taller_id = {p}", (repuesto_id, taller_id))
    conexion.commit()
    conexion.close()
    return True

def eliminar_repuestos_masivo(taller_id, lista_ids):
    if not lista_ids:
        return False
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    placeholders = ", ".join([p] * len(lista_ids))
    params = [taller_id] + [int(x) for x in lista_ids]

    cursor.execute(f"DELETE FROM inventario WHERE taller_id = {p} AND id IN ({placeholders})", params)
    conexion.commit()
    conexion.close()
    return True

def agregar_repuesto_a_orden(orden_id, inventario_id, cantidad=1, precio_unidad=0.0):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        INSERT INTO ordenes_repuestos (orden_id, inventario_id, cantidad, precio_unidad)
        VALUES ({p}, {p}, {p}, {p})
    """, (orden_id, inventario_id, cantidad, precio_unidad))

    conexion.commit()
    conexion.close()
    return True

def eliminar_repuesto_orden(item_orden_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"DELETE FROM ordenes_repuestos WHERE id = {p}", (item_orden_id,))
    conexion.commit()
    conexion.close()
    return True

def actualizar_repuesto_orden(item_orden_id, cantidad, precio_unidad):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        UPDATE ordenes_repuestos
        SET cantidad = {p}, precio_unidad = {p}
        WHERE id = {p}
    """, (cantidad, precio_unidad, item_orden_id))

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