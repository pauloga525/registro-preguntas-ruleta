from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
from jose import jwt
from bson import ObjectId

from ..models.user import User, UserLogin
from ..database import docentes_collection, revoked_tokens_collection
from ..utils.security import hash_password, verify_password
from ..utils.jwt_manager import create_token, SECRET_KEY
from pydantic import BaseModel

router = APIRouter()

# OAuth2 Schema para extraer el token del Authorization Header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------------------- MODELOS DE SALIDA ----------------------
class LoginOut(BaseModel):
    token: str
    role: str
    nombre: str
    apellido: str
    cedula: str
    id: str


class MessageOut(BaseModel):
    message: str


# ---------------------- REGISTER ----------------------
@router.post("/register", response_model=MessageOut)
async def register(user: User):
    existsEmail = await docentes_collection.find_one({"email": user.email})
    existsCedula = await docentes_collection.find_one({"cedula": user.cedula})

    if existsEmail or existsCedula:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    hashed = hash_password(user.password)

    await docentes_collection.insert_one({
        "nombre": user.nombre,
        "apellido": user.apellido,
        "cedula": user.cedula,
        "email": user.email,
        "password": hashed,
        "role": user.role
    })
    
    return {"message": "Usuario creado"}


# ---------------------- LOGIN ----------------------
@router.post("/login", response_model=LoginOut)
async def login(user: UserLogin):
    found = await docentes_collection.find_one({"email": user.email})

    if not found or not verify_password(user.password, found["password"]):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token = create_token({"email": user.email})

    return LoginOut(
        token=token,
        role=found["role"],
        nombre=found["nombre"],
        apellido=found["apellido"],
        cedula=found["cedula"],
        id=str(found["_id"]),  # ⚡ Convertir ObjectId a string
    )


# ---------------------- LOGOUT ----------------------
@router.post("/logout", response_model=MessageOut)
async def logout(token: str = Depends(oauth2_scheme)):
    await revoked_tokens_collection.insert_one({
        "token": token,
        "revoked_at": datetime.utcnow()
    })

    return {"message": "Sesión cerrada con éxito"}


# ---------------------- VERIFY TOKEN ----------------------
async def verify_token(token: str = Depends(oauth2_scheme)):
    # 1. Verificar firma JWT
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    # 2. Validar si el token está revocado
    revoked = await revoked_tokens_collection.find_one({"token": token})
    if revoked:
        raise HTTPException(status_code=401, detail="Token revocado")

    return payload
