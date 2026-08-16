import os

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def obtener_conexion():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    else:
        import sqlite3
        return sqlite3.connect("base_datos/taller.db")

def inicializar_db_saas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    serial_pk = "SERIAL PRIMARY KEY" if DATABASE_URL else "INTEGER PRIMARY KEY AUTOINCREMENT"
    bool_type = "BOOLEAN DEFAULT TRUE" if DATABASE_URL else "INTEGER DEFAULT 1"

    # 1. TABLA TALLERES
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS talleres (
            id {serial_pk},
            nombre_taller VARCHAR(150) NOT NULL,
            rut_empresa VARCHAR(30) UNIQUE,
            logo_url TEXT DEFAULT '/static/logo_defecto.png',
            color_primario VARCHAR(20) DEFAULT '#3b82f6',
            modulo_inventario {bool_type},
            modulo_citas_web {bool_type},
            modulo_correos {bool_type},
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conexion.commit()

    # 2. TABLA USUARIOS
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS usuarios (
            id {serial_pk},
            taller_id INT NOT NULL,
            usuario VARCHAR(50) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol VARCHAR(20) DEFAULT 'mecanico',
            FOREIGN KEY (taller_id) REFERENCES talleres(id)
        );
    """)
    conexion.commit()

    # 3. TABLA CLIENTES
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS clientes (
            id {serial_pk},
            taller_id INT NOT NULL,
            nombre VARCHAR(100) NOT NULL,
            rut VARCHAR(30) NOT NULL,
            telefono VARCHAR(30),
            correo VARCHAR(100),
            FOREIGN KEY (taller_id) REFERENCES talleres(id)
        );
    """)
    conexion.commit()

    # 4. TABLA VEHÍCULOS
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS vehiculos (
            id {serial_pk},
            cliente_id INT NOT NULL,
            patente_vin VARCHAR(30) NOT NULL,
            marca VARCHAR(50),
            modelo VARCHAR(50),
            anio INT,
            kilometraje INT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        );
    """)
    conexion.commit()

    # 5. TABLA INVENTARIO
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS inventario (
            id {serial_pk},
            taller_id INT NOT NULL,
            codigo VARCHAR(50) NOT NULL,
            categoria VARCHAR(80) DEFAULT 'General',
            nombre VARCHAR(150) NOT NULL,
            stock INT DEFAULT 0,
            precio_costo FLOAT DEFAULT 0,
            precio_venta FLOAT DEFAULT 0,
            mano_obra FLOAT DEFAULT 0,
            modelos_compatibles TEXT,
            FOREIGN KEY (taller_id) REFERENCES talleres(id)
        );
    """)
    conexion.commit()

    # 6. TABLA ÓRDENES DE TRABAJO
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS ordenes_trabajo (
            id {serial_pk},
            taller_id INT NOT NULL,
            vehiculo_id INT NOT NULL,
            token VARCHAR(80) UNIQUE,
            estado VARCHAR(50) DEFAULT 'recepcion',
            sintomas_cliente TEXT,
            costo_estimado FLOAT DEFAULT 0,
            km_ingreso INT DEFAULT 0,
            nivel_combustible VARCHAR(20) DEFAULT '1/2',
            detalles_carrocería TEXT,
            tiempo_estimado_horas INT DEFAULT 4,
            foto_frontal TEXT,
            foto_trasera TEXT,
            foto_costado_izq TEXT,
            foto_costado_der TEXT,
            foto_tablero TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (taller_id) REFERENCES talleres(id),
            FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id)
        );
    """)
    conexion.commit()

# 7. TABLA VÍNCULO ÓRDENES - REPUESTOS
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS ordenes_repuestos (
            id {serial_pk},
            orden_id INT NOT NULL,
            inventario_id INT NOT NULL,
            cantidad INT DEFAULT 1,
            precio_unidad FLOAT DEFAULT 0,
            descontado {bool_type},
            FOREIGN KEY (orden_id) REFERENCES ordenes_trabajo(id),
            FOREIGN KEY (inventario_id) REFERENCES inventario(id)
        );
    """)
    conexion.commit()

    # MIGRACIONES INDIVIDUALES AISLADAS
    migraciones = [
        "ALTER TABLE ordenes_trabajo ADD COLUMN token VARCHAR(80);",
        "ALTER TABLE ordenes_trabajo ADD COLUMN tiempo_estimado_horas INT DEFAULT 4;",
        "ALTER TABLE ordenes_trabajo ADD COLUMN km_ingreso INT DEFAULT 0;",
        "ALTER TABLE ordenes_trabajo ADD COLUMN nivel_combustible VARCHAR(20) DEFAULT '1/2';",
        "ALTER TABLE ordenes_trabajo ADD COLUMN detalles_carrocería TEXT;",
        "ALTER TABLE ordenes_trabajo ADD COLUMN foto_frontal TEXT;",
        "ALTER TABLE ordenes_trabajo ADD COLUMN foto_trasera TEXT;",
        "ALTER TABLE ordenes_trabajo ADD COLUMN foto_costado_izq TEXT;",
        "ALTER TABLE ordenes_trabajo ADD COLUMN foto_costado_der TEXT;",
        "ALTER TABLE ordenes_trabajo ADD COLUMN foto_tablero TEXT;"
    ]

    for mig in migraciones:
        try:
            cursor.execute(mig)
            conexion.commit()
        except Exception:
            conexion.rollback()

    conexion.close()

if __name__ == "__main__":
    inicializar_db_saas()