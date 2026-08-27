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

    # 1. Asegurar que la tabla talleres tenga las columnas necesarias
    try:
        cursor.execute("ALTER TABLE talleres ADD COLUMN IF NOT EXISTS estado VARCHAR(20) DEFAULT 'activo'")
        cursor.execute("ALTER TABLE talleres ADD COLUMN IF NOT EXISTS fecha_vencimiento TIMESTAMP")
        conexion.commit()
    except Exception as e:
        conexion.rollback()
        print(f"Error alter table: {e}")

    # 2. Consultar todos los talleres
    cursor.execute("""
        SELECT t.id, t.nombre_taller, t.telefono_taller, t.email_taller, 
               COALESCE(u.usuario, u.email, 'Admin') as usuario,
               COALESCE(t.estado, 'activo') as estado,
               t.fecha_vencimiento
        FROM talleres t
        LEFT JOIN usuarios u ON t.id = u.taller_id
        ORDER BY t.id DESC
    """)
    talleres_raw = cursor.fetchall()

    talleres_dict = {}
    total_activos = 0
    total_suspendidos = 0
    ahora = datetime.now()

    for t in talleres_raw:
        tid = t[0]
        if tid not in talleres_dict:
            nombre = t[1] if len(t) > 1 and t[1] else "Sin Nombre"
            telefono = t[2] if len(t) > 2 and t[2] else "N/I"
            email = t[3] if len(t) > 3 and t[3] else "N/I"
            usuario = t[4] if len(t) > 4 and t[4] else "Admin"
            estado = t[5] if len(t) > 5 and t[5] else "activo"
            fecha_venc = t[6] if len(t) > 6 else None

            # Asignar 14 días si no tiene fecha de vencimiento
            if not fecha_venc:
                fecha_venc = ahora + timedelta(days=14)
                try:
                    p = obtener_placeholder()
                    cursor.execute(f"UPDATE talleres SET fecha_vencimiento = {p} WHERE id = {p}", (fecha_venc, tid))
                    conexion.commit()
                except Exception as err_upd:
                    conexion.rollback()
                    print(f"Error actualizando fecha_vencimiento: {err_upd}")

            # Convertir a datetime si viene en formato texto
            if isinstance(fecha_venc, str):
                try:
                    fecha_venc = datetime.strptime(fecha_venc, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    fecha_venc = ahora + timedelta(days=14)

            dias_restantes = (fecha_venc - ahora).days if fecha_venc else 14

            if dias_restantes < 0 and estado == 'activo':
                estado = 'vencido'

            if estado in ['suspendido', 'vencido']:
                total_suspendidos += 1
            else:
                total_activos += 1

            talleres_dict[tid] = {
                "id": tid,
                "nombre": nombre,
                "telefono": telefono,
                "email": email,
                "usuario": usuario,
                "estado": estado,
                "fecha_vencimiento": fecha_venc.strftime("%d/%m/%Y") if fecha_venc else "Sin Fecha",
                "dias_restantes": dias_restantes
            }

    talleres = list(talleres_dict.values())
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

    cursor.execute(f"SELECT fecha_vencimiento FROM talleres WHERE id = {p}", (taller_id,))
    res = cursor.fetchone()
    
    ahora = datetime.now()
    fecha_actual = res[0] if res and res[0] else ahora

    if isinstance(fecha_actual, str):
        try:
            fecha_actual = datetime.strptime(fecha_actual, "%Y-%m-%d %H:%M:%S")
        except Exception:
            fecha_actual = ahora

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