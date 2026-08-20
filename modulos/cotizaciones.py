import secrets
from datetime import datetime, timedelta
from modulos.conexion import obtener_conexion, obtener_placeholder

def calcular_dias_habiles(fecha_inicio, fecha_fin):
    """Calcula la cantidad de días hábiles transcurridos (excluyendo Sábados y Domingos)."""
    dias_habiles = 0
    actual = fecha_inicio
    while actual.date() < fecha_fin.date():
        if actual.weekday() < 5:  # 0 es Lunes, 4 es Viernes
            dias_habiles += 1
        actual += timedelta(days=1)
    return dias_habiles

def buscar_vehiculo_o_cliente_por_patente(taller_id, patente):
    """Devuelve los datos del propietario y auto si la patente ya existe."""
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

        # Cálculo de días hábiles
        dias_habiles = calcular_dias_habiles(fecha_obj, ahora)
        f_list.append(dias_habiles)

        # Evaluar si venció por 15 días hábiles
        if f_list[8] == 'pendiente' and dias_habiles > 15:
            f_list[8] = 'vencida'

        resultado.append(f_list)

    return resultado

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
    """Reinicia la fecha de creación a la actual para refrescar la validez por otros 15 días hábiles."""
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