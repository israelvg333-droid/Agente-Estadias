from __future__ import annotations

import re
import unicodedata
from typing import Any


EMERGENCY_TERMS = {
    "emergencia", "auxilio", "ayuda", "urgente", "ambulancia", "policia",
    "bomberos", "incendio", "choque", "accidente", "asalto", "robo",
    "arma", "balazo", "disparo", "herido", "sangre", "violencia",
    "golpearon", "secuestro", "amenaza", "desmayo", "infarto", "medico",
}
JOKE_TERMS = {
    "jaja", "jeje", "risa", "broma", "mentira", "jugando", "molestar",
    "troleo", "falso", "no es cierto", "era broma", "jajaja", "xd",
}
LOCATION_HINTS = {
    "calle", "avenida", "colonia", "municipio", "delegacion", "esquina",
    "numero", "km", "kilometro", "carretera", "casa", "edificio",
    "parque", "escuela", "hospital", "tienda", "plaza",
}
VICTIM_HINTS = {
    "persona", "senor", "senora", "nino", "nina", "adulto", "herido",
    "victima", "mi mama", "mi papa", "mi hijo", "mi hija", "alguien",
    "conductor", "pasajero",
}
INCIDENT_HINTS = {
    "incendio", "robo", "asalto", "choque", "accidente", "pelea",
    "agresion", "violencia", "disparo", "balazo", "desmayo", "fuga",
    "gas", "inundacion", "amenaza", "secuestro",
}


def normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def analyze_text(text: str) -> dict[str, Any]:
    normalized = normalize_text(text)
    tokens = re.findall(r"\b[\w]+\b", normalized)
    word_count = len(tokens)
    emergency_matches = _find_terms(normalized, EMERGENCY_TERMS)
    joke_matches = _find_terms(normalized, JOKE_TERMS)
    has_location = bool(_find_terms(normalized, LOCATION_HINTS) or _has_address_like_text(normalized))
    has_victim = bool(_find_terms(normalized, VICTIM_HINTS))
    incident_matches = _find_terms(normalized, INCIDENT_HINTS)

    completeness_items = {
        "has_location": has_location,
        "has_affected_people": has_victim,
        "has_incident_type": bool(incident_matches),
        "has_minimum_detail": word_count >= 12,
    }
    completeness_score = sum(completeness_items.values()) / len(completeness_items)

    return {
        "word_count": word_count,
        "emergency_keywords": emergency_matches,
        "joke_or_mockery_keywords": joke_matches,
        "incident_keywords": incident_matches,
        "has_location": has_location,
        "has_affected_people": has_victim,
        "has_incident_type": bool(incident_matches),
        "completeness_items": completeness_items,
        "completeness_score": round(completeness_score, 3),
        "text_is_empty": word_count == 0,
    }


def _find_terms(text: str, terms: set[str]) -> list[str]:
    found = []
    for term in sorted(terms):
        normalized_term = normalize_text(term)
        if " " in normalized_term:
            if normalized_term in text:
                found.append(term)
        elif re.search(rf"\b{re.escape(normalized_term)}\b", text):
            found.append(term)
    return found


def _has_address_like_text(text: str) -> bool:
    return bool(re.search(r"\b(no\.?|numero|#)\s*\d+\b", text) or re.search(r"\b\d{2,5}\b", text))
