from __future__ import annotations

from typing import Dict, List
from math import asin, cos, radians, sin, sqrt


def distance_km(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    earth_radius_km = 6371.0
    delta_latitude = radians(latitude_b - latitude_a)
    delta_longitude = radians(longitude_b - longitude_a)
    value = sin(delta_latitude / 2) ** 2 + cos(radians(latitude_a)) * cos(radians(latitude_b)) * sin(delta_longitude / 2) ** 2
    return earth_radius_km * 2 * asin(sqrt(value))


def crew_recommendation(transformer: dict, crews: List[dict]) -> Dict[str, object]:
    valid = []
    for crew in crews:
        if not crew.get('available', False):
            continue
        if all(key in transformer for key in ('latitude', 'longitude')) and all(key in crew for key in ('base_latitude', 'base_longitude')):
            distance = distance_km(float(crew['base_latitude']), float(crew['base_longitude']), float(transformer['latitude']), float(transformer['longitude']))
        else:
            distance = float(crew.get('distance_km', 0.0))
        if distance > float(crew.get('max_distance_km', 0.0)):
            continue
        valid.append({
            'crew_id': crew.get('crew_id'),
            'crew_name': crew.get('crew_name'),
            'crew_type': crew.get('crew_type'),
            'skill_level': crew.get('skill_level'),
            'distance_km': distance,
            'available': True,
            'score': (5 if crew.get('skill_level') == 'Expert' else 3) - (distance * 0.1),
        })
    if not valid:
        return {
            'crew_id': None,
            'crew_name': None,
            'crew_type': None,
            'skill_level': None,
            'distance_km': None,
            'deployment_action': 'NO ACTION',
            'reason': 'No valid crew is available within the allowed deployment distance.',
        }
    chosen = sorted(valid, key=lambda x: (x['distance_km'], -x['score']))[0]
    risk = transformer.get('risk_level', 'MEDIUM')
    if risk in ('CRITICAL', 'HIGH'):
        action = 'PRE-POSITION CREW'
    elif risk == 'MEDIUM':
        action = 'DISPATCH CREW'
    else:
        action = 'MONITOR'
    return {
        'crew_id': chosen['crew_id'],
        'crew_name': chosen['crew_name'],
        'crew_type': chosen['crew_type'],
        'skill_level': chosen['skill_level'],
        'distance_km': round(chosen['distance_km'], 2),
        'deployment_action': action,
        'reason': f'{risk} risk requires {chosen["crew_type"]} response within {chosen["distance_km"]:.2f} km.',
    }
