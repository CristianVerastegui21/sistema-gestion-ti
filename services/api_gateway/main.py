from fastapi import FastAPI, Request, HTTPException
import httpx
import os

app = FastAPI(title="API Gateway - Sistema TI")

# Definir URLs de los microservicios (nombres de host de Docker)
SERVICES = {
    "equipos": os.getenv("EQUIPOS_SERVICE_URL", "http://equipos-service:8000"),
    "proveedores": os.getenv("PROVEEDORES_SERVICE_URL", "http://proveedores-service:8000"),
    "mantenimientos": os.getenv("MANTENIMIENTO_SERVICE_URL", "http://mantenimiento-service:8000"),
    "reportes": os.getenv("REPORTES_SERVICE_URL", "http://reportes-service:8000"),
    "agents": os.getenv("AGENT_SERVICE_URL", "http://agent-service:8000"),
}

@app.get("/")
async def root():
    return {"message": "API Gateway Funcionando"}

@app.get("/health")
async def health_check():
    return {"status": "gateway_active"}

# Proxy genérico para redirigir tráfico
@app.api_route("/api/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway_proxy(service_name: str, path: str, request: Request):
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Servicio '{service_name}' no encontrado")
    
    target_url = f"{SERVICES[service_name]}/{path}"
    
    # Manejar Query Params
    params = dict(request.query_params)
    
    async with httpx.AsyncClient() as client:
        try:
            # Leer el cuerpo si existe
            body = await request.body()
            
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=request.headers,
                params=params,
                content=body,
                timeout=30.0
            )
            return response.json()
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail=f"El servicio {service_name} no está disponible")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))