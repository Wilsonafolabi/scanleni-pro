from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.schemas import OCRResponse

client = TestClient(app)

def test_health():
    assert client.get("/health").json() == {"status": "ok"}

@patch("app.ocr_engine.ocr_engine")
def test_scan_success(mock_engine):
    mock_engine.process_image.return_value = OCRResponse(status="success", data=[], count=0)
    response = client.post("/scan", files={"file": ("test.jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF", "image/jpeg")})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_scan_missing_file():
    response = client.post("/scan")
    assert response.status_code == 422
