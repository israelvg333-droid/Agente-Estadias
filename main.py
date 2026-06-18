from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.asr.transcriber import read_manual_transcript, transcribe_audio
from src.audio.acoustic_features import (
    empty_acoustic_features,
    enrich_with_text_rate,
    extract_acoustic_features,
)
from src.audio.preprocessing import load_audio, validate_audio_path
from src.report.implementation_report import build_result_payload, save_result
from src.scoring.seriousness_scorer import score_call
from src.semantic.coherence_analyzer import analyze_coherence
from src.semantic.intent_analyzer import analyze_intent
from src.semantic.text_analyzer import analyze_text
from src.utils.config import AppConfig, ensure_directories
from src.utils.logger import get_logger


logger = get_logger("subagente_seriedad")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MVP local para estimar probabilisticamente la seriedad de llamadas."
    )
    parser.add_argument("--audio", help="Ruta a archivo .wav, .mp3 o .m4a")
    parser.add_argument("--transcript", help="Ruta a transcripcion manual .txt")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directorio de salida. Por defecto: data/outputs/",
    )
    parser.add_argument("--language", default="es", help="Idioma para Whisper local.")
    return parser.parse_args()


def run_pipeline(args: argparse.Namespace) -> Path:
    config = AppConfig()
    ensure_directories()
    output_dir = Path(args.output_dir) if args.output_dir else config.output_dir

    if not args.audio and not args.transcript:
        raise ValueError("Debe proporcionar --audio o --transcript.")

    transcript = _get_transcript(args)
    transcript_text = transcript.get("text", "")
    acoustic = _get_acoustic_features(args.audio, transcript_text, config)
    semantic = analyze_text(transcript_text)
    intent = analyze_intent(semantic)
    coherence = analyze_coherence(transcript_text)
    score = score_call(acoustic, semantic, intent, coherence)

    payload = build_result_payload(
        transcript=transcript,
        acoustic_features=acoustic,
        semantic_analysis=semantic,
        intent_analysis=intent,
        coherence_analysis=coherence,
        score=score,
        input_metadata={
            "audio": str(args.audio) if args.audio else None,
            "transcript": str(args.transcript) if args.transcript else None,
            "mode": "audio" if args.audio else "transcript_only",
        },
    )
    output_path = save_result(payload, output_dir)
    print(json.dumps(payload["score"], ensure_ascii=False, indent=2))
    print(f"\nResultado guardado en: {output_path}")
    return output_path


def _get_transcript(args: argparse.Namespace) -> dict[str, Any]:
    if args.transcript:
        return read_manual_transcript(args.transcript)
    validate_audio_path(args.audio)
    transcript = transcribe_audio(args.audio, language=args.language)
    if transcript.get("status") != "ok":
        logger.warning(transcript.get("message", "No se pudo transcribir audio."))
    return transcript


def _get_acoustic_features(
    audio_path: str | None, transcript_text: str, config: AppConfig
) -> dict[str, Any]:
    if not audio_path:
        return empty_acoustic_features("modo_transcript_only")
    try:
        audio, sample_rate = load_audio(audio_path, sample_rate=config.sample_rate)
        features = extract_acoustic_features(audio, sample_rate)
        return enrich_with_text_rate(features, transcript_text)
    except Exception as exc:
        logger.warning("No se pudieron extraer features acusticas: %s", exc)
        return empty_acoustic_features(str(exc))


def main() -> None:
    args = parse_args()
    try:
        run_pipeline(args)
    except Exception as exc:
        logger.error("Ejecucion fallida: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
