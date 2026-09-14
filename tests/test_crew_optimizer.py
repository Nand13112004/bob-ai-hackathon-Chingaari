from src.advisor.crew_optimizer import crew_recommendation


def test_crew_recommendation_uses_available_valid_crew():
    result = crew_recommendation({'risk_level': 'HIGH'}, [
        {'crew_id': 'CR004', 'crew_name': 'Crew Delta', 'crew_type': 'Transformer Repair', 'skill_level': 'Advanced', 'available': True, 'distance_km': 12.5, 'max_distance_km': 75},
        {'crew_id': 'CR999', 'crew_name': 'Unavailable', 'crew_type': 'Transformer Repair', 'skill_level': 'Advanced', 'available': False, 'distance_km': 10, 'max_distance_km': 50},
    ])
    assert result['crew_id'] == 'CR004'
    assert result['deployment_action'] in {'PRE-POSITION CREW', 'DISPATCH CREW', 'MONITOR'}
