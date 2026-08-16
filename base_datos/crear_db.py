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
        )
    """)

    # 2. TABLA USUARIOS
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS usuarios (
            id {serial_pk},
            taller_id INT NOT NULL,
            usuario VARCHAR(50) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol VARCHAR(20) DEFAULT 'mecanico',
            FOREIGN KEY (taller_id) REFERENCES talleres(id)
        )
    """)

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
        )
    """)

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
        )
    """)

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
        )
    """)

    # 6. TABLA ÓRDENES DE TRABAJO (KANBAN)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS ordenes_trabajo (
            id {serial_pk},
            taller_id INT NOT NULL,
            vehiculo_id INT NOT NULL,
            estado VARCHAR(50) DEFAULT 'recepcion',
            sintomas_cliente TEXT,
            costo_estimado FLOAT DEFAULT 0,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (taller_id) REFERENCES talleres(id),
            FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id)
        )
    """)

    # Migraciones preventivas
    try:
        cursor.execute("ALTER TABLE inventario ADD COLUMN categoria VARCHAR(80) DEFAULT 'General';")
        conexion.commit()
    except Exception:
        conexion.rollback()

    # CREAR TALLER Y USUARIO INICIAL SI NO EXISTE
    cursor.execute("SELECT COUNT(*) FROM talleres")
    if cursor.fetchone()[0] == 0:
        if DATABASE_URL:
            cursor.execute("""
                INSERT INTO talleres (nombre_taller, rut_empresa, color_primario, modulo_inventario, modulo_citas_web, modulo_correos)
                VALUES ('Taller Mecánico Central', '76.123.456-7', '#1e293b', TRUE, TRUE, TRUE) RETURNING id;
            """)
            taller_id = cursor.fetchone()[0]
            cursor.execute("""
                INSERT INTO usuarios (taller_id, usuario, password, rol)
                VALUES (%s, 'admin', 'admin123', 'administrador')
            """, (taller_id,))
        else:
            cursor.execute("""
                INSERT INTO talleres (nombre_taller, rut_empresa, color_primario, modulo_inventario, modulo_citas_web, modulo_correos)
                VALUES ('Taller Mecánico Central', '76.123.456-7', '#1e293b', 1, 1, 1)
            """)
            taller_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO usuarios (taller_id, usuario, password, rol)
                VALUES (?, 'admin', 'admin123', 'administrador')
            """, (taller_id,))

    conexion.commit()
    conexion.close()

if __name__ == "__main__":
    inicializar_db_saas()