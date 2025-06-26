"""Smoke tests for SafeStream FastAPI application.

# Requires httpx via fastapi.testclient – declared in [project.optional-dependencies].dev
"""


def test_root_endpoint(client):
    """Test that root endpoint returns HTTP 200 and correct response."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_endpoint(client):
    """Test that health endpoint returns HTTP 200 and correct response."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_openapi_docs_available(client):
    """Test that OpenAPI documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_schema_available(client):
    """Test that OpenAPI schema is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert schema["info"]["title"] == "SafeStream"


# TODO(stage-2): Add WebSocket connection tests
# def test_websocket_connection(websocket_client):
#     """Test WebSocket connection establishment."""
#     pass


# TODO(stage-4): Add gift API tests
# def test_gift_endpoint(client):
#     """Test gift endpoint functionality."""
#     pass
