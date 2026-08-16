
import io
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generar_pdf_ficha_recepcion(orden_detalle, host_base="https://taller-mecanico-saas.onrender.com"):
    """
    Genera en memoria un documento PDF profesional para la Ficha de Recepción.
    orden_detalle contiene los campos retornados por obtener_detalle_orden_por_token.
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

    # Extraer variables de orden_detalle
    # o[0]=id, o[1]=estado, o[2]=sintomas, o[3]=costo, o[4]=km, o[5]=combustible, o[6]=detalles,
    # o[7..11]=fotos, o[12]=patente, o[13]=marca, o[14]=modelo, o[15]=anio, o[16]=cliente,
    # o[17]=telefono, o[18]=taller_nombre, o[19]=logo, o[20]=color, o[21]=token
    
    token = orden_detalle[21] if len(orden_detalle) > 21 and orden_detalle[21] else orden_detalle[12]
    url_seguimiento = f"{host_base}/seguimiento/{token}"

    # 1. GENERAR CÓDIGO QR EN MEMORIA
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(url_seguimiento)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    qr_buffer = io.BytesIO()
    img_qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_rl_img = RLImage(qr_buffer, width=1.2*inch, height=1.2*inch)

    # 2. ENCABEZADO CON CABECERA Y QR
    info_encabezado = [
        [
            Paragraph(f"<b>{orden_detalle[18]}</b>", titulo_style),
            qr_rl_img
        ],
        [
            Paragraph("<b>FICHA DE RECEPCIÓN Y ESTADO DE VEHÍCULO</b><br/>Comprobante oficial de ingreso al taller", subtitulo_style),
            Paragraph("<font size=7 color='#64748b'>Escanear para ver estado en vivo</font>", subtitulo_style)
        ]
    ]

    tabla_encabezado = Table(info_encabezado, colWidths=[5.2*inch, 2.0*inch])
    tabla_encabezado.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
    ]))
    story.append(tabla_encabezado)
    story.append(Spacer(1, 12))

    # 3. DATOS DE VEHÍCULO Y CLIENTE
    datos_resumen = [
        [
            Paragraph(f"<b>PATENTE / VIN:</b> {orden_detalle[12]}", texto_normal),
            Paragraph(f"<b>VEHÍCULO:</b> {orden_detalle[13]} {orden_detalle[14]} ({orden_detalle[15]})", texto_normal)
        ],
        [
            Paragraph(f"<b>CLIENTE:</b> {orden_detalle[16]}", texto_normal),
            Paragraph(f"<b>TELÉFONO:</b> {orden_detalle[17]}", texto_normal)
        ],
        [
            Paragraph(f"<b>KILOMETRAJE:</b> {orden_detalle[4]} KM", texto_normal),
            Paragraph(f"<b>COMBUSTIBLE:</b> {orden_detalle[5]}", texto_normal)
        ]
    ]
    tabla_datos = Table(datos_resumen, colWidths=[3.6*inch, 3.6*inch])
    tabla_datos.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(tabla_datos)
    story.append(Spacer(1, 14))

    # 4. SÍNTOMAS Y TRABAJOS SOLICITADOS
    story.append(Paragraph("Síntomas Declarados & Trabajos Solicitados", seccion_style))
    tabla_sintomas = Table([[Paragraph(orden_detalle[2] if orden_detalle[2] else 'Sin observaciones', texto_normal)]], colWidths=[7.2*inch])
    tabla_sintomas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(tabla_sintomas)
    story.append(Spacer(1, 14))

    # 5. INSPECCIÓN FOTOGRÁFICA DE RECEPCIÓN
    fotos_rutas = [orden_detalle[7], orden_detalle[8], orden_detalle[9], orden_detalle[10], orden_detalle[11]]
    fotos_validas = [f for f in fotos_rutas if f and f.strip() != '']

    if fotos_validas:
        story.append(Paragraph("Inspección Fotográfica Inicial", seccion_style))
        filas_fotos = []
        fila_actual = []
        
        for f_path in fotos_validas:
            # Convertir ruta relativa (/static/...) a ruta local real
            ruta_disco = f_path.lstrip('/')
            try:
                img_f = RLImage(ruta_disco, width=2.2*inch, height=1.5*inch)
                fila_actual.append(img_f)
            except Exception:
                pass
            
            if len(fila_actual) == 3:
                filas_fotos.append(fila_actual)
                fila_actual = []
        
        if fila_actual:
            while len(fila_actual) < 3:
                fila_actual.append("")
            filas_fotos.append(fila_actual)

        if filas_fotos:
            tabla_fotos = Table(filas_fotos, colWidths=[2.4*inch, 2.4*inch, 2.4*inch])
            tabla_fotos.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('PADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(tabla_fotos)
            story.append(Spacer(1, 14))

    # 6. FIRMA DE CONFORMIDAD Y PIE DE PÁGINA
    firmas = [
        [
            Paragraph("____________________________________<br/>Firma del Cliente", subtitulo_style),
            Paragraph("____________________________________<br/>Recepción Taller Mecánico", subtitulo_style)
        ]
    ]
    tabla_firmas = Table(firmas, colWidths=[3.6*inch, 3.6*inch])
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 20),
    ]))
    story.append(Spacer(1, 10))
    story.append(tabla_firmas)

    # Construir el documento
    doc.build(story)
    pdf_val = buffer.getvalue()
    buffer.close()
    return pdf_val