"""
Servicio de Productos - PATRON MVC + GOF
"""

from fastapi import FastAPI, HTTPException, Depends, status
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
import logging
from configuracion import configuration
from modelos import Producto, ProductoCrear, ProductoActualizar
from repositorio import ProductoRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PATRON MVC - Controller principal
app = FastAPI(
    title="Servicio de Productos - POS Core",
    description="Microservicio para gestión de catálogo de productos",
    version="1.0.0"
)

# PATRON DEPENDENCY INJECTION
def get_database():
    """PATRON FACTORY METHOD: Crea conexión a MongoDB"""
    try:
        client = MongoClient(configuration.MONGODB_URL)
        database = client[configuration.BASE_DATOS]
        collection = database[configuration.COLECCION_PRODUCTOS]
        client.admin.command('ping')
        logger.info("Conexión a MongoDB establecida correctamente")
        return collection
    except Exception as e:
        logger.error(f"Error conectando a MongoDB: {e}")
        raise

def get_producto_repository():
    """PATRON FACTORY: Crea instancia del repositorio"""
    database = get_database()
    return ProductoRepository(database)

# PATTERN SERVICE LAYER
class ProductoService:
    """Service Layer: Contiene la lógica de negocio de productos"""
    
    def __init__(self, repository: ProductoRepository):
        self.repository = repository
    
    async def crear_producto(self, producto: ProductoCrear) -> dict:
        """PATRON FACTORY: Crea nuevo producto con validaciones"""
        # Validar SKU único
        producto_existente = await self.repository.obtener_por_sku(producto.sku)
        if producto_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un producto con este SKU"
            )
        
        producto_data = producto.dict()
        producto_data["stock"] = producto_data.pop("stock_inicial")
        producto_data["fecha_creacion"] = datetime.now()
        producto_data["fecha_actualizacion"] = datetime.now()
        producto_data["activo"] = True
        
        producto_id = await self.repository.crear(producto_data)
        producto_creado = await self.repository.obtener_por_id(producto_id)
        
        return self._adaptar_producto(producto_creado)
    
    async def obtener_producto(self, producto_id: str) -> dict:
        """Obtiene producto por ID"""
        producto = await self.repository.obtener_por_id(producto_id)
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        if not producto.get("activo", True):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no disponible"
            )
        return self._adaptar_producto(producto)
    
    async def listar_productos(self, categoria: Optional[str] = None, skip: int = 0, limit: int = 10) -> List[dict]:
        """Lista productos con filtros opcionales"""
        filtro = {"activo": True}
        if categoria:
            filtro["categoria"] = categoria
        
        productos = await self.repository.listar_todos(filtro, skip, limit)
        return [self._adaptar_producto(prod) for prod in productos]
    
    async def actualizar_producto(self, producto_id: str, producto_actualizar: ProductoActualizar) -> dict:
        """Actualiza producto existente"""
        producto = await self.repository.obtener_por_id(producto_id)
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        datos_actualizacion = {k: v for k, v in producto_actualizar.dict().items() if v is not None}
        
        actualizado = await self.repository.actualizar(producto_id, datos_actualizacion)
        if not actualizado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo actualizar el producto"
            )
        
        producto_actualizado = await self.repository.obtener_por_id(producto_id)
        return self._adaptar_producto(producto_actualizado)
    
    async def eliminar_producto(self, producto_id: str):
        """Elimina producto (borrado lógico)"""
        producto = await self.repository.obtener_por_id(producto_id)
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        eliminado = await self.repository.eliminar(producto_id)
        if not eliminado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo eliminar el producto"
            )
    
    def _adaptar_producto(self, producto_db: dict) -> dict:
        """PATRON ADAPTER: Convierte producto de BD a formato API"""
        if not producto_db:
            return None
        producto_adaptado = producto_db.copy()
        producto_adaptado["id"] = str(producto_adaptado["_id"])
        del producto_adaptado["_id"]
        return producto_adaptado

def get_producto_service() -> ProductoService:
    """PATRON DEPENDENCY INJECTION: Proporciona instancia del servicio"""
    repository = get_producto_repository()
    return ProductoService(repository)

# PATRON MVC - Endpoints Controller
@app.get("/")
async def raiz():
    return {
        "servicio": "Productos POS Core",
        "estado": "Funcionando",
        "version": "1.0.0"
    }

@app.get("/health")
async def salud():
    try:
        client = MongoClient(configuration.MONGODB_URL)
        client.admin.command('ping')
        base_datos_status = "Conectado"
    except Exception as e:
        base_datos_status = f"Error: {str(e)}"
        logger.error(f"Health check falló: {e}")

    return {
        "estado": "Saludable",
        "servicio": "Productos",
        "base_datos": base_datos_status,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/productos", response_model=Producto, status_code=status.HTTP_201_CREATED)
async def crear_producto(
    producto: ProductoCrear,
    producto_service: ProductoService = Depends(get_producto_service)
):
    """PATRON MVC - Controller: Endpoint para crear producto"""
    try:
        producto_creado = await producto_service.crear_producto(producto)
        return Producto(**producto_creado)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando producto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.get("/api/v1/productos", response_model=List[Producto])
async def listar_productos(
    categoria: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    producto_service: ProductoService = Depends(get_producto_service)
):
    """PATRON MVC - Controller: Endpoint para listar productos"""
    try:
        productos = await producto_service.listar_productos(categoria, skip, limit)
        return [Producto(**prod) for prod in productos]
    except Exception as e:
        logger.error(f"Error listando productos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.get("/api/v1/productos/{producto_id}", response_model=Producto)
async def obtener_producto(
    producto_id: str,
    producto_service: ProductoService = Depends(get_producto_service)
):
    """PATRON MVC - Controller: Endpoint para obtener producto"""
    try:
        producto = await producto_service.obtener_producto(producto_id)
        return Producto(**producto)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo producto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.put("/api/v1/productos/{producto_id}", response_model=Producto)
async def actualizar_producto(
    producto_id: str,
    producto_actualizar: ProductoActualizar,
    producto_service: ProductoService = Depends(get_producto_service)
):
    """PATRON MVC - Controller: Endpoint para actualizar producto"""
    try:
        producto_actualizado = await producto_service.actualizar_producto(producto_id, producto_actualizar)
        return Producto(**producto_actualizado)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando producto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.delete("/api/v1/productos/{producto_id}")
async def eliminar_producto(
    producto_id: str,
    producto_service: ProductoService = Depends(get_producto_service)
):
    """PATRON MVC - Controller: Endpoint para eliminar producto"""
    try:
        await producto_service.eliminar_producto(producto_id)
        return {"mensaje": "Producto eliminado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando producto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)