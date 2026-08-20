from datetime import datetime
from modulos.conexion import obtener_conexion, obtener_placeholder
from modulos.vehiculos import CALENDARIO_RT_CHILE

def obtener_lista_vehiculos_crm(taller_id, orden_por="visita"):
    """
    Obtiene la lista completa de vehículos del taller con cálculo de alertas:
    - Revisión Técnica (según patente)
    - Próximo Cambio de Aceite (basado en el último KM registrado + 10.000)
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        SELECT v.id, v.patente_vin, COALESCE(v.marca, 'S/M'), COALESCE(v.modelo, 'S/M'),
               COALESCE(v.anio, 2020), COALESCE(v.kilometraje, 0),
               c.nombre AS cliente_nombre, COALESCE(c.telefono, '') AS cliente_telefono,
               COALESCE(c.email, '') AS cliente_email,
               MAX(ot.fecha_creacion) AS ultima_visita,
               COUNT(ot.id) AS total_visitas
        FROM vehiculos v
        JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN ordenes_trabajo ot ON ot.vehiculo_id = v.id
        WHERE c.taller_id = {p}
        GROUP BY v.id, v.patente_vin, v.marca, v.modelo, v.anio, v.kilometraje, c.nombre, c.telefono, c.email
        ORDER BY ultima_visita DESC NULLS LAST
    """, (taller_id,))

    filas = cursor.fetchall()
    conexion.close()

    vehiculos_procesados = []
    mes_actual = datetime.now().month

    for f in filas:
        v_id, patente, marca, modelo, anio, km, cliente, fono, email, u_visita, total_ots = f

        # 1. Alerta RT
        patente_clean = str(patente).strip().upper()
        digitos = [c for c in patente_clean if c.isdigit()]
        u_digito = digitos[-1] if digitos else '0'
        mes_rt = CALENDARIO_RT_CHILE.get(u_digito, 12)
        
        alerta_rt = "normal"
        if mes_rt == mes_actual:
            alerta_rt = "urgente"
        elif mes_rt == (mes_actual + 1) or (mes_actual == 12 and mes_rt == 1):
            alerta_rt = "proximo"

        # 2. Estimación Cambio de Aceite (Próximo servicio sugerido)
        km_proximo_aceite = km + 10000

        vehiculos_procesados.append({
            "id": v_id,
            "patente": patente_clean,
            "vehiculo": f"{marca} {modelo} ({anio})",
            "km_actual": km,
            "km_proximo_aceite": km_proximo_aceite,
            "cliente": cliente,
            "telefono": fono,
            "email": email,
            "ultima_visita": u_visita.strftime("%d/%m/%Y") if isinstance(u_visita, datetime) else "Sin Visitas",
            "total_ots": total_ots,
            "alerta_rt": alerta_rt,
            "mes_rt": mes_rt,
            "digito": u_digito
        })

    # Ordenamiento
    if orden_por == "alerta":
        prioridades = {"urgente": 0, "proximo": 1, "normal": 2}
        vehiculos_procesados.sort(key=lambda x: prioridades.get(x["alerta_rt"], 2))
    elif orden_por == "patente":
        vehiculos_procesados.sort(key=lambda x: x["patente"])

    return vehiculos_procesados