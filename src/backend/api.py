from __future__ import annotations

import json
import os
from functools import lru_cache
from threading import Lock
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.advisor.crew_optimizer import crew_recommendation, distance_km
from src.advisor.maintenance_advisor import maintenance_recommendation
from src.bob.bob_service import BobService
from src.backend.supabase_store import prediction_store
from src.model.predict import load_config, load_historical_sensor_data, load_model, predict_batch, predict_single, validate_reading_df
from src.model.risk_scoring import calculate_risk
from src.model.feature_engineering import LOCATION_BY_SUBSTATION

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / 'data'

app = FastAPI(title='Grid Operations Advisor')

# Vite proxies API calls during local development. In production the dashboard
# is hosted on Vercel and calls this Render service directly, so allow only the
# explicitly configured frontend origins.
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        'CORS_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173',
    ).split(',')
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)
_risk_assets_cache: List[Dict[str, Any]] | None = None
_risk_assets_lock = Lock()
_prediction_history: List[Dict[str, Any]] = []
_prediction_history_lock = Lock()


@lru_cache(maxsize=1)
def load_transformers() -> pd.DataFrame:
    transformers = pd.read_csv(DATA_DIR / 'transformers.csv')
    required = {'transformer_id', 'substation_id', 'latitude', 'longitude', 'customer_count', 'criticality_score'}
    missing = required.difference(transformers.columns)
    if missing:
        raise HTTPException(status_code=500, detail=f'Transformer data is missing columns: {sorted(missing)}')
    if transformers['transformer_id'].duplicated().any():
        raise HTTPException(status_code=500, detail='Transformer data contains duplicate transformer IDs.')
    return transformers


