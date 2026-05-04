from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(REPO_ROOT / ".env")
load_dotenv(BACKEND_ROOT / ".env")

PROJECT_ROOT = REPO_ROOT


@dataclass(frozen=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    backend_root: Path = BACKEND_ROOT
    raw_data_dir: Path = PROJECT_ROOT / os.getenv("RAW_DATA_DIR", "data")
    interim_data_dir: Path = PROJECT_ROOT / os.getenv("INTERIM_DATA_DIR", "data/interim")
    processed_data_dir: Path = PROJECT_ROOT / os.getenv("PROCESSED_DATA_DIR", "data/processed")
    reports_dir: Path = PROJECT_ROOT / os.getenv("REPORTS_DIR", "reports")
    models_dir: Path = PROJECT_ROOT / os.getenv("MODELS_DIR", "models")
    logs_dir: Path = PROJECT_ROOT / os.getenv("LOGS_DIR", "logs")
    backend_logs_dir: Path = PROJECT_ROOT / os.getenv("BACKEND_LOGS_DIR", "logs/backend")
    frontend_logs_dir: Path = PROJECT_ROOT / os.getenv("FRONTEND_LOGS_DIR", "logs/frontend")
    transaction_file: str = os.getenv("TRANSACTION_FILE", "tran_data.xlsx")
    property_shapefile: str = os.getenv("PROPERTY_SHAPEFILE", "ai_usecase_data240326.shp")
    road_shapefile: str = os.getenv("ROAD_SHAPEFILE", "ai_usecase_road240326.shp")
    facility_shapefile: str = os.getenv("FACILITY_SHAPEFILE", "ai_usecase_facilities240326.shp")
    mvdb_file: str = os.getenv("MVDB_FILE", "")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file_name: str = os.getenv("LOG_FILE_NAME", "valuation_poc.log")
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    cors_allowed_origins: str = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )

    @property
    def transaction_path(self) -> Path:
        configured_path = self.raw_data_dir / self.transaction_file
        preferred_autorecovered = self.raw_data_dir / "tran_data(AutoRecovered).xlsx"
        if preferred_autorecovered.exists():
            return preferred_autorecovered
        return configured_path

    @property
    def property_path(self) -> Path:
        return self.raw_data_dir / self.property_shapefile

    @property
    def road_path(self) -> Path:
        return self.raw_data_dir / self.road_shapefile

    @property
    def facility_path(self) -> Path:
        return self.raw_data_dir / self.facility_shapefile

    @property
    def mvdb_path(self) -> Path | None:
        if not self.mvdb_file:
            return None
        return self.raw_data_dir / self.mvdb_file

    @property
    def log_file_path(self) -> Path:
        return self.backend_logs_dir / self.log_file_name

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


settings = Settings()


def ensure_directories() -> None:
    for path in (
        settings.raw_data_dir,
        settings.interim_data_dir,
        settings.processed_data_dir,
        settings.reports_dir,
        settings.models_dir,
        settings.logs_dir,
        settings.backend_logs_dir,
        settings.frontend_logs_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def configure_logging() -> None:
    ensure_directories()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        settings.log_file_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=log_level,
        handlers=[stream_handler, file_handler],
        force=True,
    )
