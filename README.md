# AURA Grid: AI-Powered Transformer Failure Prediction & Crew Optimization

> **From predicting transformer risk to helping utility teams decide what to do next.**

AURA Grid is a predictive maintenance and decision-support platform designed to help power utility teams identify transformer failure risk early, understand why an asset is at risk, recommend appropriate maintenance actions, and connect those priorities with available maintenance crews.

The platform combines transformer telemetry, historical asset information, weather conditions, machine learning, operational rules, crew information, and IBM Bob into one workflow.

---

## Team

### Chingaari

**Bob AI Hackathon Submission**

| Role | Team Member |
|---|---|
| Team Lead | Mishva Bhadja |
| Member | Tirth Butani |
| Member | Nand Delvadiya |
| Member | Jeel Sadariya |

---

## The Problem

Transformer failures can quickly become an operational problem for utility teams.

The challenge is not only detecting an abnormal sensor value. Operators also need to understand:

- Is this transformer actually becoming risky?
- How urgent is the situation?
- What could happen if it fails?
- What maintenance should be considered?
- Which available crew is appropriate?
- Which transformer should be prioritized when several assets are at risk?

In many operational environments, this information is spread across sensor readings, historical records, maintenance data, weather information, and crew schedules.

That creates a gap between **detecting a problem** and **deciding what to do about it**.

AURA Grid is designed to close that gap.

---

## Our Solution

AURA Grid follows an end-to-end workflow:

```text
Transformer Data
      ↓
Sensor + History + Weather
      ↓
Feature Engineering
      ↓
Failure Risk Prediction
      ↓
Multi-Factor Risk Assessment
      ↓
Maintenance Recommendation
      ↓
Crew Matching
      ↓
Operator Dashboard
      ↓
IBM Bob / Ask AURA
      ↓
Actionable Decision
```

Instead of providing only a prediction, the platform turns that prediction into operational context.

### What AURA Grid does

1. **Predicts transformer failure risk** using an XGBoost-based ML pipeline.
2. **Combines multiple sources of information** including telemetry, asset history, maintenance, incidents, and weather.
3. **Ranks transformer risk** using prediction and operational context.
4. **Generates maintenance recommendations** based on observed conditions.
5. **Connects priority assets with crew information** such as skills and availability.
6. **Supports individual and batch analysis** so operators can investigate one transformer or analyze multiple assets.
7. **Provides conversational assistance through IBM Bob** so operators can ask questions about the current analysis.

---

## Key Features

### 🔮 Predictive Transformer Risk

AURA Grid uses machine learning to estimate transformer failure risk from structured operational data.

The prediction pipeline can use information such as:

- Temperature
- Vibration
- Partial discharge
- Oil temperature
- Oil moisture
- Oil acidity
- Load
- Voltage
- Current
- Humidity
- Weather conditions
- Historical incidents
- Maintenance history
- Transformer metadata

---

### 📊 Multi-Factor Risk Assessment

A failure probability alone does not tell the whole story.

AURA Grid combines the predicted risk with operational context such as:

- Grid impact
- Asset criticality
- Environmental/weather conditions

The result is presented using understandable risk categories:

```text
LOW → MEDIUM → HIGH → CRITICAL
```

This helps operators focus attention on the assets that matter most.

---

### 🛠️ Maintenance Advisor

AURA Grid translates abnormal operating conditions into practical maintenance guidance.

For example, combinations of elevated temperature, vibration, oil degradation, partial discharge, or excessive loading can lead to recommendations such as:

```text
Inspect transformer
Check thermal stress
Review oil condition
Investigate insulation condition
Consider load redistribution
```

The purpose is to move from:

> **"This transformer is risky."**

to:

> **"This transformer is risky, these are the contributing conditions, and this is the action to consider."**

---

### 👷 Crew Optimization

Maintenance decisions also depend on whether the right people are available.

AURA Grid considers operational crew information such as:

- Availability
- Skills/certifications
- Location/distance
- Type of maintenance response

This helps produce more useful crew options for priority assets.

---

### 📁 Individual + Batch Prediction

AURA Grid supports two analysis modes.

#### Individual Transformer

An operator can select or enter a transformer ID and investigate that specific asset.

```text
Transformer ID
      ↓
Retrieve Asset Data
      ↓
Prepare Features
      ↓
Run Prediction
      ↓
Risk + Recommendation
```

#### Batch CSV

An operator can upload multiple transformer records.

```text
CSV Upload
    ↓
Validate Data
    ↓
Predict Each Transformer
    ↓
Calculate Individual Risks
    ↓
Rank Results
    ↓
Generate Batch Summary
```

This makes the platform useful for both **asset-level investigation** and **fleet-level analysis**.

---

### 🤖 Ask AURA — IBM Bob

Operators can interact with the system using natural language through IBM Bob.

Example questions include:

