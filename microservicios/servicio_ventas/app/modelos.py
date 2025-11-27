"""
Modelos de ventas - PATRON MVC Model Layer
"""

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from enum import Enum

class EstadoVenta(str, Enum):
    """PATRON STRATEGY: Estados como estrategias de flujo"""
    PENDIENTE = "pendiente"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"

class ItemVenta(BaseModel):
    """PATRON COMPOSITE: Item como parte de una venta compuesta"""
    producto_id: str = Field(..., description="ID del producto")
    nombre: str = Field(..., description="Nombre del producto")
    cantidad: int = Field(..., gt=0, description="Cantidad vendida")
    precio_unitario: float = Field(..., gt=0, description="Precio unitario")
    subtotal: float = Field(..., gt=0, description="Subtotal del ítem")

class VentaBase(BaseModel):
    """Modelo base para ventas"""
    cliente: str = Field(..., min_length=1, max_length=100, description="Nombre del cliente")
    items: List[ItemVenta] = Field(..., min_items=1, description="Items de la venta")
    total: float = Field(..., gt=0, description="Total de la venta")

class VentaCrear(VentaBase):
    """PATRON FACTORY METHOD: Para creación de ventas"""
    pass

class Venta(VentaBase):
    """Modelo completo de venta - PATRON DOMAIN MODEL"""
    id: str = Field(..., description="ID único de la venta")
    fecha_creacion: datetime = Field(..., description="Fecha de creación")
    vendedor: str = Field(..., description="Nombre del vendedor")
    estado: EstadoVenta = Field(..., description="Estado de la venta")

class VentaResponse(BaseModel):
    """Response compuesto - PATRON COMPOSITE"""
    venta: Venta
    mensaje: str