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

    # Redis (SSE용)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # RAG Settings
    rag_enabled: bool = True
    rag_top_k: int = 5
    rag_similarity_threshold: float = 1.5

    # LLM Translation
    translation_model: str = ""
    translation_max_completion_tokens: int = 2000

    # Embedding Model
    embedding_model: str = "text-embedding-3-small"

    # Data Paths
    jeju_dictionary_path: str = "data/jeju_dictionary.json"
    jeju_chroma_path: str = "data/jeju_chroma"

    @property
    def origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]


settings = Settings()
