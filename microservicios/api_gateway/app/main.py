"""
API Gateway - PATRON FACADE + PROXY + MVC
Proporciona una interfaz unificada para todos los microservicios
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import httpx
import logging
from datetime import datetime
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PATRON MVC - Controller principal
app = FastAPI(
    title="API Gateway - POS Core",
    description="Gateway unificado para microservicios POS Core",
    version="1.0.0"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PATRON STRATEGY: Esquema de autenticación
security = HTTPBearer()

# PATRON SINGLETON: Configuración centralizada de servicios
SERVICIOS = {
    "auth": "http://servicio_autenticacion:8001",
    "inventario": "http://servicio_inventario:8000", 
    "productos": "http://servicio_productos:8002",
    "ventas": "http://servicio_ventas:8003",
    "reportes": "http://servicio_reportes:8004",
    "impresion": "http://servicio_impresion:8006"
}

# PATRON STRATEGY: Servicio de validación de tokens
class ServicioAutenticacion:
    """Strategy para validación de tokens JWT"""
    
    @staticmethod
    async def validar_token(token: str) -> Optional[dict]:
        """Valida un token JWT con el servicio de autenticación"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{SERVICIOS['auth']}/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            logger.error(f"Error validando token: {e}")
            return None

# PATRON DEPENDENCY INJECTION
async def obtener_usuario_actual(credentials: HTTPBearer = Depends(security)):
    """Dependency Injection: Obtiene usuario actual del token"""
    token = credentials.credentials
    usuario = await ServicioAutenticacion.validar_token(token)
    if not usuario:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return usuario

# PATRON FACADE: Endpoints principales
@app.get("/")
async def raiz():
    """Endpoint raíz del API Gateway"""
    return {
        "servicio": "API Gateway POS Core",
        "estado": "Funcionando",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "microservicios": list(SERVICIOS.keys())
    }

@app.get("/health")
async def salud():
    """Health check del gateway y servicios dependientes"""
    servicios_status = {}
    
    # Verificar estado de cada microservicio
    for nombre, url in SERVICIOS.items():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health", timeout=5.0)
                servicios_status[nombre] = {
                    "estado": "saludable" if response.status_code == 200 else "error",
                    "status_code": response.status_code
                }
        except Exception as e:
            servicios_status[nombre] = {
                "estado": "no disponible",
                "error": str(e)
            }
    
    return {
        "estado": "saludable",
        "servicio": "API Gateway", 
        "timestamp": datetime.now().isoformat(),
        "servicios": servicios_status
    }

@app.get("/api/health")
async def health_completo():
    """Health check extendido para todos los servicios"""
    return await salud()

# PATRON PROXY: Routing dinámico a microservicios
@app.api_route("/api/{servicio}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(
    servicio: str,
    path: str, 
    request: Request,
    usuario: dict = Depends(obtener_usuario_actual)
):
    """
    PATRON PROXY + FACADE: 
    - PROXY: Reenvía requests a los microservicios
    - FACADE: Oculta la complejidad del sistema backend
    """
    
    # Validar que el servicio existe
    if servicio not in SERVICIOS:
        raise HTTPException(
            status_code=404, 
            detail=f"Servicio '{servicio}' no encontrado. Servicios disponibles: {list(SERVICIOS.keys())}"
        )
    
    # Construir URL destino
    url_destino = f"{SERVICIOS[servicio]}/{path}"
    
    # PATRON ADAPTER: Preparar headers para el reenvío
    headers = {}
    for key, value in request.headers.items():
        # Filtrar headers que no deben reenviarse
        if key.lower() not in ["host", "content-length"]:
            headers[key] = value
    
    # Mantener la autenticación
    if "authorization" in request.headers:
        headers["authorization"] = request.headers["authorization"]
    
    # Agregar headers de trazabilidad
    headers["x-user-id"] = usuario.get("id", "unknown")
    headers["x-user-email"] = usuario.get("email", "unknown")
    
    logger.info(f"Proxying {request.method} {servicio}/{path} para usuario {usuario.get('email')}")
    
    # PATRON PROXY: Reenviar request al microservicio
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=url_destino,
                headers=headers,
                params=dict(request.query_params),
                content=await request.body(),
                timeout=30.0  # Timeout para evitar bloqueos
            )
            
            # PATRON ADAPTER: Adaptar respuesta
            if response.status_code >= 400:
                logger.warning(f"Error {response.status_code} from {servicio}: {response.text}")
            
            return JSONResponse(
                content=response.json() if response.content else {},
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except httpx.ConnectError:
            logger.error(f"No se pudo conectar con el servicio: {servicio}")
            raise HTTPException(
                status_code=503, 
                detail=f"Servicio {servicio} no disponible temporalmente"
            )
        except httpx.TimeoutException:
            logger.error(f"Timeout al conectar con: {servicio}")
            raise HTTPException(
                status_code=504,
                detail=f"Timeout del servicio {servicio}"
            )
        except Exception as e:
            logger.error(f"Error interno comunicando con {servicio}: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error interno del servidor: {str(e)}"
            )

# Rutas públicas (sin autenticación)
@app.post("/api/auth/login")
async def login_proxy(request: Request):
    """Proxy para login - ruta pública"""
    return await proxy_request_publico("auth", "api/v1/auth/login", request)

@app.post("/api/auth/registro") 
async def registro_proxy(request: Request):
    """Proxy para registro - ruta pública"""
    return await proxy_request_publico("auth", "api/v1/auth/registro", request)

async def proxy_request_publico(servicio: str, path: str, request: Request):
    """PATRON PROXY: Para rutas públicas sin autenticación"""
    if servicio not in SERVICIOS:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    
    url_destino = f"{SERVICIOS[servicio]}/{path}"
    
    headers = {}
    for key, value in request.headers.items():
        if key.lower() not in ["host", "content-length"]:
            headers[key] = value
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=url_destino,
                headers=headers,
                params=dict(request.query_params),
                content=await request.body(),
                timeout=30.0
            )
            
            return JSONResponse(
                content=response.json() if response.content else {},
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Servicio no disponible")
        except Exception as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)