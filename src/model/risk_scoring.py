from __future__ import annotations

from typing import Dict, List


def classify_risk(score: float) -> str:
    if score >= 70:
        return 'CRITICAL'
    if score >= 50:
        return 'HIGH'
    if score >= 25:
        return 'MEDIUM'
    return 'LOW'


def priority_for_risk(risk: str) -> str:
    mapping = {
        'CRITICAL': 'P1 - CRITICAL',
        'HIGH': 'P2 - HIGH',
        'MEDIUM': 'P3 - MEDIUM',
        'LOW': 'P4 - LOW',
    }
    return mapping.get(risk, 'P4 - LOW')


def calculate_risk(probability: float, grid_impact: float, weather_risk: float, asset_criticality: float = 0.0, historical_risk: float = 0.0, maintenance_condition: float = 0.0) -> Dict[str, float | str]:
    score = (
        probability * 100.0 * 0.55
        + grid_impact * 100.0 * 0.30
        + weather_risk * 100.0 * 0.15
        + asset_criticality * 10.0
        + historical_risk * 10.0
        + maintenance_condition * 10.0
    )
    risk = classify_risk(score)
    return {
        'risk_score': round(score, 2),
        'risk_level': risk,
        'priority': priority_for_risk(risk),
    }
