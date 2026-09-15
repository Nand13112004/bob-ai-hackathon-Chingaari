# Contributing to AURA Grid

Thank you for your interest in AURA Grid.

AURA Grid is a collaborative project focused on predictive transformer maintenance and grid decision support. Contributions are welcome across the backend, machine-learning pipeline, frontend, data layer, IBM Bob integration, testing, and documentation.

This guide explains how to make changes while keeping the project stable and easy for the team to maintain.

---

## Code of Conduct

We want contributions to remain professional and constructive.

- Be respectful and inclusive.
- Discuss technical decisions openly.
- Give constructive feedback.
- Credit existing work and contributors.
- Focus discussions on the problem and the solution, not on individuals.
- Keep the project's purpose and reliability in mind.

---

# Development Setup

## 1. Clone the Repository

```powershell
git clone https://github.com/Nand13112004/bob-ai-hackathon-Chingaari.git
cd bob-ai-hackathon-Chingaari
```

Create and activate a Python virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
pip install -r requirements.txt
```

For frontend development:

```powershell
cd src/frontend
npm install
```

---

## 2. Configure the Local Environment

AURA Grid uses environment variables for configuration such as the PostgreSQL connection.

Create a local `.env` file and add the required values.

Example:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/grid_prediction
```

Never commit real passwords, API keys, or other secrets.

Before opening a pull request, check:

```powershell
git status
```

and make sure `.env` and other local secrets are not included.

---

## 3. Start the Application Locally

### Backend

From the repository root:

```powershell
python -m uvicorn src.backend.app:app --host 0.0.0.0 --port 8000 --reload
```

The API is available at:

```text
http://localhost:8000
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

### Frontend

In another terminal:

```powershell
cd src/frontend
npm run dev -- --host 0.0.0.0
```

The frontend is normally available at:

```text
http://localhost:5173
```

---

# Development Workflow

We recommend keeping changes small and focused.

```text
Create branch
     ↓
Make change
     ↓
Run tests
     ↓
Review diff
     ↓
Update documentation if needed
     ↓
Commit
     ↓
Open Pull Request
```

---

## Bug Fixes

For a bug fix:

1. Create a focused branch.
2. Reproduce the problem when possible.
3. Make the smallest reasonable change.
4. Add or update a regression test.
5. Run the relevant tests.
6. Check the final Git diff.
7. Commit with a clear message.
8. Open a pull request.

Example:

```bash
git checkout -b fix/missing-sensor-handling
```

Commit:

```text
fix: handle missing sensor values in prediction
```

---

## New Features

For a new feature:

1. Create a feature branch.
2. Decide which module should own the functionality.
3. Implement the feature without unnecessarily changing unrelated code.
4. Add tests.
5. Update relevant documentation.
6. Test the complete workflow locally.
7. Commit the change.
8. Open a pull request.

Example:

```bash
git checkout -b feature/batch-risk-summary
```

Commit:

```text
feature: add batch risk summary
```

---

## Documentation Changes

Documentation is part of the product.

When changing a feature, check whether these files also need updates:

- `README.md`
- `docs/problem-statement.md`
- `docs/solution-overview.md`
- `docs/architecture.md`
- `docs/setup-guide.md`

For Markdown changes, preview the file in VS Code before committing.

---

# Code Style

## Python

Follow normal Python best practices and keep code readable.

- Follow PEP 8.
- Use type hints where they improve clarity.
- Keep functions focused on one responsibility.
- Prefer clear names over overly short names.
- Add docstrings to important public functions.
- Avoid unnecessary global state.
- Handle errors explicitly.
- Keep database queries parameterized.
- Never put credentials directly in source code.

Example:

```python
def calculate_risk_score(
    probability: float,
    grid_impact: float,
    criticality: float,
    weather_risk: float,
) -> float:
    """Calculate an operational transformer risk score."""
    return (
        probability * 0.4
        + grid_impact * 0.3
        + criticality * 0.2
        + weather_risk * 0.1
    )
