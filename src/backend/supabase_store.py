from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List

from dotenv import load_dotenv

try:
    from supabase import Client, create_client
except ImportError:  # Supabase is optional until configured in the deployment environment.
    Client = Any
    create_client = None


class PredictionStore:
    def __init__(self) -> None:
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))
        self._lock = Lock()
        self._local_history: List[Dict[str, Any]] = []
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        self.client: Client | None = None
        self.last_error: str | None = None
        self.last_operation = 'not_configured'
        if create_client and url and key and 'your-project' not in url:
            try:
                self.client = create_client(url, key)
                self.last_operation = 'ready'
            except Exception as exc:
                self.last_error = self._safe_error(exc)
                self.last_operation = 'client_initialization_failed'
                self.client = None
        self.table = os.getenv('SUPABASE_PREDICTIONS_TABLE', 'prediction_history')


    @property
    def configured(self) -> bool:
        return self.client is not None

    def _json_safe(self, value: Dict[str, Any]) -> Dict[str, Any]:
        return json.loads(json.dumps(value, default=str))

    def _safe_error(self, exc: Exception) -> str:
        """Keep a useful operational error without exposing credentials."""
        message = str(exc)
        secret = os.getenv('SUPABASE_KEY', '')
        if secret:
            message = message.replace(secret, '[redacted]')
        return message[:300] or type(exc).__name__

    def status(self) -> Dict[str, Any]:
        return {
            'configured': self.configured,
            'table': self.table,
            'last_operation': self.last_operation,
            'last_error': self.last_error,
            'using_local_fallback': not self.configured or self.last_operation.endswith('_failed'),
            'local_records': len(self._local_history),
        }

    def add(self, result: Dict[str, Any]) -> Dict[str, Any]:
        record = self._json_safe({
            'checked_at': datetime.now(timezone.utc).isoformat(),
            'transformer_id': result['transformer_id'],
            'failure_probability': result['failure_probability'],
            'risk_level': result['risk_level'],
            'priority': result['priority'],
            'risk_score': result['risk_score'],
            'grid_impact': result.get('grid_impact'),
            'weather_risk': result.get('weather_risk'),
            'reasons': result.get('reasons', []),
            'maintenance_recommendation': result.get('maintenance_recommendation'),
            'crew_recommendation': result.get('crew_recommendation'),
            'reading': result.get('reading', {}),
            'asset': result.get('asset', {}),
        })
        with self._lock:
            if self.client:
                try:
                    response = self.client.table(self.table).insert(record).execute()
                    if response.data:
                        self.last_error = None
                        self.last_operation = 'inserted_in_supabase'
                        return response.data[0]
                    self.last_error = 'Supabase returned no inserted row.'
                    self.last_operation = 'insert_failed'
                except Exception as exc:
                    self.last_error = self._safe_error(exc)
                    self.last_operation = 'insert_failed'
            self._local_history.append(record)
            if not self.client:
                self.last_operation = 'stored_locally'
        return record

    def clear_local(self) -> None:
        with self._lock:
            self._local_history.clear()

    def list(self) -> List[Dict[str, Any]]:
        with self._lock:
            if self.client:
                try:
                    response = self.client.table(self.table).select('*').order('checked_at', desc=True).execute()
                    self.last_error = None
                    self.last_operation = 'read_from_supabase'
                    return response.data or []
                except Exception as exc:
                    self.last_error = self._safe_error(exc)
                    self.last_operation = 'read_failed'
            return list(reversed(self._local_history))



prediction_store = PredictionStore()
