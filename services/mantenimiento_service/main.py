from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import aiomysql
import os
from datetime import date

app = FastAPI(title="Mantenimiento Service")

# Configuración para MySQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql'),
    'user': os.getenv('DB_USER', 'user_ti'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'db': os.getenv('DB_NAME', 'ti_management'),
    'port': 3306,
    'autocommit': True,
    'charset': 'utf8mb4'  # <--- AQUÍ ES DONDE SE AÑADE EL CHARSET
}

class MantenimientoCreate(BaseModel):
    equipo_id: int
    tipo: str
    fecha_programada: date
    descripcion: str
    prioridad: str = "media"

class MantenimientoUpdate(BaseModel):
    fecha_realizada: Optional[date] = None
    costo: Optional[float] = None
    estado: Optional[str] = None
    observaciones: Optional[str] = None

async def get_db_pool():
    return await aiomysql.create_pool(**DB_CONFIG)

@app.get("/")
async def root():
    return {"service": "Mantenimiento Service"}

@app.get("/mantenimientos")
async def get_mantenimientos():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Usamos sintaxis MySQL
            await cur.execute("""
                SELECT m.*, e.nombre as equipo_nombre, e.codigo_inventario 
                FROM mantenimientos m
                JOIN equipos e ON m.equipo_id = e.id 
                ORDER BY m.fecha_programada ASC
            """)
            result = await cur.fetchall()
            
            # Convertir fechas a string para evitar errores de JSON
            for r in result:
                if r.get('fecha_programada'): r['fecha_programada'] = str(r['fecha_programada'])
                if r.get('fecha_realizada'): r['fecha_realizada'] = str(r['fecha_realizada'])
            return result

@app.post("/mantenimientos")
async def create_mantenimiento(mant: MantenimientoCreate):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Usamos %s en lugar de $1 para MySQL
            await cur.execute("""
                INSERT INTO mantenimientos (equipo_id, tipo, fecha_programada, descripcion, prioridad)
                VALUES (%s, %s, %s, %s, %s)
            """, (mant.equipo_id, mant.tipo, mant.fecha_programada, mant.descripcion, mant.prioridad))
            return {"message": "Mantenimiento programado", "id": cur.lastrowid}

@app.put("/mantenimientos/{mant_id}")
async def update_mantenimiento(mant_id: int, mant: MantenimientoUpdate):
    pool = await get_db_pool()
    updates = []
    params = []
    
    if mant.fecha_realizada:
        updates.append("fecha_realizada = %s")
        params.append(mant.fecha_realizada)
    if mant.costo is not None:
        updates.append("costo = %s")
        params.append(mant.costo)
    if mant.estado:
        updates.append("estado = %s")
        params.append(mant.estado)
    if mant.observaciones:
        updates.append("observaciones = %s")
        params.append(mant.observaciones)

    if not updates:
        raise HTTPException(status_code=400, detail="Nada que actualizar")

    params.append(mant_id)
    query = f"UPDATE mantenimientos SET {', '.join(updates)} WHERE id = %s"

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, tuple(params))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Mantenimiento no encontrado")
            
    return {"message": "Mantenimiento actualizado"}