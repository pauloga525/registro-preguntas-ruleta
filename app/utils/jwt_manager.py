from datetime import datetime, timedelta
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from ..config import settings

# ------------------------
# 🔐 Declarar SECRET_KEY
# ------------------------
SECRET_KEY = settings.JWT_SECRET
ALGORITHM = settings.JWT_ALGORITHM


def decode_token(token: str):
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None


def create_token(data: dict):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=12)

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token
