from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "King Mave Digital Automation Hub"
    app_env: str = "development"
    database_url: str = "sqlite:///./kmd.db"
    whatsapp_token: str = "demo_token"
    whatsapp_phone_number_id: str = "demo_phone_number_id"
    whatsapp_webhook_verify_token: str = "demo_verify_token"
    scheduler_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
