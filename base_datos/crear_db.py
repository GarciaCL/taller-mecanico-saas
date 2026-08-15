import sqlite3
import os

DB_PATH = "base_datos/taller.db"

def inicializar_db_saas():
    # Crear la carpeta base_datos si no existe
    if not os.path.exists("base_datos"):
        os.makedirs("base_datos")

    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    # 1. TABLA DE TALLERES (Clientes SaaS)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS talleres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_taller TEXT NOT NULL,
            rut_empresa TEXT UNIQUE,
            logo_url TEXT DEFAULT '/static/logo_defecto.png',
            color_primario TEXT DEFAULT '#3b82f6',
            modulo_inventario INTEGER DEFAULT 1,
            modulo_citas_web INTEGER DEFAULT 1,
            modulo_correos INTEGER DEFAULT 0,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. TABLA DE USUARIOS (Inicios de sesión)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            taller_id INTEGER NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT DEFAULT 'mecanico',
            FOREIGN KEY (taller_id) REFERENCES talleres(id)
        )
    """)

    # 3. TABLA DE CLIENTES (Asociada a un Taller)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            taller_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            rut TEXT NOT NULL,
            telefono TEXT,
            correo TEXT,
            FOREIGN KEY (taller_id) REFERENCES talleres(id)
        )
    """)

    # 4. TABLA DE VEHÍCULOS (Asociada a un Cliente)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            patente_vin TEXT NOT NULL,
            marca TEXT,
            modelo TEXT,
            anio INTEGER,
            kilometraje INTEGER,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)

    # 5. TABLA DE INVENTARIO (Asociada a un Taller con Compatibilidades)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            taller_id INTEGER NOT NULL,
            codigo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            stock INTEGER DEFAULT 0,
            precio_costo REAL DEFAULT 0,
            precio_venta REAL DEFAULT 0,
            mano_obra REAL DEFAULT 0,
            modelos_compatibles TEXT,
            FOREIGN KEY (taller_id) REFERENCES talleres(id)
        )
    """)

    # 6. TABLA DE FICHAS DE TRABAJO
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fichas_trabajo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehiculo_id INTEGER NOT NULL,
            observaciones_mecanico TEXT,
            costo_total REAL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id)
        )
    """)

    # --- CREAR UN TALLER DE PRUEBA INICIAL ---
    cursor.execute("SELECT COUNT(*) FROM talleres")
    if cursor.fetchone()[0] == 0:
        # Taller de demostración
        cursor.execute("""
            INSERT INTO talleres (nombre_taller, rut_empresa, color_primario, modulo_inventario, modulo_citas_web, modulo_correos)
            VALUES ('Taller Mecánico Central', '76.123.456-7', '#1e293b', 1, 1, 1)
        """)
        taller_id = cursor.lastrowid

        # Usuario administrador por defecto
        cursor.execute("""
            INSERT INTO usuarios (taller_id, usuario, password, rol)
            VALUES (?, 'admin', 'admin123', 'administrador')
        """, (taller_id,))

        print("✅ Base de datos SaaS inicializada con Taller y Usuario de prueba ('admin' / 'admin123').")

    conexion.commit()
    conexion.close()

if __name__ == "__main__":
    inicializar_db_saas()