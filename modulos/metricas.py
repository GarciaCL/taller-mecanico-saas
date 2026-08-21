from datetime import datetime
from modulos.conexion import obtener_conexion, obtener_placeholder

def obtener_metricas_estimadas(taller_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    # 1. Total estimado OTs activas (en taller)
    cursor.execute(f"""
        SELECT COALESCE(SUM(costo_estimado), 0), COUNT(id)
        FROM ordenes_trabajo
        WHERE taller_id = {p} AND estado != 'finalizado'
    """, (taller_id,))
    total_activas, cant_activas = cursor.fetchone()

    # 2. Total facturado/cerrado (OTs finalizadas)
    cursor.execute(f"""
        SELECT COALESCE(SUM(costo_estimado), 0), COUNT(id)
        FROM ordenes_trabajo
        WHERE taller_id = {p} AND estado = 'finalizado'
    """, (taller_id,))
    total_cerradas, cant_cerradas = cursor.fetchone()

    # 3. Desglose estimado de Repuestos en OTs vs Mano de obra
    cursor.execute(f"""
        SELECT COALESCE(SUM(nr.cantidad * nr.precio_unidad), 0)
        FROM ordenes_repuestos nr
        JOIN ordenes_trabajo ot ON nr.orden_id = ot.id
        WHERE ot.taller_id = {p}
    """, (taller_id,))
    total_repuestos = cursor.fetchone()[0] or 0.0

    # 4. Conteo por estado de OTs
    cursor.execute(f"""
        SELECT estado, COUNT(id)
        FROM ordenes_trabajo
        WHERE taller_id = {p}
        GROUP BY estado
    """, (taller_id,))
    estados_raw = dict(cursor.fetchall())
    conexion.close()

    total_general = total_activas + total_cerradas
    total_ots = cant_activas + cant_cerradas
    ticket_promedio = (total_general / total_ots) if total_ots > 0 else 0.0
    mano_obra_estimada = max(0.0, total_general - total_repuestos)

    return {
        "total_proyectado": total_general,
        "total_cerrado": total_cerradas,
        "total_en_taller": total_activas,
        "ticket_promedio": ticket_promedio,
        "total_repuestos": total_repuestos,
        "mano_obra_estimada": mano_obra_estimada,
        "cant_activas": cant_activas,
        "cant_cerradas": cant_cerradas,
        "estados": {
            "recepcion": estados_raw.get('recepcion', 0),
            "diagnostico": estados_raw.get('diagnostico', 0),
            "reparacion": estados_raw.get('reparacion', 0),
            "entrega": estados_raw.get('entrega', 0),
            "finalizado": estados_raw.get('finalizado', 0)
        }
    }