from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    base_domain: str
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",      # loads .env automatically
        case_sensitive=False
    )

# instantiate
settings = Settings()