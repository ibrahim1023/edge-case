from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    elevenlabs_api_key: str | None = None
    elevenlabs_agent_id: str | None = None
    context_dev_api_key: str | None = None
    context_dev_base_url: str = "https://api.context.dev/v1"
    devin_token: str | None = None
    devin_base_url: str = "https://api.devin.ai/v3"
    github_token: str | None = None
    use_mocks: bool = True
    repo_clone_dir: Path = Path("/tmp/edgecase_repos")


settings = Settings()
