import os
import io
from flask import Flask, render_template, request, redirect, session, jsonify, send_file
from base_datos.crear_db import inicializar_db_saas
from modulos.gestion_db import (
    validar_login, crear_orden_recepcion_guiada, obtener_ordenes_kanban,
    actualizar_estado_orden, obtener_detalle_orden_por_token,
    obtener_inventario, agregar_repuesto, actualizar_orden_trabajo,
    finalizar_orden_trabajo, obtener_historial_vehiculo,
    agregar_repuesto_a_orden, descontar_stock_orden, obtener_repuestos_orden,
    obtener_marcas_y_modelos, agregar_repuestos_masivo,
    eliminar_repuesto, eliminar_repuestos_masivo,
    eliminar_repuesto_orden, actualizar_repuesto_orden  # <--- Nuevas importaciones
)
from modulos.generador_pdf import generar_pdf_ficha_recepcion

app = Flask(__name__)
app.secret_key = "clave_secreta_saas_taller"

inicializar_db_saas()

def guardar_foto(file, nombre_base):
    if not file or file.filename == '':
        return ''
    from werkzeug.utils import secure_filename
    filename = secure_filename(f"{nombre_base}_{file.filename}")
    path = os.path.join('static', 'uploads', filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file.save(path)
    return f"/static/uploads/{filename}"

@app.route("/")
def inicio():
    if "taller_id" not in session:
        return redirect("/login")
    
    taller = {
        "nombre": session.get("nombre_taller", "Taller Mecánico"),
        "logo": session.get("logo_url", "/static/logo_defecto.png"),
        "color": session.get("color_primario", "#3b82f6")
    }
    
    taller_id = session["taller_id"]
    ordenes = obtener_ordenes_kanban(taller_id)
    inventario = obtener_inventario(taller_id)
    marcas = obtener_marcas_y_modelos()
    
    return render_template("index.html", taller=taller, ordenes=ordenes, inventario=inventario, marcas=marcas)

@app.route("/login", methods=["GET", "POST"])
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

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/crear_ot", methods=["POST"])
def crear_ot_web():
    if "taller_id" not in session:
        return redirect("/login")
    
    patente = request.form["patente"]
    cliente = request.form.get("cliente", "Cliente General")
    telefono = request.form.get("telefono", "")
    marca = request.form.get("marca_input") or request.form.get("marca", "Marca")
    modelo = request.form.get("modelo_input") or request.form.get("modelo", "Modelo")
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
    
    crear_orden_recepcion_guiada(
        session["taller_id"], patente, sintomas, costo, km, combustible, 
        detalles, fotos, tiempo_horas, cliente, telefono, marca, modelo
    )
    return redirect("/")

@app.route("/vincular_repuesto_ot", methods=["POST"])
def vincular_repuesto_ot_web():
    if "taller_id" not in session:
        return jsonify({"success": False}), 401
    
    orden_id = int(request.form["orden_id"])
    inventario_id = int(request.form["inventario_id"])
    cantidad = int(request.form.get("cantidad", 1))
    precio_unidad = float(request.form.get("precio_unidad", 0.0)) if request.form.get("precio_unidad") else 0.0

    agregar_repuesto_a_orden(orden_id, inventario_id, cantidad, precio_unidad)
    return redirect("/")

@app.route("/obtener_repuestos_ot/<int:orden_id>")
def obtener_repuestos_ot_web(orden_id):
    if "taller_id" not in session:
        return jsonify([])
    items = obtener_repuestos_orden(orden_id)
    return jsonify([{"id": i[0], "nombre": i[1], "cantidad": i[2], "precio": i[3], "descontado": i[4]} for i in items])

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

@app.route("/finalizar_ot", methods=["POST"])
def finalizar_ot_web():
    if "taller_id" not in session:
        return redirect("/login")
    
    orden_id = int(request.form["orden_id"])
    descontar_stock_orden(orden_id, session["taller_id"])
    finalizar_orden_trabajo(orden_id, session["taller_id"])
    return redirect("/")

@app.route("/cambiar_estado_ot", methods=["POST"])
def cambiar_estado_ot_web():
    if "taller_id" not in session:
        return jsonify({"success": False}), 401
    
    data = request.get_json()
    orden_id = data["orden_id"]
    nuevo_estado = data["nuevo_estado"]

    actualizar_estado_orden(orden_id, session["taller_id"], nuevo_estado)

    if nuevo_estado == 'entrega':
        descontar_stock_orden(orden_id, session["taller_id"])

    return jsonify({"success": True})

@app.route("/seguimiento/<token>")
def seguimiento_cliente(token):
    orden = obtener_detalle_orden_por_token(token)
    if not orden:
        return render_template("seguimiento.html", error="Orden no encontrada"), 404
    return render_template("seguimiento.html", o=orden)

@app.route("/historial/<patente>")
def historial_vehiculo_web(patente):
    if "taller_id" not in session:
        return redirect("/login")
    
    historial = obtener_historial_vehiculo(session["taller_id"], patente)
    return render_template("historial.html", historial=historial, patente=patente.upper())

@app.route("/descargar_pdf/<token>")
def descargar_pdf_web(token):
    orden = obtener_detalle_orden_por_token(token)
    if not orden:
        return "Orden no encontrada", 404
    
    pdf_data = generar_pdf_ficha_recepcion(orden, request.host_url.rstrip('/'))
    
    return send_file(
        io.BytesIO(pdf_data),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Ficha_Recepcion_{orden[12]}.pdf"
    )

@app.route("/guardar_repuesto", methods=["POST"])
def guardar_repuesto_web():
    if "taller_id" not in session:
        return redirect("/login")
    
    codigo = request.form.get("codigo", "").strip()
    categoria = request.form.get("categoria", "General").strip()
    nombre = request.form.get("nombre", "").strip()
    stock = int(request.form["stock"]) if request.form.get("stock") and request.form.get("stock").isdigit() else 0
    costo = 0.0
    venta = 0.0
    mano_obra = 0.0
    
    compatabilidades = request.form.get("compatabilidades_final", "Universal").strip()
    if not compatabilidades:
        compatabilidades = "Universal"

    agregar_repuesto(session["taller_id"], codigo, categoria, nombre, stock, costo, venta, mano_obra, compatabilidades)
    return redirect("/")

@app.route("/carga_masiva_repuestos", methods=["POST"])
def carga_masiva_repuestos_web():
    if "taller_id" not in session:
        return jsonify({"success": False}), 401
    
    data = request.get_json()
    repuestos = data.get("repuestos", [])
    
    if repuestos:
        agregar_repuestos_masivo(session["taller_id"], repuestos)
        return jsonify({"success": True, "count": len(repuestos)})
    
    return jsonify({"success": False, "error": "Sin datos"}), 400

@app.route("/eliminar_repuesto/<int:repuesto_id>", methods=["POST"])
def eliminar_repuesto_web(repuesto_id):
    if "taller_id" not in session:
        return jsonify({"success": False}), 401
    
    eliminar_repuesto(session["taller_id"], repuesto_id)
    return jsonify({"success": True})

@app.route("/eliminar_repuestos_masivo", methods=["POST"])
def eliminar_repuestos_masivo_web():
    if "taller_id" not in session:
        return jsonify({"success": False}), 401
    
    data = request.get_json()
    ids = data.get("ids", [])
    
    if ids:
        eliminar_repuestos_masivo(session["taller_id"], ids)
        return jsonify({"success": True, "count": len(ids)})
    
    return jsonify({"success": False}), 400

@app.route("/eliminar_repuesto_ot/<int:item_id>", methods=["POST"])
def eliminar_repuesto_ot_web(item_id):
    if "taller_id" not in session:
        return jsonify({"success": False}), 401
    
    eliminar_repuesto_orden(item_id)
    return jsonify({"success": True})

@app.route("/actualizar_repuesto_ot", methods=["POST"])
def actualizar_repuesto_ot_web():
    if "taller_id" not in session:
        return jsonify({"success": False}), 401
    
    data = request.get_json()
    item_id = int(data["item_id"])
    cantidad = int(data.get("cantidad", 1))
    precio = float(data.get("precio", 0.0))

    actualizar_repuesto_orden(item_id, cantidad, precio)
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)

