import pytest
from app.models.pregunta import PreguntaOut


def test_from_db_full_doc():
    doc = {
        "_id": "64d1e8121c4a3f6a2c9e5b4a",
        "pregunta": "¿Cuál es el resultado de la ecuación 2x + 5 = 13?",
        "respuesta1": "x = 3",
        "respuesta2": "x = 4",
        "respuesta3": "x = 5",
        "respuesta4": "x = 6",
        "respuestaCorrecta": 1,
        "hasImage": False,
        "subject": "mat_8",
        "level": "8vo",
    }

    p = PreguntaOut.from_db(doc)
    assert p.id == str(doc["_id"]) and p.question == doc["pregunta"]
    assert p.options == [doc["respuesta1"], doc["respuesta2"], doc["respuesta3"], doc["respuesta4"]]
    assert p.correctAnswer == 1
    assert p.hasImage is False
    assert p.subject == "mat_8"
    assert p.level == "8vo"
