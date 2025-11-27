"""
Modelos Pydantic - PATRON MVC Model Layer
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum

class RolUsuario(str, Enum):
    """PATRON STRATEGY: Roles como estrategias de permisos"""
    ADMINISTRADOR = "administrador"
    VENDEDOR = "vendedor"
    INVENTARIO = "inventario"

class UsuarioBase(BaseModel):
    """Modelo base para usuarios"""
    email: EmailStr
    nombre: str = Field(..., min_length=1, max_length=100)
    rol: RolUsuario = Field(default=RolUsuario.VENDEDOR)

class UsuarioCrear(UsuarioBase):
    """PATRON FACTORY METHOD: Para creación de usuarios"""
    password: str = Field(..., min_length=6)

class Usuario(UsuarioBase):
    """Modelo completo de usuario - PATRON DOMAIN MODEL"""
    id: str
    fecha_creacion: datetime
    activo: bool

class LoginRequest(BaseModel):
    """Modelo para solicitud de login"""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Modelo para respuesta de token"""
    access_token: str
    token_type: str
    usuario: Usuario