> "Which transformers need maintenance?"

> "Which transformer should I inspect first?"

> "Why is this transformer at high risk?"

> "What maintenance action is recommended?"

The assistant is intended to work from the application's available context rather than inventing transformer or operational information.

---

### 🖥️ Interactive Dashboard

The dashboard brings the workflow together in one place.

It provides access to areas such as:

- Grid/transformer overview
- Risk visualization
- Transformer details
- Sensor/telemetry analysis
- Batch upload
- Maintenance recommendations
- Crew information
- Ask AURA

The goal is to give an operator a clear path from **data → risk → action**.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite |
| UI | Framer Motion, Recharts / visualization components |
| Backend | Python, FastAPI, Uvicorn |
| Machine Learning | XGBoost, scikit-learn |
| Data Processing | Pandas, NumPy |
| Model Serialization | Joblib |
| Database | PostgreSQL |
| Database Access | SQLAlchemy, Psycopg2 |
| AI Assistant | IBM Bob |
| Local Development | Windows / Linux / macOS compatible |
| Frontend Deployment | Vercel |
| Backend Deployment | Render |

---

## Architecture

At a high level, the deployed application follows:

```text
                         ┌──────────────────┐
                         │    User / Judge   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Vercel Frontend  │
                         │ React + Vite     │
                         └────────┬─────────┘
                                  │ HTTPS / REST API
                                  ▼
                         ┌──────────────────┐
                         │ Render Backend   │
                         │ FastAPI          │
                         └───────┬───┬──────┘
                                 │   │
                   ┌─────────────┘   └──────────────┐
                   ▼                                ▼
          ┌─────────────────┐              ┌─────────────────┐
          │ PostgreSQL      │              │ ML + Advisor    │
          │ Grid Data       │              │ XGBoost + Rules │
          └─────────────────┘              └────────┬────────┘
                                                    │
                                                    ▼
                                           ┌─────────────────┐
                                           │ IBM Bob / AURA  │
                                           └─────────────────┘
```

For the detailed design, see [`docs/architecture.md`](docs/architecture.md).

---

# How to Run Locally

## Prerequisites

Install:

- Python 3.12+
- Node.js 18+
- npm
- PostgreSQL
- Git

Verify:

```bash
python --version
node --version
npm --version
psql --version
```

---

## 1. Clone the Repository

```bash
git clone https://github.com/Nand13112004/bob-ai-hackathon-Chingaari.git
cd bob-ai-hackathon-Chingaari
```

---

## 2. Create the Python Environment

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Then install dependencies:

```powershell
pip install -r requirements.txt
```

---

## 3. Configure PostgreSQL

Create the database:

```sql
CREATE DATABASE grid_prediction;
```

The application uses the following database configuration:

```text
Host: localhost
Port: 5432
Database: grid_prediction
User: postgres
```

Load the project data:

```powershell
python import_to_postgres.py
```

The main tables are:

```text
transformers
sensor_readings
weather_data
incidents
maintenance
crew
```

---

## 4. Configure `.env`

Create a local `.env` file and configure:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/grid_prediction
```

Never commit the real `.env` file or database credentials.

---

## 5. Verify Database Connection

Run:

```powershell
python src/backend/test_db.py
```

You should see a successful PostgreSQL connection message.

---

## 6. Start the Backend

From the repository root:

```powershell
python -m uvicorn src.backend.app:app --host 0.0.0.0 --port 8000 --reload
```

Backend:

```text
http://localhost:8000
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

Health check:

```powershell
curl http://localhost:8000/api/health
```

---

## 7. Start the Frontend

Open another terminal:

```powershell
cd src/frontend
npm install
npm run dev -- --host 0.0.0.0
```

Open:

```text
http://localhost:5173
```

For the complete setup and troubleshooting guide, see [`docs/setup-guide.md`](docs/setup-guide.md).

---

# Deployment

AURA Grid is designed for a simple split deployment:

```text
Frontend
React + Vite
     │
     ▼
Vercel
     │
     │ HTTPS API requests
     ▼
Render
FastAPI Backend
     │
     ├──────────────► PostgreSQL
     │
     ├──────────────► ML Pipeline
     │
     └──────────────► IBM Bob
```

## Frontend — Vercel

The React/Vite application can be deployed to Vercel.

Typical build configuration:

```text
Framework: Vite
Root Directory: src/frontend
Build Command: npm run build
Output Directory: dist
```

The frontend should use an environment variable for the deployed backend URL rather than hard-coding `localhost`.

For example:

```env
VITE_API_URL=https://<your-render-backend>.onrender.com
```

The exact variable name should match the frontend implementation.

---

## Backend — Render

The FastAPI backend can be deployed as a Render Web Service.

Typical configuration:

```text
Environment: Python
Build Command: pip install -r requirements.txt
Start Command: uvicorn src.backend.app:app --host 0.0.0.0 --port $PORT
```

