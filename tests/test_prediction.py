import pandas as pd

from src.model.predict import predict_batch, predict_single


def test_predict_single_returns_probability():
    result = predict_single('TR001', {
        'timestamp': '2026-09-13 10:00:00',
        'temperature_c': 68.0,
        'vibration_mm_s': 2.2,
        'partial_discharge_pc': 18.0,
        'oil_temperature_c': 52.0,
        'oil_moisture_ppm': 22.0,
        'oil_acidity_mgKOH_g': 0.11,
        'load_percentage': 65.0,
        'voltage_kv': 11.0,
        'current_a': 92.0,
        'humidity_percentage': 70.0,
        'rainfall_mm': 0.5,
        'wind_speed_kmh': 14.0,
        'pressure_hpa': 1012.0,
        'lightning_probability': 0.01,
        'storm_probability': 0.02,
        'flood_risk': 0.03,
    })
    assert 'failure_probability' in result
    assert 0.0 <= result['failure_probability'] <= 1.0


def test_predict_batch_loads_serialized_pipeline():
    reading = {
        'transformer_id': 'TR001',
        'timestamp': '2026-09-13 10:00:00',
        'temperature_c': 68.0,
        'vibration_mm_s': 2.2,
        'partial_discharge_pc': 18.0,
        'oil_temperature_c': 52.0,
        'oil_moisture_ppm': 22.0,
        'oil_acidity_mgKOH_g': 0.11,
        'load_percentage': 65.0,
        'voltage_kv': 11.0,
        'current_a': 92.0,
        'humidity_percentage': 70.0,
        'rainfall_mm': 0.5,
        'wind_speed_kmh': 14.0,
        'pressure_hpa': 1012.0,
        'lightning_probability': 0.01,
        'storm_probability': 0.02,
        'flood_risk': 0.03,
    }
    result = predict_batch(pd.DataFrame([reading]))
    assert result[0]['transformer_id'] == 'TR001'
    assert 0.0 <= result[0]['failure_probability'] <= 1.0
