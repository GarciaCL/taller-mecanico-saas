from flask import Blueprint, render_template, request, redirect, session
from modulos.conexion import obtener_conexion, obtener_placeholder
from datetime import datetime, timedelta

superadmin_bp = Blueprint('superadmin', __name__)

def verificar_superadmin():
    # 1. Verificar si existe sesión iniciada
    if "usuario" not in session and "taller_id" not in session:
        return False
    # 2. Verificar que el rol o indicador de la sesión sea superadmin
    if not session.get("es_superadmin") and session.get("rol") != "superadmin":
        return False
    return True

@superadmin_bp.route("/superadmin")
def vista_superadmin():
    if not verificar_superadmin():
        return redirect("/login")

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        # 1. Asegurar que las columnas en talleres existan
        try:
            cursor.execute("ALTER TABLE talleres ADD COLUMN IF NOT EXISTS estado VARCHAR(20) DEFAULT 'activo'")
            cursor.execute("ALTER TABLE talleres ADD COLUMN IF NOT EXISTS fecha_vencimiento TIMESTAMP")
            conexion.commit()
        except Exception as e_alter:
            conexion.rollback()
            print(f"[SUPERADMIN] Nota en alter table: {e_alter}")

        # 2. Consultar talleres usando unicamente u.usuario (sin u.email)
        cursor.execute("""
            SELECT t.id, 
                   t.nombre_taller, 
                   t.telefono_taller, 
                   t.email_taller, 
                   COALESCE(u.usuario, 'Admin') as usuario,
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
                nombre = str(t[1]) if t[1] else "Sin Nombre"
                telefono = str(t[2]) if t[2] else "N/I"
                email = str(t[3]) if t[3] else "N/I"
                usuario = str(t[4]) if t[4] else "Admin"
                estado = str(t[5]) if t[5] else "activo"
                fecha_venc = t[6]

                if isinstance(fecha_venc, str):
                    try:
                        fecha_venc = datetime.strptime(fecha_venc[:19], "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        fecha_venc = None

                if not fecha_venc:
                    fecha_venc = ahora + timedelta(days=14)
                    try:
                        p = obtener_placeholder()
                        cursor.execute(f"UPDATE talleres SET fecha_vencimiento = {p} WHERE id = {p}", (fecha_venc, tid))
                        conexion.commit()
                    except Exception as e_upd:
                        conexion.rollback()

                try:
                    fecha_fmt = fecha_venc.strftime("%d/%m/%Y")
                except Exception:
                    fecha_fmt = "14 días asignados"

                try:
                    dias_restantes = (fecha_venc - ahora).days
                except Exception:
                    dias_restantes = 14

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
                    "fecha_vencimiento": fecha_fmt,
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

    except Exception as err_global:
        print(f"[SUPERADMIN CRITICAL ERROR]: {err_global}")
        return f"""
            <div style="font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; text-align: center; min-height: 100vh;">
                <h2>⚠️ Ocurrió un error interno en el Panel SuperAdmin</h2>
                <p style="color: #94a3b8;">Detalle técnico: <code>{err_global}</code></p>
                <a href="/" style="background: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; font-weight: bold;">Volver al Inicio</a>
            </div>
        """, 500

@superadmin_bp.route("/superadmin/extender_dias", methods=["POST"])
def extender_dias_taller():
    if not verificar_superadmin():
        return redirect("/login")

    try:
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
                fecha_actual = datetime.strptime(fecha_actual[:19], "%Y-%m-%d %H:%M:%S")
            except Exception:
                fecha_actual = ahora

        if fecha_actual < ahora:
            nueva_fecha = ahora + timedelta(days=dias_a_sumar)
        else:
            nueva_fecha = fecha_actual + timedelta(days=dias_a_sumar)

        cursor.execute(f"UPDATE talleres SET fecha_vencimiento = {p}, estado = 'activo' WHERE id = {p}", (nueva_fecha, taller_id))
        conexion.commit()
        conexion.close()
    except Exception as e:
        print(f"Error en extender_dias: {e}")

    return redirect("/superadmin")


@superadmin_bp.route("/superadmin/cambiar_estado", methods=["POST"])
def cambiar_estado_taller():
    if not verificar_superadmin():
        return redirect("/login")

    try:
        taller_id = request.form["taller_id"]
        nuevo_estado = request.form["nuevo_estado"]

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        p = obtener_placeholder()

        cursor.execute(f"UPDATE talleres SET estado = {p} WHERE id = {p}", (nuevo_estado, taller_id))
        conexion.commit()
        conexion.close()
    except Exception as e:
        print(f"Error en cambiar_estado: {e}")

    return redirect("/superadmin")


@superadmin_bp.route("/superadmin/ingresar_como_taller", methods=["POST"])
def ingresar_como_taller():
    if not verificar_superadmin():
        return redirect("/login")

    try:
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
    except Exception as e:
        print(f"Error en ingresar_como_taller: {e}")

    return redirect("/")

@superadmin_bp.route("/superadmin/actualizar_credenciales", methods=["POST"])
def actualizar_credenciales_taller():
    if not verificar_superadmin():
        return redirect("/login")

    taller_id = request.form["taller_id"]
    nuevo_correo = request.form["nuevo_correo"].strip()
    nueva_password = request.form.get("nueva_password", "").strip()

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    try:
        # 1. Actualizar email del taller
        cursor.execute(f"UPDATE talleres SET email_taller = {p} WHERE id = {p}", (nuevo_correo, taller_id))
        
        # 2. Actualizar correo del usuario administrador asociado al taller
        cursor.execute(f"UPDATE usuarios SET usuario = {p} WHERE taller_id = {p} AND rol = 'admin'", (nuevo_correo, taller_id))

        # 3. Si se ingresó una nueva contraseña, actualizarla
        if nueva_password:
            cursor.execute(f"UPDATE usuarios SET password = {p} WHERE taller_id = {p} AND rol = 'admin'", (nueva_password, taller_id))

        conexion.commit()
    except Exception as e:
        conexion.rollback()
        print(f"Error actualizando credenciales: {e}")
    finally:
        conexion.close()

    return redirect("/superadmin")


@superadmin_bp.route("/superadmin/eliminar_taller", methods=["POST"])
def eliminar_taller_definitivo():
    if not verificar_superadmin():
        return redirect("/login")

    taller_id = request.form["taller_id"]

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    try:
        # 1. Limpieza de tablas dependientes directas e indirectas
        consultas_limpieza = [
            f"DELETE FROM ordenes_repuestos WHERE orden_id IN (SELECT id FROM ordenes_trabajo WHERE taller_id = {p})",
            f"DELETE FROM detalles_cotizacion WHERE cotizacion_id IN (SELECT id FROM cotizaciones WHERE taller_id = {p})",
            f"DELETE FROM historial_vehiculos WHERE taller_id = {p}",
            f"DELETE FROM ordenes_trabajo WHERE taller_id = {p}",
            f"DELETE FROM cotizaciones WHERE taller_id = {p}",
            f"DELETE FROM inventario WHERE taller_id = {p}",
            f"DELETE FROM vehiculos WHERE taller_id = {p}",
            f"DELETE FROM clientes WHERE taller_id = {p}",
            f"DELETE FROM mecanicos WHERE taller_id = {p}",
            f"DELETE FROM usuarios WHERE taller_id = {p}"
        ]

        for query in consultas_limpieza:
            try:
                cursor.execute(query, (taller_id,))
            except Exception as e_sub:
                conexion.rollback()
                print(f"Aviso limpiando registros previos ({query}): {e_sub}")

        # 2. Borrar la entidad principal del taller
        cursor.execute(f"DELETE FROM talleres WHERE id = {p}", (taller_id,))
        conexion.commit()

    except Exception as e:
        conexion.rollback()
        print(f"Error borrando taller {taller_id}: {e}")
        # Intento de borrado forzado en cascada si la base de datos lo soporta
        try:
            cursor.execute(f"DELETE FROM talleres WHERE id = {p} CASCADE", (taller_id,))
            conexion.commit()
        except Exception as e_cascade:
            conexion.rollback()
            print(f"Error borrado en cascada: {e_cascade}")
    finally:
        conexion.close()

    return redirect("/superadmin")