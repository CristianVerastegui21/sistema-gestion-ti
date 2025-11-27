from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import aiomysql
import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

app = FastAPI(title="Reportes Service")

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql'),
    'user': os.getenv('DB_USER', 'user_ti'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'db': os.getenv('DB_NAME', 'ti_management'),
    'port': 3306,
    'autocommit': True,
    'charset': 'utf8mb4'
}

async def get_data_from_db(query):
    try:
        pool = await aiomysql.create_pool(**DB_CONFIG)
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query)
                result = await cur.fetchall()
        pool.close()
        await pool.wait_closed()
        return result
    except Exception as e:
        print(f"Error DB: {e}")
        return []

# --- DASHBOARD CONECTADO (Lógica Real) ---
@app.get("/dashboard")
async def dashboard():
    pool = await aiomysql.create_pool(**DB_CONFIG)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 1. Total Equipos
            await cur.execute("SELECT COUNT(*) FROM equipos")
            total = (await cur.fetchone())[0]
            
            # 2. Equipos Operativos
            await cur.execute("SELECT COUNT(*) FROM equipos WHERE estado_operativo='operativo'")
            operativos = (await cur.fetchone())[0]
            
            # 3. Valor Inventario
            await cur.execute("SELECT COALESCE(SUM(costo_compra), 0) FROM equipos")
            valor = (await cur.fetchone())[0]

            # 4. Mantenimientos del Mes (REAL)
            # Usamos CURRENT_DATE() de MySQL
            await cur.execute("""
                SELECT COUNT(*) FROM mantenimientos 
                WHERE MONTH(fecha_programada) = MONTH(CURRENT_DATE()) 
                AND YEAR(fecha_programada) = YEAR(CURRENT_DATE())
            """)
            mant_mes = (await cur.fetchone())[0]

            # 5. Costo Mantenimiento Mes (REAL)
            await cur.execute("""
                SELECT COALESCE(SUM(costo), 0) FROM mantenimientos 
                WHERE MONTH(fecha_programada) = MONTH(CURRENT_DATE()) 
                AND YEAR(fecha_programada) = YEAR(CURRENT_DATE())
            """)
            costo_mes = (await cur.fetchone())[0]
            
            return {
                "total_equipos": total,
                "equipos_operativos": operativos,
                "tasa_disponibilidad": round((operativos/total*100),1) if total else 0,
                "valor_inventario": float(valor),
                "mantenimientos_mes": mant_mes,             
                "equipos_reparacion": total - operativos,
                "costo_mantenimiento_mes": float(costo_mes) 
            }

@app.get("/equipos-por-ubicacion")
async def eq_ubicacion():
    data = await get_data_from_db("""
        SELECT CONCAT(IFNULL(u.edificio,''), ' - ', IFNULL(u.aula_oficina,'')) as ubicacion, COUNT(*) as cantidad
        FROM equipos e JOIN ubicaciones u ON e.ubicacion_actual_id = u.id
        GROUP BY u.id, u.edificio, u.aula_oficina
    """)
    return [{"ubicacion": r[0], "cantidad": r[1]} for r in data]

@app.get("/equipos-por-estado")
async def eq_estado():
    data = await get_data_from_db("SELECT estado_operativo as estado, COUNT(*) as cantidad FROM equipos GROUP BY estado_operativo")
    return [{"estado": r[0], "cantidad": r[1]} for r in data]

@app.get("/equipos-por-categoria")
async def eq_cat():
    data = await get_data_from_db("""
        SELECT c.nombre as categoria, COUNT(*) as cantidad, COALESCE(SUM(e.costo_compra), 0) as valor_total
        FROM equipos e JOIN categorias_equipos c ON e.categoria_id = c.id
        GROUP BY c.nombre
    """)
    return [{"categoria": r[0], "cantidad": r[1], "valor_total": float(r[2])} for r in data]

@app.get("/costos-mantenimiento")
async def costos(year: int = 2024):
    data = await get_data_from_db(f"""
        SELECT DATE_FORMAT(fecha_realizada, '%M') as mes, tipo, SUM(costo) as total_costo
        FROM mantenimientos WHERE YEAR(fecha_realizada) = {year}
        GROUP BY mes, tipo
    """)
    return [{"mes": r[0], "tipo": r[1], "total_costo": float(r[2])} for r in data]

# --- PDF GENERATOR (Versión Estable) ---
@app.post("/export/pdf")
async def export_pdf(payload: dict):
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('TitleCustom', parent=styles['Title'], fontSize=16, spaceAfter=20, textColor=colors.navy)
        subtitle_style = ParagraphStyle('SubTitleCustom', parent=styles['Normal'], fontSize=10, textColor=colors.grey)
        header_style = ParagraphStyle('HeaderCustom', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER)

        elements.append(Paragraph("UNIVERSIDAD NACIONAL DE TRUJILLO", title_style))
        elements.append(Paragraph("Dirección de Tecnologías de Información", header_style))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Fecha de Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", subtitle_style))
        elements.append(Spacer(1, 25))

        elements.append(Paragraph("Detalle de Inventario", styles['Heading2']))
        
        data = await get_data_from_db("""
            SELECT e.codigo_inventario, e.nombre, e.marca, e.estado_operativo, 
                   CONCAT(IFNULL(u.edificio,''), ' - ', IFNULL(u.aula_oficina,'')),
                   e.costo_compra
            FROM equipos e 
            LEFT JOIN ubicaciones u ON e.ubicacion_actual_id = u.id
            ORDER BY e.codigo_inventario
        """)
        
        if not data:
            elements.append(Paragraph("No hay datos para mostrar", styles['Normal']))
        else:
            table_data = [['Código', 'Equipo', 'Marca', 'Estado', 'Ubicación', 'Costo']]
            for row in data:
                costo_fmt = f"${float(row[5]):,.2f}" if row[5] else "$0.00"
                fila = [
                    str(row[0]), str(row[1])[:20], str(row[2]) if row[2] else '-', 
                    str(row[3]), str(row[4])[:20], costo_fmt
                ]
                table_data.append(fila)
            
            t = Table(table_data, colWidths=[70, 120, 60, 70, 110, 60])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white])
            ]))
            elements.append(t)

        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Generado por Sistema de Gestión TI v1.0", subtitle_style))

        doc.build(elements)
        buffer.seek(0)
        
        return StreamingResponse(
            buffer, media_type="application/pdf", 
            headers={"Content-Disposition": "attachment; filename=reporte_inventario.pdf"}
        )
    except Exception as e:
        print(f"❌ ERROR GENERANDO PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fallo PDF: {str(e)}")