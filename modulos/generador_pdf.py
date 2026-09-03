import os
import io
import urllib.request
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def obtener_imagen_reportlab(url_o_path, ancho=150, alto=100):
    """
    Intenta cargar una imagen desde una URL (Cloudinary) o disco local
    y devuelve un objeto Image de ReportLab.
    """
    if not url_o_path:
        return None
    try:
        if url_o_path.startswith("http"):
            # Es una URL de Cloudinary
            req = urllib.request.urlopen(url_o_path)
            img_data = io.BytesIO(req.read())
            return RLImage(img_data, width=ancho, height=alto)
        else:
            # Es una ruta local (resguardo)
            ruta_limpia = url_o_path.lstrip('/')
            if os.path.exists(ruta_limpia):
                return RLImage(ruta_limpia, width=ancho, height=alto)
            return None
    except Exception as e:
        print(f"Error cargando imagen en PDF ({url_o_path}): {e}")
        return None

def generar_pdf_ficha_recepcion(orden_detalle, host_base="https://taller-mecanico-saas.onrender.com"):
    """
    Genera en memoria un documento PDF profesional para la Ficha de Recepción.
    Soporta imágenes locales y URLs de Cloudinary.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    # Estilos personalizados
    titulo_style = ParagraphStyle(
        'TituloTaller',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold'
    )
    subtitulo_style = ParagraphStyle(
        'SubtituloTaller',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#64748b'),
        fontName='Helvetica'
    )
    seccion_style = ParagraphStyle(
        'SeccionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#1e293b'),
        fontName='Helvetica-Bold',
        spaceAfter=6
    )
    texto_normal = ParagraphStyle(
        'TextoNormal',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155'),
        fontName='Helvetica'
    )

    # Extraer variables con valores por defecto seguros
    # Asumiendo el orden basado en tu código original, ajusta si es necesario
    taller_nombre = orden_detalle[18] if len(orden_detalle) > 18 and orden_detalle[18] else "Taller Mecánico"
    taller_logo_url = orden_detalle[19] if len(orden_detalle) > 19 and orden_detalle[19] else None
    patente = orden_detalle[12] if len(orden_detalle) > 12 and orden_detalle[12] else "SIN-PATENTE"
    marca = orden_detalle[13] if len(orden_detalle) > 13 and orden_detalle[13] else ""
    modelo = orden_detalle[14] if len(orden_detalle) > 14 and orden_detalle[14] else ""
    anio = orden_detalle[15] if len(orden_detalle) > 15 and orden_detalle[15] else ""
    cliente = orden_detalle[16] if len(orden_detalle) > 16 and orden_detalle[16] else "Cliente General"
    telefono = orden_detalle[17] if len(orden_detalle) > 17 and orden_detalle[17] else "N/A"
    km = orden_detalle[4] if len(orden_detalle) > 4 and orden_detalle[4] else 0
    combustible = orden_detalle[5] if len(orden_detalle) > 5 and orden_detalle[5] else "1/2"
    sintomas = orden_detalle[2] if len(orden_detalle) > 2 and orden_detalle[2] else "Sin observaciones"
    token = orden_detalle[21] if len(orden_detalle) > 21 and orden_detalle[21] else patente

    url_seguimiento = f"{host_base}/seguimiento/{token}"

    # 1. GENERAR CÓDIGO QR EN MEMORIA
    try:
        qr = qrcode.QRCode(version=1, box_size=4, border=1)
        qr.add_data(url_seguimiento)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        qr_buffer = io.BytesIO()
        img_qr.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        qr_rl_img = RLImage(qr_buffer, width=1.1*inch, height=1.1*inch)
    except Exception:
        qr_rl_img = Paragraph("<b>[QR]</b>", texto_normal)

    # Cargar Logo del taller (Soporte Cloudinary)
    taller_logo = obtener_imagen_reportlab(taller_logo_url, ancho=1.0*inch, alto=1.0*inch)

    # 2. ENCABEZADO
    if taller_logo:
        header_content = [taller_logo, Paragraph(f"<b>{taller_nombre}</b>", titulo_style)]
    else:
        header_content = [Paragraph(f"<b>{taller_nombre}</b>", titulo_style), ""]

    info_encabezado = [
        header_content + [qr_rl_img],
        [
            Paragraph("<b>FICHA DE RECEPCIÓN Y ESTADO DE VEHÍCULO</b><br/>Comprobante oficial de ingreso al taller", subtitulo_style),
            "",
            Paragraph("<font size=7 color='#64748b'>Escanear para ver estado en vivo</font>", subtitulo_style)
        ]
    ]

    # Ajustar colWidths dependiendo de si hay logo
    col_widths = [1.2*inch, 4.0*inch, 2.0*inch] if taller_logo else [5.2*inch, 0, 2.0*inch]
    
    tabla_encabezado = Table(info_encabezado, colWidths=col_widths)
    tabla_encabezado.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (2,0), (2,-1), 'CENTER'), # QR centrado
        ('SPAN', (0,1), (1,1)) if not taller_logo else ('SPAN', (0,1), (0,1)), # Ajuste span subtitulo
    ]))
    story.append(tabla_encabezado)
    story.append(Spacer(1, 10))

    # 3. DATOS DE VEHÍCULO Y CLIENTE
    datos_resumen = [
        [
            Paragraph(f"<b>PATENTE / VIN:</b> {patente}", texto_normal),
            Paragraph(f"<b>VEHÍCULO:</b> {marca} {modelo} ({anio})", texto_normal)
        ],
        [
            Paragraph(f"<b>CLIENTE:</b> {cliente}", texto_normal),
            Paragraph(f"<b>TELÉFONO:</b> {telefono}", texto_normal)
        ],
        [
            Paragraph(f"<b>KILOMETRAJE:</b> {km} KM", texto_normal),
            Paragraph(f"<b>COMBUSTIBLE:</b> {combustible}", texto_normal)
        ]
    ]
    tabla_datos = Table(datos_resumen, colWidths=[3.6*inch, 3.6*inch])
    tabla_datos.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(tabla_datos)
    story.append(Spacer(1, 12))

    # 4. SÍNTOMAS Y TRABAJOS SOLICITADOS
    story.append(Paragraph("Síntomas Declarados & Trabajos Solicitados", seccion_style))
    tabla_sintomas = Table([[Paragraph(str(sintomas), texto_normal)]], colWidths=[7.2*inch])
    tabla_sintomas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(tabla_sintomas)
    story.append(Spacer(1, 12))

    # 5. INSPECCIÓN FOTOGRÁFICA (Soporte Cloudinary)
    elementos_fotos = []
    # Asumiendo índices 7 a 11 para las 5 fotos en orden_detalle
    for idx in range(7, 12):
        if len(orden_detalle) > idx and orden_detalle[idx]:
            img_obj = obtener_imagen_reportlab(orden_detalle[idx], ancho=2.1*inch, alto=1.4*inch)
            if img_obj:
                elementos_fotos.append(img_obj)

    if elementos_fotos:
        story.append(Paragraph("Inspección Fotográfica Inicial", seccion_style))
        filas_fotos = []
        fila_temp = []
        for img_elem in elementos_fotos:
            fila_temp.append(img_elem)
            if len(fila_temp) == 3:
                filas_fotos.append(fila_temp)
                fila_temp = []
        if fila_temp:
            while len(fila_temp) < 3:
                fila_temp.append("")
            filas_fotos.append(fila_temp)

        tabla_fotos = Table(filas_fotos, colWidths=[2.4*inch, 2.4*inch, 2.4*inch])
        tabla_fotos.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(tabla_fotos)
        story.append(Spacer(1, 12))

    # 6. FIRMAS DE CONFORMIDAD
    firmas = [
        [
            Paragraph("____________________________________<br/>Firma del Cliente", subtitulo_style),
            Paragraph("____________________________________<br/>Recepción Taller Mecánico", subtitulo_style)
        ]
    ]
    tabla_firmas = Table(firmas, colWidths=[3.6*inch, 3.6*inch])
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 15),
    ]))
    story.append(Spacer(1, 10))
    story.append(tabla_firmas)

    # Construir PDF
    doc.build(story)
    pdf_val = buffer.getvalue()
    buffer.close()
    return pdf_val