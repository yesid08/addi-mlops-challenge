from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    chat_timeout_seconds: float = 30.0
    max_conversation_history: int = 50
    cors_origins: list[str] = ["*"]
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()  # type: ignore[call-arg]  # reads openai_api_key from env at runtime
