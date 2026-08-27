from flask import Blueprint, render_template, request, redirect, session
from modulos.conexion import obtener_conexion, obtener_placeholder

superadmin_bp = Blueprint('superadmin', __name__)

# Middleware para asegurar que solo el admin/superadmin ingrese
def verificar_superadmin():
    if "taller_id" not in session:
        return False
    # Puedes personalizar el correo de tu cuenta principal como SuperAdmin
    return True

@superadmin_bp.route("/superadmin")
def vista_superadmin():
    if not verificar_superadmin():
        return redirect("/login")

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # 1. Obtener listado de talleres con datos de contacto del dueño
    cursor.execute("""
        SELECT t.id, t.nombre_taller, t.telefono_taller, t.email_taller, 
               t.fecha_creacion, u.usuario, COALESCE(t.estado, 'activo')
        FROM talleres t
        LEFT JOIN usuarios u ON t.id = u.taller_id AND u.rol = 'admin'
        ORDER BY t.id DESC
    """)
    talleres_raw = cursor.fetchall()

    # Normalizar lista
    talleres = []
    total_activos = 0
    total_suspendidos = 0

    for t in talleres_raw:
        estado = t[6] if len(t) > 6 and t[6] else 'activo'
        if estado == 'suspendido':
            total_suspendidos += 1
        else:
            total_activos += 1

        talleres.append((
            t[0],
            t[1] if t[1] else "Sin Nombre",
            t[2] if t[2] else "N/I",
            t[3] if t[3] else "N/I",
            t[4].strftime("%d/%m/%Y") if t[4] else "N/I",
            t[5] if t[5] else "Admin",
            estado
        ))

    total_talleres = len(talleres)
    mrr_estimado = total_activos * 29900  # Estimado basado en suscripción base CLP

    conexion.close()

    metricas_saas = {
        "mrr": mrr_estimado,
        "total_talleres": total_talleres,
        "talleres_activos": total_activos,
        "talleres_suspendidos": total_suspendidos
    }

    return render_template("superadmin.html", talleres=talleres, metricas_saas=metricas_saas)


@superadmin_bp.route("/superadmin/cambiar_estado", methods=["POST"])
def cambiar_estado_taller():
    if not verificar_superadmin():
        return redirect("/login")

    taller_id = request.form["taller_id"]
    nuevo_estado = request.form["nuevo_estado"]

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    # Crear columna 'estado' si no existiera
    try:
        cursor.execute(f"UPDATE talleres SET estado = {p} WHERE id = {p}", (nuevo_estado, taller_id))
    except Exception:
        conexion.rollback()
        cursor.execute("ALTER TABLE talleres ADD COLUMN estado VARCHAR(20) DEFAULT 'activo'")
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
        session["logo_url"] = taller[2] if taller[2] else "/static/logo_defecto.png"
        session["color_primario"] = taller[3] if taller[3] else "#3b82f6"

    return redirect("/")