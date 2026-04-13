import pytest
from httpx import AsyncClient
from app.main import app
from app.utils.jwt_manager import create_token
from app.database import docentes_collection, preguntas_collection


@pytest.mark.anyio
async def test_create_question_with_base64_image():
    test_email = "imgdoc@example.com"
    await docentes_collection.insert_one({
        "email": test_email,
        "nombre": "Img",
        "apellido": "Doc",
        "cedula": "1111111111",
        "password": "x",
        "role": "docente",
    })

    token = create_token({"email": test_email})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "pregunta": "Pregunta con imagen base64",
        "respuesta1": "A",
        "respuesta2": "B",
        "respuesta3": "C",
        "respuesta4": "D",
        "respuestaCorrecta": 1,
        "hasImage": True,
        "imageBase64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA",
        "subject": "mat_8",
        "level": "8vo",
    }

    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/preguntas/", json=payload, headers=headers)
        assert r.status_code == 201, r.text

    # Verify DB record
    record = await preguntas_collection.find_one({"pregunta": "Pregunta con imagen base64"})
    assert record is not None, "No se creó la pregunta en DB"

    assert record.get("hasImage") is True
    # imageBase64 must exist and not contain the data prefix (our endpoint strips it)
    assert record.get("imageBase64") is not None and not record.get("imageBase64").startswith("data:")

    # Cleanup
    await preguntas_collection.delete_one({"pregunta": "Pregunta con imagen base64"})
    await docentes_collection.delete_one({"email": test_email})
