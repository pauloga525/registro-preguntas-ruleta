from collections import defaultdict
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from ..database import docentes_collection, materias_collection, niveles_collection, cursos_collection
from ..routes.auth import verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


class MateriaOut(BaseModel):
    id: str
    nombre: Optional[str]
    tipo: Optional[str]


class CursoOut(BaseModel):
    id: str
    nombre: Optional[str]
    acronimo: Optional[str]
    paralelos: Optional[List[str]]
    materias: List[MateriaOut]


class NivelOut(BaseModel):
    id: str
    nombre: Optional[str]
    cursos: List[CursoOut]


class NivelesOut(BaseModel):
    niveles: List[NivelOut]


@router.get("/", name="get-niveles", response_model=NivelesOut)
async def get_niveles(token_payload: dict = Depends(verify_token)):
    """Devuelve la estructura de niveles -> cursos -> materias que tiene
    autorización el docente autenticado.
    """
    email = token_payload.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")

    docente = await docentes_collection.find_one({"email": email})
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")

    # Obtener las materias que el docente tiene permiso (desde su documento o desde la coleccion)
    materias = []
    docente_materias = docente.get("materias") or docente.get("asignaturas") or []
    # Prepare identificadores para consultas
    docente_id = docente.get("_id")
    docente_id_str = str(docente_id) if docente_id else None
    identifiers = [x for x in [docente_id, docente_id_str, docente.get("email")] if x]

    if docente_materias:
        subjects = []
        for m in docente_materias:
            if isinstance(m, str):
                subjects.append(m)
            elif isinstance(m, dict):
                subject = m.get("subject") or m.get("nombre") or m.get("asignatura")
                if subject:
                    subjects.append(subject)
        cursor = materias_collection.find({"subject": {"$in": subjects}})
        async for doc in cursor:
            materias.append(doc)
    else:
        filter_cond = {
            "$or": [
                {"docentes": {"$in": identifiers}},
                {"docenteId": {"$in": identifiers}},
                {"docente": {"$in": identifiers}},
            ]
        }
        cursor = materias_collection.find(filter_cond)
        async for doc in cursor:
            materias.append(doc)

    # Mapear: nivelId -> cursoId -> list(materia docs)
    cursos_by_id = {}
    materias_by_curso = defaultdict(list)
    all_curso_ids = set()

    # Extraer curso ids desde `nivelIds` (que en DB contienen curso ids)
    for m in materias:
        nivel_ids = m.get("nivelIds") or m.get("nivelId") or m.get("cursoIds") or m.get("cursoId") or []
        if not isinstance(nivel_ids, list):
            nivel_ids = [nivel_ids]
        for cid in nivel_ids:
            if not cid:
                continue
            # guardamos el curso como ObjectId si no lo es
            try:
                cid_obj = ObjectId(cid) if not isinstance(cid, ObjectId) else cid
            except Exception:
                cid_obj = cid
            all_curso_ids.add(cid_obj)
            materias_by_curso[cid_obj].append(m)

    # Construir salida
    niveles = []
    # Recuperar datos de cursos para todos los cursos encontrados
    cursos_by_id = {}
    if all_curso_ids:
        cursos_cursor = cursos_collection.find({"_id": {"$in": list(all_curso_ids)}})
        async for cdoc in cursos_cursor:
            cursos_by_id[cdoc.get("_id")] = cdoc

    # Mapear cursos por nivelId
    cursos_por_nivel = defaultdict(list)
    for cid, cdoc in cursos_by_id.items():
        nivel_id = cdoc.get("nivelId") or cdoc.get("nivel_id")
        cursos_por_nivel[nivel_id].append(cdoc)

    # Recuperar niveles
    nivel_ids = [k for k in cursos_por_nivel.keys() if k]
    # Ensure nivel_ids are ObjectId where possible for querying the collection
    normalized_nivel_ids = []
    for nid in nivel_ids:
        try:
            nid_obj = ObjectId(nid) if not isinstance(nid, ObjectId) else nid
        except Exception:
            nid_obj = nid
        normalized_nivel_ids.append(nid_obj)
    niveles_docs = {}
    if normalized_nivel_ids:
        ndoc_cursor = niveles_collection.find({"_id": {"$in": normalized_nivel_ids}})
        async for ndoc in ndoc_cursor:
            niveles_docs[ndoc.get("_id")] = ndoc

    # Construir salida
    niveles = []
    for nivel_id, cursos_list_docs in cursos_por_nivel.items():
        cursos_list = []
        logger.debug("Construyendo cursos para nivel %s (cantidad %s)", nivel_id, len(cursos_list_docs))
        for cdoc in cursos_list_docs:
            cid = cdoc.get("_id")
            materias_docs = materias_by_curso.get(cid, [])
            materias_list = [{"id": str(md.get("_id")), "nombre": md.get("nombre"), "tipo": md.get("tipo")} for md in materias_docs]
            try:
                cursos_list.append({
                    "id": str(cid),
                    "nombre": cdoc.get("nombre"),
                    "acronimo": cdoc.get("acronimo"),
                    "paralelos": cdoc.get("paralelos"),
                    "materias": materias_list,
                })
            except Exception as e:
                # Log unexpected structure and raise HTTP error (500)
                logger.exception("Estructura inesperada para curso %s: %s", cid, e)
                raise HTTPException(status_code=500, detail=f"Error construyendo curso {cid}: {e}")
        nivel_doc = niveles_docs.get(nivel_id)
        niveles.append({"id": str(nivel_id), "nombre": nivel_doc.get("nombre") if nivel_doc else str(nivel_id), "cursos": cursos_list})

    # Ordenar niveles por nombre (si existe) para reproducibilidad
    try:
        niveles = sorted(niveles, key=lambda x: str(x.get("nombre") or x.get("id")))
    except Exception:
        # Fallback: return unsorted if some items miss 'nombre' or 'id'
        pass

    return {"niveles": niveles}


__all__ = ["router"]
