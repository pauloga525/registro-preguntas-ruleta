from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.DB_NAME]
docentes_collection = db["docentes"]
preguntas_collection = db["preguntas"]  
revoked_tokens_collection = db["revoked_tokens"]
materias_collection = db["materias"]
cursos_collection = db["curso"]
niveles_collection = db["niveles"]