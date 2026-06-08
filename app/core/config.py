from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):

    database_url: str
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str

    app_name : str = "Event Notification System"
    debug: bool = False

    class Config:
        env_file =".env"
        case_sensitive =False


settings = Settings()
