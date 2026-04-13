import sys
from pathlib import Path
from fastapi.testclient import TestClient
import logging
import asyncio

# Ensure project root is in sys.path for direct script execution
ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import app
from app.utils.jwt_manager import create_token
from app.database import docentes_collection, preguntas_collection


def main():
    logging.basicConfig(level=logging.DEBUG)
    test_email = "imgdoc@example.com"
    # Insert docente (async) - run in event loop
    asyncio.run(docentes_collection.insert_one({
        "email": test_email,
        "nombre": "Img",
        "apellido": "Doc",
        "cedula": "1111111111",
        "password": "x",
        "role": "docente",
    }))

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

    print("Sending POST /preguntas/")
    with TestClient(app) as client:
        r = client.post("/preguntas/", json=payload, headers=headers)
        print("Status:", r.status_code, r.text)

    record = asyncio.run(preguntas_collection.find_one({"pregunta": "Pregunta con imagen base64"}))
    print("Record found:" , record)

    # Cleanup
    asyncio.run(preguntas_collection.delete_one({"pregunta": "Pregunta con imagen base64"}))
    asyncio.run(docentes_collection.delete_one({"email": test_email}))


if __name__ == "__main__":
    main()
import asyncio
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure project root is in sys.path for direct script execution
ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import app
from app.utils.jwt_manager import create_token
from app.database import docentes_collection, preguntas_collection


def main():
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

    print("Sending POST /preguntas/")
    with TestClient(app) as client:
        r = client.post("/preguntas/", json=payload, headers=headers)
        print("Status:", r.status_code, r.text)

    record = await preguntas_collection.find_one({"pregunta": "Pregunta con imagen base64"})
    print("Record found:" , record)

    # Cleanup
    await preguntas_collection.delete_one({"pregunta": "Pregunta con imagen base64"})
    await docentes_collection.delete_one({"email": test_email})

if __name__ == "__main__":
    main()
