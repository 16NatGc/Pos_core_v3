"""
Modelos Pydantic para productos - PATRON MVC Model Layer
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class CategoriaProducto(str, Enum):
    """PATRON STRATEGY: Categorías como estrategias de agrupación"""
    ELECTRONICA = "electronica"
    ROPA = "ropa"
    ALIMENTOS = "alimentos"
    HOGAR = "hogar"
    DEPORTES = "deportes"
    OFICINA = "oficina"

class ProductoBase(BaseModel):
    """Modelo base para productos - PATRON BASE MODEL"""
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: str = Field(..., min_length=1, max_length=500)
    precio: float = Field(..., gt=0)
    categoria: CategoriaProducto
    sku: str = Field(..., min_length=1, max_length=50)

class ProductoCrear(ProductoBase):
    """PATRON FACTORY METHOD: Especializado para creación de productos"""
    stock_inicial: int = Field(default=0, ge=0)
    stock_minimo: int = Field(default=5, ge=0)

class ProductoActualizar(BaseModel):
    """PATRON BUILDER: Permite actualización parcial de productos"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = Field(None, min_length=1, max_length=500)
    precio: Optional[float] = Field(None, gt=0)
    categoria: Optional[CategoriaProducto] = None
    stock: Optional[int] = Field(None, ge=0)
    stock_minimo: Optional[int] = Field(None, ge=0)

class Producto(ProductoBase):
    """Modelo completo de producto - PATRON DOMAIN MODEL"""
    id: str
    stock: int
    stock_minimo: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    activo: bool