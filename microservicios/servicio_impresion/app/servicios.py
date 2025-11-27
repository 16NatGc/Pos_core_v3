"""
Servicios de impresión - PATRON COMMAND para trabajos de impresión
"""

import redis
import json
import asyncio
from datetime import datetime
from configuracion import configuration

class ServicioImpresion:
    """PATRON COMMAND: Maneja comandos de impresión en cola"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(configuration.REDIS_URL, decode_responses=True)
    
    def encolar_trabajo(self, tipo: str, datos: dict) -> str:
        """COMMAND: Encuela un trabajo de impresión"""
        trabajo_id = f"impresion_{datetime.now().timestamp()}"
        trabajo = {
            "id": trabajo_id,
            "tipo": tipo,
            "datos": datos,
            "timestamp": datetime.now().isoformat(),
            "estado": "pendiente"
        }
        
        self.redis_client.lpush("cola_impresion", json.dumps(trabajo))
        return trabajo_id
    
    async def procesar_impresion(self, trabajo: dict):
        """COMMAND: Procesa un trabajo de impresión"""
        try:
            # Simular tiempo de impresión
            await asyncio.sleep(2)
            
            # PATRON STRATEGY: Diferentes estrategias según el tipo
            if trabajo["tipo"] == "ticket_venta":
                await self._imprimir_ticket(trabajo["datos"])
            elif trabajo["tipo"] == "reporte":
                await self._imprimir_reporte(trabajo["datos"])
            
            # Marcar como completado
            trabajo["estado"] = "completado"
            self.redis_client.lrem("cola_impresion", 1, json.dumps(trabajo))
            
        except Exception as e:
            print(f"Error en impresión: {e}")
            trabajo["estado"] = "error"
            trabajo["error"] = str(e)
    
    async def _imprimir_ticket(self, datos: dict):
        """STRATEGY: Imprimir ticket de venta"""
        print("=" * 40)
        print("          TICKET DE VENTA")
        print("=" * 40)
        print(f"Cliente: {datos.get('cliente', 'N/A')}")
        print(f"Fecha: {datos.get('fecha', 'N/A')}")
        print(f"Vendedor: {datos.get('vendedor', 'N/A')}")
        print("-" * 40)
        
        for producto in datos.get('productos', []):
            print(f"{producto['nombre'][:20]:20} {producto['cantidad']:3} x ${producto['precio_unitario']:6.2f} = ${producto['subtotal']:7.2f}")
        
        print("-" * 40)
        print(f"TOTAL: ${datos.get('total', 0):.2f}")
        print("=" * 40)
        print("     ¡Gracias por su compra!")
        print("=" * 40)
    
    async def _imprimir_reporte(self, datos: dict):
        """STRATEGY: Imprimir reporte"""
        print("=" * 50)
        print(f"       REPORTE: {datos.get('tipo', 'N/A').upper()}")
        print("=" * 50)
        print(f"Periodo: {datos.get('fecha_inicio', 'N/A')} a {datos.get('fecha_fin', 'N/A')}")
        print("-" * 50)
        
        # Aquí se imprimirían los datos específicos del reporte
        for key, value in datos.get('datos', {}).items():
            print(f"{key}: {value}")
        
        print("=" * 50)