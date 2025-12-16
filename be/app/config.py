from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")
    
    # FastAPI
    env: str = "prod"  # dev, prod
    debug: bool = False
    domain: str = ""
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

    # Translation Model (Jeju Dialect)
    translation_model_path: str = "static/models/jeju-dialect-model.gguf"
    translation_n_ctx: int = 2048
    translation_n_gpu_layers: int = 0
    translation_temperature: float = 0.7
    translation_top_p: float = 0.9
    translation_top_k: int = 40

    @property
    def origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]


settings = Settings()
