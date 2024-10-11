# infra_ai_service/config/config.py
from pathlib import Path

from pydantic import BaseSettings

BASE_DIR = Path.cwd()


class Settings(BaseSettings):
    """Application settings."""

    ENV: str = "dev"
    HOST: str = "localhost"
    PORT: int = 8000
    _BASE_URL: str = f"http://{HOST}:{PORT}"
    WORKERS_COUNT: int = 1
    RELOAD: bool = False

    # 数据库配置项
    DB_NAME: str = ""
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = ""
    DB_PORT: int = 0

    # 模型名称配置项
    MODEL_NAME: str = "model-name-here"

    # 新增的配置项
    VECTOR_EXTENSION: str = ""
    TABLE_NAME: str = ""
    VECTOR_DIMENSION: int = 0
    LANGUAGE: str = ""

    # SpecBot config
    SPECBOT_AI_MODEL: str = ""
    REPAIR_PRO_AI_MODEL: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    SRC_RPM_DIR: str = "/tmp/infra_ai_service/"

    @property
    def BASE_URL(self) -> str:
        if self._BASE_URL.endswith("/"):
            return self._BASE_URL
        else:
            return f"{self._BASE_URL}/"

    class Config:
        env_file = f"{BASE_DIR}/.env"
        env_file_encoding = "utf-8"

        fields = {
            "_BASE_URL": {"env": "BASE_URL"},
            "DB_NAME": {"env": "DB_NAME"},
            "DB_USER": {"env": "DB_USER"},
            "DB_PASSWORD": {"env": "DB_PASSWORD"},
            "DB_HOST": {"env": "DB_HOST"},
            "DB_PORT": {"env": "DB_PORT"},
            "MODEL_NAME": {"env": "MODEL_NAME"},
            "VECTOR_EXTENSION": {"env": "VECTOR_EXTENSION"},
            "TABLE_NAME": {"env": "TABLE_NAME"},
            "VECTOR_DIMENSION": {"env": "VECTOR_DIMENSION"},
            "LANGUAGE": {"env": "LANGUAGE"},
            "HOST": {"env": "HOST"},
            "PORT": {"env": "PORT"},
            "SPECBOT_AI_MODEL": {"env": "SPECBOT_AI_MODEL"},
            "REPAIR_PRO_AI_MODEL": {"env": "REPAIR_PRO_AI_MODEL"},
            "OPENAI_API_KEY": {"env": "OPENAI_API_KEY"},
            "OPENAI_BASE_URL": {"env": "OPENAI_BASE_URL"},
            "SRC_RPM_DIR": {"env": "SRC_RPM_DIR"},
        }


settings = Settings()
