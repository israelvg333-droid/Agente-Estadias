from __future__ import annotations

from dataclasses import asdict
from typing import Any

from src.audio.emergency_indicators import (
    derive_emergency_audio_indicators,
    empty_emergency_audio_indicators,
)
from src.utils.config import AudioAnalysisConfig


_SPEECH_F0_MIN_HZ = 70.0
_SPEECH_F0_MAX_HZ = 600.0
_N_MFCC = 13


def extract_acoustic_features(
    audio: Any, sample_rate: int, config: AudioAnalysisConfig | None = None
) -> dict[str, Any]:
    import numpy as np

    from src.audio.vad import estimate_silence

    cfg = config or AudioAnalysisConfig(sample_rate=sample_rate)
    duration = float(len(audio) / sample_rate) if sample_rate else 0.0
    rms_frames = _frame_rms(audio)
    rms = float(np.sqrt(np.mean(audio**2))) if audio.size else 0.0
    mean_frame_energy = float(np.mean(rms_frames)) if rms_frames.size else rms
    max_frame_energy = float(np.max(rms_frames)) if rms_frames.size else rms
    energy_std = float(np.std(rms_frames)) if rms_frames.size else 0.0
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    zcr = _zero_crossing_rate(audio)
    silence = estimate_silence(audio, sample_rate)
    f0_stats = _estimate_f0_stats(audio, sample_rate)
    tempo = _estimate_tempo(audio, sample_rate)
    clipping = _estimate_clipping(audio)
    snr = _estimate_snr(audio, rms_frames)
    mfcc_stats = _extract_mfcc_stats(audio, sample_rate)
    spectral_centroid = _extract_spectral_centroid(audio, sample_rate)
    quality = _estimate_quality(
        rms=rms,
        peak=peak,
        silence_ratio=silence.silence_ratio,
        duration=duration,
        clipping_ratio=clipping,
        snr_db=snr,
    )
    anomaly_flags = _detect_anomalies(
        mean_energy=mean_frame_energy,
        max_energy=max_frame_energy,
        silence_ratio=silence.silence_ratio,
        mean_pause_seconds=silence.mean_pause_seconds,
        longest_pause_seconds=silence.longest_pause_seconds,
        audio_quality=quality,
        clipping_ratio=clipping,
        snr_db=snr,
        energy_std=energy_std,
    )

    features = {
        "duration_seconds": round(duration, 3),
        "rms_energy": round(rms, 6),
        "mean_energy": round(mean_frame_energy, 6),
        "max_energy": round(max_frame_energy, 6),
        "energy_std": round(energy_std, 6),
        "peak_amplitude": round(peak, 6),
        "zero_crossing_rate": round(zcr, 6),
        "estimated_tempo_bpm": round(tempo, 3) if tempo else None,
        "estimated_f0_hz": _round_optional(f0_stats["mean"]),
        "estimated_f0_min_hz": _round_optional(f0_stats["min"]),
        "estimated_f0_max_hz": _round_optional(f0_stats["max"]),
        "estimated_f0_std_hz": _round_optional(f0_stats["std"]),
        "mfcc_mean": mfcc_stats["mean"],
        "mfcc_std": mfcc_stats["std"],
        "spectral_centroid_hz": _round_optional(spectral_centroid),
        "silence_ratio": round(silence.silence_ratio, 6),
        "pause_count": silence.pause_count,
        "mean_pause_seconds": round(silence.mean_pause_seconds, 3),
        "longest_pause_seconds": round(silence.longest_pause_seconds, 3),
        "silence": asdict(silence),
        "approx_speech_rate": None,
        "audio_quality": quality,
        "clipping_ratio": round(clipping, 6),
        "estimated_snr_db": round(snr, 3) if snr is not None else None,
        "acoustic_anomaly_flags": anomaly_flags,
    }
    features["emergency_audio_indicators"] = derive_emergency_audio_indicators(
        features, cfg
    )
    return features


