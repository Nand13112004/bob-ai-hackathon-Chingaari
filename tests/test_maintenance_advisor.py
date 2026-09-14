from src.advisor.maintenance_advisor import maintenance_recommendation


def test_maintenance_recommendation_contains_reason():
    advice = maintenance_recommendation({
        'temperature_c': 85,
        'vibration_mm_s': 5.2,
        'partial_discharge_pc': 35,
        'oil_moisture_ppm': 30,
        'oil_acidity_mgKOH_g': 0.15,
        'load_percentage': 90,
    }, 0.62)
    assert 'Immediate preventive inspection recommended.' in advice or 'Inspect' in advice
