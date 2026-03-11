import os

from pydantic import BaseModel


class Settings(BaseModel):
    db_url: str = os.getenv("DB_URL", "sqlite:///./cpp_template.db")
    api_key: str = os.getenv("CPP_API_KEY", "")


settings = Settings()
