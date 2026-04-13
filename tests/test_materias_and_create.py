import pytest
from httpx import AsyncClient
from app.main import app
from app.utils.jwt_manager import create_token
from app.database import docentes_collection, preguntas_collection, materias_collection, cursos_collection, niveles_collection


@pytest.mark.anyio
async def test_get_materias_requires_auth():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/materias")
        assert r.status_code == 401


@pytest.mark.anyio
async def test_materias_and_create_question_flow():
    # Preparar: insertar docente de prueba
    test_email = "testdoc@example.com"
    await docentes_collection.insert_one({
        "email": test_email,
        "nombre": "Doc",
        "apellido": "Test",
        "cedula": "1234567890",
        "password": "x",
        "role": "docente",
        # Nota: realmente los permisos se definen en la collection `materias`
    })

    # Insertar nivel y curso y materias con referencias
    nivel_res = await niveles_collection.insert_one({"nombre": "Básica Media"})
    nivel_id = nivel_res.inserted_id
    curso_res = await cursos_collection.insert_one({"nombre": "Grupo A", "acronimo": "1ro", "nivelId": nivel_id, "paralelos": ["A"]})
    curso_id = curso_res.inserted_id
    await materias_collection.insert_many([
        {"subject": "mat_8", "nombre":"Matematicas 8", "level": "8vo", "nivelIds": [curso_id], "docentes": [test_email]},
        {"subject": "mat_9", "nombre":"Lengua 9", "level": "9no", "nivelIds": [curso_id], "docentes": [test_email]},
    ])

    token = create_token({"email": test_email})
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # GET materias
        r = await ac.get("/materias", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "materias" in data
        assert any(m.get("subject") == "mat_8" and m.get("level") == "8vo" for m in data["materias"])

        # POST pregunta con materia permitida (by subject code)
        payload = {
            "pregunta": "Test pregunta",
            "respuesta1": "a",
            "respuesta2": "b",
            "respuesta3": "c",
            "respuesta4": "d",
            "respuestaCorrecta": 1,
            "hasImage": False,
            "subject": "mat_8",
            "level": "8vo",
        }

        r2 = await ac.post("/preguntas/", json=payload, headers=headers)
        assert r2.status_code == 201

        # POST pregunta con materia NO permitida
        payload2 = payload.copy()
        payload2["subject"] = "mat_10"
        payload2["level"] = "10mo"
        r3 = await ac.post("/preguntas/", json=payload2, headers=headers)
        assert r3.status_code == 403

        # Crear una nueva materia por el docente
        new_mat = {"subject": "mat_new", "level": "7vo", "curso": "C"}
        r4 = await ac.post("/materias/", json=new_mat, headers=headers)
        assert r4.status_code == 201
        # Ahora debe aparecer entre las materias si tiene permisos
        r5 = await ac.get("/materias", headers=headers)
        assert any(m.get("subject") == "mat_new" for m in r5.json().get("materias", []))

    # Cleanup
    await docentes_collection.delete_one({"email": test_email})
    # Cleanup materias
    await materias_collection.delete_many({"docentes": {"$in": [test_email]}})
    # Cleanup curso and nivel
    await cursos_collection.delete_one({"nombre": "Grupo A"})
    await niveles_collection.delete_one({"nombre": "Básica Media"})
    # eliminar materia creada
    await materias_collection.delete_one({"subject": "mat_new"})
    # eliminar preguntas de prueba
    await preguntas_collection.delete_many({"subject": "mat_8", "pregunta": "Test pregunta"})
