from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://recruitment:recruitment_pass@localhost:5432/recruitment_db"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Brave Search API
    BRAVE_SEARCH_API_KEY: str = ""

    # Serper.dev (Google Search API, free: 2500 queries)
    SERPER_API_KEY: str = ""

    # Hunter.io (email finder API, optional)
    HUNTER_API_KEY: str = ""

    # Email
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@university.ac.id"

    # Email monitoring / IMAP (where replies are received, e.g. mit@president.ac.id)
    IMAP_HOST: str = ""
    IMAP_PORT: int = 993
    IMAP_USERNAME: str = ""
    IMAP_PASSWORD: str = ""
    IMAP_USE_SSL: bool = True

    # LinkedIn Scraper
    LINKEDIN_LI_AT: str = ""

    # App
    SECRET_KEY: str = "change_me"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:80"]
    BASE_URL: str = "http://localhost:8000"

    # Default admin account — auto-created at startup if it doesn't exist,
    # so a fresh deployment is immediately usable for login.
    ADMIN_EMAIL: str = "admin@president.ac.id"
    ADMIN_PASSWORD: str = "admin123"


settings = Settings()
