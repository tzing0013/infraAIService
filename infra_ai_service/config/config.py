from pathlib import Path

from pydantic import BaseSettings

BASE_DIR = Path(__file__).parent.parent.parent.resolve()


class Settings(BaseSettings):
    """Application settings."""

    ENV: str = "dev"
    HOST: str = 'localhost'
    PORT: int = 8000
    # quantity of workers for uvicorn
    WORKERS_COUNT: int = 1
    # Enable uvicorn reloading
    RELOAD: bool = False

    # SpecBot config
    SPECBOT_AI_MODEL: str = ''
    REPAIR_PRO_AI_MODEL: str = ''
    OPENAI_API_KEY: str  # must be assigned in .env
    OPENAI_BASE_URL: str = ''
    SRC_RPM_DIR: str = '/tmp/infra_ai_service/'
    XML_EXTRACT_PATH: str = ''

    @property
    def BASE_URL(self) -> str:
        return f"https://{self.HOST}:{self.PORT}/"

    class Config:
        env_file = f"{BASE_DIR}/.env"
        env_file_encoding = "utf-8"

        fields = {
            "_BASE_URL": {
                "env": "BASE_URL",
            },
            "_DB_BASE": {
                "env": "DB_BASE",
            },
            'HOST': {
                'env': 'HOST',
            },
            'PORT': {
                'env': 'PORT',
            },
            'SPECBOT_AI_MODEL': {
                'env': 'SPECBOT_AI_MODEL'
            },
            'REPAIR_PRO_AI_MODEL': {
                'env': 'REPAIR_PRO_AI_MODEL'
            },
            'OPENAI_API_KEY': {
                'env': 'OPENAI_API_KEY'
            },
            'OPENAI_BASE_URL': {
                'env': 'OPENAI_BASE_URL'
            },
            'SRC_RPM_DIR': {
                'env': 'SRC_RPM_DIR'
            },
            'XML_EXTRACT_PATH': {
                'env': 'XML_EXTRACT_PATH'
            },
        }


settings = Settings()
