# tests/test_api.py
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def test_image_file():
    return io.BytesIO(b"fake image data"), "test_image.jpg"

def test_upload_image(test_image_file):
    file_data, filename = test_image_file
    response = client.post(
        "/api/images",
        files={"file": (filename, file_data, "image/jpeg")}
    )
    assert response.status_code == 200
    json_resp = response.json()
    assert "status" in json_resp
    assert json_resp["status"] == "success"
    assert "data" in json_resp
    assert "image_id" in json_resp["data"]
    assert json_resp["data"]["original_name"] == filename

def test_list_images():
    response = client.get("/api/images")
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["status"] == "success"
    assert isinstance(json_resp["data"], list)

def test_get_image_by_id():
    file_data = io.BytesIO(b"fake image data")
    filename = "test_image.jpg"
    upload_resp = client.post(
        "/api/images",
        files={"file": (filename, file_data, "image/jpeg")}
    )
    image_id = upload_resp.json()["data"]["image_id"]

    response = client.get(f"/api/images/{image_id}")
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["status"] == "success"
    assert json_resp["data"]["image_id"] == image_id 

def test_invalid_image_id():
    response = client.get("/api/images/invalid-id")
    assert response.status_code == 404
    json_resp = response.json()
    assert json_resp["detail"] == "Image not found"

def test_get_thumbnail_invalid_size():
    file_data = io.BytesIO(b"fake image data")
    filename = "test_image.jpg"
    upload_resp = client.post(
        "/api/images",
        files={"file": (filename, file_data, "image/jpeg")}
    )
    image_id = upload_resp.json()["data"]["image_id"]

    response = client.get(f"/api/images/{image_id}/thumbnails/large")
    assert response.status_code == 400
