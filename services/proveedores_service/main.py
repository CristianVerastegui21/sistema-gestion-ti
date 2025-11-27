from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import aiomysql
import os

app = FastAPI(title="Proveedores Service")

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql'),
    'user': os.getenv('DB_USER', 'user_ti'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'db': os.getenv('DB_NAME', 'ti_management'),
    'port': 3306,
    'autocommit': True,
    'charset': 'utf8mb4'
}

class ProveedorCreate(BaseModel):
    razon_social: str
    ruc: str
    email: Optional[str] = None
    contacto_nombre: Optional[str] = None
    telefono: Optional[str] = None
    sitio_web: Optional[str] = None

@app.get("/proveedores")
async def get_proveedores():
    pool = await aiomysql.create_pool(**DB_CONFIG)
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM proveedores ORDER BY razon_social")
                return await cur.fetchall()
    finally:
        pool.close()
        await pool.wait_closed()

@app.post("/proveedores")
async def create_proveedor(p: ProveedorCreate):
    pool = await aiomysql.create_pool(**DB_CONFIG)
    query = """
        INSERT INTO proveedores (razon_social, ruc, email, contacto_nombre, telefono, sitio_web)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(query, (p.razon_social, p.ruc, p.email, p.contacto_nombre, p.telefono, p.sitio_web))
                    return {"id": cur.lastrowid, "message": "Proveedor registrado"}
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Error (duplicado?): {e}")
    finally:
        pool.close()
        await pool.wait_closed()