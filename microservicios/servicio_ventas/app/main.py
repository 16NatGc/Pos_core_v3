"""
Servicio de Ventas - PATRON MVC + GOF
"""

from fastapi import FastAPI, HTTPException, Depends, status, Header
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from typing import List
import logging
from configuracion import configuration
from modelos import VentaCrear, Venta, VentaResponse, EstadoVenta
from servicios import ProductoService, InventarioService
from repositorio import VentaRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PATRON MVC - Controller principal
app = FastAPI(
    title="Servicio de Ventas - POS Core",
    description="Microservicio para gestión de ventas",
    version="1.0.0"
)

# PATRON DEPENDENCY INJECTION
def get_database():
    client = MongoClient(configuration.MONGODB_URL)
    return client[configuration.BASE_DATOS]

def get_venta_repository():
    db = get_database()
    return VentaRepository(db)

def obtener_token_autorizacion(authorization: str = Header(None)):
    """PATRON STRATEGY: Extrae token de autorización"""
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ")[1]
    return None

@app.get("/")
async def raiz():
    return {
        "servicio": "Ventas POS Core",
        "estado": "Funcionando",
        "version": "1.0.0"
    }

@app.get("/health")
async def salud():
    return {
        "estado": "Saludable",
        "servicio": "Ventas",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/ventas", response_model=VentaResponse, status_code=status.HTTP_201_CREATED)
async def crear_venta(
    venta: VentaCrear,
    authorization: str = Header(None),
    repo: VentaRepository = Depends(get_venta_repository)
):
    """PATRON MVC - Controller: Endpoint para crear venta"""
    token = obtener_token_autorizacion(authorization)
    
    # Validar productos y stock - PATRON FACADE: interfaz simple para validación compleja
    for item in venta.items:
        producto = await ProductoService.obtener_producto(item.producto_id, token)
        if not producto:
            raise HTTPException(
                status_code=400,
                detail=f"Producto {item.producto_id} no encontrado"
            )
        
        if producto["stock"] < item.cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {producto['nombre']}"
            )
    
    # PATRON FACTORY: Crear venta
    venta_data = venta.dict()
    venta_data["fecha_creacion"] = datetime.now()
    venta_data["vendedor"] = "Sistema"  # En producción, obtener del token
    venta_data["estado"] = EstadoVenta.COMPLETADA
    
    venta_id = await repo.crear(venta_data)
    venta_creada = await repo.obtener_por_id(venta_id)
    
    # Actualizar inventario - PATRON ADAPTER: comunicación con otros servicios
    for item in venta.items:
        success = await InventarioService.actualizar_stock(
            item.producto_id, 
            item.cantidad, 
            token
        )
        if not success:
            logger.warning(f"No se pudo actualizar stock para producto {item.producto_id}")
    
    return VentaResponse(
        venta=Venta(**venta_creada),
        mensaje="Venta procesada exitosamente"
    )

@app.get("/api/v1/ventas", response_model=List[Venta])
async def listar_ventas(
    skip: int = 0,
    limit: int = 10,
    repo: VentaRepository = Depends(get_venta_repository)
):
    """PATRON MVC - Controller: Endpoint para listar ventas"""
    ventas = await repo.listar_todas(skip, limit)
    return [Venta(**venta) for venta in ventas]

@app.get("/api/v1/ventas/{venta_id}", response_model=Venta)
async def obtener_venta(
    venta_id: str,
    repo: VentaRepository = Depends(get_venta_repository)
):
    """PATRON MVC - Controller: Endpoint para obtener venta específica"""
    venta = await repo.obtener_por_id(venta_id)
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return Venta(**venta)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)