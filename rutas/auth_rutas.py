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

# --- NUEVAS RUTAS DE REGISTRO COMERCIAL ---

@auth_bp.route("/registro")
def vista_registro():
    return render_template("registro.html")

@auth_bp.route("/procesar_registro", methods=["POST"])
def procesar_registro_web():
    nombre_taller = request.form["nombre_taller"].strip()
    nombre_admin = request.form["nombre_admin"].strip()
    email = request.form["email"].strip().lower()
    telefono = request.form["telefono"].strip()
    password = request.form["password"].strip()
    plan = request.form.get("plan", "mensual")

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    # 1. Verificar si el correo ya existe en usuarios
    cursor.execute(f"SELECT id FROM usuarios WHERE email = {p}", (email,))
    if cursor.fetchone():
        conexion.close()
        return "El correo ya está registrado en el sistema. <a href='/login'>Iniciar sesión</a>", 400

    # 2. Crear el nuevo taller
    cursor.execute(f"""
        INSERT INTO talleres (nombre_taller, telefono_taller, email_taller)
        VALUES ({p}, {p}, {p})
    """, (nombre_taller, telefono, email))
    
    cursor.execute(f"SELECT id FROM talleres WHERE email_taller = {p} ORDER BY id DESC LIMIT 1", (email,))
    taller_id = cursor.fetchone()[0]

    # 3. Crear el usuario administrador del taller
    cursor.execute(f"""
        INSERT INTO usuarios (taller_id, nombre, email, password, rol)
        VALUES ({p}, {p}, {p}, {p}, 'admin')
    """, (taller_id, nombre_admin, email, password))

    conexion.commit()
    conexion.close()

    # 4. Iniciar sesión automáticamente
    session["usuario_id"] = None
    session["taller_id"] = taller_id
    session["usuario"] = email
    session["usuario_nombre"] = nombre_admin
    session["rol"] = "admin"
    session["nombre_taller"] = nombre_taller
    session["logo_url"] = "/static/logo_defecto.png"
    session["color_primario"] = "#3b82f6"

    # Redirigir a la aplicación
    return redirect("/#ajustes")