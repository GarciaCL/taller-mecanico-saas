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

def obtener_placeholder():
    return "%s" if DATABASE_URL else "?"

def inicializar_db_saas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    p = obtener_placeholder()

    is_postgres = True if DATABASE_URL else False
    serial_pk = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
    bool_type = "BOOLEAN DEFAULT FALSE" if is_postgres else "INTEGER DEFAULT 0"

    # 1. TABLA CATÁLOGO MARCAS Y MODELOS BASE
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS catalogo_vehiculos (
            id {serial_pk},
            marca VARCHAR(100) NOT NULL,
            modelo VARCHAR(100) NOT NULL,
            anio_inicio INT DEFAULT 2000
        );
    """)

    # 2. TABLA TALLERES
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS talleres (
            id {serial_pk},
            nombre_taller VARCHAR(150) NOT NULL,
            logo_url VARCHAR(255),
            color_primario VARCHAR(20) DEFAULT '#3b82f6',
            modulo_inventario {bool_type},
            modulo_citas_web {bool_type},
            modulo_correos {bool_type}
        );
    """)

    # 3. TABLA USUARIOS
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS usuarios (
            id {serial_pk},
            taller_id INT NOT NULL,
            usuario VARCHAR(50) NOT NULL,
            password VARCHAR(255) NOT NULL,
            rol VARCHAR(20) DEFAULT 'mecanico',
            FOREIGN KEY (taller_id) REFERENCES talleres(id)
        );
    """)

    # 4. TABLA CLIENTES
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS clientes (
            id {serial_pk},
            taller_id INT NOT NULL,
            nombre VARCHAR(100) NOT NULL,
            rut VARCHAR(20),
            telefono VARCHAR(20),
            FOREIGN KEY (taller_id) REFERENCES talleres(id)
        );
    """)

    # 5. TABLA VEHÍCULOS
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS vehiculos (
            id {serial_pk},
            cliente_id INT NOT NULL,
            patente_vin VARCHAR(20) NOT NULL,
            marca VARCHAR(50),
            modelo VARCHAR(50),
            anio INT,
            kilometraje INT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        );
    """)

    # 6. TABLA ÓRDENES DE TRABAJO
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS ordenes_trabajo (
            id {serial_pk},
            taller_id INT NOT NULL,
            vehiculo_id INT NOT NULL,
            token VARCHAR(100),
            estado VARCHAR(30) DEFAULT 'recepcion',
            sintomas_cliente TEXT,
            costo_estimado FLOAT,
            km_ingreso INT,
            nivel_combustible VARCHAR(20),
            detalles_carrocería TEXT,
            tiempo_estimado_horas INT DEFAULT 4,
            foto_frontal VARCHAR(255),
            foto_trasera VARCHAR(255),
            foto_costado_izq VARCHAR(255),
            foto_costado_der VARCHAR(255),
            foto_tablero VARCHAR(255),
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (taller_id) REFERENCES talleres(id),
            FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id)
        );
    """)

    # 7. TABLA INVENTARIO
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS inventario (
            id {serial_pk},
            taller_id INT NOT NULL,
            codigo VARCHAR(50) NOT NULL,
            categoria VARCHAR(50),
            nombre VARCHAR(100) NOT NULL,
            stock INT DEFAULT 0,
            precio_costo FLOAT DEFAULT 0,
            precio_venta FLOAT DEFAULT 0,
            mano_obra FLOAT DEFAULT 0,
            modelos_compatibles TEXT,
            FOREIGN KEY (taller_id) REFERENCES talleres(id)
        );
    """)

    # 8. TABLA VÍNCULO ÓRDENES Y REPUESTOS
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

    # --- POBLAR MARCAS Y MODELOS BASE SI LA TABLA ESTÁ VACÍA ---
    cursor.execute("SELECT COUNT(*) FROM catalogo_vehiculos")
    cant_cat = cursor.fetchone()[0]

    if cant_cat == 0:
        base_autos = [
            ("Toyota", "Yaris", 2005), ("Toyota", "Corolla", 2000), ("Toyota", "RAV4", 2008), ("Toyota", "Hilux", 2005),
            ("Nissan", "Qashqai", 2010), ("Nissan", "X-Trail", 2008), ("Nissan", "Versa", 2012), ("Nissan", "NP300 Navara", 2010),
            ("Hyundai", "Accent", 2003), ("Hyundai", "Elantra", 2005), ("Hyundai", "Tucson", 2007), ("Hyundai", "Santa Fe", 2008),
            ("Kia", "Rio", 2006), ("Kia", "Cerato", 2008), ("Kia", "Sportage", 2008), ("Kia", "Morning", 2008),
            ("Chevrolet", "Sail", 2011), ("Chevrolet", "Spark", 2008), ("Chevrolet", "Tracker", 2014), ("Chevrolet", "D-Max", 2008),
            ("Suzuki", "Swift", 2007), ("Suzuki", "Grand Vitara", 2006), ("Suzuki", "Baleno", 2016), ("Suzuki", "S-Cross", 2015),
            ("Ford", "Ranger", 2008), ("Ford", "EcoSport", 2008), ("Ford", "Focus", 2006), ("Ford", "Fiesta", 2008),
            ("Peugeot", "208", 2013), ("Peugeot", "301", 2013), ("Peugeot", "2008", 2015), ("Peugeot", "3008", 2012),
            ("MG", "ZS", 2018), ("MG", "3", 2015), ("MG", "6", 2016), ("MG", "RX5", 2019),
            ("Volkswagen", "Gol", 2006), ("Volkswagen", "Polo", 2008), ("Volkswagen", "Amarok", 2011), ("Volkswagen", "Tiguan", 2010)
        ]
        for m, mod, anio in base_autos:
            cursor.execute(f"INSERT INTO catalogo_vehiculos (marca, modelo, anio_inicio) VALUES ({p}, {p}, {p})", (m, mod, anio))
        conexion.commit()

    # POBLAR TALLER Y USUARIO DEMO
    cursor.execute("SELECT COUNT(*) FROM talleres")
    cant_talleres = cursor.fetchone()[0]

    if cant_talleres == 0:
        cursor.execute(f"""
            INSERT INTO talleres (nombre_taller, logo_url, color_primario, modulo_inventario, modulo_citas_web, modulo_correos)
            VALUES ('Taller Mecánico Central', '/static/logo_defecto.png', '#3b82f6', TRUE, TRUE, TRUE)
        """)
        conexion.commit()

        cursor.execute(f"""
            INSERT INTO usuarios (taller_id, usuario, password, rol)
            VALUES (1, 'admin', 'admin123', 'admin')
        """)
        conexion.commit()

    conexion.close()