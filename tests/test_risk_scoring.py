from src.model.risk_scoring import calculate_risk, classify_risk, priority_for_risk


def test_risk_scoring_returns_ranked_levels():
    result = calculate_risk(0.75, 0.5, 0.4, asset_criticality=0.8, historical_risk=0.6, maintenance_condition=0.9)
    assert result['risk_level'] in {'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'}
    assert 'priority' in result
    assert classify_risk(80) == 'CRITICAL'
    assert priority_for_risk('HIGH') == 'P2 - HIGH'
