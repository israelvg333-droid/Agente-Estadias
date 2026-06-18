from __future__ import annotations

from pathlib import Path
from typing import Any


def transcribe_audio(audio_path: str | Path, language: str = "es") -> dict[str, Any]:
    path = Path(audio_path)
    try:
        import whisper
    except ImportError:
        return {
            "text": "",
            "engine": "fallback_required",
            "language": language,
            "status": "whisper_not_installed",
            "message": "Whisper no esta instalado. Use --transcript archivo.txt.",
        }

    model = whisper.load_model("base")
    result = model.transcribe(str(path), language=language)
    return {
        "text": (result.get("text") or "").strip(),
        "engine": "openai-whisper-local-base",
        "language": result.get("language", language),
        "status": "ok",
        "segments": result.get("segments", []),
    }


def read_manual_transcript(transcript_path: str | Path) -> dict[str, Any]:
    path = Path(transcript_path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de transcripcion: {path}")
    if path.suffix.lower() != ".txt":
        raise ValueError("La transcripcion manual debe ser un archivo .txt")
    return {
        "text": path.read_text(encoding="utf-8").strip(),
        "engine": "manual_txt",
        "language": "es",
        "status": "ok",
        "source": str(path),
    }
