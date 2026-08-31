from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "KnowFlow AI API is running",
        "documentation": "/docs",
        "health": "/api/v1/health",
        "documents": "/api/v1/documents",
    }


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "KnowFlow AI",
        "version": "0.4.0",
        "environment": "development",
    }