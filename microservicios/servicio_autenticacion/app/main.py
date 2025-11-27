"""
Servicio de Autenticación - PATRON MVC + GOF
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from configuracion import configuration
from modelos import UsuarioCrear, Usuario, LoginRequest, TokenResponse
from seguridad import obtener_password_hash, verificar_password, crear_token_acceso, verificar_token_acceso
from repositorio import UsuarioRepository
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PATRON MVC - Controller principal
app = FastAPI(
    title="Servicio de Autenticación - POS Core",
    description="Microservicio para gestión de usuarios y autenticación",
    version="1.0.0"
)

# PATRON STRATEGY: Esquema de autenticación Bearer
security = HTTPBearer()

# PATRON DEPENDENCY INJECTION: Factory para base de datos
def get_database():
    client = MongoClient(configuration.MONGODB_URL)
    return client[configuration.BASE_DATOS]

def get_usuario_repository():
    db = get_database()
    return UsuarioRepository(db)

@app.get("/")
async def raiz():
    return {
        "servicio": "Autenticación POS Core",
        "estado": "Funcionando",
        "version": "1.0.0"
    }

@app.get("/health")
async def salud():
    return {
        "estado": "Saludable",
        "servicio": "Autenticación",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/auth/registro", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def registrar_usuario(usuario: UsuarioCrear, repo: UsuarioRepository = Depends(get_usuario_repository)):
    """PATRON MVC - Controller: Endpoint de registro"""
    # Validar usuario existente
    usuario_existente = await repo.obtener_por_email(usuario.email)
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    # PATRON FACTORY: Crear usuario
    usuario_data = usuario.dict()
    usuario_data["password"] = obtener_password_hash(usuario.password)
    usuario_data["fecha_creacion"] = datetime.now()
    usuario_data["activo"] = True
    
    usuario_id = await repo.crear(usuario_data)
    usuario_creado = await repo.obtener_por_id(usuario_id)
    
    # PATRON FACTORY: Crear token
    token = crear_token_acceso({
        "sub": usuario_creado["email"],
        "user_id": str(usuario_creado["_id"]),
        "rol": usuario_creado["rol"]
    })
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        usuario=Usuario(
            id=str(usuario_creado["_id"]),
            email=usuario_creado["email"],
            nombre=usuario_creado["nombre"],
            rol=usuario_creado["rol"],
            fecha_creacion=usuario_creado["fecha_creacion"],
            activo=usuario_creado["activo"]
        )
    )

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, repo: UsuarioRepository = Depends(get_usuario_repository)):
    """PATRON MVC - Controller: Endpoint de login"""
    usuario = await repo.obtener_por_email(login_data.email)
    if not usuario or not verificar_password(login_data.password, usuario["password"]):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if not usuario.get("activo", True):
        raise HTTPException(status_code=401, detail="Usuario inactivo")
    
    token = crear_token_acceso({
        "sub": usuario["email"],
        "user_id": str(usuario["_id"]),
        "rol": usuario["rol"]
    })
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        usuario=Usuario(
            id=str(usuario["_id"]),
            email=usuario["email"],
            nombre=usuario["nombre"],
            rol=usuario["rol"],
            fecha_creacion=usuario["fecha_creacion"],
            activo=usuario["activo"]
        )
    )

@app.get("/api/v1/auth/me", response_model=Usuario)
async def obtener_usuario_actual(credentials: HTTPBearer = Depends(security), repo: UsuarioRepository = Depends(get_usuario_repository)):
    """PATRON MVC - Controller: Endpoint para obtener usuario actual"""
    # PATRON STRATEGY: Verificar token
    payload = verificar_token_acceso(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    usuario = await repo.obtener_por_id(payload["user_id"])
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return Usuario(
        id=str(usuario["_id"]),
        email=usuario["email"],
        nombre=usuario["nombre"],
        rol=usuario["rol"],
        fecha_creacion=usuario["fecha_creacion"],
        activo=usuario["activo"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)