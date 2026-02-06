"""Application configuration via environment variables."""

from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BODHISATTVA_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Database
    database_url: str = "postgresql+asyncpg://localhost:5432/bodhisattva"
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Invariant defaults
    u_max: Decimal = Decimal("0.5")
    ethics_margin_threshold: Decimal = Decimal("0.05")
    irreversibility_threshold: Decimal = Decimal("0.3")
    structural_risk_scale_threshold: Decimal = Decimal("5")
    uncertainty_dominance_threshold: Decimal = Decimal("0.7")

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False

    # Crypto
    signing_key: str = ""

    # Logging
    log_level: str = "INFO"
