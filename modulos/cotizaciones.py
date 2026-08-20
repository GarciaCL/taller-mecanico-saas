import secrets
from datetime import datetime
from modulos.conexion import obtener_conexion, obtener_placeholder

def crear_cotizacion(taller_id, cliente_nombre, cliente_telefono, patente, marca, modelo, sintomas, total=0.0):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    patente_limpia = patente.strip().upper()
    hash_unico = secrets.token_hex(3).upper()
    token = f"COT-{patente_limpia}-{hash_unico}"

    cursor.execute(f"""
        INSERT INTO cotizaciones (taller_id, cliente_nombre, cliente_telefono, patente, marca, modelo, sintomas, total, token)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
    """, (taller_id, cliente_nombre.strip(), cliente_telefono.strip(), patente_limpia, marca.strip(), modelo.strip(), sintomas.strip(), total, token))

    conexion.commit()
    
    cursor.execute(f"SELECT id FROM cotizaciones WHERE token = {p}", (token,))
    cot_id = cursor.fetchone()[0]
    conexion.close()
    return cot_id, token

def obtener_lista_cotizaciones(taller_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        SELECT id, cliente_nombre, cliente_telefono, patente, marca, modelo, sintomas, total, estado, token, fecha_creacion
        FROM cotizaciones
        WHERE taller_id = {p}
        ORDER BY id DESC
    """, (taller_id,))

    filas = cursor.fetchall()
    conexion.close()

    resultado = []
    for f in filas:
        f_list = list(f)
        f_list[10] = f_list[10].strftime("%d/%m/%Y %H:%M") if isinstance(f_list[10], datetime) else str(f_list[10])
        resultado.append(f_list)

    return resultado

def obtener_detalle_cotizacion(cot_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        SELECT c.id, c.cliente_nombre, c.cliente_telefono, c.patente, c.marca, c.modelo, c.sintomas, c.total, c.estado, c.token,
               t.nombre_taller, COALESCE(t.logo_url, '/static/logo_defecto.png'), COALESCE(t.color_primario, '#3b82f6')
        FROM cotizaciones c
        JOIN talleres t ON c.taller_id = t.id
        WHERE c.id = {p} OR c.token = {p}
    """, (str(cot_id), str(cot_id)))

    cot = cursor.fetchone()
    if not cot:
        conexion.close()
        return None, []

    cursor.execute(f"""
        SELECT ci.id, COALESCE(i.nombre, ci.descripcion), ci.cantidad, ci.precio_unidad
        FROM cotizaciones_items ci
        LEFT JOIN inventario i ON ci.inventario_id = i.id
        WHERE ci.cotizacion_id = {p}
    """, (cot[0],))

    items = cursor.fetchall()
    conexion.close()
    return cot, items

def agregar_item_cotizacion(cot_id, inventario_id, descripcion, cantidad, precio_unidad):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        INSERT INTO cotizaciones_items (cotizacion_id, inventario_id, descripcion, cantidad, precio_unidad)
        VALUES ({p}, {p}, {p}, {p}, {p})
    """, (cot_id, inventario_id, descripcion, cantidad, precio_unidad))

    # Recalcular Total Cotización
    cursor.execute(f"SELECT SUM(cantidad * precio_unidad) FROM cotizaciones_items WHERE cotizacion_id = {p}", (cot_id,))
    nuevo_total = cursor.fetchone()[0] or 0.0

    cursor.execute(f"UPDATE cotizaciones SET total = {p} WHERE id = {p}", (nuevo_total, cot_id))

    conexion.commit()
    conexion.close()
    return nuevo_total

def convertir_cotizacion_a_ot(cot_id, taller_id):
    """Transforma el Presupuesto aprobado en una Orden de Trabajo (OT) activa."""
    from modulos.ordenes import crear_orden_recepcion_guiada
    
    cot, items = obtener_detalle_cotizacion(cot_id)
    if not cot:
        return False

    # Crear la OT en Kanban
    fotos_vacias = {'frontal':'', 'trasera':'', 'costado_izq':'', 'costado_der':'', 'tablero':''}
    crear_orden_recepcion_guiada(
        taller_id, cot[3], cot[6], cot[7], 0, "1/2", 
        "Convertido desde Cotización #" + str(cot[0]), fotos_vacias, 4, 
        cot[1], cot[2], cot[4], cot[5]
    )

    # Actualizar estado de Cotización
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()
    cursor.execute(f"UPDATE cotizaciones SET estado = 'aprobada' WHERE id = {p}", (cot_id,))
    conexion.commit()
    conexion.close()
    return True