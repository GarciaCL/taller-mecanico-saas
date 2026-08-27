from flask import Blueprint, render_template, request, redirect, session
from modulos.auth import validar_login
from modulos.conexion import obtener_conexion, obtener_placeholder

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]
        
        user = validar_login(usuario, password)
        if user:
            session["usuario_id"] = user[0]
            session["taller_id"] = user[1]
            session["usuario"] = user[2]
            session["rol"] = user[3]
            session["nombre_taller"] = user[4]
            session["logo_url"] = user[5]
            session["color_primario"] = user[6]
            return redirect("/")
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

    return redirect("/#dash")

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
        # 1. Validar previamente si el correo ya está registrado
        cursor.execute(f"SELECT id FROM usuarios WHERE usuario = {p}", (datos["email"],))
        if cursor.fetchone():
            conexion.close()
            return f"""
                <div style="font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; text-align: center; min-height: 100vh; flex-direction: column; display: flex; align-items: center; justify-content: center;">
                    <div style="background: #1e293b; border: 1px solid #334155; padding: 30px; border-radius: 16px; max-width: 400px;">
                        <h2 style="color: #f59e0b; margin-top: 0;">⚠️ El correo ya está registrado</h2>
                        <p style="color: #94a3b8; font-size: 14px;">El correo <b>{datos['email']}</b> ya tiene una cuenta asociada.</p>
                        <div style="margin-top: 20px; display: flex; gap: 10px; justify-content: center;">
                            <a href="/login" style="background: #2563eb; color: white; padding: 10px 16px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 12px;">Iniciar Sesión</a>
                            <a href="/registro" style="background: #334155; color: white; padding: 10px 16px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 12px;">Probar otro correo</a>
                        </div>
                    </div>
                </div>
            """, 400

        # 2. Crear el nuevo taller
        cursor.execute(f"""
            INSERT INTO talleres (nombre_taller, telefono_taller, email_taller)
            VALUES ({p}, {p}, {p})
        """, (datos["nombre_taller"], datos["telefono"], datos["email"]))
        
        cursor.execute(f"SELECT id FROM talleres WHERE email_taller = {p} ORDER BY id DESC LIMIT 1", (datos["email"],))
        taller_id = cursor.fetchone()[0]

        # 3. Crear el usuario administrador
        cursor.execute(f"""
            INSERT INTO usuarios (taller_id, usuario, password, rol)
            VALUES ({p}, {p}, {p}, 'admin')
        """, (taller_id, datos["email"], datos["password"]))

        conexion.commit()

        # 4. Iniciar sesión automáticamente
        session["usuario_id"] = None
        session["taller_id"] = taller_id
        session["usuario"] = datos["email"]
        session["usuario_nombre"] = datos["nombre_admin"]
        session["rol"] = "admin"
        session["nombre_taller"] = datos["nombre_taller"]
        session["logo_url"] = "/static/logo_defecto.png"
        session["color_primario"] = "#3b82f6"

        # Limpiar datos temporales
        session.pop("registro_temp", None)

        conexion.close()
        return redirect("/#ajustes")

    except Exception as e:
        conexion.rollback()
        conexion.close()
        print(f"Error en confirmar_pago_registro: {e}")
        return f"Ocurrió un detalle al activar la cuenta: {e}. <a href='/registro'>Volver a intentar</a>", 500