def load_dashboard_data() -> Dict[str, Any]:
    assets = risk_assets()
    transformers = load_transformers()
    counts = pd.Series([asset['risk_level'] for asset in assets]).value_counts().to_dict()
    crews = pd.read_csv(DATA_DIR / 'crew.csv')
    return {
        'total_transformers': len(transformers),
        'risk_counts': {level: int(counts.get(level, 0)) for level in ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')},
        'predicted_failures': sum(asset['risk_level'] in ('HIGH', 'CRITICAL') for asset in assets),
        'available_crews': int(crews['available'].sum()),
        'maintenance_recommendations': sum(asset['risk_level'] in ('HIGH', 'CRITICAL') for asset in assets),
        'overall_grid_risk': assets[0]['risk_level'] if assets else 'LOW',
    }


@app.get('/api/health')
def health() -> Dict[str, Any]:
    return {'status': 'ok', 'storage': prediction_store.status()}


@app.get('/api/storage/status')
def storage_status() -> Dict[str, Any]:
    """Expose Supabase connectivity so local fallback never goes unnoticed."""
    return prediction_store.status()


@app.get('/api/dashboard')
def dashboard() -> Dict[str, Any]:
    return load_dashboard_data()


@app.get('/api/transformers')
def transformers() -> List[Dict[str, Any]]:
    return load_transformers().to_dict(orient='records')


@lru_cache(maxsize=1)
def load_sensor_readings() -> pd.DataFrame:
    return load_historical_sensor_data()


@lru_cache(maxsize=1)
def load_crews() -> List[Dict[str, Any]]:
    return pd.read_csv(DATA_DIR / 'crew.csv').to_dict(orient='records')


@lru_cache(maxsize=1)
def load_weather_data() -> pd.DataFrame:
    weather = pd.read_csv(DATA_DIR / 'weather_data.csv')
    weather['timestamp'] = pd.to_datetime(weather['timestamp'], errors='coerce', utc=True)
    weather['timestamp_rounded'] = weather['timestamp'].dt.floor('30min')
    return weather


def latest_reading(transformer_id: str) -> Dict[str, Any]:
    readings = load_sensor_readings()
    record = readings[readings['transformer_id'] == transformer_id].sort_values('timestamp').tail(1)
    if record.empty:
        raise HTTPException(status_code=404, detail='No sensor reading found')
    return record.iloc[0].to_dict()


def build_prediction(transformer_id: str, reading: Dict[str, Any], model_result: Dict[str, Any] | None = None) -> Dict[str, Any]:
    asset = load_transformers().query('transformer_id == @transformer_id')
    if asset.empty:
        raise HTTPException(status_code=404, detail='Transformer not found')
    asset_data = asset.iloc[0].to_dict()
    enriched_reading = dict(reading)
    reading_timestamp = pd.to_datetime(enriched_reading.get('timestamp'), errors='coerce', utc=True)
    if pd.notna(reading_timestamp):
        location_id = LOCATION_BY_SUBSTATION.get(asset_data.get('substation_id'))
        weather = load_weather_data()
        weather_row = weather[(weather['location_id'] == location_id) & (weather['timestamp_rounded'] == reading_timestamp.floor('30min'))]
        if not weather_row.empty:
            for key in ('humidity_percentage', 'rainfall_mm', 'wind_speed_kmh', 'pressure_hpa', 'lightning_probability', 'storm_probability', 'flood_risk'):
                if enriched_reading.get(key) is None or pd.isna(enriched_reading.get(key)):
                    enriched_reading[key] = weather_row.iloc[-1][key]
    if model_result is None:
        try:
            model_result = predict_single(transformer_id, reading)
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    probability = model_result['failure_probability']
    weather_values = [max(0.0, min(1.0, float(enriched_reading.get(key, 0) or 0))) for key in ('storm_probability', 'flood_risk', 'lightning_probability')]
    weather_risk = max(weather_values)
    grid_impact = min(float(asset_data.get('customer_count', 0)) / 10000.0, 1.0)
    risk = calculate_risk(probability, grid_impact, weather_risk, asset_criticality=float(asset_data.get('criticality_score', 0)) / 100.0)
    sensor = {key: float(reading.get(key, 0) or 0) for key in ('temperature_c', 'vibration_mm_s', 'partial_discharge_pc', 'oil_moisture_ppm', 'oil_acidity_mgKOH_g', 'load_percentage')}
    maintenance_text = maintenance_recommendation(sensor, probability, asset_data)
    crews = load_crews()
    crew_result = crew_recommendation({**asset_data, **risk}, crews)
    reasons = []
    thresholds = [('temperature_c', 80, 'high temperature'), ('vibration_mm_s', 5, 'elevated vibration'), ('partial_discharge_pc', 30, 'partial discharge'), ('oil_moisture_ppm', 25, 'oil moisture'), ('oil_acidity_mgKOH_g', 0.12, 'oil acidity'), ('load_percentage', 85, 'high operating load')]
    reasons.extend(label for key, threshold, label in thresholds if sensor[key] > threshold)
    if probability >= model_result['threshold']:
        reasons.append('failure probability exceeds the 7-day threshold')
    if not reasons:
        reasons.append('current readings are within monitored operating ranges')
    return {
        **risk,
        'transformer_id': transformer_id,
        'failure_probability': round(probability * 100.0, 6),
        'probability_window': 'NEXT 7 DAYS',
        'grid_impact': round(grid_impact * 100.0, 2),
        'weather_risk': round(weather_risk * 100.0, 2),
        'reasons': reasons,
        'maintenance_recommendation': maintenance_text,
        'crew_recommendation': crew_result,
        'asset': asset_data,
        'reading': reading,
    }


@app.get('/api/transformers/{transformer_id}')
def transformer_detail(transformer_id: str) -> Dict[str, Any]:
    df = load_transformers()
    rec = df[df['transformer_id'] == transformer_id]
    if rec.empty:
        raise HTTPException(status_code=404, detail='Transformer not found')
    checked = [item for item in prediction_store.list() if item['transformer_id'] == transformer_id]
    if not checked:
        raise HTTPException(status_code=404, detail='Transformer has not been checked in this session')
    latest_check = checked[-1]
    checked_readings = [item.get('reading', {}) for item in checked]
    return {**latest_check, 'sensor_history': checked_readings}


def _build_risk_assets() -> List[Dict[str, Any]]:
    transformer_ids = load_transformers()['transformer_id'].tolist()
    readings = load_sensor_readings()
    latest = readings.sort_values('timestamp').groupby('transformer_id', as_index=False).tail(1)
    for column in ('humidity_percentage', 'rainfall_mm', 'wind_speed_kmh', 'pressure_hpa', 'lightning_probability', 'storm_probability', 'flood_risk'):
        if column not in latest.columns:
            latest[column] = float('nan')
    try:
        model_results = {item['transformer_id']: item for item in predict_batch(latest)}
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = [build_prediction(transformer_id, latest_reading(transformer_id), model_results[transformer_id]) for transformer_id in transformer_ids]
    return sorted(result, key=lambda item: item['risk_score'], reverse=True)


def risk_assets() -> List[Dict[str, Any]]:
    return prediction_store.list()


@app.get('/api/risk-assets')
def risk_assets_endpoint() -> List[Dict[str, Any]]:
    return risk_assets()


@app.get('/api/crew')
def crew(transformer_id: str | None = None) -> List[Dict[str, Any]]:
    crews = load_crews()
    if not transformer_id:
        return crews
    asset = load_transformers().query('transformer_id == @transformer_id')
    if asset.empty:
        raise HTTPException(status_code=404, detail='Transformer not found')
    transformer = asset.iloc[0].to_dict()
    recommendation = crew_recommendation(transformer, crews)
    recommended_id = recommendation.get('crew_id')
    rows = []
    for item in crews:
        row = dict(item)
        row['distance_km'] = round(distance_km(float(item['base_latitude']), float(item['base_longitude']), float(transformer['latitude']), float(transformer['longitude'])), 2)
        row['within_allowed_distance'] = row['distance_km'] <= float(item['max_distance_km'])
        row['eligible'] = bool(item.get('available')) and row['within_allowed_distance']
        row['recommended'] = item.get('crew_id') == recommended_id
        rows.append(row)
    return rows


@app.get('/api/maintenance')
def maintenance() -> List[Dict[str, Any]]:
    assets = risk_assets()
    return [{
        'transformer_id': asset['transformer_id'], 'urgency': asset['priority'],
        'risk_level': asset['risk_level'], 'why': ', '.join(asset['reasons']),
        'maintenance_required': not asset['maintenance_recommendation'].startswith('Routine monitoring'),
        'recommended_action': asset['maintenance_recommendation'],
        'failure_probability': asset['failure_probability'],
        'checked_at': asset.get('checked_at'),
    } for asset in assets]


@app.get('/api/analytics')
def analytics() -> Dict[str, Any]:
    model_bundle = load_model()
    model = model_bundle['model']
    importance = getattr(model, 'feature_importances_', [])
    features = model_bundle.get('features', [])
    ranked = sorted(zip(features, importance), key=lambda item: float(item[1]), reverse=True)
    return {'model_name': load_config().get('model_name', type(model).__name__), 'threshold': model_bundle.get('threshold', 0.55), 'feature_importance': [{'feature': name, 'importance': round(float(value), 6)} for name, value in ranked[:15]], 'metrics': model_bundle.get('metrics', {})}


@app.post('/api/predict')
def predict(request: Dict[str, Any]) -> Dict[str, Any]:
    transformer_id = request.get('transformer_id')
    if not transformer_id:
        raise HTTPException(status_code=400, detail='transformer_id is required')
    reading = {k: v for k, v in request.items() if k != 'transformer_id'}
    reading.setdefault('timestamp', pd.Timestamp.now(tz='UTC').isoformat())
    result = build_prediction(transformer_id, reading)
    try:
        prediction_store.add(result)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return result


@app.get('/api/prediction-history')
def prediction_history() -> List[Dict[str, Any]]:
    try:
        return prediction_store.list()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get('/api/prediction-history/analysis')
def prediction_history_analysis() -> Dict[str, Any]:
    try:
        history = prediction_store.list()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not history:
        return {'checks': 0, 'transformers': 0, 'average_failure_probability': 0, 'risk_counts': {}, 'highest_risk': None}
    counts = pd.Series([item['risk_level'] for item in history]).value_counts().to_dict()
    highest = max(history, key=lambda item: item['risk_score'])
    return {
        'checks': len(history),
        'transformers': len({item['transformer_id'] for item in history}),
        'average_failure_probability': round(sum(item['failure_probability'] for item in history) / len(history), 2),
        'risk_counts': {level: int(counts.get(level, 0)) for level in ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')},
        'highest_risk': {'transformer_id': highest['transformer_id'], 'risk_level': highest['risk_level'], 'risk_score': highest['risk_score']},
    }


@app.post('/api/predict/batch')
def predict_batch_api(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = payload.get('rows', [])
    if not rows:
        raise HTTPException(status_code=400, detail='No rows provided')
    df = pd.DataFrame(rows)
    try:
        validate_reading_df(df)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        model_results = {item['transformer_id']: item for item in predict_batch(df)}
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    results = []
    for transformer_id, group in df.groupby('transformer_id', sort=True):
        reading = group.sort_values('timestamp').iloc[-1].to_dict()
        results.append(build_prediction(transformer_id, reading, model_results[transformer_id]))
    for result in results:
        try:
            prediction_store.add(result)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    return results


@app.get('/api/bob/status')
def bob_status() -> Dict[str, Any]:
    history = prediction_store.list()
    service = BobService({'risk_assets': history, 'maintenance': maintenance(), 'crew': crew(), 'prediction_history': history})
    return service.get_status()


@app.post('/api/bob/query')
def bob_query(payload: Dict[str, Any]) -> Dict[str, Any]:
    question = payload.get('question', '')
    if not question:
        raise HTTPException(status_code=400, detail='Question is required')
    history = prediction_store.list()
    service = BobService({'risk_assets': history, 'maintenance': maintenance(), 'crew': crew(), 'prediction_history': history})
    return service.query_detailed(question)