def enrich_with_text_rate(features: dict[str, Any], transcript: str) -> dict[str, Any]:
    duration = float(features.get("duration_seconds") or 0.0)
    words = [w for w in transcript.split() if w.strip()]
    rate = len(words) / duration * 60.0 if duration > 0 else None
    features["approx_speech_rate"] = round(rate, 2) if rate is not None else None
    features["word_count_from_transcript"] = len(words)
    if features.get("duration_seconds"):
        features["emergency_audio_indicators"] = derive_emergency_audio_indicators(
            features
        )
    return features


def empty_acoustic_features(reason: str = "sin_audio") -> dict[str, Any]:
    return {
        "duration_seconds": None,
        "rms_energy": None,
        "mean_energy": None,
        "max_energy": None,
        "energy_std": None,
        "peak_amplitude": None,
        "zero_crossing_rate": None,
        "estimated_tempo_bpm": None,
        "estimated_f0_hz": None,
        "estimated_f0_min_hz": None,
        "estimated_f0_max_hz": None,
        "estimated_f0_std_hz": None,
        "mfcc_mean": None,
        "mfcc_std": None,
        "spectral_centroid_hz": None,
        "silence_ratio": None,
        "pause_count": None,
        "mean_pause_seconds": None,
        "longest_pause_seconds": None,
        "silence": {
            "silence_ratio": None,
            "pause_count": None,
            "mean_pause_seconds": None,
            "longest_pause_seconds": None,
        },
        "approx_speech_rate": None,
        "word_count_from_transcript": None,
        "audio_quality": "no_evaluada",
        "clipping_ratio": None,
        "estimated_snr_db": None,
        "acoustic_anomaly_flags": [],
        "emergency_audio_indicators": empty_emergency_audio_indicators(reason),
        "note": reason,
    }


def _frame_rms(audio: Any, frame_length: int = 2048, hop_length: int = 512) -> Any:
    import numpy as np

    if audio.size == 0:
        return np.array([], dtype=np.float32)
    if audio.size < frame_length:
        return np.array([float(np.sqrt(np.mean(audio**2)))], dtype=np.float32)
    try:
        import librosa

        return librosa.feature.rms(
            y=audio, frame_length=frame_length, hop_length=hop_length
        )[0]
    except Exception:
        frame_count = 1 + (len(audio) - frame_length) // hop_length
        frames = np.stack(
            [
                audio[i * hop_length : i * hop_length + frame_length]
                for i in range(frame_count)
            ]
        )
        return np.sqrt(np.mean(frames**2, axis=1))


def _zero_crossing_rate(audio: Any) -> float:
    import numpy as np

    if audio.size < 2:
        return 0.0
    return float(np.mean(np.abs(np.diff(np.signbit(audio)))))


def _estimate_tempo(audio: Any, sample_rate: int) -> float | None:
    try:
        import librosa

        analysis_audio = _analysis_window(audio, sample_rate)
        tempo = librosa.feature.rhythm.tempo(y=analysis_audio, sr=sample_rate)
        if len(tempo) == 0:
            return None
        return float(tempo[0])
    except Exception:
        return None


def _estimate_f0_stats(audio: Any, sample_rate: int) -> dict[str, float | None]:
    """Estima estadísticas de F0 filtrando solo el rango de voz humana típica."""
    try:
        import librosa
        import numpy as np

        analysis_audio = _analysis_window(audio, sample_rate)
        f0_values = librosa.yin(
            analysis_audio,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sample_rate,
        )
        # Filtrar rango de voz humana (70-600 Hz); librosa.yin devuelve fmin para tramos
        # no vocales, por lo que np.isfinite no es suficiente como filtro.
        valid = f0_values[
            np.isfinite(f0_values)
            & (f0_values >= _SPEECH_F0_MIN_HZ)
            & (f0_values <= _SPEECH_F0_MAX_HZ)
        ]
        if valid.size == 0:
            return {"mean": None, "min": None, "max": None, "std": None}
        return {
            "mean": float(np.mean(valid)),
            "min": float(np.min(valid)),
            "max": float(np.max(valid)),
            "std": float(np.std(valid)),
        }
    except Exception:
        return {"mean": None, "min": None, "max": None, "std": None}


