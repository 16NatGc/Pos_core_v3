"""
Configuración del servicio de autenticación
PATRON SINGLETON: Una única instancia de configuración
"""

import os

class Configuration:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Configuration, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:password@mongodb:27017/")
        self.BASE_DATOS = os.getenv("BASE_DATOS", "pos_core")
        self.COLECCION_USUARIOS = "usuarios"
        self.JWT_SECRET = os.getenv("JWT_SECRET", "pos_core_secret_key_2024")
        self.JWT_ALGORITHM = "HS256"

configuration = Configuration()