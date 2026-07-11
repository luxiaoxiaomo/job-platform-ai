"""Health endpoint observability tests."""

import uuid


async def test_health_returns_and_propagates_request_id(client):
    request_id = str(uuid.uuid4())

    response = await client.get("/health", headers={"X-Request-ID": request_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


async def test_health_generates_request_id_when_missing(client):
    response = await client.get("/health")

    assert response.status_code == 200
    uuid.UUID(response.headers["X-Request-ID"])
