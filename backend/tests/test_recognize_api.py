import pytest
import numpy as np
import cv2
import io
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def sample_image_bytes():
    """Create a 640x480 black image as JPEG bytes."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "models_loaded" in data


@pytest.mark.asyncio
async def test_recognize_image_no_hand(sample_image_bytes):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/recognize/image",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            data={"mode": "auto"}
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "label" in data
    assert "confidence" in data
    assert data["landmarks_detected"] is False


@pytest.mark.asyncio
async def test_recognize_image_invalid_type():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/recognize/image",
            files={"file": ("test.txt", b"hello world", "text/plain")},
            data={"mode": "auto"}
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_vocab_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/vocab")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "words" in data
