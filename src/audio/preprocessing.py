from __future__ import annotations

from pathlib import Path
from typing import Any, Tuple


SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a"}


def validate_audio_path(audio_path: str | Path) -> Path:
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de audio: {path}")
    if path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
        raise ValueError(
            f"Formato no soportado: {path.suffix}. Use .wav, .mp3 o .m4a"
        )
    return path


def load_audio(audio_path: str | Path, sample_rate: int = 16000) -> Tuple[Any, int]:
    """Carga audio con librosa si esta disponible."""
    path = validate_audio_path(audio_path)
    try:
        import librosa
    except ImportError as exc:
        raise RuntimeError(
            "Para analizar audio instale dependencias: pip install -r requirements.txt. "
            "Tambien puede usar --transcript para ejecutar solo el analisis textual."
        ) from exc

    audio, sr = librosa.load(path, sr=sample_rate, mono=True)
    if audio.size == 0:
        raise ValueError("El archivo de audio no contiene muestras utiles.")
    return normalize_audio(audio), sr


def normalize_audio(audio: Any) -> Any:
    import numpy as np

    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak <= 1e-8:
        return audio.astype(np.float32)
    return (audio / peak).astype(np.float32)
