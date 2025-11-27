"""
Servicios de seguridad - PATRON STRATEGY para algoritmos
"""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from configuracion import configuration

# PATRON STRATEGY: Diferentes esquemas de hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_password(plain_password: str, hashed_password: str) -> bool:
    """Strategy para verificación de contraseñas"""
    return pwd_context.verify(plain_password, hashed_password)

def obtener_password_hash(password: str) -> str:
    """Strategy para hashing de contraseñas"""
    return pwd_context.hash(password)

def crear_token_acceso(data: dict, expires_delta: Optional[timedelta] = None):
    """PATRON FACTORY: Crea tokens JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, configuration.JWT_SECRET, algorithm=configuration.JWT_ALGORITHM)
    return encoded_jwt

def verificar_token_acceso(token: str):
    """Strategy para verificación de tokens"""
    try:
        payload = jwt.decode(token, configuration.JWT_SECRET, algorithms=[configuration.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None