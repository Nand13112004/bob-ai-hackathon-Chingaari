from fastapi.testclient import TestClient

from src.backend.app import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_bob_query_endpoint():
    response = client.post('/api/bob/query', json={'question': 'Why is TR068 risky?'})
    assert response.status_code == 200
    assert 'answer' in response.json()
    assert 'provider' in response.json()


def test_bob_status_endpoint():
    response = client.get('/api/bob/status')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'online'
    assert 'provider' in data

