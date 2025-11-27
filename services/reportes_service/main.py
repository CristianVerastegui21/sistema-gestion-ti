from fastapi import FastAPI
import aiomysql
import os
import pandas as pd
from datetime import datetime

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

async def get_data(query, params=None):
    pool = await aiomysql.create_pool(**DB_CONFIG)
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, params or ())
            return await cur.fetchall()

@app.get("/dashboard")
async def dashboard():
    pool = await aiomysql.create_pool(**DB_CONFIG)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM equipos")
            total = (await cur.fetchone())[0]
            
            await cur.execute("SELECT COUNT(*) FROM equipos WHERE estado_operativo='operativo'")
            operativos = (await cur.fetchone())[0]
            
            await cur.execute("SELECT COALESCE(SUM(costo_compra), 0) FROM equipos")
            valor = (await cur.fetchone())[0]
            
            return {
                "total_equipos": total,
                "equipos_operativos": operativos,
                "tasa_disponibilidad": round((operativos/total*100),1) if total else 0,
                "valor_inventario": float(valor),
                "mantenimientos_mes": 0, # Simplificado para el ejemplo
                "equipos_reparacion": total - operativos,
                "costo_mantenimiento_mes": 0
            }

@app.get("/equipos-por-ubicacion")
async def eq_ubicacion():
    # CONCAT es la forma de unir strings en MySQL
    return await get_data("""
        SELECT CONCAT(u.edificio, ' - ', u.aula_oficina) as ubicacion, COUNT(*) as cantidad
        FROM equipos e JOIN ubicaciones u ON e.ubicacion_actual_id = u.id
        GROUP BY u.id, u.edificio, u.aula_oficina
    """)

@app.get("/equipos-por-estado")
async def eq_estado():
    return await get_data("SELECT estado_operativo as estado, COUNT(*) as cantidad FROM equipos GROUP BY estado_operativo")

@app.get("/equipos-por-categoria")
async def eq_cat():
    return await get_data("""
        SELECT c.nombre as categoria, COUNT(*) as cantidad, COALESCE(SUM(e.costo_compra), 0) as valor_total
        FROM equipos e JOIN categorias_equipos c ON e.categoria_id = c.id
        GROUP BY c.nombre
    """)

@app.get("/costos-mantenimiento")
async def costos(year: int = 2024):
    return await get_data("""
        SELECT DATE_FORMAT(fecha_realizada, '%M') as mes, tipo, SUM(costo) as total_costo
        FROM mantenimientos WHERE YEAR(fecha_realizada) = %s
        GROUP BY mes, tipo
    """, (year,))
    
@app.post("/export/pdf")
async def export_pdf(data: dict):
    # Dummy response para evitar errores en frontend si no instalas reportlab
    return {"filename": "reporte_mysql.pdf", "message": "PDF generado (simulado)"}