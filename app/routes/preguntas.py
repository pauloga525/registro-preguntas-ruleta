import base64
from fastapi import APIRouter, HTTPException, status, Depends
import logging
from typing import List
from bson import ObjectId
from fastapi import UploadFile, Request
from typing import Optional
from starlette.datastructures import UploadFile as StarletteUploadFile
from ..models.pregunta import PreguntaIn, PreguntaOut
from ..database import preguntas_collection, docentes_collection, materias_collection
from ..routes.auth import verify_token

router = APIRouter()
logger = logging.getLogger("app.preguntas")


@router.get("/", response_model=List[PreguntaOut])
async def get_preguntas():
    """Obtiene todas las preguntas en el formato público."""
    cursor = preguntas_collection.find()
    preguntas = []
    async for d in cursor:
        preguntas.append(PreguntaOut.from_db(d))
    return preguntas


@router.post("/", response_model=PreguntaOut, status_code=201)
async def create_pregunta(
    request: Request,
    image: Optional[UploadFile] = None,
    token_payload: dict = Depends(verify_token)
):
    """
    Crea una nueva pregunta. Puede recibir JSON o FormData con opción de archivo o Base64.
    """

    # Determinar si viene JSON o FormData
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        body = await request.json()
        pregunta = body.get("pregunta")
        respuesta1 = body.get("respuesta1")
        respuesta2 = body.get("respuesta2")
        respuesta3 = body.get("respuesta3")
        respuesta4 = body.get("respuesta4")
        respuestaCorrecta = body.get("respuestaCorrecta")
        subject = body.get("subject")
        level = body.get("level")
        imageBase64 = body.get("imageBase64")
        image_upload = None
    else:
        form = await request.form()
        pregunta = form.get("pregunta")
        respuesta1 = form.get("respuesta1")
        respuesta2 = form.get("respuesta2")
        respuesta3 = form.get("respuesta3")
        respuesta4 = form.get("respuesta4")
        respuestaCorrecta = form.get("respuestaCorrecta")
        subject = form.get("subject")
        level = form.get("level")
        imageBase64 = form.get("imageBase64")
        # Priorizar archivo subido
        image_upload = image or form.get("image")

    # Validar y convertir respuestaCorrecta a int
    try:
        rc = int(respuestaCorrecta) if respuestaCorrecta is not None else None # type: ignore
    except (ValueError, TypeError):
        rc = None

    # Inicializar datos
    data = {
        "pregunta": pregunta,
        "respuesta1": respuesta1,
        "respuesta2": respuesta2,
        "respuesta3": respuesta3,
        "respuesta4": respuesta4,
        "respuestaCorrecta": rc,
        "subject": subject,
        "level": level,
        "hasImage": False,
        "imageBase64": None,
    }

    # 1️⃣ Priorizar archivo si se envía
    if image_upload is not None and hasattr(image_upload, "read"):
        content = await image_upload.read() # type: ignore
        data["imageBase64"] = base64.b64encode(content).decode("utf-8")
        data["hasImage"] = True
    # 2️⃣ Si viene Base64 desde front
    elif isinstance(imageBase64, str) and imageBase64.strip():
        # remover prefijo "data:image/..."
        if imageBase64.startswith("data:"):
            data["imageBase64"] = imageBase64.split(",")[1]
        else:
            data["imageBase64"] = imageBase64
        data["hasImage"] = True

    logger.debug("create_pregunta: image=%s imageBase64=%s hasImage=%s",
                 getattr(image_upload, "filename", None) if image_upload else None,
                 data["imageBase64"][:30] + "..." if data["imageBase64"] else None,
                 data["hasImage"])

    # Insertar en DB
    result = await preguntas_collection.insert_one(data)
    doc = await preguntas_collection.find_one({"_id": result.inserted_id})
    if not doc:
        raise HTTPException(status_code=500, detail="Pregunta creada pero no encontrada")

    return PreguntaOut.from_db(doc)

@router.put("/{pregunta_id}", response_model=PreguntaOut)
async def update_pregunta(
    pregunta_id: str,
    pregunta: PreguntaIn,
    token_payload: dict = Depends(verify_token)
):
    docente = await docentes_collection.find_one({"email": token_payload.get("email")})
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")

    try:
        oid = ObjectId(pregunta_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de pregunta inválido")

    pregunta_doc = await preguntas_collection.find_one({"_id": oid})
    if not pregunta_doc:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")

    # Validar permisos
    # owner_id = str(pregunta_doc.get("docenteId"))
    # requester_id = str(docente.get("_id"))

   #  if owner_id != requester_id and docente.get("role") != "admin":
    #     raise HTTPException(status_code=403, detail="No autorizado")

    # Bloquear cambio de materia / nivel
    if pregunta.subject != pregunta_doc.get("subject") or pregunta.level != pregunta_doc.get("level"):
        raise HTTPException(status_code=400, detail="No se permite cambiar materia/nivel")

    data = pregunta.dict()

    # 🔄 Manejo de imagen
    if pregunta.imageBase64:
        data["hasImage"] = True
        if pregunta.imageBase64.startswith("data:"):
            data["imageBase64"] = pregunta.imageBase64.split(",")[1]
    else:
        data["hasImage"] = False
        data["imageBase64"] = None

    await preguntas_collection.update_one({"_id": oid}, {"$set": data})
    updated = await preguntas_collection.find_one({"_id": oid})
    return PreguntaOut.from_db(updated) # type: ignore


@router.delete("/{pregunta_id}")
async def delete_pregunta(pregunta_id: str, token_payload: dict = Depends(verify_token)):
    """Borra una pregunta si el docente que solicita es el propietario o es admin."""
    payload_email = token_payload.get("email")
    if not payload_email:
        raise HTTPException(status_code=401, detail="Token inválido")

    docente = await docentes_collection.find_one({"email": payload_email})
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")

    try:
        oid = ObjectId(pregunta_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    pregunta_doc = await preguntas_collection.find_one({"_id": oid})
    if not pregunta_doc:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")
    else:
        await preguntas_collection.delete_one({"_id": oid})
        return {"message": "Pregunta eliminada"}

    # Validar permisos
    #owner_id = pregunta_doc.get("docenteId") or pregunta_doc.get("owner") or pregunta_doc.get("docente")
    #requester_id = str(docente.get("_id"))
    #if owner_id == requester_id or docente.get("role") == "admin" or docente.get("role") == "docente":
        #await preguntas_collection.delete_one({"_id": oid})
        #return {"message": "Pregunta eliminada"}
    #else:
    #    raise HTTPException(status_code=403, detail="No autorizado para borrar esta pregunta")
