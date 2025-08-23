import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Core AI APIs
    openai_api_key: str = ""
    google_api_key: str = ""
    anthropic_api_key: str = ""
    brave_api_key: str = ""
    replicate_api_key: str = ""
    
    # Gemini model settings
    gemini_model: str = "gemini-2.0-flash-exp"
    
    # Web Scraping
    playwright_headless: bool = True
    
    # Optional APIs (removed deprecated ones)
    uberduck_api_key: Optional[str] = None
    uberduck_secret: Optional[str] = None
    
    # Caching
    redis_url: str = "redis://localhost:6379"
    cache_enabled: bool = True
    
    # Configuration
    demo_mode: bool = False
    max_generation_time: int = 15
    target_audience: str = "yc"
    debug: bool = False
    log_level: str = "INFO"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # File paths
    assets_dir: str = "backend/assets"
    beats_dir: str = "backend/assets/beats"
    samples_dir: str = "backend/assets/samples"
    cache_dir: str = "cache"
    
    class Config:
        env_file = "backend/.env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    return settings


# Logging configuration
import logging

def setup_logging():
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("backend.log")
        ]
    )
    
    # Suppress verbose logs from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def validate_api_keys():
    """Validate that required API keys are present"""
    # At least one AI API key is required
    ai_keys = [
        ("OPENAI_API_KEY", settings.openai_api_key),
        ("GOOGLE_API_KEY", settings.google_api_key),
        ("ANTHROPIC_API_KEY", settings.anthropic_api_key),
    ]
    
    available_ai_keys = []
    for name, value in ai_keys:
        if value:
            available_ai_keys.append(name)
    
    if not available_ai_keys:
        raise ValueError("At least one AI API key is required: OPENAI_API_KEY, GOOGLE_API_KEY, or ANTHROPIC_API_KEY")
    
    logging.info(f"Available AI APIs: {', '.join(available_ai_keys)}")
    
    # Warn about recommended combinations
    if settings.google_api_key and not settings.openai_api_key:
        logging.warning("GOOGLE_API_KEY available but OPENAI_API_KEY missing - audio generation will use fallbacks")
    
    if not settings.google_api_key and not settings.anthropic_api_key:
        logging.warning("Only OPENAI_API_KEY available - consider adding GOOGLE_API_KEY for better profile analysis")


# Initialize logging on import (but not API validation)
setup_logging()

# Note: API validation is now optional - call validate_api_keys() explicitly when needed