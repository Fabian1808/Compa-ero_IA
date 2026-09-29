from enum import Enum
from dataclasses import dataclass


class ConfidenceTier(str, Enum):
    AUTO_CREATE = "auto_create"
    SUGGEST_CONFIRM = "suggest_confirm"
    LOW_CONFIDENCE = "low_confidence"


@dataclass
class ConfidenceDecision:
    tier: ConfidenceTier
    score: int
    reasoning: str
    requires_confirmation: bool


def evaluate_confidence(score: int, risk_level: str = "medium") -> ConfidenceDecision:
    """
    Evaluate confidence score and determine action tier.

    risk_level:
    - low: crear tarea (bajo riesgo)
    - medium: crear compromiso, deadline (medio riesgo)
    - high: enviar correo, modificar datos importantes (alto riesgo)
    """
    if risk_level == "high":
        auto_threshold, suggest_threshold = 98, 90
    elif risk_level == "low":
        auto_threshold, suggest_threshold = 90, 70
    else:
        auto_threshold, suggest_threshold = 95, 80

    if score >= auto_threshold:
        return ConfidenceDecision(
            ConfidenceTier.AUTO_CREATE,
            score,
            "Alta confianza, acción de bajo riesgo",
            False
        )
    elif score >= suggest_threshold:
        return ConfidenceDecision(
            ConfidenceTier.SUGGEST_CONFIRM,
            score,
            "Confianza media, requiere confirmación del usuario",
            True
        )
    else:
        return ConfidenceDecision(
            ConfidenceTier.LOW_CONFIDENCE,
            score,
            "Baja confianza, no actuar automáticamente",
            True
        )


def get_default_thresholds() -> dict[str, int]:
    return {
        "auto_create": 95,
        "suggest_confirm": 80,
    }