from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "ruleta_db"
    JWT_SECRET: str = "b7f9e243adb05e3bf4c86f33ab1d8217804147a65f00467fcbfaa8bdfb6e3b3e"
    JWT_ALGORITHM: str = "HS256"

settings = Settings()