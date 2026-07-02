from __future__ import annotations

from src.audio.emergency_indicators import (
    derive_emergency_audio_indicators,
    empty_emergency_audio_indicators,
)


def test_empty_indicators_are_explicitly_unavailable():
    result = empty_emergency_audio_indicators("sin_audio")

    assert result["seriousness_audio_score"] is None
    assert result["audio_reliability"] == 0.0
    assert result["method"] == "not_available"


def test_high_stress_audio_features_raise_audio_seriousness():
    features = {
        "duration_seconds": 18.0,
        "energy_std": 0.13,
        "mean_energy": 0.12,
        "max_energy": 0.55,
        "estimated_f0_hz": 250.0,
        "estimated_f0_min_hz": 110.0,
        "estimated_f0_max_hz": 390.0,
        "estimated_f0_std_hz": 85.0,
        "approx_speech_rate": 225.0,
        "silence_ratio": 0.12,
        "pause_count": 4,
        "longest_pause_seconds": 0.8,
        "estimated_snr_db": 20.0,
        "clipping_ratio": 0.0,
        "zero_crossing_rate": 0.12,
        "spectral_centroid_hz": 2600.0,
        "audio_quality": "aceptable",
    }

    result = derive_emergency_audio_indicators(features)

    assert result["seriousness_audio_score"] >= 0.6
    assert "stress_vocal_alto" in result["indicator_flags"]
    assert result["audio_reliability"] >= 0.8


def test_calm_features_keep_audio_seriousness_lower():
    features = {
        "duration_seconds": 20.0,
        "energy_std": 0.01,
        "mean_energy": 0.03,
        "max_energy": 0.1,
        "estimated_f0_hz": 150.0,
        "estimated_f0_min_hz": 130.0,
        "estimated_f0_max_hz": 170.0,
        "estimated_f0_std_hz": 8.0,
        "approx_speech_rate": 120.0,
        "silence_ratio": 0.25,
        "pause_count": 2,
        "longest_pause_seconds": 0.6,
        "estimated_snr_db": 18.0,
        "clipping_ratio": 0.0,
        "zero_crossing_rate": 0.04,
        "spectral_centroid_hz": 1400.0,
        "audio_quality": "aceptable",
    }

    result = derive_emergency_audio_indicators(features)

    assert result["seriousness_audio_score"] < 0.35
    assert result["calm_score"] >= 0.6
