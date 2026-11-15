import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    app_name: str = "VerbalPause — Adversarial Voice AI Negotiation Platform"
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    deepgram_api_key: str = os.getenv("DEEPGRAM_API_KEY", "")
    cartesia_api_key: str = os.getenv("CARTESIA_API_KEY", "")
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")

    # LLM Settings
    default_model: str = "llama-3.3-70b-versatile"
    fast_model: str = "llama-3.1-8b-instant"

    # Emotion & Interruption Thresholds
    initial_patience: float = 100.0
    initial_skepticism: float = 50.0
    patience_decay_rate: float = 3.5  # points per second after talk threshold
    monologue_warn_seconds: float = 12.0
    monologue_interrupt_seconds: float = 18.0
    interruption_patience_threshold: float = 35.0

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
