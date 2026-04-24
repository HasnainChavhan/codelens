"""
CodeLens — Core Configuration
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "CodeLens"
    app_version: str = "1.0.0"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    max_retries: int = 3
    diff_cache_file: str = ".codelens_cache.json"
    output_dir: str = "codelens_output"

    class Config:
        env_file = ".env"


settings = Settings()
