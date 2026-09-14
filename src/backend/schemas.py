from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class PredictionRequest(BaseModel):
    transformer_id: str
    timestamp: str
    temperature_c: float
    vibration_mm_s: float
    partial_discharge_pc: float
    oil_temperature_c: float
    oil_moisture_ppm: float
    oil_acidity_mgKOH_g: float
    load_percentage: float
    voltage_kv: float
    current_a: float
    humidity_percentage: Optional[float] = None
    rainfall_mm: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    pressure_hpa: Optional[float] = None
    lightning_probability: Optional[float] = None
    storm_probability: Optional[float] = None
    flood_risk: Optional[float] = None


class BatchPredictionRequest(BaseModel):
    rows: List[Dict[str, Any]]


class BobQueryRequest(BaseModel):
    question: str
