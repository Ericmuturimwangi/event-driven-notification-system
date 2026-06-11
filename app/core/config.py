from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):

    database_url: str
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str

    app_name : str = "Event Notification System"
    debug: bool = False


    task_max_retries: int = 5
    task_retry_base_delay: int = 60
    task_retry_max_delay: int = 960

    circuit_breaker_fail_max: int = 5
    circuit_breaker_reset_timeout: int = 60

    circuit_open_reschedule_delay: int = 60

    circuit_open_max_reschedules: int = 30

    class Config:
        env_file =".env"
        case_sensitive =False


settings = Settings()
