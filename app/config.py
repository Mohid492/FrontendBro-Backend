from pydantic_settings import BaseSettings

# Reads these values .env file
# Makes sure they exist and are the right type (string, number, etc.)
# Stores them in an organized way

class Settings(BaseSettings):
    DATABASE_HOSTNAME: str
    DB_PORT: int
    DB_PASSWORD: str
    DB_NAME: str
    DB_USER: str
    SECRET_KEY: str
    ALGORITHM: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_TIME: int = 1
    FRONTEND_URL: str
    GOOGLE_REDIRECT_URI: str
    REDIS_URL: str
    class Config:
        env_file = ".env"

settings = Settings()