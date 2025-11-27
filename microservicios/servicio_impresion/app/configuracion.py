"""
Configuración del servicio de impresión - PATRON SINGLETON
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
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

configuration = Configuration()