def _extract_mfcc_stats(audio: Any, sample_rate: int) -> dict[str, list[float] | None]:
    """Extrae media y desviación estándar de los primeros N MFCCs."""
    try:
        import librosa
        import numpy as np

        analysis_audio = _analysis_window(audio, sample_rate)
        mfccs = librosa.feature.mfcc(y=analysis_audio, sr=sample_rate, n_mfcc=_N_MFCC)
        return {
            "mean": [round(float(np.mean(mfccs[i])), 4) for i in range(_N_MFCC)],
            "std": [round(float(np.std(mfccs[i])), 4) for i in range(_N_MFCC)],
        }
    except Exception:
        return {"mean": None, "std": None}


def _extract_spectral_centroid(audio: Any, sample_rate: int) -> float | None:
    """Calcula la media del centroide espectral (Hz). Relacionado con el brillo tonal."""
    try:
        import librosa
        import numpy as np

        analysis_audio = _analysis_window(audio, sample_rate)
        centroid = librosa.feature.spectral_centroid(y=analysis_audio, sr=sample_rate)
        return float(np.mean(centroid))
    except Exception:
        return None


def _analysis_window(audio: Any, sample_rate: int, max_seconds: float = 20.0) -> Any:
    max_samples = int(sample_rate * max_seconds)
    if audio.size <= max_samples:
        return audio
    return audio[:max_samples]


def _estimate_clipping(audio: Any, threshold: float = 0.98) -> float:
    import numpy as np

    if audio.size == 0:
        return 0.0
    return float(np.mean(np.abs(audio) >= threshold))


def _estimate_snr(audio: Any, rms_frames: Any) -> float | None:
    import numpy as np

    if audio.size == 0 or rms_frames.size < 4:
        return None
    noise_floor = float(np.percentile(rms_frames, 10))
    signal_level = float(np.percentile(rms_frames, 90))
    if noise_floor <= 1e-8 or signal_level <= 1e-8:
        return None
    return float(20.0 * np.log10(signal_level / noise_floor))


def _estimate_quality(
    rms: float,
    peak: float,
    silence_ratio: float,
    duration: float,
    clipping_ratio: float,
    snr_db: float | None,
) -> str:
    if duration < 0.5:
        return "muy_corta"
    if rms < 0.005 or peak < 0.02:
        return "baja_senal"
    if silence_ratio > 0.75:
        return "mucho_silencio"
    if clipping_ratio > 0.01 or peak > 0.995:
        return "posible_saturacion"
    if snr_db is not None and snr_db < 8.0:
        return "ruido_alto"
    return "aceptable"


def _detect_anomalies(
    mean_energy: float,
    max_energy: float,
    silence_ratio: float,
    mean_pause_seconds: float,
    longest_pause_seconds: float,
    audio_quality: str,
    clipping_ratio: float,
    snr_db: float | None,
    energy_std: float,
) -> list[str]:
    flags: list[str] = []
    if silence_ratio >= 0.65:
        flags.append("alta_proporcion_silencio")
    if mean_energy < 0.025 and max_energy < 0.12:
        flags.append("energia_vocal_baja")
    if mean_pause_seconds >= 1.0 or longest_pause_seconds >= 2.0:
        flags.append("pausas_prolongadas")
    if audio_quality in {"baja_senal", "mucho_silencio", "posible_saturacion", "ruido_alto"}:
        flags.append("posible_mala_calidad_audio")
    if clipping_ratio > 0.01:
        flags.append("posible_clipping")
    if snr_db is not None and snr_db < 8.0:
        flags.append("snr_bajo")
    if energy_std > 0.08:
        flags.append("variabilidad_acustica")
    return flags


def _round_optional(value: float | None, digits: int = 3) -> float | None:
    return round(value, digits) if value is not None else None
