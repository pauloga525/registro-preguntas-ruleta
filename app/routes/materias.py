from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from pydantic import BaseModel
from ..database import docentes_collection, materias_collection
from ..routes.auth import verify_token


class MateriaOut(BaseModel):
    id: Optional[str]
    subject: Optional[str]
    nombre: Optional[str]
    level: Optional[str]


class MateriasOut(BaseModel):
    materias: List[MateriaOut]


class MateriaIn(BaseModel):
    subject: str
    level: Optional[str] = None
    curso: Optional[str] = None

router = APIRouter()


@router.get("/", name="get-materias", response_model=MateriasOut)
async def get_materias(token_payload: dict = Depends(verify_token)):
    """Devuelve las materias y niveles asignados al docente autenticado.
    Usa `email` en el payload del JWT para recuperar el documento del docente
    y normaliza `materias` a un array de objetos con `subject` y `level`.
    """
    email = token_payload.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")

    docente = await docentes_collection.find_one({"email": email})
    if not docente:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Primero intentar leer derechos desde el documento del docente
    allowed_materias = []
    docente_materias = docente.get("materias") or docente.get("asignaturas") or []
    if docente_materias:
        # Si la lista existe, normalizar y buscar en la collection `materias`
        subjects = []
        for m in docente_materias:
            if isinstance(m, str):
                subjects.append(m)
            elif isinstance(m, dict):
                subject = m.get("subject") or m.get("nombre") or m.get("asignatura")
                if subject:
                    subjects.append(subject)
        # Obtener los documentos reales desde `materias_collection`
        cursor = materias_collection.find({"subject": {"$in": subjects}})
        async for doc in cursor:
            allowed_materias.append({"id": str(doc.get("_id")), "subject": doc.get("subject"), "nombre": doc.get("nombre"), "level": doc.get("level")})
    else:
        # Si no hay lista en el 'docente', buscar en la collection `materias` documentos
        # que permitan al docente (campo 'docentes' o 'owner')
        filter_cond = {
            "$or": [
                {"docentes": {"$in": [docente.get("email")] }},
                {"docente": docente.get("email")},
                {"owner_email": docente.get("email")},
                {"owner": docente.get("email")},
            ]
        }
        cursor = materias_collection.find(filter_cond)
        async for doc in cursor:
            allowed_materias.append({"id": str(doc.get("_id")), "subject": doc.get("subject"), "nombre": doc.get("nombre"), "level": doc.get("level")})

    return {"materias": allowed_materias}


@router.post("/", response_model=MateriaOut, status_code=status.HTTP_201_CREATED)
async def create_materia(materia: MateriaIn, token_payload: dict = Depends(verify_token)):
    """Crear una nueva materia y asignar el docente logeado como propietario.
    Si la materia ya existe por el mismo subject, respondemos 400.
    """
    email = token_payload.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")

    exists = await materias_collection.find_one({"subject": materia.subject})
    if exists:
        raise HTTPException(status_code=400, detail="Materia ya existe")

    doc = {
        "subject": materia.subject,
        "level": materia.level,
        "curso": materia.curso,
        "docentes": [email]
    }
    result = await materias_collection.insert_one(doc)
    inserted = await materias_collection.find_one({"_id": result.inserted_id})
    if not inserted:
        raise HTTPException(status_code=500, detail="No se pudo crear la materia")
    return {"subject": inserted.get("subject"), "level": inserted.get("level")}


__all__ = ["router"]