Configure the PostgreSQL connection as a Render environment variable:

```env
DATABASE_URL=<your-postgresql-connection-string>
```

Do not commit database credentials to the repository.

After deployment, verify:

```text
https://<your-render-backend>.onrender.com/api/health
```

Then configure the Vercel frontend to call that backend URL.

---

# Demo

The recommended demonstration follows the complete decision workflow:

```text
Dashboard
   ↓
Select Transformer
   ↓
Inspect Telemetry
   ↓
Run Prediction
   ↓
View Risk
   ↓
View Maintenance Recommendation
   ↓
View Crew Options
   ↓
Upload Batch CSV
   ↓
Review Batch Summary
   ↓
Ask AURA / IBM Bob
```

### Demo Video

The final demo video link will be available through:

`demo/demo-video-link.txt`

### Screenshots

Demo screenshots are stored in:

`demo/screenshots/`

### Live Deployment

The deployed URLs will be maintained in the project submission materials once the Vercel frontend and Render backend are live.

---

# API Overview

The backend exposes REST endpoints for the main application workflows.

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Backend and model health |
| `GET /api/transformers` | List transformers |
| `GET /api/transformers/{transformer_id}` | Transformer details |
| `POST /api/predict` | Individual prediction |
| `POST /api/predict/batch` | Batch CSV prediction |
| `GET /api/risk-assets` | Ranked risk assets |
| `GET /api/crew` | Crew information |
| `GET /api/maintenance` | Maintenance recommendations |
| `GET /api/dashboard` | Dashboard summary |
| `POST /api/bob/query` | Ask AURA / IBM Bob |

The interactive API documentation is available at `/docs` when the FastAPI backend is running.

---

# Documentation

| Document | Description |
|---|---|
| [`docs/problem-statement.md`](docs/problem-statement.md) | The operational problem AURA Grid addresses |
| [`docs/solution-overview.md`](docs/solution-overview.md) | Detailed explanation of the solution |
| [`docs/architecture.md`](docs/architecture.md) | System architecture and technical design |
| [`docs/setup-guide.md`](docs/setup-guide.md) | Local setup, database configuration, testing, and troubleshooting |

---

# Known Limitations

AURA Grid is a hackathon/prototype decision-support platform. It is not intended to directly control critical grid infrastructure.

### Model validation

The ML pipeline should be evaluated on representative utility data before any production deployment.

### Data quality

Prediction quality depends on the accuracy, completeness, and freshness of sensor, maintenance, incident, weather, and asset data.

### Model compatibility

Serialized ML models can be sensitive to library versions. The project includes resilience/fallback behavior where supported by the implementation.

### Crew information

Crew recommendations depend on the quality and freshness of crew availability, skill, and location information.

### Deployment cold starts

On some hosting configurations, the backend may take time to start after a period of inactivity. This is a hosting consideration rather than a prediction feature.

### Production security

A production deployment should use restricted CORS settings, secure secret management, authentication/authorization, HTTPS, database access controls, logging, and monitoring.

---

# What We Are Most Proud Of

### 1. Turning prediction into action

We did not want to stop at a probability score.

AURA Grid connects:

```text
Prediction
    ↓
Risk
    ↓
Recommendation
    ↓
Crew
    ↓
Decision
```

That makes the system more useful from an operator's perspective.

### 2. Supporting both asset-level and fleet-level analysis

An operator can investigate one transformer or upload multiple transformer records for batch analysis.

### 3. Connecting technical and operational context

Sensor values alone do not determine operational priority. AURA Grid also considers asset and grid context.

### 4. Building for resilience

The application is designed to degrade gracefully where supported, rather than making one unavailable component bring down the entire decision-support workflow.

### 5. Integrating IBM Bob into the workflow

IBM Bob gives operators a natural-language way to explore the current analysis instead of forcing them to manually inspect every data point.

---

# Future Direction

AURA Grid can evolve beyond the current prototype by adding:

- Continuous streaming telemetry
- More extensive historical transformer datasets
- Automated model retraining and monitoring
- Stronger model explainability
- Real-time weather feeds
- More advanced crew scheduling
- Authentication and role-based access
- Production observability and alerting
- Integration with utility asset-management systems
- Feedback loops from completed maintenance work

The long-term vision is a platform that continuously moves through:

```text
Observe
  ↓
Understand
  ↓
Predict
  ↓
Prioritize
  ↓
Recommend
  ↓
Respond
  ↓
Learn
```

---

# Repository

**GitHub:**  
https://github.com/Nand13112004/bob-ai-hackathon-Chingaari

**Hackathon:**  
Bob AI Hackathon

---

## Closing Thought

> **AURA Grid is built around one simple idea: give utility teams enough context to act before a transformer problem becomes a grid outage.**
