import pandas as pd

from src.model.feature_engineering import build_feature_frame


def test_feature_build_generates_columns():
    sensor = pd.DataFrame([
        {
            'timestamp': '2026-01-01 00:00:00',
            'transformer_id': 'TR001',
            'temperature_c': 65.0,
            'vibration_mm_s': 2.1,
            'partial_discharge_pc': 11.0,
            'oil_temperature_c': 50.0,
            'oil_moisture_ppm': 20.0,
            'oil_acidity_mgKOH_g': 0.09,
            'load_percentage': 60.0,
            'voltage_kv': 10.0,
            'current_a': 80.0,
        }
    ])
    features = build_feature_frame(sensor, sensor)
    assert 'temperature_c_mean_24h' in features.columns
    assert 'partial_discharge_pc_max_24h' in features.columns
    assert 'maintenance_result_risk' in features.columns
