from fastapi.testclient import TestClient
from app.main import app 
import pytest

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200


def test_get_services():
    response = client.get("/services")
    assert response.status_code == 401


def test_create_appointment_unauthorized():
    response = client.post("/appointments/", json={"notes": "Test randevu"})
    assert response.status_code == 401  