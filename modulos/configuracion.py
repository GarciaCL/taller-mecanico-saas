from modulos.conexion import obtener_conexion, obtener_placeholder

def obtener_ajustes_taller(taller_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        SELECT id, nombre_taller, COALESCE(logo_url, '/static/logo_defecto.png'), COALESCE(color_primario, '#3b82f6'),
               COALESCE(rut_taller, ''), COALESCE(direccion_taller, ''), COALESCE(telefono_taller, ''), COALESCE(email_taller, ''),
               COALESCE(msg_whatsapp_listo, ''), COALESCE(msg_whatsapp_cotizacion, ''),
               COALESCE(mecanico_puede_finalizar, FALSE), COALESCE(mecanico_puede_rechazar, FALSE)
        FROM talleres
        WHERE id = {p}
    """, (taller_id,))

    taller = cursor.fetchone()
    conexion.close()
    return taller

def actualizar_ajustes_taller(taller_id, datos):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        UPDATE talleres
        SET nombre_taller = {p}, logo_url = {p}, color_primario = {p},
            rut_taller = {p}, direccion_taller = {p}, telefono_taller = {p}, email_taller = {p},
            msg_whatsapp_listo = {p}, msg_whatsapp_cotizacion = {p},
            mecanico_puede_finalizar = {p}, mecanico_puede_rechazar = {p}
        WHERE id = {p}
    """, (
        datos["nombre_taller"], datos["logo_url"], datos["color_primario"],
        datos["rut_taller"], datos["direccion_taller"], datos["telefono_taller"], datos["email_taller"],
        datos["msg_whatsapp_listo"], datos["msg_whatsapp_cotizacion"],
        datos.get("mecanico_puede_finalizar", False), datos.get("mecanico_puede_rechazar", False),
        taller_id
    ))

    conexion.commit()
    conexion.close()
    return True