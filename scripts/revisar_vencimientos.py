import os
import sys
from datetime import datetime, timedelta

# Asegurar que el script encuentre la raíz del proyecto para importar los módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modulos.conexion import obtener_conexion
from modulos.notificaciones import enviar_aviso_vencimiento

def verificar_y_notificar_vencimientos():
    print(f"[{datetime.now()}] Iniciando revisión de vencimientos...")
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # Buscamos los talleres activos cuya fecha de vencimiento sea dentro de 3 días exactos
    # o que venzan hoy y no hayan sido notificados
    query = """
        SELECT id, nombre_taller, email_taller, fecha_vencimiento 
        FROM talleres 
        WHERE estado = 'activo' 
          AND fecha_vencimiento IS NOT NULL
          AND DATE(fecha_vencimiento) = CURRENT_DATE + INTERVAL '3 days';
    """
    
    try:
        cursor.execute(query)
        talleres_por_vencer = cursor.fetchall()
        
        if not talleres_por_vencer:
            print("[INFO] No hay talleres próximos a vencer hoy.")
        
        for taller in talleres_por_vencer:
            taller_id, nombre_taller, email, fecha_venc = taller
            fecha_formateada = fecha_venc.strftime("%d-%m-%Y")
            
            print(f"[ENVIANDO AVISO] Taller: {nombre_taller} ({email}) - Vence: {fecha_formateada}")
            enviar_aviso_vencimiento(email, fecha_formateada)
            
    except Exception as e:
        print(f"[ERROR] Ocurrió un fallo al revisar vencimientos: {e}")
    finally:
        cursor.close()
        conexion.close()

if __name__ == "__main__":
    verificar_y_notificar_vencimientos()