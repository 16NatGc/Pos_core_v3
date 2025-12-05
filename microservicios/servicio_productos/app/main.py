"""
Servicio de Productos - PATRON MVC + DAO + Repository + Factory + Adapter + Service Layer
"""

from fastapi import FastAPI, HTTPException, Depends, status, Query
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
from configuracion import configuration
from modelos import Producto, ProductoCrear, ProductoActualizar
from repositorio import ProductoRepository
from dao.producto_dao import ProductoDAO, DAOError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PATRON MVC - Controller principal
app = FastAPI(
    title="Servicio de Productos - POS Core",
    description="Microservicio para gestión de catálogo de productos con DAO Pattern",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ==============================
# PATRON FACTORY + DEPENDENCY INJECTION
# ==============================

def get_database():
    """PATRON FACTORY METHOD: Crea conexión a MongoDB"""
    try:
        client = MongoClient(configuration.MONGODB_URL)
        database = client[configuration.BASE_DATOS]
        client.admin.command('ping')
        logger.info("Conexión a MongoDB establecida correctamente")
        return database
    except Exception as e:
        logger.error(f"Error conectando a MongoDB: {e}")
        raise

def get_producto_repository():
    """PATRON FACTORY: Crea instancia del repositorio"""
    database = get_database()
    return ProductoRepository(database)

def get_producto_dao():
    """PATRON FACTORY: Crea instancia del DAO"""
    database = get_database()
    return ProductoDAO(database)

# ==============================
# PATRON SERVICE LAYER con DAO + Repository
# ==============================

class ProductoService:
    """Service Layer: Contiene la lógica de negocio de productos"""
    
    def __init__(self, repository: ProductoRepository, dao: ProductoDAO):
        self.repository = repository
        self.dao = dao
    
    async def crear_producto(self, producto: ProductoCrear) -> dict:
        """PATRON FACTORY + DAO: Crea nuevo producto con validaciones"""
        # Validar SKU único usando DAO
        producto_existente = await self.dao.obtener_por_codigo(producto.sku)
        if producto_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un producto con este SKU"
            )
        
        producto_data = producto.dict()
        producto_data["codigo"] = producto_data.pop("sku")
        producto_data["stock"] = producto_data.pop("stock_inicial", 0)
        producto_data["fecha_creacion"] = datetime.now()
        producto_data["fecha_actualizacion"] = datetime.now()
        producto_data["activo"] = True
        
        # Usar DAO para crear el producto
        try:
            producto_creado = await self.dao.crear(producto_data)
            logger.info(f"Producto creado exitosamente: {producto_data['codigo']}")
            return self._adaptar_producto(producto_creado)
        except DAOError as e:
            logger.error(f"Error DAO al crear producto: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear producto: {str(e)}"
            )
    
    async def obtener_producto(self, producto_id: str) -> dict:
        """Obtiene producto por ID usando DAO"""
        try:
            producto = await self.dao.obtener_por_id(producto_id)
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
        except DAOError as e:
            logger.error(f"Error DAO al obtener producto: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener producto: {str(e)}"
            )
    
    async def listar_productos(self, categoria: Optional[str] = None, 
                              skip: int = 0, limit: int = 10) -> List[dict]:
        """Lista productos con filtros opcionales usando DAO"""
        filtro = {"activo": True}
        if categoria:
            filtro["categoria"] = categoria
        
        # Usar DAO con paginación
        try:
            resultado = await self.dao.obtener_todos(filtro, skip, limit)
            productos = resultado.get("productos", [])
            return [self._adaptar_producto(prod) for prod in productos]
        except DAOError as e:
            logger.error(f"Error DAO al listar productos: {e}")
            return []
    
    async def actualizar_producto(self, producto_id: str, 
                                 producto_actualizar: ProductoActualizar) -> dict:
        """Actualiza producto existente usando DAO"""
        # Verificar que existe
        producto = await self.dao.obtener_por_id(producto_id)
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        # Preparar datos de actualización
        datos_actualizacion = {k: v for k, v in producto_actualizar.dict().items() 
                              if v is not None}
        
        # Si se actualiza el SKU, verificar que no exista
        if 'sku' in datos_actualizacion:
            producto_existente = await self.dao.obtener_por_codigo(datos_actualizacion['sku'])
            if producto_existente and str(producto_existente.get('id')) != producto_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un producto con este SKU"
                )
            datos_actualizacion['codigo'] = datos_actualizacion.pop('sku')
        
        try:
            actualizado = await self.dao.actualizar(producto_id, datos_actualizacion)
            if not actualizado:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se pudo actualizar el producto"
                )
            
            producto_actualizado = await self.dao.obtener_por_id(producto_id)
            return self._adaptar_producto(producto_actualizado)
        except DAOError as e:
            logger.error(f"Error DAO al actualizar producto: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al actualizar producto: {str(e)}"
            )
    
    async def eliminar_producto(self, producto_id: str):
        """Elimina producto (borrado lógico) usando DAO"""
        producto = await self.dao.obtener_por_id(producto_id)
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        try:
            eliminado = await self.dao.eliminar(producto_id)
            if not eliminado:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se pudo eliminar el producto"
                )
        except DAOError as e:
            logger.error(f"Error DAO al eliminar producto: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al eliminar producto: {str(e)}"
            )
    
    async def obtener_productos_bajo_stock(self, limite: int = 10) -> List[dict]:
        """PATRON DAO: Obtiene productos con stock bajo usando DAO"""
        try:
            productos = await self.dao.obtener_productos_bajo_stock(limite)
            return [self._adaptar_producto(prod) for prod in productos]
        except DAOError as e:
            logger.error(f"Error DAO al obtener productos bajo stock: {e}")
            return []
    
    async def buscar_productos(self, consulta: str) -> List[dict]:
        """PATRON DAO: Busca productos por texto usando DAO"""
        try:
            productos = await self.dao.buscar(consulta, campo="nombre")
            return [self._adaptar_producto(prod) for prod in productos]
        except DAOError as e:
            logger.error(f"Error DAO al buscar productos: {e}")
            return []
    
    async def actualizar_stock(self, producto_id: str, cantidad: int) -> dict:
        """Actualiza stock usando DAO"""
        try:
            producto_actualizado = await self.dao.actualizar_stock(producto_id, cantidad)
            if not producto_actualizado:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Producto no encontrado"
                )
            return self._adaptar_producto(producto_actualizado)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except DAOError as e:
            logger.error(f"Error DAO al actualizar stock: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al actualizar stock: {str(e)}"
            )
    
    def _adaptar_producto(self, producto_db: dict) -> dict:
        """PATRON ADAPTER: Convierte producto de BD a formato API"""
        if not producto_db:
            return None
        producto_adaptado = producto_db.copy()
        # El DAO ya convierte _id a id, pero asegurar
        if '_id' in producto_adaptado:
            producto_adaptado['id'] = str(producto_adaptado['_id'])
            del producto_adaptado['_id']
        elif 'id' not in producto_adaptado:
            producto_adaptado['id'] = producto_db.get('_id')
        return producto_adaptado

