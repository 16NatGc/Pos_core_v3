"""
Modelos de reportes - PATRON MVC Model Layer
"""

from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

class ReporteVentas(BaseModel):
    """PATRON COMPOSITE: Reporte compuesto de múltiples métricas"""
    total_ventas: float
    cantidad_ventas: int
    ventas_por_dia: List[Dict[str, Any]]
    productos_mas_vendidos: List[Dict[str, Any]]

class ReporteInventario(BaseModel):
    """Reporte de inventario compuesto"""
    total_productos: int
    productos_stock_bajo: List[Dict[str, Any]]
    valor_inventario_total: float

class ReporteGeneral(BaseModel):
    """PATRON COMPOSITE: Reporte general que contiene otros reportes"""
    ventas: ReporteVentas
    inventario: ReporteInventario
    fecha_generacion: datetime