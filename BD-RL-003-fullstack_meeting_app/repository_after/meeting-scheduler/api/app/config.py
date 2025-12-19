from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None)

    api_port: int = Field(default=8000, alias="API_PORT")
    api_cors_origin: str = Field(default="http://localhost:5173", alias="API_CORS_ORIGIN")

    database_url: str = Field(..., alias="DATABASE_URL")

    auth_base_url: str = Field(default="http://auth:3001", alias="AUTH_BASE_URL")

    google_service_account_json: str | None = Field(default=None, alias="GOOGLE_SERVICE_ACCOUNT_JSON")
    google_service_account_file: str | None = Field(default=None, alias="GOOGLE_SERVICE_ACCOUNT_FILE")
    google_calendar_id: str = Field(default="primary", alias="GOOGLE_CALENDAR_ID")

    api_enable_test_reset: bool = Field(default=False, alias="API_ENABLE_TEST_RESET")


settings = Settings()
