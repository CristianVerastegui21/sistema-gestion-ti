from fastapi import FastAPI
import aiomysql
import os

app = FastAPI(title="Agent Service")

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql'),
    'user': os.getenv('DB_USER', 'user_ti'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'db': os.getenv('DB_NAME', 'ti_management'),
    'port': 3306,
    'autocommit': True,
    'charset': 'utf8mb4'
}

@app.post("/run-all-agents")
async def run_agents():
    # Lógica simplificada para MySQL
    return {"message": "Agentes ejecutados"}

@app.get("/notificaciones")
async def notificaciones(leida: int = 0):
    # MySQL usa 1/0 para booleanos
    pool = await aiomysql.create_pool(**DB_CONFIG)
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM notificaciones WHERE leida = %s ORDER BY id DESC LIMIT 10", (leida,))
            return await cur.fetchall()