from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import jwt
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import redis
import os

# Security
security = HTTPBearer()

# Configuración
JWT_SECRET = os.getenv("JWT_SECRET", "pos_core_secret_key_2024")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = timedelta(hours=24)

# Modelos Pydantic - Capa de Modelo
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str = "vendedor"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    created_at: datetime
    is_active: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Repository Pattern - Abstracción del acceso a datos
class UserRepository:
    def __init__(self, database):
        self.collection = database.users

    async def create_user(self, user_data: dict) -> str:
        result = await self.collection.insert_one(user_data)
        return str(result.inserted_id)

    async def find_user_by_email(self, email: str) -> Optional[dict]:
        return await self.collection.find_one({"email": email})

    async def find_user_by_id(self, user_id: str) -> Optional[dict]:
        if ObjectId.is_valid(user_id):
            return await self.collection.find_one({"_id": ObjectId(user_id)})
        return None

# Service Layer - Lógica de negocio
class AuthService:
    def __init__(self, user_repository: UserRepository, redis_client: redis.Redis):
        self.user_repository = user_repository
        self.redis_client = redis_client

    @staticmethod
    def hash_password(password: str) -> str:
        # Strategy Pattern para hashing
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    def create_token(self, user_data: dict) -> str:
        # Factory Method para creación de tokens
        payload = {
            "user_id": user_data["id"],
            "email": user_data["email"],
            "role": user_data["role"],
            "exp": datetime.utcnow() + JWT_EXPIRATION
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token inválido")

    async def register_user(self, user_data: UserCreate) -> dict:
        # Verificar si el usuario ya existe
        existing_user = await self.user_repository.find_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="El usuario ya existe")

        # Crear usuario
        user_dict = user_data.dict()
        user_dict["password"] = self.hash_password(user_data.password)
        user_dict["created_at"] = datetime.utcnow()
        user_dict["is_active"] = True

        user_id = await self.user_repository.create_user(user_dict)
        
        # Preparar respuesta
        user_response = user_dict.copy()
        user_response["id"] = user_id
        user_response.pop("password")
        
        return user_response

    async def authenticate_user(self, login_data: UserLogin) -> dict:
        user = await self.user_repository.find_user_by_email(login_data.email)
        if not user or not self.verify_password(login_data.password, user["password"]):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        if not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="Usuario inactivo")

        user_response = {
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "created_at": user["created_at"],
            "is_active": user.get("is_active", True)
        }

        return user_response

# Dependency Injection
def get_auth_service() -> AuthService:
    # Singleton Pattern para la conexión a MongoDB
    mongo_client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    database = mongo_client.get_database()
    user_repository = UserRepository(database)
    
    # Redis client con connection pooling
    redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    
    return AuthService(user_repository, redis_client)

# FastAPI App - Capa de Controlador
app = FastAPI(
    title="Servicio de Autenticación - POS Core",
    description="Microservicio para gestión de usuarios y autenticación JWT",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "servicio": "Autenticación POS Core",
        "estado": "Funcionando",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "auth",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    """
    Registrar nuevo usuario - Implementa Factory Method para creación de usuarios
    """
    try:
        user = await auth_service.register_user(user_data)
        token = auth_service.create_token(user)
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(**user)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(login_data: UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    """
    Iniciar sesión - Strategy Pattern para autenticación
    """
    try:
        user = await auth_service.authenticate_user(login_data)
        token = auth_service.create_token(user)
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(**user)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Obtener usuario actual - Decorator Pattern para protección de rutas
    """
    try:
        payload = auth_service.verify_token(credentials.credentials)
        user = await auth_service.user_repository.find_user_by_id(payload["user_id"])
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            name=user["name"],
            role=user["role"],
            created_at=user["created_at"],
            is_active=user.get("is_active", True)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)