from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from src.bob.prompts import BOB_SYSTEM_PROMPT

# Automatically load environment variables from root .env with override=True
env_path = Path(__file__).resolve().parents[2] / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    load_dotenv(override=True)


class BobService:
    """AURA AI Assistant / Gemini Operational Assistant Service.
    
    Supports Google Gemini API, IBM Cloud / watsonx.ai APIs, and falls back to an
    intelligent grounded operational reasoning engine.
    """

    def __init__(self, data_store: Dict[str, Any] | None = None) -> None:
        self.data_store = data_store or {}
        
        # Load Gemini API Key from environment
        self.gemini_api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or ""
        ).strip()
        # Keep the model configurable so deployments can move to a Gemini model
        # available to their Google AI project without changing application code.
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
        self.gemini_error: str | None = None

        # Load Watsonx / Legacy credentials if present
        self.api_key = (
            os.getenv("IBM_BOB_API_KEY")
            or os.getenv("WATSONX_APIKEY")
            or os.getenv("IBM_WATSONX_APIKEY")
            or ""
        ).strip()
        self.project_id = (
            os.getenv("IBM_BOB_PROJECT_ID")
            or os.getenv("WATSONX_PROJECT_ID")
            or os.getenv("IBM_WATSONX_PROJECT_ID")
            or ""
        ).strip()
        self.url = (
            os.getenv("IBM_BOB_URL")
            or os.getenv("WATSONX_URL")
            or os.getenv("IBM_WATSONX_URL")
            or "https://us-south.ml.cloud.ibm.com"
        ).rstrip("/")
        self.model_id = (
            os.getenv("IBM_BOB_MODEL_ID")
            or os.getenv("WATSONX_MODEL_ID")
            or os.getenv("IBM_WATSONX_MODEL_ID")
            or "ibm/granite-3-8b-instruct"
        ).strip()
        self.iam_url = os.getenv("IBM_IAM_URL", "https://iam.cloud.ibm.com/identity/token")

    @property
    def is_gemini_configured(self) -> bool:
        """Returns True if Google Gemini API key is configured."""
        return bool(self.gemini_api_key)

    @property
    def is_api_configured(self) -> bool:
        """Returns True if live IBM API credentials are fully configured."""
        return bool(self.api_key and self.project_id)

    def get_status(self) -> Dict[str, Any]:
        """Returns the current AI Assistant service configuration status."""
        if self.is_gemini_configured:
            return {
                "status": "online",
                "mode": "live_gemini_api",
                "provider": "AURA AI (Google Gemini AI)",
                "model": self.gemini_model,
                "project_id_configured": True,
                "url": "https://generativelanguage.googleapis.com",
                "last_error": self.gemini_error,
            }
        if self.is_api_configured:
            return {
                "status": "online",
                "mode": "live_api",
                "provider": "AURA AI (watsonx.ai)",
                "model": self.model_id,
                "project_id_configured": True,
                "url": self.url,
            }
        return {
            "status": "online",
            "mode": "grounded_engine",
            "provider": "AURA AI (Grounded Engine)",
            "model": "AURA Grounded Core",
            "project_id_configured": False,
            "note": "Running on Grounded Intelligence Engine. Configure GEMINI_API_KEY in .env for live Gemini LLM API.",
        }

    def _get_iam_token(self) -> Optional[str]:
        """Fetches IBM Cloud IAM OAuth Bearer Token using the API key."""
        if not self.api_key:
            return None
        data = urllib.parse.urlencode({
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": self.api_key,
        }).encode("utf-8")
        req = urllib.request.Request(
            self.iam_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("access_token")
        except Exception:
            return None

    def _build_grounded_db_context(self) -> str:
        """Constructs rich, strictly grounded database context from live grid data."""
        assets = self.data_store.get("risk_assets", [])
        crews = self.data_store.get("crew", [])
        
        # The API injects this same database snapshot into the service. Avoid a
        # second network query while preparing the LLM prompt; it keeps an
        # answer internally consistent with the data shown to the operator.
        history = self.data_store.get("prediction_history")
        if history is None:
            try:
                from src.backend.supabase_store import prediction_store
                history = prediction_store.list()
            except Exception:
                history = []

        summary_lines = []
        summary_lines.append("=== AUTHORITATIVE LIVE GRID DATABASE CONTEXT ===")
        summary_lines.append(f"Total Monitored Assets Currently Evaluated: {len(assets)}")

        if assets:
            summary_lines.append("\n--- ACTIVE TRANSFORMER ASSET TELEMETRY & RISK DB ---")
            for item in assets:
                tid = item.get("transformer_id")
                level = item.get("risk_level", "UNKNOWN")
                prob = item.get("failure_probability", 0)
                score = item.get("risk_score", 0)
                prio = item.get("priority", "N/A")
                reasons = ", ".join(item.get("reasons", [])) or "Nominal operation"
                rec_maint = item.get("maintenance_recommendation", "Routine monitoring")
                
                crew_rec = item.get("crew_recommendation", {})
                rec_crew = crew_rec.get("crew_name", "None")
                act_crew = crew_rec.get("deployment_action", "MONITOR")

                reading = item.get("reading", {})
                temp = reading.get("temperature_c", "N/A")
                vib = reading.get("vibration_mm_s", "N/A")
                pd_val = reading.get("partial_discharge_pc", "N/A")
                oil_acid = reading.get("oil_acidity_mgKOH_g", "N/A")
                load_pct = reading.get("load_percentage", "N/A")

                summary_lines.append(
                    f"• Transformer Asset [{tid}]: Risk Level={level} | 7-Day Failure Probability={prob:.1f}% | Risk Score={score:.1f} | Priority={prio}\n"
                    f"   - Anomaly Drivers: {reasons}\n"
                    f"   - Live Telemetry: Temp={temp}°C, Vibration={vib}mm/s, Partial Discharge={pd_val}pC, Oil Acidity={oil_acid}mgKOH/g, Load={load_pct}%\n"
                    f"   - Prescriptive Maintenance: {rec_maint}\n"
                    f"   - Fleet Dispatch: {rec_crew} (Action: {act_crew})"
                )

        if crews:
            summary_lines.append("\n--- FIELD DISPATCH CREWS DB ---")
            for c in crews:
                c_name = c.get("crew_name")
                c_id = c.get("crew_id")
                c_type = c.get("crew_type")
                c_skill = c.get("skill_level")
                c_avail = "Active & Available" if c.get("available") else "Unavailable"
                c_dist = c.get("max_distance_km")
                summary_lines.append(f"• Crew [{c_name}] (ID: {c_id}): Type={c_type}, Skill={c_skill}, Status={c_avail}, Max Range={c_dist}km")

        if history:
            summary_lines.append(f"\n--- AUDIT LOG (Total Historical Checks Stored: {len(history)}) ---")
            for h in history[:10]:
                summary_lines.append(
                    f"• Check at {h.get('checked_at', '')} -> {h.get('transformer_id')}: Risk={h.get('risk_level')}, FailProb={h.get('failure_probability')}%, Score={h.get('risk_score')}"
                )

        return "\n".join(summary_lines)

    def _call_gemini_api(self, question: str) -> Optional[str]:
        """Calls Google Gemini API using GEMINI_API_KEY with strict DB grounding."""
        if not self.gemini_api_key:
            return None

        db_context = self._build_grounded_db_context()
        
        system_instructions = (
            "You are AURA AI Assistant, an expert AI Grid Operations Copilot grounded strictly in live database telemetry and model prediction outputs.\n\n"
            "STRICT GROUNDING & ANTI-HALLUCINATION RULES:\n"
            "1. Answer the user's question using ONLY the facts, telemetry values, risk scores, maintenance directives, and crew data provided in the AUTHORITATIVE LIVE GRID DATABASE CONTEXT below.\n"
            "2. Do NOT invent, assume, or fabricate any transformer IDs, metrics, temperatures, failure probabilities, or crew names that are not in the provided database context.\n"
            "3. If the user asks about a transformer ID or asset that is NOT present in the database context, explicitly inform them that the specified asset has not been evaluated in the current database session.\n"
            "4. Format your answer cleanly using GitHub-style Markdown (bolding key transformer IDs, risk scores, and percentages).\n"
            "5. Be direct, authoritative, professional, and clear."
        )

        payload = {
            "systemInstruction": {
                "parts": [{"text": system_instructions}]
            },
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                f"{db_context}\n\n"
                                f"OPERATOR QUESTION: {question}\n\n"
                                "GROUNDED ANSWER:"
                            )
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,  # Low temperature for strict factual adherence
                "maxOutputTokens": 850,
            }
        }
        
        encoded_data = json.dumps(payload).encode("utf-8")

        # Try the configured model first, then a currently available alias.
        # Do not fall back to retired Gemini 2.0 models.
        models_to_try = list(dict.fromkeys([self.gemini_model, "gemini-3-flash-preview", "gemini-flash-latest"]))
        attempt_errors: List[str] = []
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_api_key}"
            req = urllib.request.Request(
                url,
                data=encoded_data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=12) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    candidates = res_data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            ans = parts[0]["text"].strip()
                            if ans:
                                self.gemini_error = None
                                return ans
            except urllib.error.HTTPError as e:
                # The server body contains the actionable reason (for example,
                # billing, quota, or model access) but never include the API key.
                try:
                    details = json.loads(e.read().decode("utf-8")).get("error", {}).get("message", "")
                except Exception:
                    details = ""
                attempt_errors.append(f"Gemini {model}: HTTP {e.code}" + (f" — {details[:240]}" if details else ""))
                continue
            except Exception as exc:
                attempt_errors.append(f"Gemini {model}: {type(exc).__name__} — {str(exc)[:240]}")
                continue

        self.gemini_error = " | ".join(attempt_errors)[:600] or "Gemini returned no candidate response."
        return None

    def _call_watsonx_api(self, question: str) -> Optional[str]:
        """Calls IBM watsonx.ai text generation endpoint."""
        token = self._get_iam_token()
        if not token:
            return None

        db_context = self._build_grounded_db_context()
        prompt = f"{BOB_SYSTEM_PROMPT}\n\n{db_context}\n\nOPERATOR QUESTION: {question}\n\nAURA AI ANSWER:"
        endpoint = f"{self.url}/ml/v1/text/generation?version=2023-05-29"
        
        payload = {
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": 400,
                "min_new_tokens": 10,
                "repetition_penalty": 1.1,
            },
            "model_id": self.model_id,
            "project_id": self.project_id,
        }

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                results = result.get("results", [])
                if results and "generated_text" in results[0]:
                    return results[0]["generated_text"].strip()
        except Exception:
            return None
        return None

    def query_detailed(self, question: str) -> Dict[str, Any]:
        """Queries AURA AI Assistant and returns answer alongside metadata."""
        if not question or not question.strip():
            return {
                "answer": "Please enter a valid operational question.",
                "provider": "AURA AI Assistant",
                "model": self.gemini_model,
            }

        # 1. Primary: Google Gemini API (if GEMINI_API_KEY configured)
        if self.is_gemini_configured:
            gemini_ans = self._call_gemini_api(question)
            if gemini_ans:
                return {
                    "answer": gemini_ans,
                    "provider": "AURA AI (Google Gemini AI)",
                    "model": self.gemini_model,
                }

        # 2. Secondary: Watsonx API (if credentials configured)
        if self.is_api_configured:
            api_answer = self._call_watsonx_api(question)
            if api_answer:
                return {
                    "answer": api_answer,
                    "provider": "AURA AI (watsonx.ai)",
                    "model": self.model_id,
                }

        # 3. Grounded Intelligence Engine fallback
        grounded_answer = self._query_grounded_engine(question)
        return {
            "answer": grounded_answer,
            "provider": "AURA AI (Grounded DB Fallback)",
            "model": "AURA Grounded Core",
        }

    def query(self, question: str) -> str:
        """Query method for backward compatibility."""
        return self.query_detailed(question)["answer"]

    def _query_grounded_engine(self, question: str) -> str:
        """Grounded Operational Intelligence Engine for AURA AI Assistant."""
        q = question.lower()
        raw_assets = self.data_store.get("risk_assets", [])
        # Prediction history can contain more than one check for the same
        # transformer. Keep the newest entry supplied by the database so a
        # request for "all transformers" returns each asset once.
        assets_by_id: Dict[str, Dict[str, Any]] = {}
        for asset in raw_assets:
            transformer_id = asset.get("transformer_id")
            if transformer_id and transformer_id not in assets_by_id:
                assets_by_id[transformer_id] = asset
        assets = list(assets_by_id.values())
        crews = self.data_store.get("crew", [])

        # 0. Count / Quantity Questions (e.g. "how many transformers do you have?")
        if any(w in q for w in ["how many", "count", "number of", "total transformer"]):
            total_assets = len(assets)
            if total_assets == 0:
                return (
                    "### 🤖 AURA AI Assistant\n\n"
                    "Currently, no transformer risk evaluations have been performed in this active session. "
                    "You can run an evaluation from the Overview Matrix or Risk Portal to ingest transformer readings."
                )
            crit = sum(1 for a in assets if a.get("risk_level") == "CRITICAL")
            high = sum(1 for a in assets if a.get("risk_level") == "HIGH")
            med = sum(1 for a in assets if a.get("risk_level") == "MEDIUM")
            low = sum(1 for a in assets if a.get("risk_level") == "LOW")
            return (
                f"### 🤖 AURA AI Assistant\n\n"
                f"Currently, there are **{total_assets}** active transformer assets evaluated in the live database context:\n\n"
                f"- 🚨 **Critical Risk:** `{crit}`\n"
                f"- ⚠️ **High Risk:** `{high}`\n"
                f"- 🟡 **Medium Risk:** `{med}`\n"
                f"- 🟢 **Low Risk:** `{low}`\n"
            )

        # 1. List evaluated assets. This also handles natural follow-ups such
        # as "list all of them" after asking for a transformer count.
        asset_list_phrases = (
            "list all", "show all", "all transformers", "all assets",
            "list them", "show them", "all of them",
        )
        is_crew_question = any(k in q for k in ("crew", "deploy", "team", "dispatch"))
        if any(phrase in q for phrase in asset_list_phrases) and not is_crew_question:
            if not assets:
                return "No transformer check data is currently available. Run a risk evaluation to populate the database."
            ranked_assets = sorted(assets, key=lambda item: item.get("risk_score", 0), reverse=True)
            lines = [f"### Evaluated Transformer Assets ({len(ranked_assets)})", ""]
            for index, item in enumerate(ranked_assets, 1):
                reasons = ", ".join(item.get("reasons", [])) or "No active anomaly drivers"
                lines.append(
                    f"{index}. **{item.get('transformer_id')}** — **{item.get('risk_level', 'UNKNOWN')}** risk "
                    f"| Failure probability: **{float(item.get('failure_probability') or 0):.1f}%** "
                    f"| Score: `{float(item.get('risk_score') or 0):.1f}`\n"
                    f"   - Drivers: {reasons}\n"
                    f"   - Action: {item.get('maintenance_recommendation') or 'Routine monitoring'}"
                )
            return "\n".join(lines)

        # 2. Specific Transformer Query (e.g. TR068, TR012, etc.)
        transformer_match = re.search(r"tr\d+", q)
        if transformer_match:
            transformer_id = transformer_match.group(0).upper()
            asset = next((item for item in assets if item["transformer_id"] == transformer_id), None)
            if asset:
                prob = asset.get("failure_probability", 0)
                level = asset.get("risk_level", "UNKNOWN")
                score = asset.get("risk_score", 0)
                reasons = asset.get("reasons", [])
                reasons_str = ", ".join(reasons) if reasons else "no critical telemetry anomalies"
                rec = asset.get("maintenance_recommendation", "Routine monitoring")
                crew_rec = asset.get("crew_recommendation", {})
                crew_name = crew_rec.get("crew_name", "No crew assigned")
                deployment = crew_rec.get("deployment_action", "MONITOR")
                
                reading = item.get("reading", {}) if 'item' in locals() else asset.get("reading", {})
                temp = reading.get("temperature_c", "N/A")
                vib = reading.get("vibration_mm_s", "N/A")
                pd_val = reading.get("partial_discharge_pc", "N/A")
                oil_acid = reading.get("oil_acidity_mgKOH_g", "N/A")
                load_pct = reading.get("load_percentage", "N/A")

                return (
                    f"### 🤖 AURA AI Analysis for **{transformer_id}**\n\n"
                    f"- **Status & Priority:** **{level}** Risk | Priority {asset.get('priority', 'P3')} | Score **{score:.1f}**\n"
                    f"- **Failure Probability (Next 7 Days):** **{prob:.2f}%**\n"
                    f"- **Risk Drivers:** {reasons_str}\n"
                    f"- **Latest Telemetry:** Temp: `{temp}°C` | Vibration: `{vib} mm/s` | Partial Discharge: `{pd_val} pC` | Oil Acidity: `{oil_acid} mgKOH/g` | Load: `{load_pct}%`\n"
                    f"- **Recommended Maintenance Action:** {rec}\n"
                    f"- **Recommended Crew Response:** **{crew_name}** ({deployment})\n"
                )
            return f"I searched the active grid dataset, but **{transformer_id}** has not been evaluated in the current session. Please perform a risk evaluation first."

        # 3. Top Risky Assets / Critical Transformers
        if any(phrase in q for phrase in ["top 5", "top risk", "risky transformers", "highest risk", "most critical"]):
            if not assets:
                return "No transformer check data is currently available. Evaluate risk from the Dashboard to populate live assets."
            top = sorted(assets, key=lambda item: item.get("risk_score", 0), reverse=True)[:5]
            lines = ["### 🤖 Top Risky Transformers (Ranked by 7-Day Failure Score)\n"]
            for idx, item in enumerate(top, 1):
                lines.append(
                    f"{idx}. **{item['transformer_id']}** — **{item['risk_level']}** Risk (Score: `{item['risk_score']:.1f}`, Fail Prob: `{item['failure_probability']:.1f}%`)\n"
                    f"   *Drivers:* {', '.join(item.get('reasons', []))}\n"
                    f"   *Action:* {item.get('maintenance_recommendation')}\n"
                )
            return "\n".join(lines)

        # 4. Urgent Maintenance Questions
        if "maintenance" in q or "repair" in q or "urgent" in q:
            urgent = [item for item in assets if item.get("risk_level") in ("CRITICAL", "HIGH")]
            if urgent:
                lines = [f"### 🤖 Immediate Maintenance Required ({len(urgent)} Assets)\n"]
                for item in urgent:
                    lines.append(
                        f"- **{item['transformer_id']}** [{item['risk_level']} / {item.get('priority')}]: {item.get('maintenance_recommendation')} *(Fail Prob: {item.get('failure_probability'):.1f}%)*"
                    )
                return "\n".join(lines)
            return "### 🤖 Maintenance Status\nNo transformers currently require immediate high-priority maintenance. All monitored assets are within acceptable operating parameters."

        # 5. Crew Optimization / Dispatch Questions
        if any(k in q for k in ["crew", "deploy", "team", "dispatch"]):
            available_crews = [c for c in crews if c.get("available")]
            if available_crews:
                lines = [f"### 🤖 Available Field Response Crews ({len(available_crews)} Active)\n"]
                for c in available_crews:
                    lines.append(
                        f"- **{c.get('crew_name')}** (`{c.get('crew_id')}`): Type: **{c.get('crew_type')}** | Skill: {c.get('skill_level')} | Max Range: `{c.get('max_distance_km')} km`"
                    )
                lines.append("\n*Note: Crew deployment is automatically matched based on transformer proximity, skill level, and urgency.*")
                return "\n".join(lines)
            return "### 🤖 Crew Status\nNo available response crews are currently marked active in the database."

        # 6. Grid Summary / Health Overview
        if any(k in q for k in ["summary", "overview", "health", "status", "grid", "report"]):
            total = len(assets)
            if total == 0:
                return "### 🤖 Grid Overview\nNo transformer check records in current session. Run an evaluation from the Check Portal."
            crit = sum(1 for a in assets if a.get("risk_level") == "CRITICAL")
            high = sum(1 for a in assets if a.get("risk_level") == "HIGH")
            med = sum(1 for a in assets if a.get("risk_level") == "MEDIUM")
            low = sum(1 for a in assets if a.get("risk_level") == "LOW")
            avg_prob = sum(a.get("failure_probability", 0) for a in assets) / total
            highest = max(assets, key=lambda item: item.get("risk_score", 0))

            return (
                "### 🤖 Live Grid Health & Risk Summary\n\n"
                f"- **Total Checked Assets:** `{total}`\n"
                f"- **Risk Breakdown:** 🚨 Critical: `{crit}` | ⚠️ High: `{high}` | 🟡 Medium: `{med}` | 🟢 Low: `{low}`\n"
                f"- **Average 7-Day Failure Probability:** `{avg_prob:.2f}%`\n"
                f"- **Highest Threat Asset:** **{highest['transformer_id']}** ({highest['risk_level']} Risk, Score `{highest['risk_score']:.1f}`)\n"
                "- **System Readiness:** XGBoost prediction model & maintenance advisor active.\n"
            )

        # 7. Default Grounded Assistance Prompt
        return (
            "### 🤖 AURA AI Operational Assistant\n\n"
            "I can answer operational grid questions grounded in your live transformer telemetry and XGBoost model predictions. Try asking:\n\n"
            "- *\"How many transformers do you have?\"*\n"
            "- *\"List all transformers\"*\n"
            "- *\"Why is TR068 risky?\"*\n"
            "- *\"Show top 5 risky transformers\"*\n"
            "- *\"Which transformers need urgent maintenance?\"*\n"
            "- *\"Show available deployment crews\"*\n"
            "- *\"Give a summary of overall grid health\"*\n"
        )
