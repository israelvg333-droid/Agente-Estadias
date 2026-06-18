from __future__ import annotations

from typing import Any


VALID_RECOMMENDATIONS = {
    "continuar",
    "pedir_mas_informacion",
    "escalar_humano",
    "posible_improcedente",
}


def decide_recommendation(
    seriousness_score: float,
    improcedence_score: float,
    semantic: dict[str, Any],
    intent: dict[str, Any],
    coherence: dict[str, Any],
) -> tuple[str, list[str]]:
    evidence: list[str] = []
    has_location = bool(semantic.get("has_location"))
    has_incident = bool(semantic.get("has_incident_type"))
    completeness = float(semantic.get("completeness_score") or 0.0)
    coherence_score = float(coherence.get("coherence_score") or 0.0)
    has_joke = bool(semantic.get("joke_or_mockery_keywords"))

    if intent.get("has_high_risk_terms"):
        evidence.append("Se detectaron terminos de alto riesgo; se prioriza seguridad.")
        return "escalar_humano", evidence

    if has_incident and has_location and coherence_score >= 0.55:
        evidence.append("Hay incidente, ubicacion y coherencia suficiente.")
        return "continuar", evidence

    if improcedence_score >= 0.7 and has_joke and completeness < 0.5 and coherence_score < 0.6:
        evidence.append("Hay risas/broma, baja completitud y coherencia baja.")
        return "posible_improcedente", evidence

    if completeness < 0.75:
        evidence.append("Falta informacion critica para evaluar el reporte.")
        return "pedir_mas_informacion", evidence

    if seriousness_score < 0.45 and improcedence_score > 0.55:
        evidence.append("La estimacion sugiere baja seriedad, sin accion automatica de cierre.")
        return "posible_improcedente", evidence

    evidence.append("El caso conserva incertidumbre operativa.")
    return "pedir_mas_informacion", evidence
