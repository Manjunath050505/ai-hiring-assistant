from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./app.db"
    hunar_base_url: str = "https://api.voice.hunar.ai/external/v1"
    hunar_api_key: str | None = None
    hunar_webhook_secrets: str = ""
    hunar_mock_mode: bool = True
    frontend_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"
    public_base_url: str = "http://localhost:3000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_list(self):
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]
    @property
    def webhook_secrets(self):
        return [x.strip() for x in self.hunar_webhook_secrets.split(",") if x.strip()]

settings = Settings()
