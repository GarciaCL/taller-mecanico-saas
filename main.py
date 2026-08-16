from flask import Flask, render_template, request, redirect, session, jsonify
import os
from werkzeug.utils import secure_filename
from base_datos.crear_db import inicializar_db_saas
from modulos.gestion_db import actualizar_orden_trabajo # Importar la nueva función

@app.route("/editar_ot", methods=["POST"])
def editar_ot_web():
    if "taller_id" not in session:
        return redirect("/login")
    
    orden_id = int(request.form["orden_id"])
    km = int(request.form["km"]) if request.form.get("km") else 0
    combustible = request.form.get("combustible", "1/2")
    tiempo_horas = int(request.form.get("tiempo_estimado", 4))
    sintomas = request.form.get("sintomas", "")
    costo = float(request.form["costo"]) if request.form.get("costo") else 0.0

    actualizar_orden_trabajo(session["taller_id"], orden_id, km, combustible, tiempo_horas, sintomas, costo)
    return redirect("/")

app = Flask(__name__)
app.secret_key = "CLAVE-SUPER-SECRETA-SAAS-TALLER"

UPLOAD_FOLDER = "static/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

inicializar_db_saas()

@app.route("/")
def inicio():
    if "taller_id" not in session:
        return redirect("/login")
    
    taller_id = session["taller_id"]
    repuestos = obtener_inventario(taller_id)
    ordenes = obtener_ordenes_kanban(taller_id)
    
    taller_info = {
        "nombre": session.get("nombre_taller"),
        "color": session.get("color_primario", "#1e293b"),
    }
    return render_template("index.html", taller=taller_info, repuestos=repuestos, ordenes=ordenes)

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
            return redirect("/")
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

def guardar_foto(file, prefijo):
    if file and file.filename != '':
        filename = secure_filename(f"{prefijo}_{file.filename}")
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        return f"/static/uploads/{filename}"
    return ""

@app.route("/crear_ot", methods=["POST"])
@app.route("/crear_ot", methods=["POST"])
def crear_ot_web():
    if "taller_id" not in session:
        return redirect("/login")
    
    patente = request.form["patente"]
    sintomas = request.form["sintomas"]
    costo = float(request.form["costo"]) if request.form.get("costo") else 0.0
    km = int(request.form["km"]) if request.form.get("km") else 0
    combustible = request.form.get("combustible", "1/2")
    detalles = request.form.get("detalles", "")
    tiempo_horas = int(request.form.get("tiempo_estimado", 4))

    fotos = {
        'frontal': guardar_foto(request.files.get('foto_frontal'), f"{patente}_frontal"),
        'trasera': guardar_foto(request.files.get('foto_trasera'), f"{patente}_trasera"),
        'costado_izq': guardar_foto(request.files.get('foto_izq'), f"{patente}_izq"),
        'costado_der': guardar_foto(request.files.get('foto_der'), f"{patente}_der"),
        'tablero': guardar_foto(request.files.get('foto_tablero'), f"{patente}_tablero")
    }
    
    crear_orden_recepcion_guiada(session["taller_id"], patente, sintomas, costo, km, combustible, detalles, fotos, tiempo_horas)
    return redirect("/")

@app.route("/cambiar_estado_ot", methods=["POST"])
def cambiar_estado_ot_web():
    if "taller_id" not in session:
        return jsonify({"status": "error", "message": "No autorizado"}), 401
    
    data = request.json
    orden_id = data.get("orden_id")
    nuevo_estado = data.get("nuevo_estado")
    
    actualizar_estado_orden(orden_id, session["taller_id"], nuevo_estado)
    return jsonify({"status": "ok"})

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
        compatabilidades=""
    )
    return redirect("/")

if __name__ == "__main__":
    app.run(port=5000, debug=True)

    from modulos.gestion_db import obtener_detalle_orden_publico  # Asegúrate de agregarla a la importación

from modulos.gestion_db import obtener_detalle_orden_por_token

@app.route("/seguimiento/<token>")
def seguimiento_cliente(token):
    orden = obtener_detalle_orden_por_token(token)
    if not orden:
        return render_template("seguimiento.html", error="Orden no encontrada"), 404
    return render_template("seguimiento.html", o=orden)

from modulos.gestion_db import obtener_detalle_orden_por_token

