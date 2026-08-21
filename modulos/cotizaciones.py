import secrets
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from modulos.conexion import obtener_conexion, obtener_placeholder
import io

def calcular_dias_habiles(fecha_inicio, fecha_fin):
    dias_habiles = 0
    actual = fecha_inicio
    while actual.date() < fecha_fin.date():
        if actual.weekday() < 5:
            dias_habiles += 1
        actual += timedelta(days=1)
    return dias_habiles

def buscar_vehiculo_o_cliente_por_patente(taller_id, patente):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        SELECT v.marca, v.modelo, c.nombre, c.telefono
        FROM vehiculos v
        JOIN clientes c ON v.cliente_id = c.id
        WHERE c.taller_id = {p} AND UPPER(v.patente_vin) = UPPER({p})
        ORDER BY v.id DESC LIMIT 1
    """, (taller_id, patente.strip()))

    resultado = cursor.fetchone()
    conexion.close()
    if resultado:
        return {
            "encontrado": True,
            "marca": resultado[0] or "",
            "modelo": resultado[1] or "",
            "cliente": resultado[2] or "",
            "telefono": resultado[3] or ""
        }
    return {"encontrado": False}

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

    ahora = datetime.now()
    resultado = []

    for f in filas:
        f_list = list(f)
        fecha_obj = f_list[10] if isinstance(f_list[10], datetime) else datetime.now()
        f_list[10] = fecha_obj.strftime("%d/%m/%Y")

        dias_habiles = calcular_dias_habiles(fecha_obj, ahora)
        f_list.append(dias_habiles)

        if f_list[8] == 'pendiente' and dias_habiles > 15:
            f_list[8] = 'vencida'

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

def cambiar_estado_cotizacion(cot_id, taller_id, nuevo_estado):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        UPDATE cotizaciones
        SET estado = {p}
        WHERE id = {p} AND taller_id = {p}
    """, (nuevo_estado, cot_id, taller_id))

    conexion.commit()
    conexion.close()
    return True

def revalidar_cotizacion_vencida(cot_id, taller_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        UPDATE cotizaciones
        SET estado = 'pendiente', fecha_creacion = CURRENT_TIMESTAMP
        WHERE id = {p} AND taller_id = {p}
    """, (cot_id, taller_id))

    conexion.commit()
    conexion.close()
    return True

def convertir_cotizacion_a_ot(cot_id, taller_id):
    """Transforma el Presupuesto aprobado en una Orden de Trabajo (OT) activa."""
    from modulos.ordenes import crear_orden_recepcion_guiada
    
    cot, items = obtener_detalle_cotizacion(cot_id)
    if not cot:
        return False

    fotos_vacias = {'frontal':'', 'trasera':'', 'costado_izq':'', 'costado_der':'', 'tablero':''}
    crear_orden_recepcion_guiada(
        taller_id, cot[3], cot[6], cot[7], 0, "1/2", 
        "Convertido desde Cotización #" + str(cot[0]), fotos_vacias, 4, 
        cot[1], cot[2], cot[4], cot[5]
    )

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()
    cursor.execute(f"UPDATE cotizaciones SET estado = 'aprobada' WHERE id = {p}", (cot_id,))
    conexion.commit()
    conexion.close()
    return True

def generar_pdf_cotizacion(cot_id):
    cot, items = obtener_detalle_cotizacion(cot_id)
    if not cot:
        return None

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Encabezado
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, f"PRESUPUESTO / COTIZACIÓN #{cot[0]}")
    c.setFont("Helvetica", 10)
    c.drawString(50, 735, f"Taller: {cot[10]}")
    c.drawString(50, 720, f"Cliente: {cot[1]} ({cot[2]})")
    c.drawString(50, 705, f"Vehículo: {cot[3]} - {cot[4]} {cot[5]}")
    
    # Tabla de Ítems
    y = 660
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Descripción / Repuesto")
    c.drawString(350, y, "Cant.")
    c.drawString(450, y, "Total ($)")
    c.line(50, y-5, 550, y-5)

    y -= 20
    c.setFont("Helvetica", 9)
    for item in items:
        cant = item[2] or 1
        precio = item[3] or 0.0
        subtotal = cant * precio
        c.drawString(50, y, str(item[1] or "Servicio / Repuesto"))
        c.drawString(350, y, str(cant))
        c.drawString(450, y, f"${subtotal:,.0f}")
        y -= 18

    # Total
    c.setFont("Helvetica-Bold", 12)
    c.drawString(350, y-20, f"TOTAL: ${cot[7]:,.0f}")

    c.save()
    buffer.seek(0)
    return buffer