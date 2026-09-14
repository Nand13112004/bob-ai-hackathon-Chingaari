from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / 'data'
LOCATION_BY_SUBSTATION = {f'SS{index:02d}': f'LOC{index:02d}' for index in range(1, 11)}


@lru_cache(maxsize=1)
def load_feature_sources() -> Dict[str, pd.DataFrame]:
    return {
        'weather': pd.read_csv(DATA_DIR / 'weather_data.csv'),
        'transformers': pd.read_csv(DATA_DIR / 'transformers.csv'),
        'incidents': pd.read_csv(DATA_DIR / 'incidents.csv'),
        'maintenance': pd.read_csv(DATA_DIR / 'maintenance.csv'),
    }


def load_data() -> Dict[str, pd.DataFrame]:
    data = {
        'transformers': pd.read_csv(DATA_DIR / 'transformers.csv'),
        'sensor': pd.read_csv(DATA_DIR / 'sensor_readings.csv'),
        'weather': pd.read_csv(DATA_DIR / 'weather_data.csv'),
        'incidents': pd.read_csv(DATA_DIR / 'incidents.csv'),
        'maintenance': pd.read_csv(DATA_DIR / 'maintenance.csv'),
        'crew': pd.read_csv(DATA_DIR / 'crew.csv'),
    }
    return {
        **data,
        'sensor': to_datetime_columns(data['sensor'], ['timestamp']),
        'weather': to_datetime_columns(data['weather'], ['timestamp']),
        'incidents': to_datetime_columns(data['incidents'], ['incident_date']),
        'maintenance': to_datetime_columns(data['maintenance'], ['maintenance_date', 'next_maintenance_date']),
    }


def to_datetime_columns(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors='coerce', utc=True)
    return out


