# Power Outage Prediction & Grid Equipment Failure Advisor

## Team

Team placeholder: [your-team-name]

## Problem

Power utilities must detect equipment degradation early to reduce unplanned outages, protect critical customers, and reduce emergency maintenance costs. Transformer failures are costly and operationally disruptive, especially when they affect hospitals, industrial loads, and dense customer zones.

## Solution

This project combines transformer metadata, time-series sensor readings, weather conditions, maintenance history, historical incidents, and crew data into a predictive maintenance workflow. The system ranks transformer risk, recommends maintenance, and suggests appropriate crew dispatch with a Gemini-powered operational assistant.

## Key features

- Failure forecasting for the next 7 days
- Risk ranking by probability, grid impact, and weather exposure
- Maintenance recommendation engine
- Crew deployment optimization
- New-risk validation from live reading or CSV upload
- Dashboard and transformer detail views
- Bob-style operational question answering

## Architecture

The application follows a data-to-decision pipeline:

Sensor Data → Feature Engineering → XGBoost Prediction → Risk Scoring → Maintenance Advisor → Crew Optimization → Bob Assistant → Operator Dashboard

## ML approach

The saved model artifact in `src/model/grid_failure_model.pkl` is treated as the production model. The pipeline reproduces the engineered feature vector expected by the model before applying the decision threshold of 0.55.

## Risk scoring

Risk scores combine failure probability, grid impact, asset criticality, weather risk, historical incidents, and maintenance condition. The output is classified into LOW, MEDIUM, HIGH, and CRITICAL categories with associated priority levels.

## Maintenance advisor

The maintenance advisor uses raw operational conditions such as elevated temperature, vibration, partial discharge, oil moisture, oil acidity, and overload risk to recommend clear preventive actions.

## Crew optimization

The crew optimizer checks availability, skill level, crew type, and distance constraints before recommending deployment action, including pre-positioning or dispatch.

## Gemini database-grounded assistant

The AURA AI service sends Gemini the current Supabase prediction-history snapshot, maintenance recommendations, and available crew data with strict grounding instructions. Gemini formats a concise, Markdown-ready answer without inventing assets or telemetry. Set `GEMINI_API_KEY` in `.env` (optionally `GEMINI_MODEL`, which defaults to `gemini-3.6-flash`) and restart the backend.

## Technology stack

- Python
- FastAPI
- Pandas
- NumPy
- scikit-learn
- XGBoost
- Joblib
- Vite
- JavaScript

## Setup

1. Create a Python environment.
2. Install project dependencies.
3. Ensure the data files and model are present under `src/data` and `src/model`.
4. Start the API server.
5. Build or run the frontend.

### Supabase prediction history

Prediction checks are stored in Supabase when `SUPABASE_URL` and `SUPABASE_KEY` are configured. Run `supabase_schema.sql` in the Supabase SQL editor, then set these variables before starting FastAPI. The ML input data remains in `src/data`; Supabase stores only operator-generated prediction results and readings. The publishable key works with the included RLS policies; a server-side key is preferred for production.

```powershell
$env:SUPABASE_URL = 'https://your-project.supabase.co'
$env:SUPABASE_KEY = 'your-server-side-key'
```

## Running

Backend:

```bash
cd bob-ai-hackathon-[your-team-name]
python -m uvicorn src.backend.app:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd bob-ai-hackathon-[your-team-name]/src/frontend
npm install
npm run dev -- --host 0.0.0.0
```

## Demo

The demo flow is:

1. Open the dashboard
2. Review risky assets
3. Inspect a transformer detail view
4. Check a live or uploaded reading
5. Ask the Gemini AI copilot a question grounded in current data

## Screenshots

Screenshots should be placed under `demo/screenshots/` when available.

## Limitations

- This version uses the saved training artifact as the source of truth for the production inference flow.
- Gemini is used when `GEMINI_API_KEY` is configured; the local grounded database engine is used if Gemini is unavailable.
- Some generated recommendation details are based on the current dataset and score logic rather than live utility telemetry.

## Future improvements

- Expand the ensemble model and retraining workflow
- Add richer geographic plotting and map clustering
- Connect to a real Bob or enterprise assistant configuration
- Add more advanced maintenance scheduling and crew optimization logic

## What the team is proud of

This project brings together data, forecasting, operational reasoning, and a usable operator-facing workflow in a single package that is easy to run and extend.
