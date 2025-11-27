"""
Servicio de reportes - PATRON STRATEGY para diferentes tipos de reportes
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
from configuracion import configuration
from modelos import ReporteVentas, ReporteInventario

class ReporteService:
    """PATRON STRATEGY: Diferentes estrategias para generar reportes"""
    
    def __init__(self):
        self.client = MongoClient(configuration.MONGODB_URL)
        self.db = self.client[configuration.BASE_DATOS]
    
    async def generar_reporte_ventas(self, fecha_inicio: datetime, fecha_fin: datetime) -> ReporteVentas:
        """STRATEGY: Genera reporte de ventas"""
        ventas_collection = self.db["ventas"]
        
        # Ventas en el período
        ventas = list(ventas_collection.find({
            "fecha_creacion": {
                "$gte": fecha_inicio,
                "$lte": fecha_fin
            },
            "estado": "completada"
        }))
        
        total_ventas = sum(venta["total"] for venta in ventas)
        cantidad_ventas = len(ventas)
        
        # Ventas por día - PATRON ITERATOR
        ventas_por_dia = []
        current_date = fecha_inicio
        while current_date <= fecha_fin:
            next_date = current_date + timedelta(days=1)
            ventas_dia = list(ventas_collection.find({
                "fecha_creacion": {
                    "$gte": current_date,
                    "$lt": next_date
                },
                "estado": "completada"
            }))
            
            total_dia = sum(venta["total"] for venta in ventas_dia)
            ventas_por_dia.append({
                "fecha": current_date.strftime("%Y-%m-%d"),
                "total": total_dia,
                "cantidad": len(ventas_dia)
            })
            
            current_date = next_date
        
        # Productos más vendidos - PATRON AGGREGATE
        productos_vendidos = {}
        for venta in ventas:
            for item in venta["items"]:
                producto_id = item["producto_id"]
                if producto_id not in productos_vendidos:
                    productos_vendidos[producto_id] = {
                        "nombre": item["nombre"],
                        "cantidad": 0,
                        "total": 0
                    }
                productos_vendidos[producto_id]["cantidad"] += item["cantidad"]
                productos_vendidos[producto_id]["total"] += item["subtotal"]
        
        productos_mas_vendidos = sorted(
            productos_vendidos.values(),
            key=lambda x: x["cantidad"],
            reverse=True
        )[:10]
        
        return ReporteVentas(
            total_ventas=total_ventas,
            cantidad_ventas=cantidad_ventas,
            ventas_por_dia=ventas_por_dia,
            productos_mas_vendidos=productos_mas_vendidos
        )
    
    async def generar_reporte_inventario(self) -> ReporteInventario:
        """STRATEGY: Genera reporte de inventario"""
        productos_collection = self.db["productos"]
        
        productos = list(productos_collection.find({"activo": True}))
        total_productos = len(productos)
        
        productos_stock_bajo = []
        valor_inventario_total = 0
        
        for producto in productos:
            valor_producto = producto["precio"] * producto["stock"]
            valor_inventario_total += valor_producto
            
            if producto["stock"] < producto.get("stock_minimo", 5):
                productos_stock_bajo.append({
                    "nombre": producto["nombre"],
                    "sku": producto["sku"],
                    "stock_actual": producto["stock"],
                    "stock_minimo": producto.get("stock_minimo", 5),
                    "precio": producto["precio"]
                })
        
        return ReporteInventario(
            total_productos=total_productos,
            productos_stock_bajo=productos_stock_bajo,
            valor_inventario_total=valor_inventario_total
        )