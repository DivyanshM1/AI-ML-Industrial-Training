from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py is backend/app/core/config.py; parents[3] is the Spectra project root.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SPECTRA_", env_file=".env", extra="ignore")
    dataset_dir: Path = PROJECT_ROOT / "datasets" / "ml-1m"
    model_dir: Path = PROJECT_ROOT / "models"
    database_path: Path = PROJECT_ROOT / "data" / "spectra.db"
    api_title: str = "Spectra API"
    api_version: str = "1.0.0"
    tmdb_read_access_token: str = ""

    def prepare_directories(self) -> None:
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.prepare_directories()
MODEL_PATH = settings.model_dir / "spectra_recommender.joblib"
