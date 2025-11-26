from typing import Dict, Any
import httpx

class ServicioFactory:
    @staticmethod
    def crear_servicio(tipo: str, config: Dict[str, Any]):
        if tipo == "autenticacion":
            return ServicioAutenticacion(config)
        elif tipo == "inventario":
            return ServicioInventario(config)
        elif tipo == "ventas":
            return ServicioVentas(config)
        elif tipo == "reportes":
            return ServicioReportes(config)
        else:
            raise ValueError(f"Tipo de servicio no soportado: {tipo}")

class ServicioBase:
    def __init__(self, config):
        self.url_base = config['url']
        self.timeout = config.get('timeout', 30.0)
    
    async def health_check(self):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.url_base}/salud", timeout=5.0)
                return response.status_code == 200
            except:
                return False

class ServicioAutenticacion(ServicioBase):
    async def registrar_usuario(self, datos_usuario):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url_base}/api/v1/registrar",
                json=datos_usuario,
                timeout=self.timeout
            )
            return response.json()
    
    async def login(self, credenciales):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url_base}/api/v1/login",
                json=credenciales,
                timeout=self.timeout
            )
            return response.json()

class ServicioInventario(ServicioBase):
    async def crear_producto(self, datos_producto, token):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url_base}/api/v1/productos",
                json=datos_producto,
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout
            )
            return response.json()
    
    async def listar_productos(self, token):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.url_base}/api/v1/productos",
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout
            )
            return response.json()

class ServicioVentas(ServicioBase):
    async def crear_venta(self, datos_venta, token):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url_base}/api/v1/ventas",
                json=datos_venta,
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout
            )
            return response.json()
    
    async def listar_ventas(self, token):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.url_base}/api/v1/ventas",
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout
            )
            return response.json()

class ServicioReportes(ServicioBase):
    async def generar_reporte(self, parametros_reporte, token):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url_base}/api/v1/reportes/generar",
                json=parametros_reporte,
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout
            )
            return response.json()
    
    async def obtener_tipos_reportes(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.url_base}/api/v1/reportes/tipos",
                timeout=self.timeout
            )
            return response.json()