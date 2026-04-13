# Registro de Preguntas Ruleta

## Descripción

Backend en FastAPI para administrar preguntas, materias y niveles de docentes. Incluye autenticación JWT, gestión de preguntas con imágenes Base64 o archivos, y control de acceso básico.

## Características

- Registro y login de docentes
- Autenticación con JWT
- Logout con token revocado
- CRUD de preguntas
- Soporte de imágenes en preguntas (archivo o Base64)
- Endpoints de materias y niveles autorizados
- Base de datos MongoDB

## Requisitos

- Python 3.10+ (recomendado 3.11)
- MongoDB en ejecución local o remota
- Entorno virtual Python opcional pero recomendado

## Instalación

1. Abrir terminal en la carpeta raíz del proyecto.
2. Activar el entorno virtual:

```powershell
& "venv\Scripts\Activate.ps1"
```

3. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

## Configuración

El proyecto utiliza variables de entorno para la configuración.

- `MONGO_URI`: URI de conexión a MongoDB.
- `DB_NAME`: Nombre de la base de datos.
- `JWT_SECRET`: Clave secreta para firmar tokens JWT.
- `JWT_ALGORITHM`: Algoritmo JWT (por defecto `HS256`).

Valores por defecto dentro de `app/config.py`:

```python
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "ruleta_db"
JWT_SECRET = "b7f9e243adb05e3bf4c86f33ab1d8217804147a65f00467fcbfaa8bdfb6e3b3e"
JWT_ALGORITHM = "HS256"
```

> Si deseas usar otros valores, exporta las variables de entorno antes de iniciar la aplicación.

## Ejecución

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API quedará disponible en `http://127.0.0.1:8000`.

## Colecciones de MongoDB

- `docentes`
- `preguntas`
- `revoked_tokens`
- `materias`
- `curso`
- `niveles`

## Endpoints

### Auth

#### `POST /auth/register`

Registra un nuevo docente.

Body JSON:

```json
{
  "cedula": "12345678",
  "nombre": "Juan",
  "apellido": "Pérez",
  "email": "juan@ejemplo.com",
  "password": "contraseña123",
  "role": "docente"
}
```

Respuesta:

```json
{
  "message": "Usuario creado"
}
```

#### `POST /auth/login`

Inicia sesión y devuelve token JWT.

Body JSON:

```json
{
  "email": "juan@ejemplo.com",
  "password": "contraseña123"
}
```

Respuesta:

```json
{
  "token": "<JWT>",
  "role": "docente",
  "nombre": "Juan",
  "apellido": "Pérez",
  "cedula": "12345678",
  "id": "<id_docente>"
}
```

#### `POST /auth/logout`

Cierra sesión revocando el token.

Headers:

```http
Authorization: Bearer <JWT>
```

Respuesta:

```json
{
  "message": "Sesión cerrada con éxito"
}
```

### Preguntas

#### `GET /preguntas`

Obtiene todas las preguntas.

Respuesta ejemplo:

```json
[
  {
    "id": "642...",
    "question": "¿Cuál es 2+2?",
    "options": ["1", "2", "3", "4"],
    "correctAnswer": 4,
    "hasImage": false,
    "imageBase64": null,
    "subject": "mat_8",
    "level": "8vo"
  }
]
```

#### `POST /preguntas`

Crea una nueva pregunta. Requiere JWT.

Headers:

```http
Authorization: Bearer <JWT>
```

Body JSON ejemplo:

```json
{
  "pregunta": "¿Cuál es el resultado de 2+2?",
  "respuesta1": "1",
  "respuesta2": "2",
  "respuesta3": "3",
  "respuesta4": "4",
  "respuestaCorrecta": 4,
  "subject": "mat_8",
  "level": "8vo",
  "imageBase64": "data:image/png;base64,iVBORw0KG..."
}
```

También acepta `multipart/form-data` para enviar un archivo en el campo `image`.

Respuesta:

```json
{
  "id": "642...",
  "question": "¿Cuál es el resultado de 2+2?",
  "options": ["1", "2", "3", "4"],
  "correctAnswer": 4,
  "hasImage": true,
  "imageBase64": "data:image/png;base64,...",
  "subject": "mat_8",
  "level": "8vo"
}
```

#### `PUT /preguntas/{pregunta_id}`

Actualiza una pregunta existente. Requiere JWT.

- No permite cambiar `subject` ni `level`.
- La pregunta se busca por `pregunta_id`.

Body JSON idéntico a `PreguntaIn`.

#### `DELETE /preguntas/{pregunta_id}`

Elimina una pregunta. Requiere JWT.

- Usa `pregunta_id` en la URL.

Respuesta:

```json
{
  "message": "Pregunta eliminada"
}
```

### Materias

#### `GET /materias`

Devuelve materias autorizadas para el docente autenticado.

Headers:

```http
Authorization: Bearer <JWT>
```

Respuesta ejemplo:

```json
{
  "materias": [
    {
      "id": "642...",
      "subject": "mat_8",
      "nombre": "Matemáticas",
      "level": "8vo"
    }
  ]
}
```

#### `POST /materias`

Crea una nueva materia.

Headers:

```http
Authorization: Bearer <JWT>
```

Body JSON:

```json
{
  "subject": "mat_9",
  "level": "9no",
  "curso": "9A"
}
```

Respuesta:

```json
{
  "subject": "mat_9",
  "level": "9no"
}
```

### Niveles

#### `GET /niveles`

Devuelve niveles estructurados con cursos y materias autorizadas.

Headers:

```http
Authorization: Bearer <JWT>
```

Respuesta ejemplo:

```json
{
  "niveles": [
    {
      "id": "642...",
      "nombre": "Nivel 1",
      "cursos": [
        {
          "id": "642...",
          "nombre": "9no",
          "acronimo": "9",
          "paralelos": ["A","B"],
          "materias": [
            {
              "id": "642...",
              "nombre": "Matemáticas",
              "tipo": "Obligatoria"
            }
          ]
        }
      ]
    }
  ]
}
```

## Modelos principales

### `User`

- `cedula`: string
- `nombre`: string
- `apellido`: string
- `email`: string
- `password`: string
- `role`: string

### `PreguntaIn`

- `pregunta`: string
- `respuesta1`: string
- `respuesta2`: string
- `respuesta3`: string
- `respuesta4`: string
- `respuestaCorrecta`: int
- `hasImage`: bool (opcional)
- `imageBase64`: string opcional
- `subject`: string opcional
- `level`: string opcional

### `PreguntaOut`

- `id`: string
- `question`: string
- `options`: lista de 4 strings
- `correctAnswer`: int
- `hasImage`: bool
- `imageBase64`: string opcional
- `subject`: string opcional
- `level`: string opcional

## Seguridad

- Contraseñas almacenadas con `bcrypt`.
- Tokens JWT firmados con `JWT_SECRET` y expiración de 12 horas.
- Logout agrega el token a la colección `revoked_tokens`.
- Endpoints de creación/edición/borrado requieren `Authorization: Bearer <JWT>`.

## CORS

El servidor permite solicitudes desde orígenes locales comunes y algunos dominios de prueba configurados en `app/main.py`.

## Notas adicionales

- `app/main.py` carga routers:
  - `/auth`
  - `/preguntas`
  - `/materias`
  - `/niveles`
- `app/database.py` crea la conexión asíncrona con MongoDB.
- `app/utils/jwt_manager.py` genera y decodifica tokens JWT.

## Ejemplo rápido

1. Registrar un docente.
2. Iniciar sesión y obtener token.
3. Crear una pregunta con `POST /preguntas`.
4. Consultar preguntas con `GET /preguntas`.

---

### Archivos importantes

- `app/main.py`
- `app/config.py`
- `app/database.py`
- `app/routes/auth.py`
- `app/routes/preguntas.py`
- `app/routes/materias.py`
- `app/routes/niveles.py`
- `app/models/pregunta.py`
- `app/models/user.py`
- `app/utils/jwt_manager.py`
- `app/utils/security.py`
