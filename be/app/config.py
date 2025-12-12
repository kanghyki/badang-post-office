from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")
    
    # FastAPI
    env: str = "prod"  # dev, prod
    debug: bool = False
    allowed_origins: str = ""

    # Database
    database_url: str = ""

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7

    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = ""
    jwt_access_token_expire_minutes: int = 60 * 24  # 24시간

    # SMTP Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "제주 엽서"

    # Encryption
    encryption_key: str = ""  # Fernet 키 (Base64 인코딩된 32바이트)

    @property
    def origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]


settings = Settings()
