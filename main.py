from flask import Flask, render_template, session, redirect
from base_datos.crear_db import inicializar_db_saas
from modulos.ordenes import obtener_ordenes_kanban
from modulos.inventario import obtener_inventario
from modulos.vehiculos import obtener_marcas_y_modelos, calcular_alerta_revision_tecnica
from modulos.clientes import obtener_lista_clientes

# Importar Blueprints
from rutas.auth_rutas import auth_bp
from rutas.ordenes_rutas import ordenes_bp
from rutas.inventario_rutas import inventario_bp
from rutas.clientes_rutas import clientes_bp

app = Flask(__name__)
app.secret_key = "clave_secreta_saas_taller"

inicializar_db_saas()

app.jinja_env.filters['alerta_rt'] = calcular_alerta_revision_tecnica

app.register_blueprint(auth_bp)
app.register_blueprint(ordenes_bp)
app.register_blueprint(inventario_bp)
app.register_blueprint(clientes_bp)

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
    return render_template(
        "index.html", 
        taller=taller, 
        ordenes=obtener_ordenes_kanban(taller_id), 
        inventario=obtener_inventario(taller_id), 
        marcas=obtener_marcas_y_modelos(),
        clientes=obtener_lista_clientes(taller_id)
    )

if __name__ == "__main__":
    app.run(debug=True)