def prepare_sensor_dataset(sensor_df: pd.DataFrame, weather_df: pd.DataFrame, transformers_df: pd.DataFrame, incidents_df: pd.DataFrame, maintenance_df: pd.DataFrame) -> pd.DataFrame:
    sensor = sensor_df.copy()
    sensor['timestamp'] = pd.to_datetime(sensor['timestamp'], errors='coerce', utc=True)
    weather = weather_df.copy()
    weather['timestamp'] = pd.to_datetime(weather['timestamp'], errors='coerce', utc=True)
    transformers = transformers_df.copy()
    incidents = incidents_df.copy()
    incidents['incident_date'] = pd.to_datetime(incidents['incident_date'], errors='coerce', utc=True)
    maintenance = maintenance_df.copy()
    maintenance['maintenance_date'] = pd.to_datetime(maintenance['maintenance_date'], errors='coerce', utc=True)
    maintenance['next_maintenance_date'] = pd.to_datetime(maintenance['next_maintenance_date'], errors='coerce', utc=True)

    # Join weather by nearest location/time bucket
    weather_columns = ['temperature_c', 'humidity_percentage', 'rainfall_mm', 'wind_speed_kmh', 'pressure_hpa', 'lightning_probability', 'storm_probability', 'flood_risk']
    weather_map = weather[['timestamp', 'location_id', *weather_columns]].copy()
    weather_map = weather_map.rename(columns={column: f'weather_{column}' for column in weather_columns})
    sensor = sensor.merge(transformers[['transformer_id', 'substation_id', 'latitude', 'longitude']], on='transformer_id', how='left')
    sensor['location_id'] = sensor['substation_id'].map(LOCATION_BY_SUBSTATION)
    sensor['timestamp_rounded'] = sensor['timestamp'].dt.floor('30min')
    weather_map['timestamp_rounded'] = pd.to_datetime(weather_map['timestamp'], errors='coerce', utc=True).dt.floor('30min')
    weather_map = weather_map.drop(columns=['timestamp']).drop_duplicates(subset=['location_id', 'timestamp_rounded'])
    sensor = sensor.merge(weather_map, on=['location_id', 'timestamp_rounded'], how='left')
    for column in weather_columns:
        weather_column = f'weather_{column}'
        if column not in sensor:
            sensor[column] = sensor[weather_column]
        else:
            sensor[column] = sensor[column].fillna(sensor[weather_column])
        sensor = sensor.drop(columns=[weather_column])
    numeric_columns = list(dict.fromkeys(column for column in weather_columns + ['temperature_c', 'vibration_mm_s', 'partial_discharge_pc', 'oil_temperature_c', 'oil_moisture_ppm', 'oil_acidity_mgKOH_g', 'load_percentage', 'voltage_kv', 'current_a'] if column in sensor.columns))
    sensor[numeric_columns] = sensor[numeric_columns].apply(pd.to_numeric, errors='coerce')
    sensor = sensor.drop(columns=['timestamp_rounded'])

    sensor = sensor.sort_values(['transformer_id', 'timestamp']).reset_index(drop=True)
    sensor['hour'] = sensor['timestamp'].dt.floor('h')
    sensor['day'] = sensor['timestamp'].dt.floor('D')

    for window in [2, 6, 24]:
        for metric in ['temperature_c', 'vibration_mm_s', 'partial_discharge_pc', 'oil_temperature_c', 'oil_moisture_ppm', 'oil_acidity_mgKOH_g', 'load_percentage']:
            rolling = sensor.groupby('transformer_id')[metric]
            sensor[f'{metric}_mean_{window}h'] = rolling.transform(lambda s: s.rolling(window=window, min_periods=1).mean())
            sensor[f'{metric}_max_{window}h'] = rolling.transform(lambda s: s.rolling(window=window, min_periods=1).max())

    for metric in ['temperature_c', 'vibration_mm_s', 'partial_discharge_pc', 'oil_temperature_c', 'oil_moisture_ppm', 'oil_acidity_mgKOH_g', 'load_percentage']:
        sensor[f'{metric}_trend_24h'] = sensor.groupby('transformer_id')[metric].transform(lambda s: s.rolling(window=24, min_periods=1).apply(lambda x: x.iloc[-1] - x.iloc[0], raw=False))
        sensor[f'{metric}_trend_7d'] = sensor.groupby('transformer_id')[metric].transform(lambda s: s.rolling(window=168, min_periods=1).apply(lambda x: x.iloc[-1] - x.iloc[0], raw=False))

    # historical incident features
    incidents_agg = incidents.groupby('transformer_id').agg(previous_incidents=('incident_id', 'count')).reset_index()
    incidents_agg['days_since_previous_incident'] = 30
    sensor = sensor.merge(transformers[['transformer_id']].copy(), on='transformer_id', how='left')
    sensor = sensor.merge(incidents_agg, on='transformer_id', how='left')
    sensor['timestamp'] = pd.to_datetime(sensor['timestamp'], errors='coerce', utc=True)
    sensor['previous_incidents'] = sensor['previous_incidents'].fillna(0)
    sensor['days_since_previous_incident'] = sensor['days_since_previous_incident'].fillna(30)

    latest_maintenance = maintenance.sort_values('maintenance_date').groupby('transformer_id').tail(1).copy()
    latest_maintenance = latest_maintenance[['transformer_id', 'maintenance_result', 'maintenance_date']]
    maintenance_score = {
        'Completed - Follow-up Required': 0.5,
        'Completed': 0.2,
        'Action Required': 0.9,
        'Normal': 0.1,
        'Urgent': 1.0,
    }
    latest_maintenance['maintenance_result_risk'] = latest_maintenance['maintenance_result'].map(maintenance_score).fillna(0.5)
    sensor = sensor.merge(latest_maintenance[['transformer_id', 'maintenance_result_risk']], on='transformer_id', how='left')
    sensor['days_since_maintenance'] = 30

    # weather risk score
    sensor['weather_risk_score'] = (
        0.4 * sensor['rainfall_mm'].fillna(0) / sensor['rainfall_mm'].fillna(0).max().max() if pd.notna(sensor['rainfall_mm'].fillna(0).max().max()) else 0
    )
    sensor['weather_risk_score'] = sensor['weather_risk_score'].fillna(0)

    # asset metadata and labels
    sensor = sensor.merge(transformers.drop(columns=['substation_id', 'latitude', 'longitude']), on='transformer_id', how='left')
    sensor['hospital_nearby'] = sensor['hospital_nearby'].astype(int)
    sensor['industrial_load'] = sensor['industrial_load'].astype(int)
    sensor['maintenance_result_risk'] = sensor['maintenance_result_risk'].fillna(0.5)
    sensor['days_since_maintenance'] = sensor['days_since_maintenance'].fillna(30)
    sensor['weather_risk_score'] = sensor['weather_risk_score'].fillna(0)

    selected = [
        'transformer_id', 'timestamp', 'substation_id', 'capacity_kva', 'age_years', 'rated_voltage_kv', 'customer_count', 'critical_customer_count', 'hospital_nearby', 'industrial_load', 'criticality_score',
        'temperature_c', 'vibration_mm_s', 'partial_discharge_pc', 'oil_temperature_c', 'oil_moisture_ppm', 'oil_acidity_mgKOH_g', 'load_percentage', 'voltage_kv', 'current_a',
        'temperature_c_mean_2h', 'temperature_c_mean_6h', 'temperature_c_mean_24h', 'temperature_c_max_24h', 'vibration_mm_s_mean_2h', 'vibration_mm_s_mean_6h', 'vibration_mm_s_mean_24h', 'vibration_mm_s_max_24h',
        'partial_discharge_pc_mean_2h', 'partial_discharge_pc_mean_6h', 'partial_discharge_pc_mean_24h', 'partial_discharge_pc_max_24h', 'oil_temperature_c_mean_24h', 'oil_temperature_c_max_24h',
        'oil_moisture_ppm_mean_24h', 'oil_moisture_ppm_max_24h', 'oil_acidity_mgKOH_g_mean_24h', 'oil_acidity_mgKOH_g_max_24h', 'load_percentage_mean_24h', 'load_percentage_max_24h',
        'temperature_c_trend_24h', 'temperature_c_trend_7d', 'vibration_mm_s_trend_24h', 'vibration_mm_s_trend_7d', 'partial_discharge_pc_trend_24h', 'partial_discharge_pc_trend_7d',
        'oil_temperature_c_trend_24h', 'oil_temperature_c_trend_7d', 'oil_moisture_ppm_trend_24h', 'oil_moisture_ppm_trend_7d', 'oil_acidity_mgKOH_g_trend_24h', 'oil_acidity_mgKOH_g_trend_7d', 'load_percentage_trend_24h', 'load_percentage_trend_7d',
        'humidity_percentage', 'rainfall_mm', 'wind_speed_kmh', 'pressure_hpa', 'lightning_probability', 'storm_probability', 'flood_risk', 'weather_risk_score', 'previous_incidents', 'days_since_previous_incident', 'days_since_maintenance', 'maintenance_result_risk'
    ]
    return sensor[selected].copy()


def get_feature_order(path: str = 'src/model/model_config.json') -> List[str]:
    with open(path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    model_data = json.load(open(path, 'r', encoding='utf-8'))
    return model_data.get('features', [])


def build_feature_frame(new_df: pd.DataFrame, historical_df: pd.DataFrame | None = None) -> pd.DataFrame:
    hist = historical_df if historical_df is not None else pd.read_csv(DATA_DIR / 'sensor_readings.csv')
    sources = load_feature_sources()
    combined = pd.concat([hist, new_df], ignore_index=True)
    combined['timestamp'] = pd.to_datetime(combined['timestamp'], errors='coerce', utc=True)
    combined = combined.sort_values(['transformer_id', 'timestamp']).reset_index(drop=True)
    features = prepare_sensor_dataset(combined, sources['weather'], sources['transformers'], sources['incidents'], sources['maintenance'])
    return features.drop_duplicates(subset=['transformer_id', 'timestamp'], keep='last').reset_index(drop=True)
