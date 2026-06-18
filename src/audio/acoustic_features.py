from __future__ import annotations

from dataclasses import asdict
from typing import Any


def extract_acoustic_features(audio: Any, sample_rate: int) -> dict[str, Any]:
    import numpy as np

    from src.audio.vad import estimate_silence

    duration = float(len(audio) / sample_rate) if sample_rate else 0.0
    rms = float(np.sqrt(np.mean(audio**2))) if audio.size else 0.0
    energy_std = float(np.std(audio**2)) if audio.size else 0.0
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    zcr = _zero_crossing_rate(audio)
    silence = estimate_silence(audio, sample_rate)
    f0 = _estimate_f0(audio, sample_rate)
    quality = _estimate_quality(rms, peak, silence.silence_ratio, duration)

    return {
        "duration_seconds": round(duration, 3),
        "mean_energy": round(rms, 6),
        "energy_std": round(energy_std, 6),
        "peak_amplitude": round(peak, 6),
        "zero_crossing_rate": round(zcr, 6),
        "estimated_f0_hz": round(f0, 3) if f0 else None,
        "silence": asdict(silence),
        "approx_speech_rate": None,
        "audio_quality": quality,
    }


def enrich_with_text_rate(features: dict[str, Any], transcript: str) -> dict[str, Any]:
    duration = float(features.get("duration_seconds") or 0.0)
    words = [w for w in transcript.split() if w.strip()]
    rate = len(words) / duration * 60.0 if duration > 0 else None
    features["approx_speech_rate"] = round(rate, 2) if rate is not None else None
    features["word_count_from_transcript"] = len(words)
    return features


def empty_acoustic_features(reason: str = "sin_audio") -> dict[str, Any]:
    return {
        "duration_seconds": None,
        "mean_energy": None,
        "energy_std": None,
        "peak_amplitude": None,
        "zero_crossing_rate": None,
        "estimated_f0_hz": None,
        "silence": {
            "silence_ratio": None,
            "pause_count": None,
            "mean_pause_seconds": None,
            "longest_pause_seconds": None,
        },
        "approx_speech_rate": None,
        "audio_quality": "no_evaluada",
        "note": reason,
    }


def _zero_crossing_rate(audio: Any) -> float:
    import numpy as np

    if audio.size < 2:
        return 0.0
    return float(np.mean(np.abs(np.diff(np.signbit(audio)))))


def _estimate_f0(audio: Any, sample_rate: int) -> float | None:
    try:
        import librosa
        import numpy as np

        f0_values, _, _ = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sample_rate,
        )
        valid = f0_values[~np.isnan(f0_values)]
        if valid.size == 0:
            return None
        return float(np.median(valid))
    except Exception:
        return None


def _estimate_quality(rms: float, peak: float, silence_ratio: float, duration: float) -> str:
    if duration < 0.5:
        return "muy_corta"
    if rms < 0.005 or peak < 0.02:
        return "baja_senal"
    if silence_ratio > 0.75:
        return "mucho_silencio"
    if peak > 0.98:
        return "posible_saturacion"
    return "aceptable"
