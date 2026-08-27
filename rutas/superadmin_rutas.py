from flask import Blueprint, render_template, request, redirect, session
from modulos.conexion import obtener_conexion, obtener_placeholder
from datetime import datetime, timedelta

superadmin_bp = Blueprint('superadmin', __name__)

def verificar_superadmin():
    if "taller_id" not in session:
        return False
    return True

@superadmin_bp.route("/superadmin")
def vista_superadmin():
    if not verificar_superadmin():
        return redirect("/login")

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # 1. Asegurar que existan las columnas de estado y vencimiento
    try:
        cursor.execute("ALTER TABLE talleres ADD COLUMN IF NOT EXISTS estado VARCHAR(20) DEFAULT 'activo'")
        cursor.execute("ALTER TABLE talleres ADD COLUMN IF NOT EXISTS fecha_vencimiento TIMESTAMP")
        conexion.commit()
    except Exception:
        conexion.rollback()

    # 2. Consultar talleres evitando duplicados de usuarios
    cursor.execute("""
        SELECT DISTINCT ON (t.id) 
               t.id, 
               t.nombre_taller, 
               t.telefono_taller, 
               t.email_taller, 
               COALESCE(u.usuario, u.email, 'Admin') as usuario,
               COALESCE(t.estado, 'activo') as estado,
               t.fecha_vencimiento
        FROM talleres t
        LEFT JOIN usuarios u ON t.id = u.taller_id
        ORDER BY t.id DESC
    """)
    talleres_raw = cursor.fetchall()

    talleres = []
    total_activos = 0
    total_suspendidos = 0
    ahora = datetime.now()

    for t in talleres_raw:
        tid = t[0]
        nombre = t[1] if t[1] else "Sin Nombre"
        telefono = t[2] if t[2] else "N/I"
        email = t[3] if t[3] else "N/I"
        usuario = t[4] if t[4] else "Admin"
        estado = t[5] if t[5] else "activo"
        fecha_venc = t[6]

        # Si no tiene fecha asignada aún, asignarle 14 días por defecto desde ahora
        if not fecha_venc:
            fecha_venc = ahora + timedelta(days=14)
            p = obtener_placeholder()
            cursor.execute(f"UPDATE talleres SET fecha_vencimiento = {p} WHERE id = {p}", (fecha_venc, tid))
            conexion.commit()

        # Calcular días restantes
        dias_restantes = (fecha_venc - ahora).days

        if dias_restantes < 0 and estado == 'activo':
            estado = 'vencido'

        if estado in ['suspendido', 'vencido']:
            total_suspendidos += 1
        else:
            total_activos += 1

        talleres.append({
            "id": tid,
            "nombre": nombre,
            "telefono": telefono,
            "email": email,
            "usuario": usuario,
            "estado": estado,
            "fecha_vencimiento": fecha_venc.strftime("%d/%m/%Y"),
            "dias_restantes": dias_restantes
        })

    mrr_estimado = total_activos * 29900
    conexion.close()

    metricas_saas = {
        "mrr": mrr_estimado,
        "total_talleres": len(talleres),
        "talleres_activos": total_activos,
        "talleres_suspendidos": total_suspendidos
    }

    return render_template("superadmin.html", talleres=talleres, metricas_saas=metricas_saas)


@superadmin_bp.route("/superadmin/extender_dias", methods=["POST"])
def extender_dias_taller():
    if not verificar_superadmin():
        return redirect("/login")

    taller_id = request.form["taller_id"]
    dias_a_sumar = int(request.form.get("dias", 14))

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    # Consultar fecha actual de vencimiento
    cursor.execute(f"SELECT fecha_vencimiento FROM talleres WHERE id = {p}", (taller_id,))
    res = cursor.fetchone()
    
    ahora = datetime.now()
    fecha_actual = res[0] if res and res[0] else ahora

    # Si ya estaba vencido, sumamos 14 días a partir de HOY. Si estaba activo, le sumamos 14 días a su fecha actual.
    if fecha_actual < ahora:
        nueva_fecha = ahora + timedelta(days=dias_a_sumar)
    else:
        nueva_fecha = fecha_actual + timedelta(days=dias_a_sumar)

    cursor.execute(f"UPDATE talleres SET fecha_vencimiento = {p}, estado = 'activo' WHERE id = {p}", (nueva_fecha, taller_id))
    conexion.commit()
    conexion.close()

    return redirect("/superadmin")


@superadmin_bp.route("/superadmin/cambiar_estado", methods=["POST"])
def cambiar_estado_taller():
    if not verificar_superadmin():
        return redirect("/login")

    taller_id = request.form["taller_id"]
    nuevo_estado = request.form["nuevo_estado"]

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"UPDATE talleres SET estado = {p} WHERE id = {p}", (nuevo_estado, taller_id))
    conexion.commit()
    conexion.close()

    return redirect("/superadmin")


@superadmin_bp.route("/superadmin/ingresar_como_taller", methods=["POST"])
def ingresar_como_taller():
    if not verificar_superadmin():
        return redirect("/login")

    taller_id = request.form["taller_id"]

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"SELECT id, nombre_taller, logo_url, color_primario FROM talleres WHERE id = {p}", (taller_id,))
    taller = cursor.fetchone()
    conexion.close()

    if taller:
        session["taller_id"] = taller[0]
        session["nombre_taller"] = taller[1]
        session["logo_url"] = taller[2] if len(taller) > 2 and taller[2] else "/static/logo_defecto.png"
        session["color_primario"] = taller[3] if len(taller) > 3 and taller[3] else "#3b82f6"

    return redirect("/")