from typing import List, Optional
from pydantic import BaseModel, Field, constr


class PreguntaIn(BaseModel):
    """Modelo para crear/recibir preguntas desde el cliente o API.

    Mantiene la estructura usada en la DB para compatibilidad.
    """
    pregunta: str
    respuesta1: str
    respuesta2: str
    respuesta3: str
    respuesta4: str
    respuestaCorrecta: int = Field(..., alias="respuestaCorrecta")
    hasImage: Optional[bool] = False
    imageBase64: Optional[constr(min_length=1)] = None  # type: ignore # Campo para base64
    subject: Optional[str] = None
    level: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "pregunta": "¿Cuál es el resultado de la ecuación 2x + 5 = 13?",
                "respuesta1": "x = 3",
                "respuesta2": "x = 4",
                "respuesta3": "x = 5",
                "respuesta4": "x = 6",
                "respuestaCorrecta": 1,
                "hasImage": True,
                "imageBase64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
                "subject": "mat_8",
                "level": "8vo",
            }
        }


class PreguntaOut(BaseModel):
    """Modelo público que expondrá el esquema solicitado por el usuario."""
    id: str
    question: str
    options: List[str]
    correctAnswer: int
    hasImage: bool = False
    imageBase64: Optional[str] = None
    subject: Optional[str] = None
    level: Optional[str] = None

    class Config:
        orm_mode = True

    @classmethod
    def from_db(cls, doc: dict):
        id_value = str(doc.get("_id") or doc.get("id") or "")
        question = doc.get("pregunta") or doc.get("question") or ""
        options = [
            doc.get("respuesta1") or doc.get("option1") or "",
            doc.get("respuesta2") or doc.get("option2") or "",
            doc.get("respuesta3") or doc.get("option3") or "",
            doc.get("respuesta4") or doc.get("option4") or "",
        ]
        correct_answer = doc.get("respuestaCorrecta") or doc.get("correctAnswer") or 0
        has_image = bool(doc.get("hasImage") or False)

        # 🔑 Reconstruir Base64 con prefijo si existe
        image_data = doc.get("imageBase64") or None
        if has_image and image_data:
            # Si no contiene "data:" al inicio, agregar prefijo para mostrar
            if not image_data.startswith("data:"):
                image_data = f"data:image/png;base64,{image_data}"

        subject = doc.get("subject") or doc.get("asignatura") or None
        level = doc.get("level") or doc.get("nivel") or None

        return cls(
            id=id_value,
            question=question,
            options=options,
            correctAnswer=int(correct_answer),
            hasImage=has_image,
            imageBase64=image_data,
            subject=subject,
            level=level,
        )

__all__ = ["PreguntaIn", "PreguntaOut"]


class Pregunta(BaseModel):
    """Modelo simple sin alias, usado internamente si es necesario."""
    pregunta: str
    respuesta1: str
    respuesta2: str
    respuesta3: str
    respuesta4: str
    respuestaCorrecta: int
    hasImage: Optional[bool] = False
    imageBase64: Optional[str] = None
    subject: Optional[str] = None
    level: Optional[str] = None
