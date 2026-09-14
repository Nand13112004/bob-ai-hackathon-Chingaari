# Setup guide

## Prerequisites

- Python 3.12+
- Node.js LTS
- Access to the project data files in `src/data`
- The trained model file in `src/model/grid_failure_model.pkl`

## Dependencies

Python packages:

- pandas
- numpy
- scikit-learn
- xgboost
- joblib
- fastapi
- uvicorn
- pytest
- python-multipart

Frontend dependencies:

- React
- Vite
- optional charting packages

## Environment variables

No secrets are required for the local demo. To enable Gemini-formatted, database-grounded responses, add `GEMINI_API_KEY` to the root `.env` file and restart FastAPI. Optionally set `GEMINI_MODEL=gemini-3.6-flash`. Do not commit secrets to the repository.

## Model setup

Place the trained model at:

`src/model/grid_failure_model.pkl`

The inference pipeline should match the engineered feature vector used by training.

## Backend commands

```bash
cd bob-ai-hackathon-[your-team-name]
python -m uvicorn src.backend.app:app --host 0.0.0.0 --port 8000
```

## Frontend commands

```bash
cd bob-ai-hackathon-[your-team-name]/src/frontend
npm install
npm run dev -- --host 0.0.0.0
```

## Verification

Check the API health:

```bash
curl http://localhost:8000/api/health
```

Run the test suite:

```bash
pytest
```

## Troubleshooting

- If the model cannot load, verify the package versions match those used during training.
- If CSV files are missing, ensure they are stored under `src/data`.
- If the frontend does not build, reinstall Node dependencies and rerun `npm install`.
