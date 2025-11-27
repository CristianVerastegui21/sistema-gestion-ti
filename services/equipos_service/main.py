from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import aiomysql
import os
import json
from datetime import date

app = FastAPI(title="Equipos Service")

# Configuración MySQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql'),
    'user': os.getenv('DB_USER', 'user_ti'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'db': os.getenv('DB_NAME', 'ti_management'),
    'port': 3306,
    'autocommit': True,
    'charset': 'utf8mb4'
}

async def get_db_pool():
    return await aiomysql.create_pool(**DB_CONFIG)

class EquipoCreate(BaseModel):
    codigo_inventario: str
    categoria_id: int
    nombre: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    especificaciones: Optional[dict] = None
    proveedor_id: Optional[int] = None
    fecha_compra: Optional[date] = None
    costo_compra: Optional[float] = None
    fecha_garantia_fin: Optional[date] = None
    ubicacion_actual_id: Optional[int] = None
    estado_operativo: str = "operativo"
    notas: Optional[str] = None

@app.get("/health")
async def health():
    return {"status": "healthy_mysql"}

@app.get("/equipos")
async def get_equipos(categoria: Optional[str] = None, estado: Optional[str] = None):
    pool = await get_db_pool()
    query = """
        SELECT e.*, c.nombre as categoria_nombre,
        CONCAT(u.edificio, ' - ', u.aula_oficina) as ubicacion_nombre,
        p.razon_social as proveedor_nombre
        FROM equipos e
        LEFT JOIN categorias_equipos c ON e.categoria_id = c.id
        LEFT JOIN ubicaciones u ON e.ubicacion_actual_id = u.id
        LEFT JOIN proveedores p ON e.proveedor_id = p.id
        WHERE 1=1
    """
    params = []
    if categoria:
        query += " AND c.nombre = %s"
        params.append(categoria)
    if estado:
        query += " AND e.estado_operativo = %s"
        params.append(estado)
    
    query += " ORDER BY e.fecha_registro DESC"
    
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, tuple(params))
            result = await cur.fetchall()
            return result

@app.post("/equipos")
async def create_equipo(eq: EquipoCreate):
    pool = await get_db_pool()
    specs_json = json.dumps(eq.especificaciones) if eq.especificaciones else None
    
    query = """
        INSERT INTO equipos (
        codigo_inventario, categoria_id, nombre, marca, modelo, numero_serie,
        especificaciones, proveedor_id, fecha_compra, costo_compra,
        fecha_garantia_fin, ubicacion_actual_id, estado_operativo, notas
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        eq.codigo_inventario, eq.categoria_id, eq.nombre, eq.marca, eq.modelo,
        eq.numero_serie, specs_json, eq.proveedor_id, eq.fecha_compra,
        eq.costo_compra, eq.fecha_garantia_fin, eq.ubicacion_actual_id,
        eq.estado_operativo, eq.notas
    )
    
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute(query, values)
                equipo_id = cur.lastrowid
                return {"id": equipo_id, "message": "Equipo creado"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

@app.get("/categorias")
async def get_categorias():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM categorias_equipos ORDER BY nombre")
            return await cur.fetchall()

@app.get("/ubicaciones")
async def get_ubicaciones():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT *, CONCAT(edificio, ' - ', aula_oficina) as nombre_completo FROM ubicaciones WHERE activo = 1")
            return await cur.fetchall()