def get_producto_service() -> ProductoService:
    """PATRON DEPENDENCY INJECTION: Proporciona instancia del servicio con DAO"""
    repository = get_producto_repository()
    dao = get_producto_dao()
    return ProductoService(repository, dao)

# ==============================
# PATRON MVC - Endpoints Controller
# ==============================

@app.get("/")
async def raiz():
    return {
        "servicio": "Productos POS Core",
        "estado": "Funcionando",
        "version": "2.0.0",
        "patrones": ["MVC", "DAO", "Repository", "Factory", "Adapter", "Service Layer", "Dependency Injection"],
        "descripcion": "Microservicio de productos con DAO Pattern implementado",
        "endpoints": {
            "productos": "/api/v1/productos",
            "producto_especifico": "/api/v1/productos/{id}",
            "bajo_stock": "/api/v1/productos/inventario/bajo-stock",
            "buscar": "/api/v1/productos/buscar/{consulta}",
            "actualizar_stock": "/api/v1/productos/{id}/stock"
        }
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
        "timestamp": datetime.now().isoformat(),
        "patrones_activos": ["DAO", "Repository", "Service Layer", "Factory", "Adapter"],
        "dao_operaciones": [
            "crear", "obtener_por_id", "obtener_todos", "actualizar",
            "eliminar", "obtener_por_codigo", "obtener_productos_bajo_stock",
            "buscar", "actualizar_stock"
        ]
    }

