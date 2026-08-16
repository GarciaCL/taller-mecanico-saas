from flask import Flask, render_template, request, redirect, session
import webbrowser
import threading
from base_datos.crear_db import inicializar_db_saas
from modulos.gestion_db import (
    validar_login,
    obtener_clientes_y_vehiculos,
    obtener_inventario,
    agregar_cliente_y_vehiculo,
    agregar_repuesto,
    crear_ficha_trabajo,
    buscar_vehiculo_por_patente,
    crear_copia_seguridad_zip
)

app = Flask(__name__)
app.secret_key = "CLAVE-SUPER-SECRETA-SAAS-TALLER"

inicializar_db_saas()

@app.route("/")
def inicio():
    if "taller_id" not in session:
        return redirect("/login")
    
    taller_id = session["taller_id"]
    clientes = obtener_clientes_y_vehiculos(taller_id)
    repuestos = obtener_inventario(taller_id)
    
    taller_info = {
        "nombre": session.get("nombre_taller"),
        "color": session.get("color_primario", "#1e293b"),
        "mod_inventario": session.get("mod_inventario"),
        "mod_citas": session.get("mod_citas"),
        "mod_correos": session.get("mod_correos")
    }
    return render_template("index.html", taller=taller_info, clientes=clientes, repuestos=repuestos)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["usuario"]
        pwd = request.form["password"]
        datos = validar_login(user, pwd)
        
        if datos:
            session["user_id"] = datos[0]
            session["taller_id"] = datos[1]
            session["usuario"] = datos[2]
            session["nombre_taller"] = datos[4]
            session["color_primario"] = datos[6]
            session["mod_inventario"] = datos[7]
            session["mod_citas"] = datos[8]
            session["mod_correos"] = datos[9]
            return redirect("/")
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/guardar_cliente", methods=["POST"])
def guardar_cliente_web():
    if "taller_id" not in session:
        return redirect("/login")
    agregar_cliente_y_vehiculo(
        taller_id=session["taller_id"],
        nombre=request.form["nombre"],
        rut=request.form["rut"],
        telefono=request.form.get("telefono", ""),
        correo=request.form.get("correo", ""),
        patente=request.form["patente"],
        marca=request.form.get("marca", ""),
        modelo=request.form.get("modelo", ""),
        anio=int(request.form["anio"]) if request.form.get("anio") else 0,
        km=int(request.form["km"]) if request.form.get("km") else 0
    )
    return redirect("/")

@app.route("/guardar_repuesto", methods=["POST"])
def guardar_repuesto_web():
    if "taller_id" not in session:
        return redirect("/login")
    agregar_repuesto(
        taller_id=session["taller_id"],
        codigo=request.form["codigo"],
        categoria=request.form.get("categoria", "General"),
        nombre=request.form["nombre"],
        stock=int(request.form["stock"]) if request.form.get("stock") else 0,
        costo=float(request.form["costo"]) if request.form.get("costo") else 0.0,
        venta=float(request.form["venta"]) if request.form.get("venta") else 0.0,
        mano_obra=float(request.form["mano_obra"]) if request.form.get("mano_obra") else 0.0,
        compatabilidades=request.form.get("compatibles", "")
    )
    return redirect("/")

@app.route("/guardar_ficha", methods=["POST"])
def guardar_ficha_web():
    if "taller_id" not in session:
        return redirect("/login")
    patente = request.form["patente"].strip()
    datos = buscar_vehiculo_por_patente(patente)
    if datos:
        crear_ficha_trabajo(
            vehiculo_id=datos[0],
            observaciones=request.form["observaciones"],
            costo_total=float(request.form["costo"]) if request.form.get("costo") else 0.0
        )
    return redirect("/")

@app.route("/respaldar", methods=["POST"])
def respaldar_web():
    crear_copia_seguridad_zip()
    return redirect("/")

if __name__ == "__main__":
    app.run(port=5000, debug=True)