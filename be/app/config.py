from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # FastAPI
    env: str = "dev"
    debug: bool = True
    allowed_origins: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/jeju.db"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7

    @property
    def origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
