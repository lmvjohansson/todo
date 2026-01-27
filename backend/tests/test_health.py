import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint_returns_200(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "healthy"}

def test_ready_endpoint_returns_200_when_db_connected(client):
    response = client.get('/ready')
    assert response.status_code == 200
    assert response.json["status"] == "ready"
    assert response.json["database"] == "connected"