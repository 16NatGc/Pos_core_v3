"""
Repositorio de productos - PATRON REPOSITORY
"""

from pymongo import MongoClient
from bson import ObjectId
from configuracion import configuration

class ProductoRepository:
    """Repository Pattern: Abstrae el acceso a datos de productos"""
    
    def __init__(self, database):
        self.collection = database[configuration.COLECCION_PRODUCTOS]
    
    async def crear(self, producto_data: dict) -> str:
        result = self.collection.insert_one(producto_data)
        return str(result.inserted_id)
    
    async def obtener_por_id(self, producto_id: str):
        if not ObjectId.is_valid(producto_id):
            return None
        return self.collection.find_one({"_id": ObjectId(producto_id)})
    
    async def obtener_por_sku(self, sku: str):
        return self.collection.find_one({"sku": sku})
    
    async def listar_todos(self, filtro: dict = None, skip: int = 0, limit: int = 10):
        if filtro is None:
            filtro = {}
        cursor = self.collection.find(filtro).skip(skip).limit(limit)
        return list(cursor)
    
    async def actualizar(self, producto_id: str, datos_actualizacion: dict) -> bool:
        if not ObjectId.is_valid(producto_id):
            return False
        datos_actualizacion["fecha_actualizacion"] = datetime.now()
        result = self.collection.update_one(
            {"_id": ObjectId(producto_id)},
            {"$set": datos_actualizacion}
        )
        return result.modified_count > 0
    
    async def eliminar(self, producto_id: str) -> bool:
        if not ObjectId.is_valid(producto_id):
            return False
        result = self.collection.update_one(
            {"_id": ObjectId(producto_id)},
            {"$set": {"activo": False, "fecha_actualizacion": datetime.now()}}
        )
        return result.modified_count > 0