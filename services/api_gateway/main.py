from fastapi import FastAPI, Request, HTTPException, Response
import httpx
import os

app = FastAPI(title="API Gateway - Sistema TI")

# Definir URLs de los microservicios
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

@app.api_route("/api/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway_proxy(service_name: str, path: str, request: Request):
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Servicio '{service_name}' no encontrado")
    
    target_url = f"{SERVICES[service_name]}/{path}"
    
    async with httpx.AsyncClient() as client:
        try:
            # Reenviar el cuerpo de la petición original
            body = await request.body()
            
            # Petición al microservicio
            upstream_response = await client.request(
                method=request.method,
                url=target_url,
                headers=request.headers,
                params=request.query_params,
                content=body,
                timeout=30.0
            )
            
            # --- CORRECCIÓN CLAVE ---
            # Devolvemos la respuesta cruda (bytes) y el tipo de contenido correcto
            # Esto permite pasar JSONs y también Archivos (PDFs)
            return Response(
                content=upstream_response.content,
                status_code=upstream_response.status_code,
                media_type=upstream_response.headers.get("content-type")
            )
            
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail=f"El servicio {service_name} no está disponible")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gateway Error: {str(e)}")