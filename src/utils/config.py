from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
AUDIO_DIR = DATA_DIR / "audios"
OUTPUT_DIR = DATA_DIR / "outputs"


@dataclass(frozen=True)
class AppConfig:
    sample_rate: int = 16000
    min_audio_seconds: float = 0.5
    output_dir: Path = OUTPUT_DIR
    audio_dir: Path = AUDIO_DIR


def ensure_directories() -> None:
    for path in (DATA_DIR, AUDIO_DIR, OUTPUT_DIR):
        path.mkdir(parents=True, exist_ok=True)
