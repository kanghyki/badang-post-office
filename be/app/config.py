from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # FastAPI
    env: str = "dev"
    debug: bool = True
    allowed_origins: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    # OpenAI
    openai_api_key: str = ""

    # SendGrid
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = ""
    sendgrid_from_name: str = ""

    # Storage
    storage_bucket_images: str = ""
    storage_bucket_templates: str = ""

    @property
    def origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