```

The exact formula must always match the implementation. Documentation examples should not be treated as the source of truth for application behavior.

---

## FastAPI / Backend

When adding an API endpoint:

- Keep the endpoint responsibility clear.
- Validate input.
- Return useful HTTP errors.
- Avoid exposing secrets or internal stack traces.
- Reuse existing services instead of duplicating business logic.
- Keep database access separate from request handling where practical.
- Document new endpoints.
- Add API tests where appropriate.

The existing backend is located at:

```text
src/backend/
```

Do not create another backend directory.

---

## Database

AURA Grid uses PostgreSQL for persistent grid data.

When adding or changing database access:

- Use the existing SQLAlchemy/database utilities.
- Use parameterized queries.
- Avoid loading large telemetry tables unnecessarily.
- Query only the records required for the operation.
- Add indexes when a query pattern justifies them.
- Keep database credentials in environment variables.
- Test database-dependent functionality locally.

Core data areas include:

```text
transformers
sensor_readings
weather_data
incidents
maintenance
crew
```

---

## Machine Learning

Changes to the ML pipeline should be treated carefully because they can affect prediction behavior throughout the application.

When changing:

- Feature engineering
- Model loading
- Prediction logic
- Risk calculation
- Model dependencies
- Fallback behavior

also check the related tests and documentation.

If model serialization or package versions change, document compatibility requirements clearly.

Do not claim model accuracy metrics unless they have actually been measured using a defined evaluation process.

---

## Frontend / React

The frontend is built with React and Vite.

Prefer:

- Functional components.
- React hooks where appropriate.
- Small reusable components.
- Clear component and variable names.
- `camelCase` for JavaScript variables and functions.
- Consistent UI patterns.
- Accessible controls where practical.
- Avoiding unnecessary re-renders.

Example:

```javascript
function RiskCard({ transformer, onSelect }) {
  return (
    <button onClick={() => onSelect(transformer)}>
      <strong>{transformer.transformer_id}</strong>
      <span>{transformer.risk_level}</span>
    </button>
  );
}
```

Keep presentation logic in the frontend and avoid duplicating backend business rules in multiple places.

---

# Testing

AURA Grid combines data processing, ML inference, APIs, database access, and frontend workflows, so testing should cover the important paths through the system.

## Run Tests

```powershell
pytest
```

Verbose:

```powershell
pytest -v
```

Specific file:

```powershell
pytest tests/test_api.py -v
```

Coverage:

```powershell
pytest --cov=src
```

---

## Writing Tests

Place tests in:

```text
tests/
```

Use descriptive names such as:

```text
tests/
├── test_api.py
├── test_prediction.py
├── test_risk_scoring.py
└── ...
```

A good test should verify one meaningful behavior.

Example:

```python
def test_low_risk_transformer():
    result = calculate_risk_score(
        probability=0.1,
        grid_impact=0.1,
        criticality=0.1,
        weather_risk=0.1,
    )

    assert result < 0.3
```

Keep test expectations synchronized with the actual implementation.

---

## What to Test

For prediction-related changes, consider:

- Valid input
- Missing values
- Invalid transformer IDs
- Boundary values
- Risk category transitions
- Individual predictions
- Batch predictions
- Database failures
- Model-loading failures where applicable
- API error responses

---

## Coverage

For a mature version of the project, approximately **80% coverage** is a useful engineering goal.

Coverage should support meaningful testing rather than becoming a target achieved through superficial tests.

---

# Commit Messages

Use concise commit messages that explain the change.

Recommended format:

```text
type: short description
```

Common types:

```text
fix:
feature:
refactor:
test:
docs:
chore:
```

Examples:

```text
fix: handle missing sensor values

feature: add batch transformer prediction

refactor: simplify risk calculation

test: add transformer API coverage

docs: update PostgreSQL setup instructions

chore: update Python dependencies
```

---

# Pull Request Process

Before opening a pull request:

1. Make sure the branch contains only the intended changes.
2. Run the relevant tests.
3. Check that the application starts locally.
4. Update documentation if behavior changed.
5. Make sure no secrets are included.
6. Review the Git diff.

A pull request should explain:

### What changed?

Briefly describe the implementation.

### Why was it changed?

Explain the problem or user need.

### How was it tested?

Include the commands or workflow used to verify it.

### Anything reviewers should know?

Mention important design decisions, limitations, or follow-up work.

---

# Project Structure

The main application structure is:

```text
src/
├── backend/
│   ├── app.py
│   ├── api.py
│   ├── schemas.py
│   └── database.py
│
├── model/
│   ├── predict.py
│   └── ...
│
├── advisor/
│   ├── maintenance_advisor.py
│   └── crew_optimizer.py
│
├── bob/
│   └── bob_service.py
│
├── data/
│   └── ...
│
└── frontend/
    ├── package.json
    └── src/
        ├── App.jsx
        └── ...
