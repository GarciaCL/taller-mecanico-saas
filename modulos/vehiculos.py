from datetime import datetime
from modulos.conexion import obtener_conexion

CALENDARIO_RT_CHILE = {
    '1': 6, '2': 7, '3': 8, '4': 9, '5': 10, '6': 11, '7': 1, '8': 3, '9': 4, '0': 5
}

def calcular_alerta_revision_tecnica(patente):
    try:
        if not patente or str(patente).strip() == '' or str(patente).strip().lower() == 'none':
            return {"estado": "normal", "mensaje": ""}
        
        patente_limpia = str(patente).strip().upper()
        digitos = [c for c in patente_limpia if c.isdigit()]
        if not digitos:
            return {"estado": "normal", "mensaje": ""}
        
        ultimo_digito = digitos[-1]
        mes_vencimiento = CALENDARIO_RT_CHILE.get(ultimo_digito, 12)
        mes_actual = datetime.now().month

        if mes_vencimiento == mes_actual:
            return {"estado": "urgente", "mensaje": f"🔴 RT Vence este mes (Dígito {ultimo_digito})"}
        elif mes_vencimiento == (mes_actual + 1) or (mes_actual == 12 and mes_vencimiento == 1):
            return {"estado": "proximo", "mensaje": f"⚠️ RT Vence el próximo mes (Dígito {ultimo_digito})"}
        
        return {"estado": "normal", "mensaje": ""}
    except Exception:
        return {"estado": "normal", "mensaje": ""}

def obtener_marcas_y_modelos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    filas = []

    try:
        cursor.execute("""
            SELECT DISTINCT marca, modelo FROM catalogo_vehiculos WHERE marca IS NOT NULL AND marca != ''
            UNION
            SELECT DISTINCT marca, modelo FROM vehiculos WHERE marca IS NOT NULL AND marca != ''
        """)
        filas = cursor.fetchall()
    except Exception:
        conexion.rollback()
        try:
            cursor.execute("SELECT DISTINCT marca, modelo FROM vehiculos WHERE marca IS NOT NULL AND marca != ''")
            filas = cursor.fetchall()
        except Exception:
            filas = []
    finally:
        conexion.close()

    marcas_dict = {}
    for m, mod in filas:
        if m and mod:
            m_title = str(m).strip().title()
            mod_title = str(mod).strip().title()
            if m_title not in marcas_dict:
                marcas_dict[m_title] = []
            if mod_title not in marcas_dict[m_title]:
                marcas_dict[m_title].append(mod_title)

    return marcas_dict