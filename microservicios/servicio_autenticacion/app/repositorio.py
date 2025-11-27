"""
Repositorio de usuarios - PATRON REPOSITORY
"""

from pymongo import MongoClient
from bson import ObjectId
from configuracion import configuration

class UsuarioRepository:
    """Repository Pattern: Abstrae el acceso a datos de usuarios"""
    
    def __init__(self, database):
        self.collection = database[configuration.COLECCION_USUARIOS]
    
    async def crear(self, usuario_data: dict) -> str:
        result = self.collection.insert_one(usuario_data)
        return str(result.inserted_id)
    
    async def obtener_por_id(self, usuario_id: str):
        if not ObjectId.is_valid(usuario_id):
            return None
        return self.collection.find_one({"_id": ObjectId(usuario_id)})
    
    async def obtener_por_email(self, email: str):
        return self.collection.find_one({"email": email})
    
    async def actualizar(self, usuario_id: str, datos_actualizacion: dict) -> bool:
        if not ObjectId.is_valid(usuario_id):
            return False
        result = self.collection.update_one(
            {"_id": ObjectId(usuario_id)},
            {"$set": datos_actualizacion}
        )
        return result.modified_count > 0