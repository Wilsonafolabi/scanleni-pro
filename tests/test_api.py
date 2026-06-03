from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.schemas import TextBlock, BBox

client = TestClient(app)

def test_health():
    assert client.get("/health").json()["status"] == "ok"

@patch("app.main.ocr_engine.process_image")
def test_scan_success(mock_ocr):
    mock_ocr.return_value = [
        TextBlock(text="Water, Sugar", confidence=0.9, bbox=BBox(points=[[0,0],[10,0],[10,10],[0,10]]))
    ]
    response = client.post("/scan", files={"file": ("test.jpg", b"\xff\xd8\xff\xe0", "image/jpeg")})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["ai_analysis"]["safety_status"] == "SAFE"
