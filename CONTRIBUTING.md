# Contributing

This project is built for the Bob AI Hackathon and is intended to be extended by the team after setup.

## Setup

1. Create and activate a Python environment.
2. Install dependencies from the backend and Python environment.
3. Run tests with pytest.
4. If a frontend is used, install Node dependencies and build with Vite.

## Development

- Keep the model inference pipeline and risk logic in dedicated modules under `src/model` and `src/advisor`.
- Prefer reproducible data pipelines over hard-coded demo values.
- Validate new predictions and risk outputs with tests before merging changes.
