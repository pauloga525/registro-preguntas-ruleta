import pytest
from httpx import AsyncClient
from app.main import app
from app.utils.jwt_manager import create_token
from app.database import docentes_collection, preguntas_collection, materias_collection, cursos_collection, niveles_collection


@pytest.mark.anyio
async def test_delete_pregunta_permissions():
    # Preparar: insertar docentes de prueba
    alice_email = "alice@example.com"
    bob_email = "bob@example.com"
    admin_email = "admin@example.com"

    await docentes_collection.insert_many([
        {"email": alice_email, "nombre": "Alice", "apellido": "A", "cedula": "100", "password": "x", "role": "docente"},
        {"email": bob_email, "nombre": "Bob", "apellido": "B", "cedula": "200", "password": "x", "role": "docente"},
        {"email": admin_email, "nombre": "Admin", "apellido": "A", "cedula": "300", "password": "x", "role": "admin"},
    ])

    # Crear nivel, curso, materia y asignar a alice
    nivel_res = await niveles_collection.insert_one({"nombre": "Nivel deldelete"})
    nivel_id = nivel_res.inserted_id
    curso_res = await cursos_collection.insert_one({"nombre": "Curso deldelete", "acronimo": "CD", "nivelId": nivel_id, "paralelos": []})
    curso_id = curso_res.inserted_id

    await materias_collection.insert_one({"subject": "mat_del", "nombre": "Materia Delete", "level": "X", "nivelIds": [curso_id], "docentes": [alice_email]})

    alice_token = create_token({"email": alice_email})
    bob_token = create_token({"email": bob_email})
    admin_token = create_token({"email": admin_email})

    headers_alice = {"Authorization": f"Bearer {alice_token}"}
    headers_bob = {"Authorization": f"Bearer {bob_token}"}
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    # Crear pregunta como Alice
    payload = {
        "pregunta": "Delete test",
        "respuesta1": "a",
        "respuesta2": "b",
        "respuesta3": "c",
        "respuesta4": "d",
        "respuestaCorrecta": 1,
        "hasImage": False,
        "subject": "mat_del",
        "level": "X",
    }

    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/preguntas/", json=payload, headers=headers_alice)
        assert r.status_code == 201
        data = r.json()
        pregunta_id = data.get("id")
        assert pregunta_id

        # Alice deletes her question -> should succeed
        r2 = await ac.delete(f"/preguntas/{pregunta_id}", headers=headers_alice)
        assert r2.status_code in (200, 204)

        # Re-create pregunta for further tests
        r3 = await ac.post("/preguntas/", json=payload, headers=headers_alice)
        assert r3.status_code == 201
        pregunta_id = r3.json().get("id")

        # Bob tries to delete -> should be 403
        r4 = await ac.delete(f"/preguntas/{pregunta_id}", headers=headers_bob)
        assert r4.status_code == 403

        # Admin tries to delete -> should succeed
        r5 = await ac.delete(f"/preguntas/{pregunta_id}", headers=headers_admin)
        assert r5.status_code in (200, 204)

    # Cleanup
    await docentes_collection.delete_many({"email": {"$in": [alice_email, bob_email, admin_email]}})
    await materias_collection.delete_one({"subject": "mat_del"})
    await cursos_collection.delete_one({"nombre": "Curso deldelete"})
    await niveles_collection.delete_one({"nombre": "Nivel deldelete"})
    await preguntas_collection.delete_many({"pregunta": "Delete test"})
