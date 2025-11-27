"""
Servicios externos - PATRON ADAPTER para comunicación entre microservicios
"""

import httpx
from fastapi import HTTPException
from configuracion import configuration

class ProductoService:
    """PATRON ADAPTER: Adapta comunicación con servicio de productos"""
    
    @staticmethod
    async def obtener_producto(producto_id: str, token: str = None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{configuration.PRODUCT_SERVICE_URL}/api/v1/productos/{producto_id}",
                    headers=headers,
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
            except Exception as e:
                print(f"Error obteniendo producto: {e}")
                return None

class InventarioService:
    """PATRON ADAPTER: Adapta comunicación con servicio de inventario"""
    
    @staticmethod
    async def actualizar_stock(producto_id: str, cantidad: int, token: str = None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        async with httpx.AsyncClient() as client:
            try:
                # Obtener producto actual
                producto = await ProductoService.obtener_producto(producto_id, token)
                if not producto:
                    return False
                
                nuevo_stock = producto["stock"] - cantidad
                
                response = await client.put(
                    f"{configuration.INVENTORY_SERVICE_URL}/api/v1/productos/{producto_id}",
                    headers=headers,
                    json={"stock": nuevo_stock},
                    timeout=30.0
                )
                return response.status_code == 200
            except Exception as e:
                print(f"Error actualizando stock: {e}")
                return False