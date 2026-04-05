import pytest
import json
import numpy as np
import cv2
from httpx import AsyncClient, ASGITransport
from httpx_ws import aconnect_ws
from app.main import app


@pytest.mark.asyncio
async def test_websocket_connect_and_config():
    """Test that WebSocket accepts connection and responds to config message."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with aconnect_ws("/ws/recognize/live", client) as ws:
            await ws.send_text(json.dumps({"mode": "auto"}))
            msg = await ws.receive_text()
            data = json.loads(msg)
            assert data["type"] == "config_ack"
            assert data["mode"] == "auto"


@pytest.mark.asyncio
async def test_websocket_frame_processing():
    """Test that WebSocket processes a blank frame without error."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    frame_bytes = buf.tobytes()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with aconnect_ws("/ws/recognize/live", client) as ws:
            await ws.send_text(json.dumps({"mode": "word"}))
            await ws.receive_text()  # config_ack
            await ws.send_bytes(frame_bytes)
            # Should not raise; landmark or prediction message may follow
