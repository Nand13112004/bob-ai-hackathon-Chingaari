# Solution overview

Sensor Data
     ↓
Feature Engineering
     ↓
ML Prediction
     ↓
Risk Scoring
     ↓
Maintenance Advisor
     ↓
Crew Optimization
     ↓
IBM Bob
     ↓
Operator Dashboard

The system ingests raw sensor and weather observations, merges transformer metadata and historical operational context, and builds the engineered feature vectors used by the trained XGBoost model. Those predictions feed a transparent risk-scoring model, maintenance recommendations, and crew suggestions. An operator-facing Bob service then answers structured questions using the current grid state.