```

Other important areas:

```text
docs/
demo/
presentation/
tests/
```

---

## When Adding a New Module

When a new capability is needed:

1. Put it in the most appropriate existing `src/` module.
2. Avoid creating duplicate functionality.
3. Add tests.
4. Update `docs/architecture.md` if the system design changes.
5. Update the README or setup guide when setup or user behavior changes.
6. Watch for circular imports.

Before creating a new directory, check whether an existing module already owns that responsibility.

---

# Debugging

## Backend

Start the API with detailed logging:

```powershell
python -m uvicorn src.backend.app:app --log-level debug
```

FastAPI's interactive documentation can help inspect requests:

```text
http://localhost:8000/docs
```

For Python debugging, use your IDE debugger or `pdb` where appropriate.

---

## Frontend

Use browser developer tools:

```text
F12
```

Useful areas include:

- Console
- Network
- Application
- React DevTools

For API issues, inspect the Network tab and confirm the frontend is calling the correct backend URL.

---

# Common Development Issues

| Issue | What to check |
|---|---|
| Backend does not start | Python environment, dependencies, port 8000 |
| PostgreSQL connection fails | PostgreSQL service, database, credentials, `DATABASE_URL` |
| Model fails to load | Package/model compatibility and backend logs |
| Frontend cannot reach API | Backend URL, CORS, backend health endpoint |
| CSV prediction fails | File format, required columns, input values |
| IBM Bob request fails | Bob configuration, backend logs, request payload |
| Tests fail | Run `pytest -v` and inspect the first failing test |

Avoid hiding errors with broad exception handling. If a problem cannot be safely recovered from, it should be visible to the developer.

---

# Performance Guidelines

Transformer telemetry can become large, so performance should be considered when working with sensor data.

### Backend

- Query only the data needed for a request.
- Avoid repeatedly loading large datasets into memory.
- Use database indexes for common lookup patterns.
- Reuse existing database session handling.
- Batch operations where appropriate.

### Machine Learning

For multi-transformer analysis:

- Process records efficiently.
- Reuse loaded model objects.
- Avoid unnecessary repeated feature calculations.

### Frontend

- Keep large datasets out of unnecessary component state.
- Avoid unnecessary re-renders.
- Use memoization where it provides a measurable benefit.
- Load expensive visualizations only when needed.

Prefer simple solutions first and optimize based on actual application behavior.

---

# Documentation Guidelines

Keep documentation synchronized with the implementation.

When changing a feature, ask:

> "Would a new contributor or evaluator follow the documentation and get the same behavior?"

If not, update the documentation.

Use:

- Clear headings
- Short paragraphs
- Code blocks for commands
- Tables when useful
- Relative links between repository documents
- Diagrams when they clarify architecture

Important files:

```text
README.md
docs/problem-statement.md
docs/solution-overview.md
docs/architecture.md
docs/setup-guide.md
```

---

# Deployment Considerations

AURA Grid is planned as a split deployment:

```text
React / Vite
     ↓
Vercel
     ↓
HTTPS API
     ↓
Render
     ↓
FastAPI
     ↓
PostgreSQL + ML + IBM Bob
```

When changing backend APIs:

- Check the frontend integration.
- Check CORS configuration.
- Check production environment variables.
- Test the deployed API health endpoint.
- Avoid hard-coded `localhost` URLs in production.

When changing frontend API configuration:

- Confirm the deployed Render backend URL.
- Use environment variables where appropriate.
- Test the production build locally before deployment.

---

# Security Expectations

Never commit:

```text
.env
API keys
Database passwords
Private credentials
Production secrets
```

Use environment variables for secrets.

For a production deployment, the application should also use appropriate:

- Authentication
- Authorization
- HTTPS
- CORS restrictions
- Database access controls
- Secret management
- Logging and monitoring

---

# Release Process

For releases after the hackathon:

1. Confirm tests pass.
2. Review documentation.
3. Update the project version where applicable.
4. Create a Git tag.

Example:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Then create release notes describing the main changes.

---

# Questions, Bugs, and Ideas

For project-specific issues:

- Use **GitHub Issues** for bugs and feature requests.
- Use **GitHub Discussions** when broader discussion is useful.
- For team-specific decisions, coordinate with the project maintainers.

Repository:

```text
https://github.com/Nand13112004/bob-ai-hackathon-Chingaari
```

---

## Final Principle

Contributing to AURA Grid is not simply about adding more code.

Every change should make the platform more useful, reliable, understandable, or easier to operate.

The guiding workflow remains:

```text
Better Data
    ↓
Better Prediction
    ↓
Better Risk Understanding
    ↓
Better Maintenance Decisions
    ↓
Better Grid Reliability
```

**Thank you for helping improve AURA Grid.**
