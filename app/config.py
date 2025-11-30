from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Geliştirme için basit bir secret key
    SECRET_KEY: str = "super-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # SQLite için
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./it_appointments.db"

    class Config:
        env_file = ".env"


settings = Settings()
