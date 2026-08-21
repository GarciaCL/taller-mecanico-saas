from flask import Blueprint, render_template, request, redirect, session
from modulos.auth import validar_login

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