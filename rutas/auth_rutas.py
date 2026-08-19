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