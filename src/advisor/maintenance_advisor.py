from __future__ import annotations

from typing import List


def maintenance_recommendation(sensor: dict, probability: float, asset: dict | None = None) -> str:
    reasons = []
    if sensor.get('temperature_c', 0) > 80:
        reasons.append('Inspect cooling system and thermal loading.')
    if sensor.get('vibration_mm_s', 0) > 5:
        reasons.append('Inspect mechanical mounting and transformer vibration.')
    if sensor.get('partial_discharge_pc', 0) > 30:
        reasons.append('Inspect insulation condition and perform diagnostic testing.')
    if sensor.get('oil_moisture_ppm', 0) > 25:
        reasons.append('Inspect oil moisture and dehydration requirements.')
    if sensor.get('oil_acidity_mgKOH_g', 0) > 0.12:
        reasons.append('Inspect oil quality and consider oil treatment/replacement.')
    if sensor.get('load_percentage', 0) > 85:
        reasons.append('Inspect thermal loading and overload risk.')
    if probability > 0.55:
        reasons.append('Failure probability exceeds the 7-day threshold.')
    if not reasons:
        return 'Routine monitoring is adequate for the current operating conditions.'
    if len(reasons) > 1:
        return 'Immediate preventive inspection recommended. ' + ' '.join(reasons[:2])
    return reasons[0]
