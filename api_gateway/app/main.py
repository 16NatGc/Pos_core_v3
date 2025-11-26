# puerta_de_enlace_api/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="API Gateway POS Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICES = {
    "auth": "http://servicio_autenticacion:8000",
    "products": "http://servicio_productos:8000", 
    "sales": "http://servicio_ventas:8000",
    "inventory": "http://servicio_inventario:8000",
    "reports": "http://servicio_reportes:8000",
    "print": "http://servicio_impresion:8000"
}

@app.api_route("/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(service_name: str, path: str, request: Request):
    if service_name not in SERVICES:
        raise HTTPException(404, "Servicio no encontrado")
    
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=f"{SERVICES[service_name]}/{path}",
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=await request.body()
        )
        
    return JSONResponse(content=response.json(), status_code=response.status_code)