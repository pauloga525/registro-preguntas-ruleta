from pydantic import BaseModel, EmailStr

class User(BaseModel):
    cedula: str
    nombre: str
    apellido: str   
    email: str
    password: str
    role: str

class UserLogin(BaseModel):
    email: str
    password: str


