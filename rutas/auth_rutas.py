from flask import Blueprint, render_template, request, redirect, session
from modulos.auth import validar_login
from modulos.conexion import obtener_conexion, obtener_placeholder
from modulos.notificaciones import enviar_bienvenida_usuario, enviar_aviso_registro_admin, enviar_notificacion_pago
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

# Definir correo/identificador del SuperAdministrador
CORREO_SUPERADMIN = "admin@mitalleronline.cl"

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"].strip().lower()
        password = request.form["password"].strip()
        
        # 1. Intentar validar primero contra la BD general de usuarios
        user = validar_login(usuario, password)
        
        if user:
            session["usuario_id"] = user[0]
            session["taller_id"] = user[1]
            session["usuario"] = user[2]
            session["rol"] = user[3]
            session["nombre_taller"] = user[4]
            session["logo_url"] = user[5]
            session["color_primario"] = user[6]

            # Si el usuario validado en BD tiene rol 'superadmin' o es el correo maestro
            if user[3] == "superadmin" or usuario == CORREO_SUPERADMIN:
                session["es_superadmin"] = True
                return redirect("/superadmin")

            # Usuario normal de taller
            session["es_superadmin"] = False
            return redirect("/")
            
        # 2. Respaldo: Si el superadmin no está registrado en la tabla 'usuarios' pero coincide con el correo maestro
        elif usuario == CORREO_SUPERADMIN:
            # Aquí puedes colocar una clave maestra o validarla según tus variables de entorno (.env)
            session["usuario_id"] = 0
            session["taller_id"] = 0
            session["usuario"] = usuario
            session["rol"] = "superadmin"
            session["nombre_taller"] = "Panel SuperAdmin"
            session["es_superadmin"] = True
            return redirect("/superadmin")

        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")
            
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@auth_bp.route("/actualizar_perfil_taller", methods=["POST"])
def actualizar_perfil_taller_web():
    if "taller_id" not in session:
        return redirect("/login")

    nombre = request.form["nombre_taller"]
    color = request.form.get("color_primario", "#3b82f6")

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    cursor.execute(f"""
        UPDATE talleres
        SET nombre_taller = {p}, color_primario = {p}
        WHERE id = {p}
    """, (nombre, color, session["taller_id"]))

    conexion.commit()
    conexion.close()

    session["nombre_taller"] = nombre
    session["color_primario"] = color

    return redirect("/#ajustes")

# --- RUTAS DEL FLUJO COMERCIAL Y REGISTRO ---

@auth_bp.route("/registro")
def vista_registro():
    return render_template("registro.html")

@auth_bp.route("/procesar_registro", methods=["POST"])
def procesar_registro_web():
    plan = request.form.get("plan", "mensual")
    precio = 287000 if plan == "anual" else 29900

    session["registro_temp"] = {
        "nombre_taller": request.form["nombre_taller"].strip(),
        "nombre_admin": request.form["nombre_admin"].strip(),
        "email": request.form["email"].strip().lower(),
        "telefono": request.form["telefono"].strip(),
        "password": request.form["password"].strip(),
        "plan": plan,
        "plan_nombre": "Plan Anual (Ahorras 20%)" if plan == "anual" else "Plan Mensual",
        "precio": precio,
        "frecuencia": "Anual" if plan == "anual" else "Mensual"
    }

    return redirect("/pago")

@auth_bp.route("/pago")
def vista_pago():
    datos = session.get("registro_temp")
    if not datos:
        return redirect("/registro")
    return render_template("pago.html", datos_registro=datos)

@auth_bp.route("/confirmar_pago_registro", methods=["POST"])
def confirmar_pago_registro_web():
    datos = session.get("registro_temp")
    if not datos:
        return redirect("/registro")

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    try:
        # 1. Validar si el correo ya existe
        cursor.execute(f"SELECT id FROM usuarios WHERE usuario = {p}", (datos["email"],))
        if cursor.fetchone():
            conexion.close()
            return render_template("pago.html", datos_registro=datos, error="El correo ya se encuentra registrado. Por favor usa otro o inicia sesión.")

        # 2. Asegurar que la tabla talleres tenga las columnas 'estado' y 'fecha_vencimiento'
        try:
            cursor.execute("ALTER TABLE talleres ADD COLUMN IF NOT EXISTS estado VARCHAR(20) DEFAULT 'activo'")
            cursor.execute("ALTER TABLE talleres ADD COLUMN IF NOT EXISTS fecha_vencimiento TIMESTAMP")
            conexion.commit()
        except Exception as err_alter:
            conexion.rollback()
            print(f"Nota en alter table: {err_alter}")

        # 3. Calcular fecha de vencimiento (14 días de prueba o 365 si es anual)
        dias_gratis = 365 if datos.get("plan") == "anual" else 14
        fecha_vencimiento = datetime.now() + timedelta(days=dias_gratis)

        # 4. Insertar el nuevo taller
        cursor.execute(f"""
            INSERT INTO talleres (nombre_taller, telefono_taller, email_taller, estado, fecha_vencimiento)
            VALUES ({p}, {p}, {p}, 'activo', {p})
        """, (datos["nombre_taller"], datos["telefono"], datos["email"], fecha_vencimiento))

        cursor.execute(f"SELECT id FROM talleres WHERE email_taller = {p} ORDER BY id DESC LIMIT 1", (datos["email"],))
        taller_id = cursor.fetchone()[0]

        # 5. Crear el usuario administrador
        cursor.execute(f"""
            INSERT INTO usuarios (taller_id, usuario, password, rol)
            VALUES ({p}, {p}, {p}, 'admin')
        """, (taller_id, datos["email"], datos["password"]))

        conexion.commit()

        # 6. Notificaciones automáticas por correo
        try:
            # A) Bienvenida al usuario
            enviar_bienvenida_usuario(datos["email"], datos["nombre_admin"])
            
            # B) Notificación de Pago / Suscripción
            enviar_notificacion_pago(datos["email"], datos["precio"], datos["plan_nombre"])

            # C) Alerta al SuperAdmin
            enviar_aviso_registro_admin(datos["nombre_taller"], datos["email"])
        except Exception as err_mail:
            print(f"[ALERTA NOTIFICACIÓN REGISTRO] No se enviaron correos: {err_mail}")

        # 7. Iniciar sesión automáticamente
        session["usuario_id"] = None
        session["taller_id"] = taller_id
        session["usuario"] = datos["email"]
        session["usuario_nombre"] = datos["nombre_admin"]
        session["rol"] = "admin"
        session["nombre_taller"] = datos["nombre_taller"]
        session["logo_url"] = "/static/logo_defecto.png"
        session["color_primario"] = "#3b82f6"
        session["es_superadmin"] = False

        session.pop("registro_temp", None)
        conexion.close()
        return redirect("/#ajustes")

    except Exception as e:
        conexion.rollback()
        conexion.close()
        print(f"Error en confirmar_pago_registro: {e}")
        return render_template("pago.html", datos_registro=datos, error=f"Ocurrió un detalle al activar la cuenta: {e}")