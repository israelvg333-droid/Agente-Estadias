from __future__ import annotations

from typing import Any

from src.scoring.decision_policy import decide_recommendation


def score_call(
    acoustic: dict[str, Any],
    semantic: dict[str, Any],
    intent: dict[str, Any],
    coherence: dict[str, Any],
) -> dict[str, Any]:
    evidence: list[str] = []
    completeness = float(semantic.get("completeness_score") or 0.0)
    coherence_score = float(coherence.get("coherence_score") or 0.0)
    has_emergency = bool(semantic.get("emergency_keywords") or semantic.get("incident_keywords"))
    has_location = bool(semantic.get("has_location"))
    has_joke = bool(semantic.get("joke_or_mockery_keywords"))
    silence_ratio = _nested_float(acoustic, "silence", "silence_ratio")
    audio_quality = acoustic.get("audio_quality")

    seriousness = 0.2
    seriousness += 0.25 if has_emergency else 0.0
    seriousness += 0.2 if has_location else 0.0
    seriousness += 0.2 * completeness
    seriousness += 0.15 * coherence_score
    if intent.get("has_high_risk_terms"):
        seriousness += 0.2
        evidence.append("Terminos de alto riesgo presentes.")
    if has_joke:
        seriousness -= 0.25
        evidence.append("Se detectaron terminos asociados a broma o burla.")
    if silence_ratio is not None and silence_ratio > 0.65:
        seriousness -= 0.08
        evidence.append("El audio contiene una proporcion alta de silencio.")
    if audio_quality in {"baja_senal", "mucho_silencio", "muy_corta"}:
        evidence.append(f"Calidad de audio limitada: {audio_quality}.")

    improcedence = 0.1
    improcedence += 0.35 if has_joke else 0.0
    improcedence += 0.2 if completeness < 0.5 else 0.0
    improcedence += 0.2 if coherence_score < 0.55 else 0.0
    improcedence += 0.1 if not has_emergency else 0.0
    improcedence += 0.1 if silence_ratio is not None and silence_ratio > 0.75 else 0.0
    if intent.get("has_high_risk_terms"):
        improcedence -= 0.25

    seriousness = _clamp(seriousness)
    improcedence = _clamp(improcedence)
    confidence = _estimate_confidence(acoustic, semantic, coherence)
    recommendation, policy_evidence = decide_recommendation(
        seriousness, improcedence, semantic, intent, coherence
    )
    evidence.extend(policy_evidence)
    evidence.extend(_semantic_evidence(semantic, intent, coherence))

    return {
        "seriousness_score": round(seriousness, 3),
        "improcedence_score": round(improcedence, 3),
        "confidence": round(confidence, 3),
        "recommendation": recommendation,
        "evidence": evidence,
        "safety_note": "Estimacion probabilistica. No recomienda colgar ni cerrar llamadas automaticamente.",
    }


def _semantic_evidence(
    semantic: dict[str, Any], intent: dict[str, Any], coherence: dict[str, Any]
) -> list[str]:
    evidence = []
    if semantic.get("emergency_keywords"):
        evidence.append(f"Palabras de emergencia: {', '.join(semantic['emergency_keywords'])}.")
    if semantic.get("incident_keywords"):
        evidence.append(f"Tipo de incidente detectado: {', '.join(semantic['incident_keywords'])}.")
    if semantic.get("has_location"):
        evidence.append("Se detecto posible ubicacion.")
    if semantic.get("has_affected_people"):
        evidence.append("Se mencionan posibles personas afectadas.")
    if coherence.get("evasive_responses"):
        evidence.append(f"Respuestas evasivas: {', '.join(coherence['evasive_responses'])}.")
    if coherence.get("simple_contradictions"):
        evidence.append("Se detectaron contradicciones simples.")
    if intent.get("intent"):
        evidence.append(f"Intencion estimada: {intent['intent']}.")
    return evidence


def _estimate_confidence(
    acoustic: dict[str, Any], semantic: dict[str, Any], coherence: dict[str, Any]
) -> float:
    confidence = 0.35
    if semantic.get("word_count", 0) >= 10:
        confidence += 0.2
    if acoustic.get("duration_seconds"):
        confidence += 0.15
    if acoustic.get("audio_quality") == "aceptable":
        confidence += 0.1
    confidence += 0.1 * float(semantic.get("completeness_score") or 0.0)
    confidence += 0.1 * float(coherence.get("coherence_score") or 0.0)
    return _clamp(confidence)


def _nested_float(data: dict[str, Any], key: str, nested_key: str) -> float | None:
    value = data.get(key, {})
    if not isinstance(value, dict):
        return None
    nested = value.get(nested_key)
    return float(nested) if nested is not None else None


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
