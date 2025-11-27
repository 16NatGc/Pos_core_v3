"""
Repositorio de ventas - PATRON REPOSITORY
"""

from pymongo import MongoClient
from bson import ObjectId
from configuracion import configuration

class VentaRepository:
    """Repository Pattern: Abstrae operaciones de ventas en MongoDB"""
    
    def __init__(self, database):
        self.collection = database[configuration.COLECCION_VENTAS]
    
    async def crear(self, venta_data: dict) -> str:
        result = self.collection.insert_one(venta_data)
        return str(result.inserted_id)
    
    async def obtener_por_id(self, venta_id: str):
        if not ObjectId.is_valid(venta_id):
            return None
        return self.collection.find_one({"_id": ObjectId(venta_id)})
    
    async def listar_todas(self, skip: int = 0, limit: int = 10):
        cursor = self.collection.find().sort("fecha_creacion", -1).skip(skip).limit(limit)
        return list(cursor)
    
    async def obtener_por_fecha(self, fecha_inicio, fecha_fin):
        cursor = self.collection.find({
            "fecha_creacion": {
                "$gte": fecha_inicio,
                "$lte": fecha_fin
            }
        })
        return list(cursor)