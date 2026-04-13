"""Script de prueba para crear y listar preguntas.

Requisitos: generar el server con uvicorn antes de ejecutar.
python -m uvicorn app.main:app --reload

"""
import requests

BASE = "http://localhost:8000/preguntas"
AUTH = "http://localhost:8000/auth"

def test_create_and_get():
    payload = {
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

    # Autenticarse (si el usuario ya existe, usar login; este script no maneja errores)
    login_payload = {"email": "testdoc@example.com", "password": "pass"}
    rlogin = requests.post(AUTH + "/login", json=login_payload)
    token = rlogin.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}

    print("Enviando POST...", payload)
    r = requests.post(BASE + "/", json=payload, headers=headers)
    print("Status:", r.status_code, r.text)
    r2 = requests.get(BASE + "/")
    print("GET status:", r2.status_code)
    print("Preguntas:")
    for p in r2.json()[:5]:
        print(p)

if __name__ == "__main__":
    test_create_and_get()
