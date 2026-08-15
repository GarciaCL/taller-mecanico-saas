import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from modulos.gestion_db import (
    agregar_cliente_y_vehiculo, 
    agregar_repuesto, 
    cargar_inventario_desde_csv, 
    verificar_alerta_30_dias,
    buscar_vehiculo_por_patente,
    crear_ficha_trabajo,
    registrar_respaldo_exitoso,
    crear_copia_seguridad_zip
)
from modulos.conexion_nube import simular_servidor_vps, simular_envio_correos_recordatorio

def iniciar_aplicacion():
    ventana = tk.Tk()
    ventana.title("Sistema de Gestión de Taller Mecánico (Offline SSD)")
    ventana.geometry("980x720")

    marco_alerta = None

    # 1. Alerta Roja Gigante (Regla de 30 días)
    if verificar_alerta_30_dias():
        marco_alerta = tk.Frame(ventana, bg="red", pady=8)
        marco_alerta.pack(fill="x", side="top")
        
        texto_alerta = tk.Label(
            marco_alerta, 
            text="¡URGENTE! Llevas más de 1 mes sin respaldar tus datos.\nPor favor conéctate a internet y presiona el botón 'Respaldar Ahora'",
            bg="red", 
            fg="white", 
            font=("Arial", 11, "bold")
        )
        texto_alerta.pack()

    # Contenedor de Pestañas
    pestanas = ttk.Notebook(ventana)
    pestanas.pack(expand=True, fill="both", padx=10, pady=10)

    # ==========================================
    # PESTAÑA 1: CLIENTES Y VEHÍCULOS
    # ==========================================
    p_clientes = ttk.Frame(pestanas)
    pestanas.add(p_clientes, text="🚗 Clientes y Vehículos")

    frame_form = ttk.LabelFrame(p_clientes, text=" Registro de Cliente y Vehículo ", padding=15)
    frame_form.pack(fill="x", padx=15, pady=15)

    ttk.Label(frame_form, text="Nombre Cliente:").grid(row=0, column=0, sticky="w", pady=5)
    entry_nombre = ttk.Entry(frame_form, width=30)
    entry_nombre.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(frame_form, text="RUT / ID:").grid(row=0, column=2, sticky="w", pady=5)
    entry_rut = ttk.Entry(frame_form, width=20)
    entry_rut.grid(row=0, column=3, padx=5, pady=5)

    ttk.Label(frame_form, text="Teléfono:").grid(row=1, column=0, sticky="w", pady=5)
    entry_tel = ttk.Entry(frame_form, width=30)
    entry_tel.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(frame_form, text="Correo:").grid(row=1, column=2, sticky="w", pady=5)
    entry_correo = ttk.Entry(frame_form, width=20)
    entry_correo.grid(row=1, column=3, padx=5, pady=5)

    ttk.Separator(frame_form, orient="horizontal").grid(row=2, column=0, columnspan=4, sticky="ew", pady=10)

    ttk.Label(frame_form, text="Patente / VIN:").grid(row=3, column=0, sticky="w", pady=5)
    entry_patente = ttk.Entry(frame_form, width=30)
    entry_patente.grid(row=3, column=1, padx=5, pady=5)

    ttk.Label(frame_form, text="Marca:").grid(row=3, column=2, sticky="w", pady=5)
    entry_marca = ttk.Entry(frame_form, width=20)
    entry_marca.grid(row=3, column=3, padx=5, pady=5)

    ttk.Label(frame_form, text="Modelo:").grid(row=4, column=0, sticky="w", pady=5)
    entry_modelo = ttk.Entry(frame_form, width=30)
    entry_modelo.grid(row=4, column=1, padx=5, pady=5)

    ttk.Label(frame_form, text="Año:").grid(row=4, column=2, sticky="w", pady=5)
    entry_anio = ttk.Entry(frame_form, width=20)
    entry_anio.grid(row=4, column=3, padx=5, pady=5)

    ttk.Label(frame_form, text="Kilometraje:").grid(row=5, column=0, sticky="w", pady=5)
    entry_km = ttk.Entry(frame_form, width=30)
    entry_km.grid(row=5, column=1, padx=5, pady=5)

    def guardar_datos():
        if not entry_nombre.get() or not entry_rut.get() or not entry_patente.get():
            messagebox.showwarning("Atención", "Por favor completa al menos Nombre, RUT y Patente.")
            return
        try:
            agregar_cliente_y_vehiculo(
                nombre=entry_nombre.get(),
                rut=entry_rut.get(),
                telefono=entry_tel.get(),
                correo=entry_correo.get(),
                patente=entry_patente.get(),
                marca=entry_marca.get(),
                modelo=entry_modelo.get(),
                anio=int(entry_anio.get()) if entry_anio.get() else 0,
                km=int(entry_km.get()) if entry_km.get() else 0
            )
            messagebox.showinfo("Éxito", "¡Cliente y Vehículo guardados correctamente!")
            for entry in [entry_nombre, entry_rut, entry_tel, entry_correo, entry_patente, entry_marca, entry_modelo, entry_anio, entry_km]:
                entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al guardar: {e}")

    btn_guardar = ttk.Button(frame_form, text="💾 Guardar Vehículo", command=guardar_datos)
    btn_guardar.grid(row=6, column=0, columnspan=4, pady=15)

    # ==========================================
    # PESTAÑA 2: INVENTARIO Y REPUESTOS
    # ==========================================
    p_inventario = ttk.Frame(pestanas)
    pestanas.add(p_inventario, text="📦 Inventario y Repuestos")

    frame_repuesto = ttk.LabelFrame(p_inventario, text=" Registro de Repuesto / Servicio ", padding=15)
    frame_repuesto.pack(fill="x", padx=15, pady=10)

    ttk.Label(frame_repuesto, text="Código Repuesto:").grid(row=0, column=0, sticky="w", pady=5)
    entry_cod = ttk.Entry(frame_repuesto, width=25)
    entry_cod.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(frame_repuesto, text="Nombre/Descripción:").grid(row=0, column=2, sticky="w", pady=5)
    entry_nom_rep = ttk.Entry(frame_repuesto, width=30)
    entry_nom_rep.grid(row=0, column=3, padx=5, pady=5)

    ttk.Label(frame_repuesto, text="Stock Inicial:").grid(row=1, column=0, sticky="w", pady=5)
    entry_stock = ttk.Entry(frame_repuesto, width=25)
    entry_stock.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(frame_repuesto, text="Precio Costo ($):").grid(row=1, column=2, sticky="w", pady=5)
    entry_costo = ttk.Entry(frame_repuesto, width=30)
    entry_costo.grid(row=1, column=3, padx=5, pady=5)

    ttk.Label(frame_repuesto, text="Precio Venta ($):").grid(row=2, column=0, sticky="w", pady=5)
    entry_venta = ttk.Entry(frame_repuesto, width=25)
    entry_venta.grid(row=2, column=1, padx=5, pady=5)

    ttk.Label(frame_repuesto, text="Mano de Obra ($):").grid(row=2, column=2, sticky="w", pady=5)
    entry_obra = ttk.Entry(frame_repuesto, width=30)
    entry_obra.grid(row=2, column=3, padx=5, pady=5)

    ttk.Label(frame_repuesto, text="Compatibilidades:").grid(row=3, column=0, sticky="w", pady=5)
    entry_compat = ttk.Entry(frame_repuesto, width=60)
    entry_compat.grid(row=3, column=1, columnspan=3, sticky="w", padx=5, pady=5)

    def guardar_repuesto_form():
        if not entry_cod.get() or not entry_nom_rep.get():
            messagebox.showwarning("Atención", "Ingresa al menos Código y Nombre del repuesto.")
            return
        try:
            agregar_repuesto(
                codigo=entry_cod.get(),
                nombre=entry_nom_rep.get(),
                stock=int(entry_stock.get()) if entry_stock.get() else 0,
                costo=float(entry_costo.get()) if entry_costo.get() else 0.0,
                venta=float(entry_venta.get()) if entry_venta.get() else 0.0,
                mano_obra=float(entry_obra.get()) if entry_obra.get() else 0.0,
                compatibilidades=entry_compat.get()
            )
            messagebox.showinfo("Éxito", "¡Repuesto guardado con éxito!")
            for entry in [entry_cod, entry_nom_rep, entry_stock, entry_costo, entry_venta, entry_obra, entry_compat]:
                entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar repuesto: {e}")

    btn_guardar_rep = ttk.Button(frame_repuesto, text="📦 Guardar Repuesto", command=guardar_repuesto_form)
    btn_guardar_rep.grid(row=4, column=0, columnspan=4, pady=10)

    frame_csv = ttk.LabelFrame(p_inventario, text=" Carga Masiva desde CSV / Excel ", padding=15)
    frame_csv.pack(fill="x", padx=15, pady=10)

    def seleccionar_y_cargar_csv():
        archivo_ruta = filedialog.askopenfilename(
            title="Seleccionar archivo de repuestos",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        if archivo_ruta:
            try:
                total = cargar_inventario_desde_csv(archivo_ruta)
                messagebox.showinfo("Carga Completada", f"¡Se importaron {total} repuestos exitosamente!")
            except Exception as e:
                messagebox.showerror("Error de Carga", f"Asegúrate de que el CSV tenga las columnas correctas.\nDetalle: {e}")

    btn_csv = ttk.Button(frame_csv, text="📂 Seleccionar Archivo CSV para Cargar Masivamente", command=seleccionar_y_cargar_csv)
    btn_csv.pack(pady=5)

    # ==========================================
    # PESTAÑA 3: HISTORIAL Y NOTAS
    # ==========================================
    p_fichas = ttk.Frame(pestanas)
    pestanas.add(p_fichas, text="📝 Historial y Notas")

    frame_buscar = ttk.LabelFrame(p_fichas, text=" Buscar Vehículo por Patente ", padding=15)
    frame_buscar.pack(fill="x", padx=15, pady=10)

    ttk.Label(frame_buscar, text="Patente / VIN:").grid(row=0, column=0, sticky="w", padx=5)
    entry_patente_buscar = ttk.Entry(frame_buscar, width=20)
    entry_patente_buscar.grid(row=0, column=1, padx=5)

    lbl_info_vehiculo = ttk.Label(frame_buscar, text="Estado: Ingresa una patente y presiona Buscar.", font=("Arial", 10, "italic"))
    lbl_info_vehiculo.grid(row=0, column=3, padx=15)

    vehiculo_encontrado_id = {"id": None}

    def buscar_vehiculo():
        pat = entry_patente_buscar.get().strip()
        if not pat:
            messagebox.showwarning("Atención", "Escribe una patente para buscar.")
            return
        datos = buscar_vehiculo_por_patente(pat)
        if datos:
            vehiculo_encontrado_id["id"] = datos[0]
            lbl_info_vehiculo.config(
                text=f"✅ Encontrado: {datos[2]} {datos[3]} | Cliente: {datos[4]} (RUT: {datos[5]})",
                foreground="green"
            )
        else:
            vehiculo_encontrado_id["id"] = None
            lbl_info_vehiculo.config(
                text="❌ Vehículo no encontrado. Regístralo en la Pestaña 1.",
                foreground="red"
            )

    btn_buscar = ttk.Button(frame_buscar, text="🔍 Buscar", command=buscar_vehiculo)
    btn_buscar.grid(row=0, column=2, padx=5)

    frame_notas = ttk.LabelFrame(p_fichas, text=" Ficha de Trabajo / Observaciones del Mecánico ", padding=15)
    frame_notas.pack(fill="both", expand=True, padx=15, pady=10)

    ttk.Label(frame_notas, text="Observaciones del Mecánico (Diagnóstico libre):").pack(anchor="w", pady=5)
    txt_observaciones = tk.Text(frame_notas, height=6, width=80)
    txt_observaciones.pack(fill="x", pady=5)

    frame_costo = ttk.Frame(frame_notas)
    frame_costo.pack(fill="x", pady=10)

    ttk.Label(frame_costo, text="Monto/Costo Total Estimado ($):").pack(side="left", padx=5)
    entry_costo_total = ttk.Entry(frame_costo, width=20)
    entry_costo_total.pack(side="left", padx=5)

    def guardar_ficha():
        if not vehiculo_encontrado_id["id"]:
            messagebox.showwarning("Atención", "Debes buscar y seleccionar un vehículo válido primero.")
            return
        obs = txt_observaciones.get("1.0", tk.END).strip()
        if not obs:
            messagebox.showwarning("Atención", "Escribe las observaciones o diagnóstico del mecánico.")
            return
        try:
            costo = float(entry_costo_total.get()) if entry_costo_total.get() else 0.0
            crear_ficha_trabajo(vehiculo_encontrado_id["id"], obs, costo)
            messagebox.showinfo("Éxito", "¡Ficha de Trabajo guardada en el historial!")
            txt_observaciones.delete("1.0", tk.END)
            entry_costo_total.delete(0, tk.END)
            entry_patente_buscar.delete(0, tk.END)
            lbl_info_vehiculo.config(text="Estado: Ingresa una patente y presiona Buscar.", foreground="black")
            vehiculo_encontrado_id["id"] = None
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar la ficha: {e}")

    btn_guardar_ficha = ttk.Button(frame_costo, text="📝 Guardar Ficha de Trabajo", command=guardar_ficha)
    btn_guardar_ficha.pack(side="left", padx=20)

    # ==========================================
    # PESTAÑA 4: RESPALDO Y NUBE (VPS)
    # ==========================================
    p_respaldo = ttk.Frame(pestanas)
    pestanas.add(p_respaldo, text="☁️ Respaldo y Nube")

    # --- Marco 1: Respaldo ---
    frame_resp_box = ttk.LabelFrame(p_respaldo, text=" Respaldo de Seguridad Local ", padding=15)
    frame_resp_box.pack(fill="x", padx=15, pady=10)

    def ejecutar_respaldo_ahora():
        archivo_creado = crear_copia_seguridad_zip()
        registrar_respaldo_exitoso()
        
        nonlocal marco_alerta
        if marco_alerta:
            marco_alerta.pack_forget()
            
        messagebox.showinfo(
            "Respaldo Exitoso", 
            f"¡Tus datos han sido respaldados correctamente!\n\nSe creó el archivo:\n{archivo_creado}\n\nLa alerta roja se ha desactivado."
        )

    btn_respaldar_ya = ttk.Button(frame_resp_box, text="☁️ Respaldar Ahora", command=ejecutar_respaldo_ahora)
    btn_respaldar_ya.pack(pady=5)

    # --- Marco 2: Conexión VPS y Reservas Web ---
    frame_vps = ttk.LabelFrame(p_respaldo, text=" Sincronización con Servidor VPS (Página Web) ", padding=15)
    frame_vps.pack(fill="both", expand=True, padx=15, pady=10)

    frame_key = ttk.Frame(frame_vps)
    frame_key.pack(fill="x", pady=5)

    ttk.Label(frame_key, text="API Key de Validación:").pack(side="left", padx=5)
    entry_api_key = ttk.Entry(frame_key, width=35)
    entry_api_key.insert(0, "TALLER-SECRET-KEY-2026")
    entry_api_key.pack(side="left", padx=5)

    txt_reservas = tk.Text(frame_vps, height=7, width=80)
    txt_reservas.pack(fill="both", expand=True, pady=5)

    def descargar_reservas():
        key = entry_api_key.get().strip()
        respuesta = simular_servidor_vps(key)
        
        txt_reservas.delete("1.0", tk.END)
        if respuesta["estado"] == "exito":
            txt_reservas.insert(tk.END, f"{respuesta['mensaje']}\n")
            txt_reservas.insert(tk.END, "---------------------------------------------------------\n")
            txt_reservas.insert(tk.END, "CITAS RESERVADAS DESDE LA PÁGINA WEB:\n\n")
            
            for cita in respuesta["reservas"]:
                txt_reservas.insert(tk.END, f"📌 Reserva #{cita['id_reserva']}\n")
                txt_reservas.insert(tk.END, f"   Cliente: {cita['cliente']} ({cita['telefono']})\n")
                txt_reservas.insert(tk.END, f"   Patente: {cita['patente']} | Servicio: {cita['servicio']}\n")
                txt_reservas.insert(tk.END, f"   Fecha/Hora Cita: {cita['fecha_cita']}\n")
                txt_reservas.insert(tk.END, "---------------------------------------------------------\n")
        else:
            txt_reservas.insert(tk.END, f"{respuesta['mensaje']}\n")

    btn_descargar = ttk.Button(frame_vps, text="🌐 Descargar Citas de la Web", command=descargar_reservas)
    btn_descargar.pack(pady=3)

    def enviar_correos_diferidos():
        key = entry_api_key.get().strip()
        resp = simular_envio_correos_recordatorio(key)
        
        txt_reservas.delete("1.0", tk.END)
        if resp["estado"] == "exito":
            txt_reservas.insert(tk.END, f"{resp['mensaje']}\n\n")
            for c in resp["envios"]:
                txt_reservas.insert(tk.END, f"{c}\n")
        else:
            txt_reservas.insert(tk.END, f"{resp['mensaje']}\n")

    btn_correos = ttk.Button(frame_vps, text="✉️ Enviar Correos de Recordatorio (Promociones/KM)", command=enviar_correos_diferidos)
    btn_correos.pack(pady=3)

    ventana.mainloop()