from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd

from src.model.feature_engineering import build_feature_frame, load_data

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / 'model' / 'grid_failure_model.pkl'
CONFIG_PATH = BASE_DIR / 'model' / 'model_config.json'


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f'Model file not found at {MODEL_PATH}')
    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def load_config() -> Dict[str, Any]:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_historical_sensor_data() -> pd.DataFrame:
    readings = pd.read_csv(BASE_DIR / 'data' / 'sensor_readings.csv')
    readings['timestamp'] = pd.to_datetime(readings['timestamp'], errors='coerce', utc=True)
    return readings


def recent_sensor_history(transformer_ids: List[str] | None = None) -> pd.DataFrame:
    readings = load_historical_sensor_data()
    if transformer_ids is not None:
        readings = readings[readings['transformer_id'].isin(transformer_ids)]
    return readings.sort_values(['transformer_id', 'timestamp']).groupby('transformer_id', group_keys=False).tail(168).copy()


def history_before_readings(new_df: pd.DataFrame) -> pd.DataFrame:
    history = load_historical_sensor_data().sort_values(['transformer_id', 'timestamp'])
    rows = []
    for transformer_id, group in new_df.groupby('transformer_id'):
        timestamps = pd.to_datetime(group['timestamp'], errors='coerce', utc=True)
        cutoff = timestamps.min()
        prior = history[(history['transformer_id'] == transformer_id) & (history['timestamp'] < cutoff)].tail(168)
        rows.append(prior)
    return pd.concat(rows, ignore_index=True) if rows else history.iloc[0:0].copy()


def validate_reading_df(df: pd.DataFrame) -> None:
    required = load_config().get('required_columns', [])
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f'Missing required columns: {missing}')
    if df.empty:
        raise ValueError('Input dataset is empty.')
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
        if df['timestamp'].isna().any():
            raise ValueError('One or more timestamps are invalid.')


def predict_single(transformer_id: str, reading: Dict[str, Any]) -> Dict[str, Any]:
    model_bundle = load_model()
    model = model_bundle['model']
    threshold = float(model_bundle.get('threshold', 0.55))
    features = model_bundle.get('features', [])
    if not features:
        features = load_config().get('features', [])
    transformer_df = pd.read_csv(BASE_DIR / 'data' / 'transformers.csv')
    transformer = transformer_df[transformer_df['transformer_id'] == transformer_id]
    if transformer.empty:
        raise ValueError(f'Unknown transformer: {transformer_id}')
    row = pd.DataFrame([reading])
    row['transformer_id'] = transformer_id
    row['timestamp'] = pd.to_datetime(row.get('timestamp', pd.Timestamp.now(tz='UTC')), errors='coerce', utc=True)
    if row['timestamp'].isna().any():
        raise ValueError('One or more timestamps are invalid.')
    data = build_feature_frame(row, history_before_readings(row))
    for feature in features:
        if feature not in data.columns:
            raise ValueError(f'Model feature is missing from inference frame: {feature}')
    model_input = data[features].fillna(0)
    target_rows = data['transformer_id'].eq(transformer_id) & data['timestamp'].eq(row['timestamp'].iloc[0])
    target_index = data.index[target_rows]
    prediction_index = target_index[-1] if len(target_index) else model_input.index[-1]
    prob = float(model.predict_proba(model_input.loc[[prediction_index]])[:, 1][0])
    return {'failure_probability': prob, 'predicted_fail': prob >= threshold, 'threshold': threshold}


def predict_batch(df: pd.DataFrame) -> List[Dict[str, Any]]:
    validate_reading_df(df)
    model_bundle = load_model()
    model = model_bundle['model']
    threshold = float(model_bundle.get('threshold', 0.55))
    features = model_bundle.get('features', [])
    if not features:
        features = load_config().get('features', [])
    hist = history_before_readings(df)
    feature_df = build_feature_frame(df, hist)
    for feature in features:
        if feature not in feature_df.columns:
            raise ValueError(f'Model feature is missing from inference frame: {feature}')
    results = []
    for transformer_id, group in df.groupby('transformer_id', sort=True):
        if not features:
            continue
        latest_timestamp = pd.to_datetime(group['timestamp'].max(), errors='coerce', utc=True)
        target_rows = feature_df['transformer_id'].eq(transformer_id) & feature_df['timestamp'].eq(latest_timestamp)
        target_index = feature_df.index[target_rows]
        prediction_index = target_index[-1] if len(target_index) else feature_df.index[-1]
        prob = float(model.predict_proba(feature_df.loc[[prediction_index], features].fillna(0))[:, 1][0])
        results.append({'transformer_id': transformer_id, 'failure_probability': prob, 'predicted_fail': prob >= threshold, 'threshold': threshold})
    return results