@app.post("/api/v1/productos", response_model=Producto, status_code=status.HTTP_201_CREATED)
async def crear_producto(
    producto: ProductoCrear,
    producto_service: ProductoService = Depends(get_producto_service)
):
    """PATRON MVC - Controller: Endpoint para crear producto usando DAO"""
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
    categoria: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    producto_service: ProductoService = Depends(get_producto_service)
):
    """PATRON MVC - Controller: Endpoint para listar productos usando DAO"""
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
    """PATRON MVC - Controller: Endpoint para obtener producto usando DAO"""
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
    """PATRON MVC - Controller: Endpoint para actualizar producto usando DAO"""
    try:
        producto_actualizado = await producto_service.actualizar_producto(
            producto_id, producto_actualizar
        )
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
    """PATRON MVC - Controller: Endpoint para eliminar producto usando DAO"""
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

@app.get("/api/v1/productos/inventario/bajo-stock")
async def obtener_bajo_stock(
    limite: int = Query(10, ge=1, description="Límite de stock para alerta"),
    producto_service: ProductoService = Depends(get_producto_service)
):
    """Endpoint para obtener productos con stock bajo (DAO Pattern)"""
    try:
        productos = await producto_service.obtener_productos_bajo_stock(limite)
        return {
            "productos": [Producto(**prod) for prod in productos],
            "total": len(productos),
            "limite": limite,
            "alerta": len(productos) > 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo productos bajo stock: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.get("/api/v1/productos/buscar/{consulta}")
async def buscar_productos(
    consulta: str,
    producto_service: ProductoService = Depends(get_producto_service)
):
    """Endpoint para buscar productos por texto (DAO Pattern)"""
    try:
        productos = await producto_service.buscar_productos(consulta)
        return {
            "productos": [Producto(**prod) for prod in productos],
            "total": len(productos),
            "consulta": consulta,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error buscando productos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.post("/api/v1/productos/{producto_id}/stock")
async def actualizar_stock(
    producto_id: str,
    cantidad: int = Query(..., description="Cantidad a ajustar (positivo o negativo)"),
    producto_service: ProductoService = Depends(get_producto_service)
):
    """Endpoint para actualizar stock de producto (DAO Pattern)"""
    try:
        producto_actualizado = await producto_service.actualizar_stock(producto_id, cantidad)
        return {
            "mensaje": f"Stock actualizado: {cantidad} unidades",
            "producto": Producto(**producto_actualizado),
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando stock: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.get("/api/v1/patrones")
async def listar_patrones():
    """Endpoint para listar patrones implementados en este servicio"""
    return {
        "servicio": "Productos",
        "patrones_implementados": [
            {
                "nombre": "DAO Pattern",
                "ubicacion": "app/dao/producto_dao.py",
                "descripcion": "Data Access Object para abstraer operaciones de base de datos",
                "beneficios": ["Separación de responsabilidades", "Facilita testing", "Permite cambiar fuente de datos"]
            },
            {
                "nombre": "MVC Pattern",
                "ubicacion": "main.py (Controller)",
                "descripcion": "Model-View-Controller para separar lógica de presentación",
                "beneficios": ["Organización clara", "Mantenibilidad", "Separación de concerns"]
            },
            {
                "nombre": "Repository Pattern",
                "ubicacion": "app/repositorio.py",
                "descripcion": "Abstracción para acceso a datos de productos",
                "beneficios": ["Encapsulamiento", "Reusabilidad", "Consistencia"]
            },
            {
                "nombre": "Factory Pattern",
                "ubicacion": "main.py (funciones get_*)",
                "descripcion": "Creación de instancias de servicios y repositorios",
                "beneficios": ["Centralización", "Flexibilidad", "Control de instancias"]
            },
            {
                "nombre": "Adapter Pattern",
                "ubicacion": "ProductoService._adaptar_producto()",
                "descripcion": "Adapta datos de MongoDB a formato de API",
                "beneficios": ["Compatibilidad", "Separación", "Mantenibilidad"]
            },
            {
                "nombre": "Service Layer Pattern",
                "ubicacion": "ProductoService class",
                "descripcion": "Capa de servicio para lógica de negocio",
                "beneficios": ["Reusabilidad", "Testabilidad", "Separación"]
            },
            {
                "nombre": "Dependency Injection",
                "ubicacion": "FastAPI Depends()",
                "descripcion": "Inyección de dependencias para desacoplamiento",
                "beneficios": ["Testabilidad", "Flexibilidad", "Mantenibilidad"]
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)