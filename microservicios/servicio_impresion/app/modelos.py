"""
Modelos de impresión - PATRON MVC Model Layer
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime

class ItemTicket(BaseModel):
    """PATRON COMPOSITE: Item como parte del ticket"""
    nombre: str
    cantidad: int
    precio_unitario: float
    subtotal: float

class TicketRequest(BaseModel):
    """PATRON COMMAND: Representa un comando de impresión"""
    id_venta: str = Field(..., description="ID de la venta")
    productos: List[ItemTicket] = Field(..., description="Productos del ticket")
    total: float = Field(..., description="Total de la venta")
    fecha: datetime = Field(..., description="Fecha de la venta")
    cliente: str = Field("Cliente General", description="Nombre del cliente")
    vendedor: str = Field("Sistema", description="Nombre del vendedor")

class ReporteRequest(BaseModel):
    """PATRON COMMAND: Comando para imprimir reporte"""
    tipo: str = Field(..., description="Tipo de reporte")
    fecha_inicio: datetime = Field(..., description="Fecha inicio")
    fecha_fin: datetime = Field(..., description="Fecha fin")
    datos: Dict[str, Any] = Field(..., description="Datos del reporte")

class ImpresionResponse(BaseModel):
    """Response de impresión"""
    mensaje: str
    id_trabajo: str
    timestamp: datetime