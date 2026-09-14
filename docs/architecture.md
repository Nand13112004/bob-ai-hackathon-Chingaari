# Architecture

## High-level flow

```mermaid
flowchart TD
    A[Transformer + Sensor + Weather + Incident + Maintenance + Crew Data] --> B[Feature Engineering]
    B --> C[XGBoost Model]
    C --> D[Probability / Threshold]
    D --> E[Risk Scoring]
    E --> F[Maintenance Advisor]
    E --> G[Crew Optimizer]
    F --> H[Operator Dashboard]
    G --> H
    H --> I[IBM Bob Assistant]
    I --> J[Operational Decision Support]
```

## Components

- Data layer: CSV-based source data in `src/data`
- Feature engineering: handles rolling windows, trends, incident and maintenance features
- Model layer: evaluates the saved XGBoost pipeline and applies threshold 0.55
- Risk engine: translates probability into LOW/MEDIUM/HIGH/CRITICAL and P1/P2/P3/P4 priorities
- Advisor layer: recommends maintenance and crew actions
- API layer: exposes health, dashboard, transformer, risk, and prediction endpoints
- Frontend: operational dashboard, maps, risk tables, details, and aid tools
- Bob layer: answers grounded questions using current application data
