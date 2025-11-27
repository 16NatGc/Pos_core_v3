"""
Configuración del servicio de ventas - PATRON SINGLETON
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
        self.COLECCION_VENTAS = "ventas"
        self.PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://servicio_productos:8002")
        self.INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://servicio_inventario:8000")

configuration = Configuration()