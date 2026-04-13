import pytest
from httpx import AsyncClient
from app.main import app
from app.utils.jwt_manager import create_token
from app.database import docentes_collection, materias_collection, cursos_collection, niveles_collection


@pytest.mark.anyio
async def test_get_niveles_requires_auth():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/niveles")
        assert r.status_code == 401


@pytest.mark.anyio
async def test_niveles_hierarchy_flow():
    test_email = "nivelesdoc@example.com"
    res_doc = await docentes_collection.insert_one({
        "email": test_email,
        "nombre": "DocN",
        "apellido": "Test",
        "cedula": "9876543210",
        "password": "x",
        "role": "docente",
        # No necesitamos poner la lista en el docente, la permission vendra de `materias` collection
    })

    # Insertar nivel y curso
    nivel_res = await niveles_collection.insert_one({"nombre": "Básica Media"})
    nivel_id = nivel_res.inserted_id
    curso_res = await cursos_collection.insert_one({"nombre": "Grupo A", "acronimo": "1ro", "nivelId": nivel_id, "paralelos": ["A", "B"]})
    curso_id = curso_res.inserted_id

    # Insertar materias con referencia a curso_id
    await materias_collection.insert_many([
        {"nombre": "Ciencias Naturales", "tipo": "BÁSICA", "nivelIds": [curso_id], "docenteId": res_doc.inserted_id},
        {"nombre": "Física", "tipo": "BÁSICA", "nivelIds": [curso_id], "docenteId": res_doc.inserted_id},
    ])

    token = create_token({"email": test_email})
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/niveles", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "niveles" in data
        niveles = data["niveles"]
        # Buscar nivel insertado por nombre
        assert any(n.get("nombre") == "Básica Media" for n in niveles)
        # Encontrar curso A dentro de 8vo
        for n in niveles:
            if n.get("level") == "8vo":
                cursos = n.get("cursos")
                assert any(c.get("nombre") == "Grupo A" for c in cursos)
                # materias en curso A
                cursoA = next(c for c in cursos if c.get("nombre") == "Grupo A")
                temas = [m.get("nombre") for m in cursoA.get("materias")]
                assert "Ciencias Naturales" in temas and "Física" in temas

    await docentes_collection.delete_one({"email": test_email})
    await materias_collection.delete_many({"docentes": {"$in": [test_email]}})
    await cursos_collection.delete_one({"_id": curso_id})
    await niveles_collection.delete_one({"_id": nivel_id})
    await materias_collection.delete_many({"docentes": {"$in": [test_email]}})
