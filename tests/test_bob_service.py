import os
import json
from unittest.mock import patch, MagicMock

from src.bob.bob_service import BobService


def test_bob_service_status_default():
    service = BobService()
    status = service.get_status()
    assert status["status"] == "online"
    assert status["mode"] == "grounded_engine"
    assert "Grounded" in status["provider"]


def test_bob_service_status_api_configured(monkeypatch):
    monkeypatch.setenv("IBM_BOB_API_KEY", "mock_key")
    monkeypatch.setenv("IBM_BOB_PROJECT_ID", "mock_project")
    service = BobService()
    status = service.get_status()
    assert status["status"] == "online"
    assert status["mode"] == "live_api"
    assert "watsonx.ai" in status["provider"]


def test_bob_query_transformer():
    mock_assets = [
        {
            "transformer_id": "TR068",
            "risk_level": "HIGH",
            "priority": "P1",
            "risk_score": 88.5,
            "failure_probability": 74.2,
            "reasons": ["high temperature", "oil acidity"],
            "maintenance_recommendation": "Perform immediate oil filtration",
            "crew_recommendation": {"crew_name": "Alpha Response Crew", "deployment_action": "DISPATCH CREW"},
            "reading": {"temperature_c": 89, "vibration_mm_s": 4.1, "partial_discharge_pc": 20, "oil_acidity_mgKOH_g": 0.15, "load_percentage": 92},
        }
    ]
    service = BobService({"risk_assets": mock_assets})
    res = service.query_detailed("Why is TR068 risky?")
    assert "TR068" in res["answer"]
    assert "74.20%" in res["answer"]
    assert "Perform immediate oil filtration" in res["answer"]


def test_bob_query_top_risky():
    mock_assets = [
        {"transformer_id": "TR001", "risk_score": 90.0, "risk_level": "CRITICAL", "failure_probability": 85.0, "reasons": ["vibration"], "maintenance_recommendation": "Inspect coils"},
        {"transformer_id": "TR002", "risk_score": 60.0, "risk_level": "MEDIUM", "failure_probability": 40.0, "reasons": ["load"], "maintenance_recommendation": "Monitor"},
    ]
    service = BobService({"risk_assets": mock_assets})
    ans = service.query("Show top 5 risky transformers")
    assert "TR001" in ans
    assert "CRITICAL" in ans


def test_bob_query_list_all_transformers_and_follow_up_wording():
    mock_assets = [
        {"transformer_id": "TR001", "risk_score": 90.0, "risk_level": "CRITICAL", "failure_probability": 85.0, "reasons": ["vibration"], "maintenance_recommendation": "Inspect coils"},
        {"transformer_id": "TR002", "risk_score": 60.0, "risk_level": "MEDIUM", "failure_probability": 40.0, "reasons": ["load"], "maintenance_recommendation": "Monitor"},
        # An older duplicate must not be listed as a separate transformer.
        {"transformer_id": "TR001", "risk_score": 20.0, "risk_level": "LOW", "failure_probability": 10.0},
    ]
    service = BobService({"risk_assets": mock_assets, "prediction_history": []})
    answer = service._query_grounded_engine("list all of them")
    assert "Evaluated Transformer Assets (2)" in answer
    assert answer.count("**TR001**") == 1
    assert "**TR002**" in answer


def test_bob_query_maintenance():
    mock_assets = [
        {"transformer_id": "TR068", "risk_level": "CRITICAL", "priority": "P1", "maintenance_recommendation": "Emergency replacement", "failure_probability": 92.0}
    ]
    service = BobService({"risk_assets": mock_assets})
    ans = service.query("Which transformers need urgent maintenance?")
    assert "TR068" in ans
    assert "Emergency replacement" in ans


def test_bob_query_crew():
    mock_crews = [
        {"crew_id": "C01", "crew_name": "Grid Squad 1", "crew_type": "HIGH VOLTAGE", "available": True, "skill_level": "SENIOR", "max_distance_km": 50}
    ]
    service = BobService({"crew": mock_crews})
    ans = service.query("Show available crews for dispatch")
    assert "Grid Squad 1" in ans
    assert "HIGH VOLTAGE" in ans


def test_bob_query_summary():
    mock_assets = [
        {"transformer_id": "TR001", "risk_score": 95.0, "risk_level": "CRITICAL", "failure_probability": 88.0},
        {"transformer_id": "TR002", "risk_score": 30.0, "risk_level": "LOW", "failure_probability": 12.0},
    ]
    service = BobService({"risk_assets": mock_assets})
    ans = service.query("Give a grid summary")
    assert "Total Checked Assets" in ans
    assert "TR001" in ans


def test_bob_service_status_gemini_configured(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "mock_gemini_key")
    service = BobService()
    status = service.get_status()
    assert status["status"] == "online"
    assert status["mode"] == "live_gemini_api"
    assert "Google Gemini AI" in status["provider"]


def test_gemini_answer_is_grounded_in_database_context(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    asset = {
        "transformer_id": "TR068", "risk_level": "HIGH", "priority": "P1",
        "risk_score": 88.5, "failure_probability": 74.2,
        "reasons": ["high temperature"], "maintenance_recommendation": "Inspect cooling system",
        "crew_recommendation": {}, "reading": {"temperature_c": 89},
    }
    service = BobService({"risk_assets": [asset], "prediction_history": []})
    response = MagicMock()
    response.read.return_value = json.dumps({
        "candidates": [{"content": {"parts": [{"text": "**TR068** needs inspection."}]}}]
    }).encode("utf-8")

    with patch("src.bob.bob_service.urllib.request.urlopen") as urlopen:
        urlopen.return_value.__enter__.return_value = response
        result = service.query_detailed("What should we do about TR068?")

    request = urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))
    prompt = payload["contents"][0]["parts"][0]["text"]
    assert "TR068" in prompt
    assert "74.2%" in prompt
    assert result["answer"] == "**TR068** needs inspection."
    assert "Google Gemini AI" in result["provider"]
